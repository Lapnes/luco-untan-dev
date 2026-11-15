from __future__ import annotations

import json
import logging
from typing import Any, Sequence

import httpx
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseAsyncGen,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.tools import BaseTool
from llama_index.llms.openai_like import OpenAILike
from pydantic import ConfigDict, Field

from .config import Settings

logger = logging.getLogger(__name__)


class ResilientBifrostTransport(httpx.AsyncHTTPTransport):
    """Transport httpx yang menangani respons syntax error / unmarshal 500 dari upstream Bifrost.
    
    Bifrost mengembalikan error unmarshal bila upstream menyisipkan marker SSE pada mode non-streaming.
    Transport ini otomatis beralih ke mode stream SSE dan merakit respons JSON standar OpenAI.
    """

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        resp = await super().handle_async_request(request)
        if resp.status_code == 500 and request.method == "POST" and b"is_bifrost_error" in (await resp.aread()):
            try:
                payload = json.loads(request.content.decode("utf-8"))
            except Exception:
                return resp

            payload["stream"] = True
            safe_headers = {k: v for k, v in request.headers.items() if k.lower() != "content-length"}
            stream_req = httpx.Request(
                method="POST",
                url=request.url,
                headers=safe_headers,
                content=json.dumps(payload).encode("utf-8"),
            )
            stream_resp = await super().handle_async_request(stream_req)
            if stream_resp.status_code == 200:
                full_content = ""
                role = "assistant"
                model = payload.get("model", "")
                tool_calls: list[dict[str, Any]] = []
                buffer = ""

                async for chunk in stream_resp.aiter_bytes():
                    buffer += chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data)
                            choices = parsed.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            if delta.get("content"):
                                full_content += delta["content"]
                            if delta.get("role"):
                                role = delta["role"]
                            if delta.get("tool_calls"):
                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", len(tool_calls))
                                    while len(tool_calls) <= idx:
                                        tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                    curr = tool_calls[idx]
                                    if tc.get("id"):
                                        curr["id"] = tc["id"]
                                    fn = tc.get("function", {})
                                    if fn.get("name"):
                                        curr["function"]["name"] += fn["name"]
                                    if fn.get("arguments"):
                                        curr["function"]["arguments"] += fn["arguments"]
                        except Exception:
                            continue

                msg: dict[str, Any] = {"role": role, "content": full_content or None}
                if tool_calls:
                    msg["tool_calls"] = tool_calls

                assembled = {
                    "id": "chatcmpl-resilient",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": msg,
                        "finish_reason": "tool_calls" if tool_calls else "stop",
                    }],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
                }
                return httpx.Response(
                    status_code=200,
                    headers={"Content-Type": "application/json"},
                    content=json.dumps(assembled).encode("utf-8"),
                    request=request,
                )
        return resp


def create_resilient_httpx_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=ResilientBifrostTransport(), timeout=60.0)


def create_sync_resilient_client() -> httpx.Client:
    return httpx.Client(timeout=60.0)


class MultiProviderLLM(FunctionCallingLLM):
    """LLM wrapper yang memprioritaskan Primary (Antigravity Proxy) dan beralih ke Fallback (Bifrost)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    primary_llm: Any = Field(description="Instance LLM utama")
    fallback_llm: Any = Field(description="Instance LLM cadangan")
    primary_name: str = Field(default="Primary")
    fallback_name: str = Field(default="Fallback")

    def __init__(
        self,
        primary_llm: Any,
        fallback_llm: Any,
        primary_name: str = "Antigravity-Proxy",
        fallback_name: str = "Bifrost-Gateway",
        **kwargs: Any,
    ):
        super().__init__(
            primary_llm=primary_llm,
            fallback_llm=fallback_llm,
            primary_name=primary_name,
            fallback_name=fallback_name,
            **kwargs,
        )

    @property
    def metadata(self) -> LLMMetadata:
        if hasattr(self.primary_llm, "metadata"):
            return self.primary_llm.metadata
        return LLMMetadata(
            context_window=32768,
            num_output=4096,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name=self.primary_name,
        )

    def get_tool_calls_from_response(
        self,
        response: ChatResponse,
        error_on_no_tool_call: bool = True,
        **kwargs: Any,
    ) -> list[Any]:
        if hasattr(self.primary_llm, "get_tool_calls_from_response"):
            try:
                return self.primary_llm.get_tool_calls_from_response(
                    response, error_on_no_tool_call=error_on_no_tool_call, **kwargs
                )
            except Exception:
                pass
        if hasattr(self.fallback_llm, "get_tool_calls_from_response"):
            return self.fallback_llm.get_tool_calls_from_response(
                response, error_on_no_tool_call=error_on_no_tool_call, **kwargs
            )
        return []

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return self.primary_llm.stream(*args, **kwargs)
        except Exception:
            return self.fallback_llm.stream(*args, **kwargs)

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return await self.primary_llm.astream(*args, **kwargs)
        except Exception:
            return await self.fallback_llm.astream(*args, **kwargs)

    def _prepare_chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> dict[str, Any]:
        return self.primary_llm._prepare_chat_with_tools(tools, **kwargs)

    async def achat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> ChatResponse:
        try:
            return await self.primary_llm.achat_with_tools(tools, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' gagal (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return await self.fallback_llm.achat_with_tools(tools, **kwargs)

    async def astream_chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> Any:
        try:
            gen = await self.primary_llm.astream_chat_with_tools(tools, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' astream_chat_with_tools gagal inisiasi (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return await self.fallback_llm.astream_chat_with_tools(tools, **kwargs)

        async def _resilient_stream():
            fallback_needed = False
            first = True
            try:
                async for chunk in gen:
                    first = False
                    yield chunk
            except Exception as e:
                if first:
                    fallback_needed = True
                    logger.warning(
                        "Primary provider '%s' astream_chat_with_tools chunk gagal (%s). Mengalihkan ke fallback '%s'...",
                        self.primary_name,
                        e,
                        self.fallback_name,
                    )
                else:
                    raise
            if fallback_needed:
                fb_gen = await self.fallback_llm.astream_chat_with_tools(tools, **kwargs)
                async for chunk in fb_gen:
                    yield chunk

        return _resilient_stream()

    def chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> ChatResponse:
        try:
            return self.primary_llm.chat_with_tools(tools, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' gagal (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return self.fallback_llm.chat_with_tools(tools, **kwargs)

    def stream_chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> Any:
        try:
            gen = self.primary_llm.stream_chat_with_tools(tools, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' gagal (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return self.fallback_llm.stream_chat_with_tools(tools, **kwargs)

        def _resilient_sync_stream():
            fallback_needed = False
            first = True
            try:
                for chunk in gen:
                    first = False
                    yield chunk
            except Exception as e:
                if first:
                    fallback_needed = True
                    logger.warning(
                        "Primary provider '%s' stream_chat_with_tools chunk gagal (%s). Mengalihkan ke fallback '%s'...",
                        self.primary_name,
                        e,
                        self.fallback_name,
                    )
                else:
                    raise
            if fallback_needed:
                for chunk in self.fallback_llm.stream_chat_with_tools(tools, **kwargs):
                    yield chunk

        return _resilient_sync_stream()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        primary = self.__dict__.get("primary_llm")
        if primary is not None and hasattr(primary, name):
            return getattr(primary, name)
        raise AttributeError(name)

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        try:
            return await self.primary_llm.achat(messages, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' gagal (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return await self.fallback_llm.achat(messages, **kwargs)

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        try:
            return self.primary_llm.chat(messages, **kwargs)
        except Exception as e:
            logger.warning(
                "Primary provider '%s' gagal (%s). Mengalihkan ke fallback '%s'...",
                self.primary_name,
                e,
                self.fallback_name,
            )
            return self.fallback_llm.chat(messages, **kwargs)

    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        try:
            return await self.primary_llm.acomplete(prompt, **kwargs)
        except Exception as e:
            logger.warning("Primary provider '%s' gagal (%s). Mengalihkan ke fallback...", self.primary_name, e)
            return await self.fallback_llm.acomplete(prompt, **kwargs)

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        try:
            return self.primary_llm.complete(prompt, **kwargs)
        except Exception as e:
            logger.warning("Primary provider '%s' gagal (%s). Mengalihkan ke fallback...", self.primary_name, e)
            return self.fallback_llm.complete(prompt, **kwargs)

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        try:
            return self.primary_llm.stream_chat(messages, **kwargs)
        except Exception:
            return self.fallback_llm.stream_chat(messages, **kwargs)

    async def astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseAsyncGen:
        try:
            return await self.primary_llm.astream_chat(messages, **kwargs)
        except Exception:
            return await self.fallback_llm.astream_chat(messages, **kwargs)

    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        try:
            return self.primary_llm.stream_complete(prompt, **kwargs)
        except Exception:
            return self.fallback_llm.stream_complete(prompt, **kwargs)

    async def astream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseAsyncGen:
        try:
            return await self.primary_llm.astream_complete(prompt, **kwargs)
        except Exception:
            return await self.fallback_llm.astream_complete(prompt, **kwargs)


def make_llm(settings: Settings) -> MultiProviderLLM | OpenAILike:
    primary_async_client = create_resilient_httpx_client()
    primary = OpenAILike(
        model=settings.llm_model,
        api_base=settings.llm_api_base,
        api_key=settings.llm_api_key or "none",
        is_chat_model=True,
        is_function_calling_model=True,
        temperature=0.2,
        max_retries=0,
        async_http_client=primary_async_client,
    )

    # Bila konfigurasi fallback tersedia dan berbeda dari primary
    has_fallback = bool(settings.llm_fallback_api_base and settings.llm_fallback_model)
    is_distinct = (
        settings.llm_fallback_api_base != settings.llm_api_base
        or settings.llm_fallback_model != settings.llm_model
    )
    if has_fallback and is_distinct:
        fallback_async_client = create_resilient_httpx_client()
        fallback = OpenAILike(
            model=settings.llm_fallback_model,
            api_base=settings.llm_fallback_api_base,
            api_key=settings.llm_fallback_api_key or "none",
            is_chat_model=True,
            is_function_calling_model=True,
            temperature=0.2,
            max_retries=2,
            async_http_client=fallback_async_client,
        )
        return MultiProviderLLM(
            primary_llm=primary,
            fallback_llm=fallback,
            primary_name=f"Primary({settings.llm_model})",
            fallback_name=f"Fallback({settings.llm_fallback_model})",
        )

    return primary
