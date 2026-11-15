from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, CompletionResponse
import pytest

from luco.config import Settings
from luco.llm import MultiProviderLLM, ResilientBifrostTransport, make_llm


@pytest.mark.asyncio
async def test_resilient_transport_passes_normal_200():
    transport = ResilientBifrostTransport()
    dummy_req = httpx.Request("POST", "https://api.example.com/v1/chat/completions", content=b'{"stream": false}')

    dummy_resp = httpx.Response(status_code=200, json={"choices": [{"message": {"content": "Halo!"}}]})

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", AsyncMock(return_value=dummy_resp)):
        resp = await transport.handle_async_request(dummy_req)
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["choices"][0]["message"]["content"] == "Halo!"


@pytest.mark.asyncio
async def test_resilient_transport_intercepts_bifrost_500_and_assembles_stream():
    transport = ResilientBifrostTransport()
    req = httpx.Request(
        "POST",
        "https://bifrost.tenzly.pro/v1/chat/completions",
        headers={"Content-Type": "application/json", "Content-Length": "50"},
        content=json.dumps({"model": "test-model", "messages": [{"role": "user", "content": "tes"}]}).encode("utf-8"),
    )

    # Respons pertama simulasi error 500 dari Bifrost
    resp_500 = httpx.Response(
        status_code=500,
        content=b'{"is_bifrost_error":true,"error":{"error":"Syntax error: data: ["}}',
    )

    # Respons kedua simulasi stream SSE sukses
    sse_lines = (
        b'data: {"choices":[{"delta":{"role":"assistant","content":"Jawaban"}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":" streaming"}}]}\n\n'
        b'data: [DONE]\n\n'
    )
    resp_stream = httpx.Response(status_code=200, content=sse_lines)

    call_count = 0

    async def mock_handle(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return resp_500
        return resp_stream

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", side_effect=mock_handle):
        result = await transport.handle_async_request(req)
        assert result.status_code == 200
        body = json.loads(result.content)
        assert body["choices"][0]["message"]["role"] == "assistant"
        assert body["choices"][0]["message"]["content"] == "Jawaban streaming"
        assert call_count == 2


@pytest.mark.asyncio
async def test_multi_provider_llm_primary_success():
    primary_mock = MagicMock()
    primary_mock.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role="assistant", content="Primary OK")))
    primary_mock.chat = MagicMock(return_value=ChatResponse(message=ChatMessage(role="assistant", content="Primary Chat OK")))

    fallback_mock = MagicMock()
    fallback_mock.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role="assistant", content="Fallback OK")))

    llm = MultiProviderLLM(primary_llm=primary_mock, fallback_llm=fallback_mock)

    # Test achat
    res_async = await llm.achat([ChatMessage(role="user", content="Halo")])
    assert res_async.message.content == "Primary OK"
    primary_mock.achat.assert_called_once()
    fallback_mock.achat.assert_not_called()

    # Test chat sync
    res_sync = llm.chat([ChatMessage(role="user", content="Halo")])
    assert res_sync.message.content == "Primary Chat OK"


@pytest.mark.asyncio
async def test_multi_provider_llm_switches_to_fallback_on_error():
    primary_mock = MagicMock()
    primary_mock.achat = AsyncMock(side_effect=RuntimeError("HTTP 429 Quota Exhausted on Primary"))
    primary_mock.chat = MagicMock(side_effect=RuntimeError("Connection refused"))
    primary_mock.acomplete = AsyncMock(side_effect=RuntimeError("500 Internal Server Error"))

    fallback_mock = MagicMock()
    fallback_mock.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role="assistant", content="Dari Fallback!")))
    fallback_mock.chat = MagicMock(return_value=ChatResponse(message=ChatMessage(role="assistant", content="Dari Fallback Sync!")))
    fallback_mock.acomplete = AsyncMock(return_value=CompletionResponse(text="Fallback Complete OK"))

    llm = MultiProviderLLM(
        primary_llm=primary_mock,
        fallback_llm=fallback_mock,
        primary_name="Antigravity",
        fallback_name="Bifrost",
    )

    # Verify achat fallback
    res = await llm.achat([ChatMessage(role="user", content="Halo")])
    assert res.message.content == "Dari Fallback!"
    primary_mock.achat.assert_called_once()
    fallback_mock.achat.assert_called_once()

    # Verify chat fallback
    res_chat = llm.chat([ChatMessage(role="user", content="Halo")])
    assert res_chat.message.content == "Dari Fallback Sync!"

    # Verify acomplete fallback
    res_comp = await llm.acomplete("Prompt tes")
    assert res_comp.text == "Fallback Complete OK"


def test_make_llm_factory_dual_provider():
    settings = Settings(
        llm_api_base="http://127.0.0.1:3000/v1",
        llm_model="antigravity-gemini-3-flash",
        llm_fallback_api_base="https://bifrost.tenzly.pro/v1",
        llm_fallback_model="yogathedev/deepseek-v4.1-flash",
    )
    llm = make_llm(settings)
    assert isinstance(llm, MultiProviderLLM)
    assert "antigravity" in llm.primary_name.lower()
    assert "deepseek" in llm.fallback_name.lower()


def test_make_llm_factory_single_provider():
    settings = Settings(
        llm_api_base="http://127.0.0.1:3000/v1",
        llm_model="antigravity-gemini-3-flash",
        llm_fallback_api_base="",
        llm_fallback_model="",
    )
    llm = make_llm(settings)
    assert not isinstance(llm, MultiProviderLLM)


@pytest.mark.asyncio
async def test_multi_provider_llm_satisfies_function_calling_interface():
    primary_mock = MagicMock()
    primary_mock.metadata = MagicMock(is_function_calling_model=True)
    fallback_mock = MagicMock()
    fallback_mock.metadata = MagicMock(is_function_calling_model=True)

    # Pastikan get_tool_calls_from_response tidak raise NotImplementedError
    primary_mock.get_tool_calls_from_response = MagicMock(return_value=[])
    fallback_mock.get_tool_calls_from_response = MagicMock(return_value=[])

    llm = MultiProviderLLM(primary_llm=primary_mock, fallback_llm=fallback_mock)
    assert llm.metadata.is_function_calling_model is True

    resp = ChatResponse(message=ChatMessage(role="assistant", content="Halo"))
    tool_calls = llm.get_tool_calls_from_response(resp, error_on_no_tool_call=False)
    assert tool_calls == []
    primary_mock.get_tool_calls_from_response.assert_called_once()


@pytest.mark.asyncio
async def test_multi_provider_llm_astream_chat_with_tools_generator_failover():
    # Simulasi kasus kritis: inisiasi generator berhasil, tapi chunk pertama raise error HTTP 403 / 500
    async def failing_generator():
        raise RuntimeError("HTTP 403 Forbidden on first streaming chunk")
        yield  # make it a generator

    async def successful_fallback_generator():
        yield ChatResponse(message=ChatMessage(role="assistant", content="Dari "))
        yield ChatResponse(message=ChatMessage(role="assistant", content="Fallback Stream!"))

    primary_mock = MagicMock()
    primary_mock.astream_chat_with_tools = AsyncMock(return_value=failing_generator())

    fallback_mock = MagicMock()
    fallback_mock.astream_chat_with_tools = AsyncMock(return_value=successful_fallback_generator())

    llm = MultiProviderLLM(primary_llm=primary_mock, fallback_llm=fallback_mock)

    stream = await llm.astream_chat_with_tools([])
    chunks = []
    async for chunk in stream:
        chunks.append(chunk.message.content)

    assert "".join(chunks) == "Dari Fallback Stream!"
    primary_mock.astream_chat_with_tools.assert_called_once()
    fallback_mock.astream_chat_with_tools.assert_called_once()


def test_multi_provider_llm_stream_chat_with_tools_sync_failover():
    def failing_sync_generator():
        raise RuntimeError("Sync stream failure")
        yield

    def successful_sync_generator():
        yield ChatResponse(message=ChatMessage(role="assistant", content="Sync Fallback"))

    primary_mock = MagicMock()
    primary_mock.stream_chat_with_tools = MagicMock(return_value=failing_sync_generator())

    fallback_mock = MagicMock()
    fallback_mock.stream_chat_with_tools = MagicMock(return_value=successful_sync_generator())

    llm = MultiProviderLLM(primary_llm=primary_mock, fallback_llm=fallback_mock)

    stream = llm.stream_chat_with_tools([])
    chunks = [c.message.content for c in stream]
    assert chunks == ["Sync Fallback"]

