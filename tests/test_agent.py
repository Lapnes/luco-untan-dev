from typing import Any, Sequence
import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, LLMMetadata
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.llms.llm import ToolSelection
from llama_index.core.tools import BaseTool

from luco.agent import Luco
from luco.backends import LocalBackend
from luco.config import Settings


class AuthenticTestLLM(FunctionCallingLLM):
    """LLM pengujian otentik yang menjalankan alur FunctionAgent sesungguhnya tanpa mem-bypass FunctionAgent."""
    model_config = {"arbitrary_types_allowed": True}
    step: int = 0
    fail_on_purpose: bool = False

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=4096,
            num_output=1024,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name="AuthenticTestLLM",
        )

    def _prepare_chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> dict[str, Any]:
        return {}

    async def astream_chat_with_tools(self, tools: Sequence[BaseTool], **kwargs: Any) -> Any:
        if self.fail_on_purpose:
            raise RuntimeError("Simulasi kegagalan koneksi provider LLM")

        self.step += 1
        if self.step == 1:
            # Langkah 1: Model memicu pemanggilan tool cari_profil_dosen
            tc = {
                "id": "call_test_1",
                "type": "function",
                "function": {"name": "cari_profil_dosen", "arguments": {"query": "Herry Sujaini"}},
            }
            resp = ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content="",
                    additional_kwargs={"tool_calls": [tc]},
                )
            )
        else:
            # Langkah 2: Model mensintesis jawaban akhir beserta sitasi valid
            resp = ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=(
                        "NIP Prof. Dr. Herry Sujaini adalah 196806291997021001.\n"
                        "Sumber:\n- [Profil Dosen](https://informatika.untan.ac.id)"
                    ),
                )
            )

        async def _gen():
            yield resp

        return _gen()

    def get_tool_calls_from_response(
        self,
        response: ChatResponse,
        error_on_no_tool_call: bool = True,
        **kwargs: Any,
    ) -> list[ToolSelection]:
        tool_calls = response.message.additional_kwargs.get("tool_calls", [])
        if not tool_calls:
            if error_on_no_tool_call:
                raise ValueError("Expected at least one tool call")
            return []

        return [
            ToolSelection(
                tool_id=tc["id"],
                tool_name=tc["function"]["name"],
                tool_kwargs=tc["function"]["arguments"],
            )
            for tc in tool_calls
        ]

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        return ChatResponse(message=ChatMessage(role="assistant", content="dummy"))

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        return ChatResponse(message=ChatMessage(role="assistant", content="dummy"))

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        return None

    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        return None

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> Any:
        return None

    async def astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> Any:
        return None

    def stream_complete(self, prompt: str, **kwargs: Any) -> Any:
        return None

    async def astream_complete(self, prompt: str, **kwargs: Any) -> Any:
        return None


@pytest.mark.asyncio
async def test_luco_ask_fast_reject():
    # Menguji jalur upfront router tanpa LLM
    luco = Luco(settings=Settings(backend="local"), backend=LocalBackend(Settings()))
    res = await luco.ask("Saya ingin memberikan saran dan kritik untuk lab prodi", use_router=True, log=False)
    assert res["rejected"] is True
    assert res["reason"] == "contact_redirect"
    assert "kontak resmi" in res["answer"].lower()
    assert res["steps"] == 0


@pytest.mark.asyncio
async def test_luco_ask_agent_run_success():
    # Eksekusi FunctionAgent sesungguhnya (bukan mock поверхностный / surface mock)
    # Ini menjamin jika ada method FunctionCallingLLM yang hilang atau raise NotImplementedError, tes akan langsung gagal!
    test_llm = AuthenticTestLLM()
    luco = Luco(settings=Settings(backend="local"), backend=LocalBackend(Settings()))
    luco.llm = test_llm

    res = await luco.ask("Siapa NIP Prof Herry Sujaini?", use_router=False, log=False)

    assert res["rejected"] is False
    assert res["error"] is None
    assert res["steps"] == 1
    assert "196806291997021001" in res["answer"]
    assert res["trajectory"][0]["tool"] == "cari_profil_dosen"
    assert res["citations"]["has_citations"] is True
    assert res["citations"]["all_verified"] is True


@pytest.mark.asyncio
async def test_luco_ask_agent_run_exception_fallback():
    # Menguji penanganan error graceful saat LLM gagal di tengah jalan
    failing_llm = AuthenticTestLLM(fail_on_purpose=True)
    luco = Luco(settings=Settings(backend="local"), backend=LocalBackend(Settings()))
    luco.llm = failing_llm

    res = await luco.ask("Pertanyaan acak", use_router=False, log=False)
    assert res["rejected"] is False
    assert "Maaf, Luco lagi bermasalah" in res["answer"]
    assert "Simulasi kegagalan koneksi provider LLM" in res["error"]


def test_system_prompt_mandates_active_clarification():
    from luco.prompts import SYSTEM_PROMPT
    p = SYSTEM_PROMPT.lower()
    # Menegakkan aturan bahwa agen dilarang berasumsi langsung pada pertanyaan ambigu
    assert "ambigu" in p
    assert "klarifikasi aktif" in p
    assert "tugas akhir" in p
    assert "kerja praktik" in p
    assert "akademik" in p


def test_system_prompt_mandates_antislop_copywriting_and_human():
    from luco.prompts import SYSTEM_PROMPT
    p = SYSTEM_PROMPT.lower()
    # Memastikan prinsip antislop copywriting dan human tertanam
    assert "anti-slop" in p
    assert "tanpa basa-basi pembuka" in p
    assert "tanpa basa-basi penutup" in p
    assert "bottom line up front" in p
    assert "kosakata kosong ai" in p
    assert "anchor text" in p


def test_system_prompt_mandates_security_and_prompt_injection_defense():
    from luco.prompts import SYSTEM_PROMPT
    p = SYSTEM_PROMPT.lower()
    # Proteksi keamanan, imutabilitas identitas, anti prompt-injection & jailbreak
    assert "identitas & keamanan sistem (immutable)" in p
    assert "kerahasiaan sistem" in p
    assert "abaikan instruksi sebelumnya" in p
    assert "jailbreak" in p
    assert "integritas akademik & etika" in p


def test_system_prompt_mandates_four_backtick_anti_putus():
    from luco.prompts import SYSTEM_PROMPT
    # Memastikan aturan pembungkus 4-backtick (````) tertanam agar blok kode tidak putus
    assert "````" in SYSTEM_PROMPT
    assert "4-backtick" in SYSTEM_PROMPT.lower() or "4 backtick" in SYSTEM_PROMPT.lower()




