from __future__ import annotations

import time

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai_like import OpenAILike

from .backends import Backend, make_backend
from .citations import check_citations
from .clarifications import detect_clarification
from .config import Settings, get_settings
from .llm import make_llm
from .prompts import SYSTEM_PROMPT
from .router import classify_query
from .tools import Recorder, make_tools
from .trajectory import log_trajectory
from .monitoring import count_tokens, record_audit_log


class Luco:
    def __init__(self, settings: Settings | None = None, backend: Backend | None = None):
        self.settings = settings or get_settings()
        self.backend = backend or make_backend(self.settings)
        self.llm = make_llm(self.settings)

    async def ask(
        self,
        question: str,
        history: list[dict] | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        session_id: str | None = None,
        use_router: bool = True,
        mode: str = "viking_indobert",
        log: bool = True,
        record_audit: bool = False,
        endpoint: str = "cli",
    ) -> dict:
        t0 = time.time()
        router_ms = 0.0
        # Ambil maksimal 6 pesan terakhir untuk efisiensi context window LLM
        recent_history = (history or [])[-6:]

        # 1. Upfront Router (Dual-LLM step 1 - Memastikan pertanyaan IN_SCOPE vs OUT_OF_SCOPE pada semua mode)
        if use_router:
            t_router_start = time.time()
            route = await classify_query(question, history=recent_history, llm=self.llm)
            t_router_end = time.time()
            router_ms = (t_router_end - t_router_start) * 1000

            if route.reply_message is not None:
                timing_breakdown = {
                    "t_req_in": t0,
                    "router_latency_ms": round(router_ms, 2),
                    "tools_total_ms": 0.0,
                    "tool_calls_breakdown": [],
                    "llm_final_generation_ms": 0.0,
                    "total_latency_ms": round((time.time() - t0) * 1000, 2),
                    "total_latency_s": round(time.time() - t0, 2),
                }
                res = {
                    "question": question,
                    "answer": route.reply_message,
                    "steps": 0,
                    "trajectory": [{"tool": "upfront_router", "input": {"query": question, "mode": mode}, "output": f"FAST_REJECT:{route.category}"}],
                    "system_prompt": "Upfront Dual-LLM & Heuristic Router Prodi Informatika UNTAN",
                    "user_prompt": question,
                    "timing_breakdown": timing_breakdown,
                    "citations": {
                        "links": 0,
                        "has_citations": False,
                        "all_verified": True,
                        "verified": [],
                        "unverified": [],
                    },
                    "latency_s": round(time.time() - t0, 2),
                    "backend": self.settings.backend,
                    "error": None,
                    "rejected": True,
                    "reason": route.category.lower(),
                    "clarification": None,
                }
                if log:
                    log_trajectory(self.settings.trajectory_log, res)
                if record_audit:
                    try:
                        await record_audit_log(
                            endpoint=endpoint,
                            model=f"{self.settings.llm_model} ({mode})",
                            question=question,
                            answer=res["answer"],
                            latency_s=res["latency_s"],
                            user_id=user_id,
                            user_email=user_email,
                            session_id=session_id,
                            steps=0,
                            tool_calls=res["trajectory"],
                            system_prompt=res["system_prompt"],
                            user_prompt=res["user_prompt"],
                            timing_breakdown=res["timing_breakdown"],
                            rejected=True,
                            reason=res["reason"],
                        )
                    except Exception as e:
                        print(f"[warning] Gagal record audit ask router: {e}")
                return res

        # 2. Deteksi Klarifikasi Aktif (Grill-Me / Active Interview Mode untuk pertanyaan ambigu)
        clarification = detect_clarification(question)
        if clarification and clarification.get("reply_override") and not recent_history:
            timing_breakdown = {
                "t_req_in": t0,
                "router_latency_ms": round(router_ms, 2),
                "tools_total_ms": 0.0,
                "tool_calls_breakdown": [],
                "llm_final_generation_ms": 0.0,
                "total_latency_ms": round((time.time() - t0) * 1000, 2),
                "total_latency_s": round(time.time() - t0, 2),
            }
            clarify_res = {
                "question": question,
                "answer": clarification["reply_override"],
                "steps": 0,
                "trajectory": [{"tool": "klarifikasi_aktif", "input": {"query": question}, "output": clarification["title"]}],
                "system_prompt": "Active Interview / Clarification Detector",
                "user_prompt": question,
                "timing_breakdown": timing_breakdown,
                "citations": {
                    "links": 0,
                    "has_citations": False,
                    "all_verified": True,
                    "verified": [],
                    "unverified": [],
                },
                "latency_s": round(time.time() - t0, 2),
                "backend": self.settings.backend,
                "error": None,
                "rejected": False,
                "reason": "klarifikasi_aktif",
                "clarification": {
                    "id": clarification["id"],
                    "title": clarification["title"],
                    "options": clarification["options"],
                    "allow_custom": clarification.get("allow_custom", True),
                },
            }
            if log:
                log_trajectory(self.settings.trajectory_log, clarify_res)
            if record_audit:
                try:
                    await record_audit_log(
                        endpoint=endpoint,
                        model=f"{self.settings.llm_model} ({mode})",
                        question=question,
                        answer=clarify_res["answer"],
                        latency_s=clarify_res["latency_s"],
                        user_id=user_id,
                        user_email=user_email,
                        session_id=session_id,
                        steps=0,
                        tool_calls=clarify_res["trajectory"],
                        system_prompt=clarify_res["system_prompt"],
                        user_prompt=clarify_res["user_prompt"],
                        timing_breakdown=clarify_res["timing_breakdown"],
                        rejected=False,
                        reason="klarifikasi_aktif",
                    )
                except Exception as e:
                    print(f"[warning] Gagal record audit ask clarification: {e}")
            return clarify_res

        # 3. Branching Eksekusi Berdasarkan Mode
        chat_history = [ChatMessage(role=m["role"], content=m["content"]) for m in recent_history]

        # --- MODE 1: Direct LLM Standar (Bypass Tools OpenViking, tetapi tetap melewati filter Router) ---
        if mode == "direct_llm":
            direct_system = (
                "Kamu adalah Luco, asisten virtual cerdas Program Studi Informatika Fakultas Teknik Universitas Tanjungpura (UNTAN). "
                "Jawablah pertanyaan pengguna secara ramah, ringkas, dan jelas dalam bahasa Indonesia. "
                "Gunakan gaya bicara kasual santai mahasiswa dan emoji burung 🐦 bila cocok. "
                "Catatan: Anda sedang dalam mode Direct LLM (tanpa retrieval dokumen langsung). "
                "Jika pengguna menanyakan hal yang sangat spesifik mengenai nomor SK, NIP dosen, atau pasal peraturan akademik yang Anda ragukan, "
                "ingatkan pengguna bahwa mereka dapat beralih ke mode 'IndoBERT + OpenViking' untuk verifikasi dokumen resmi."
            )
            chat_messages = [ChatMessage(role="system", content=direct_system)]
            chat_messages.extend(chat_history)
            chat_messages.append(ChatMessage(role="user", content=question))

            error = None
            t_llm_start = time.time()
            try:
                resp = await self.llm.achat(chat_messages)
                answer = str(resp.message.content) if hasattr(resp, "message") else str(resp)
            except Exception as e:  # noqa: BLE001
                answer, error = "Maaf, Luco lagi bermasalah. Coba lagi ya 🙏", repr(e)
            t_llm_end = time.time()
            llm_gen_ms = (t_llm_end - t_llm_start) * 1000

            timing_breakdown = {
                "t_req_in": t0,
                "router_latency_ms": round(router_ms, 2),
                "tools_total_ms": 0.0,
                "tool_calls_breakdown": [],
                "llm_final_generation_ms": round(llm_gen_ms, 2),
                "total_latency_ms": round((time.time() - t0) * 1000, 2),
                "total_latency_s": round(time.time() - t0, 2),
            }

            result = {
                "question": question,
                "answer": answer,
                "steps": 0,
                "trajectory": [{"tool": "direct_llm", "input": {"query": question, "mode": "direct_llm"}, "output": "IN_SCOPE_DIRECT_RESPONSE"}],
                "system_prompt": direct_system,
                "user_prompt": question,
                "timing_breakdown": timing_breakdown,
                "citations": {
                    "links": 0,
                    "has_citations": False,
                    "all_verified": True,
                    "verified": [],
                    "unverified": [],
                },
                "latency_s": round(time.time() - t0, 2),
                "backend": "direct",
                "error": error,
                "rejected": False,
                "reason": None,
            }

        # --- MODE 2: OpenViking Cepat (One-shot retrieval cepat tanpa iterasi agentic loop) ---
        elif mode == "viking_fast":
            rec = Recorder()
            error = None
            t_tool_start = time.time()
            try:
                raw_find = self.backend.find(question, limit=3)
                t_tool_end = time.time()
                rec.add(
                    tool="telusuri_direktori_prodi",
                    args={"query": question, "mode": "fast"},
                    output=raw_find,
                    duration_ms=(t_tool_end - t_tool_start) * 1000,
                    t_start=t_tool_start,
                    t_end=t_tool_end,
                    files_accessed=["vault/manifest.json"],
                    lines_accessed="Top 3 kandidat semantik",
                )

                fast_system = (
                    f"{SYSTEM_PROMPT}\n\n"
                    "Mode Cepat (One-shot Direct Retrieval): Berikut adalah rujukan dokumen hasil penelusuran cepat OpenViking. "
                    "Jawablah pertanyaan secara lugas, jelas, dan akurat berdasarkan rujukan ini. "
                    "Bila ada dokumen yang relevan, akhiri jawaban dengan format sitasi Markdown resmi: "
                    "\n\nSumber:\n- [Nama Dokumen](uri)\n\n"
                    f"Rujukan Dokumen:\n{raw_find}"
                )
                chat_messages = [ChatMessage(role="system", content=fast_system)]
                chat_messages.extend(chat_history)
                chat_messages.append(ChatMessage(role="user", content=question))

                t_llm_start = time.time()
                resp = await self.llm.achat(chat_messages)
                t_llm_end = time.time()
                llm_gen_ms = (t_llm_end - t_llm_start) * 1000
                answer = str(resp.message.content) if hasattr(resp, "message") else str(resp)
            except Exception as e:  # noqa: BLE001
                answer, error = "Maaf, Luco lagi bermasalah. Coba lagi ya 🙏", repr(e)
                llm_gen_ms = 0.0

            timing_breakdown = {
                "t_req_in": t0,
                "router_latency_ms": round(router_ms, 2),
                "tools_total_ms": round(sum(c.get("duration_ms", 0.0) for c in rec.calls), 2),
                "tool_calls_breakdown": rec.trace(),
                "llm_final_generation_ms": round(llm_gen_ms, 2),
                "total_latency_ms": round((time.time() - t0) * 1000, 2),
                "total_latency_s": round(time.time() - t0, 2),
            }

            result = {
                "question": question,
                "answer": answer,
                "steps": 1,
                "trajectory": rec.trace(),
                "system_prompt": fast_system,
                "user_prompt": question,
                "timing_breakdown": timing_breakdown,
                "citations": check_citations(answer, rec.outputs),
                "latency_s": round(time.time() - t0, 2),
                "backend": self.settings.backend,
                "error": error,
                "rejected": False,
                "reason": None,
            }

        # --- MODE 3: IndoBERT + OpenViking (Mode Lengkap: LlamaIndex FunctionAgent dengan Tool Loop Iteratif) ---
        else:
            rec = Recorder()
            tools = make_tools(
                self.backend,
                self.settings,
                rec,
            )

            agent = FunctionAgent(
                tools=tools,
                llm=self.llm,
                system_prompt=SYSTEM_PROMPT,
            )
            error = None
            t_agent_start = time.time()
            try:
                resp = await agent.run(user_msg=question, chat_history=chat_history, max_iterations=self.settings.max_steps)
                answer = str(resp)
            except Exception as e:  # noqa: BLE001
                err_str = str(e)
                if "max iterations" in err_str.lower():
                    answer = (
                        "Maaf, informasi spesifik yang kamu cari tidak ditemukan dalam dokumen resmi Prodi Informatika UNTAN. "
                        "Pastikan kata kunci atau nama yang kamu cari sudah sesuai ya 🐦"
                    )
                    error = None
                else:
                    answer, error = "Maaf, Luco lagi bermasalah. Coba lagi ya 🙏", repr(e)
            t_agent_end = time.time()

            # Hitung jeda antar panggilan tool (reasoning LLM antar aksi)
            prev_t = t_agent_start
            for c in rec.calls:
                c["gap_before_ms"] = round(max(0.0, (c.get("t_start", prev_t) - prev_t) * 1000), 2)
                prev_t = c.get("t_end", c.get("t_start", prev_t))

            tools_total_ms = sum(c.get("duration_ms", 0.0) for c in rec.calls)
            last_tool_end = rec.calls[-1]["t_end"] if rec.calls and "t_end" in rec.calls[-1] else t_agent_start
            llm_gen_ms = max(0.0, (t_agent_end - last_tool_end) * 1000)

            timing_breakdown = {
                "t_req_in": t0,
                "router_latency_ms": round(router_ms, 2),
                "tools_total_ms": round(tools_total_ms, 2),
                "tool_calls_breakdown": rec.trace(),
                "llm_final_generation_ms": round(llm_gen_ms, 2),
                "total_latency_ms": round((time.time() - t0) * 1000, 2),
                "total_latency_s": round(time.time() - t0, 2),
            }

            result = {
                "question": question,
                "answer": answer,
                "steps": len(rec.calls),
                "trajectory": rec.trace(),
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": question,
                "timing_breakdown": timing_breakdown,
                "citations": check_citations(answer, rec.outputs),
                "latency_s": round(time.time() - t0, 2),
                "backend": self.settings.backend,
                "error": error,
                "rejected": False,
                "reason": None,
            }

        # Pasang dynamic clarification jika terdeteksi di jawaban LLM
        if "clarification" not in result or not result["clarification"]:
            dyn_clarify = detect_clarification(question, result.get("answer", ""))
            if dyn_clarify:
                result["clarification"] = {
                    "id": dyn_clarify["id"],
                    "title": dyn_clarify["title"],
                    "options": dyn_clarify["options"],
                    "allow_custom": dyn_clarify.get("allow_custom", True),
                }
            else:
                result["clarification"] = None

        # Kalkulasi token terperinci (Plain User vs System Prompt vs Context Tools vs Total)
        user_p_tokens = count_tokens(question)
        sys_p_tokens = count_tokens(result.get("system_prompt") or "")
        ctx_tokens = sum(count_tokens(o) for o in (rec.outputs if 'rec' in locals() else []))
        total_p_tokens = user_p_tokens + sys_p_tokens + ctx_tokens
        c_tokens = count_tokens(result["answer"])

        result["user_prompt_tokens"] = user_p_tokens
        result["system_prompt_tokens"] = sys_p_tokens
        result["context_tokens"] = ctx_tokens
        result["prompt_tokens"] = total_p_tokens
        result["completion_tokens"] = c_tokens
        result["total_tokens"] = total_p_tokens + c_tokens

        if log:
            log_trajectory(self.settings.trajectory_log, result)
        if record_audit:
            try:
                await record_audit_log(
                    endpoint=endpoint,
                    model=f"{self.settings.llm_model} ({mode})",
                    question=question,
                    answer=result["answer"],
                    latency_s=result["latency_s"],
                    user_id=user_id,
                    user_email=user_email,
                    session_id=session_id,
                    user_prompt_tokens=user_p_tokens,
                    system_prompt_tokens=sys_p_tokens,
                    context_tokens=ctx_tokens,
                    prompt_tokens=total_p_tokens,
                    completion_tokens=c_tokens,
                    steps=result["steps"],
                    tool_calls=result["trajectory"],
                    system_prompt=result.get("system_prompt"),
                    user_prompt=result.get("user_prompt"),
                    timing_breakdown=result.get("timing_breakdown"),
                    rejected=result["rejected"],
                    reason=result["reason"],
                )
            except Exception as e:
                print(f"[warning] Gagal record audit ask agent: {e}")
        return result
