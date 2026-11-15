from __future__ import annotations

import asyncio
import csv
import io
import json
from pathlib import Path
import time
from typing import Any
import uuid

import asyncpg
import tiktoken

from .config import get_settings

_encoding: Any = None


def get_token_encoder():
    global _encoding
    if _encoding is None:
        try:
            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoding = None
    return _encoding


def count_tokens(text: str) -> int:
    if not text:
        return 0
    enc = get_token_encoder()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    # Fallback aproksimasi (~4 karakter per token)
    return max(1, len(text) // 4)


MODEL_PRICING_PER_1M = {
    # Gemini Flash tier: ~$0.10 / 1M input, ~$0.40 / 1M output
    "gemini": {"prompt": 0.10, "completion": 0.40},
    "deepseek": {"prompt": 0.14, "completion": 0.28},
    "default": {"prompt": 0.15, "completion": 0.60},
}

def get_usd_to_idr() -> float:
    return get_settings().usd_to_idr


def calculate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    m = model.lower()
    rates = MODEL_PRICING_PER_1M["default"]
    for key, val in MODEL_PRICING_PER_1M.items():
        if key in m:
            rates = val
            break
    cost_prompt = (prompt_tokens / 1_000_000.0) * rates["prompt"]
    cost_comp = (completion_tokens / 1_000_000.0) * rates["completion"]
    return round(cost_prompt + cost_comp, 6)


def _safe_uuid(val: Any) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _parse_iso_datetime(val: str | datetime | None) -> datetime | None:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        clean_val = str(val).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


async def record_audit_log(
    endpoint: str,
    model: str,
    question: str,
    answer: str,
    latency_s: float,
    user_id: str | uuid.UUID | None = None,
    user_email: str | None = None,
    session_id: str | uuid.UUID | None = None,
    message_id: str | uuid.UUID | None = None,
    user_prompt_tokens: int | None = None,
    system_prompt_tokens: int | None = None,
    context_tokens: int | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    steps: int = 0,
    tool_calls: list[dict] | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
    timing_breakdown: dict | None = None,
    feedback: str | None = None,
    rejected: bool = False,
    reason: str | None = None,
    pool: asyncpg.Pool | None = None,
    log_file: Path | None = None,
) -> dict[str, Any]:
    # 1. Hitung token terperinci (Plain User Prompt vs System Prompt vs Tools Data Context vs Total Input)
    u_tokens = user_prompt_tokens if user_prompt_tokens is not None else count_tokens(question)
    s_tokens = system_prompt_tokens if system_prompt_tokens is not None else count_tokens(system_prompt or "")
    if context_tokens is not None:
        ctx_tokens = context_tokens
    else:
        ctx_tokens = sum(
            count_tokens(str(c.get("output", "") or c.get("_output", "") or ""))
            for c in (tool_calls or [])
        )
    tot_input_tokens = prompt_tokens if prompt_tokens is not None else (u_tokens + s_tokens + ctx_tokens)
    c_tokens = completion_tokens if completion_tokens is not None else count_tokens(answer)
    tot_tokens = tot_input_tokens + c_tokens
    cost_usd = calculate_cost_usd(model, tot_input_tokens, c_tokens)

    record = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "user_id": str(user_id) if user_id else None,
        "user_email": user_email,
        "session_id": str(session_id) if session_id else None,
        "message_id": str(message_id) if message_id else None,
        "endpoint": endpoint,
        "model": model,
        "question": question,
        "answer": answer,
        "user_prompt_tokens": u_tokens,
        "system_prompt_tokens": s_tokens,
        "context_tokens": ctx_tokens,
        "prompt_tokens": tot_input_tokens,
        "completion_tokens": c_tokens,
        "total_tokens": tot_tokens,
        "estimated_cost_usd": cost_usd,
        "estimated_cost_idr": round(cost_usd * get_usd_to_idr(), 2),
        "latency_s": round(latency_s, 2),
        "steps": steps,
        "tool_calls": tool_calls or [],
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "timing_breakdown": timing_breakdown or {},
        "feedback": feedback,
        "rejected": rejected,
        "reason": reason,
    }

    # 2. Simpan ke file logs/audit.jsonl secara asinkron (worker thread)
    target_file = log_file or Path(get_settings().trajectory_log).parent / "audit.jsonl"
    try:
        def _write_audit():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with target_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        await asyncio.to_thread(_write_audit)
    except Exception as e:
        print(f"[warning] Gagal menulis audit file: {e}")

    # 3. Simpan ke PostgreSQL jika pool database tersedia
    conn_to_close = None
    db_conn = None
    if pool is not None:
        try:
            db_conn = await pool.acquire()
        except Exception as e:
            print(f"[warning] Gagal acquire pool database: {e}")
    else:
        try:
            settings = get_settings()
            conn_to_close = await asyncpg.connect(settings.database_url, timeout=1.5)
            db_conn = conn_to_close
        except Exception:
            db_conn = None

    if db_conn is not None:
        try:
            await db_conn.execute(
                """
                INSERT INTO audit_logs (
                    id, user_id, user_email, session_id, message_id, endpoint, model,
                    question, answer, user_prompt_tokens, system_prompt_tokens, context_tokens,
                    prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd,
                    latency_s, steps, tool_calls, system_prompt, user_prompt, timing_breakdown, feedback,
                    rejected, reason
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8, $9, $10, $11, $12,
                    $13, $14, $15, $16,
                    $17, $18, $19::jsonb, $20, $21, $22::jsonb, $23,
                    $24, $25
                )
                """,
                _safe_uuid(record["id"]) or uuid.uuid4(),
                _safe_uuid(user_id),
                user_email,
                _safe_uuid(session_id),
                _safe_uuid(message_id),
                endpoint,
                model,
                question,
                answer,
                u_tokens,
                s_tokens,
                ctx_tokens,
                tot_input_tokens,
                c_tokens,
                tot_tokens,
                cost_usd,
                record["latency_s"],
                steps,
                json.dumps(tool_calls or []),
                system_prompt,
                user_prompt,
                json.dumps(timing_breakdown or {}),
                feedback,
                rejected,
                reason,
            )
        except Exception as e:
            print(f"[warning] Gagal insert audit ke database: {e}")
        finally:
            if pool is not None and db_conn is not None:
                await pool.release(db_conn)
            elif conn_to_close is not None:
                await conn_to_close.close()

    return record


async def get_audit_summary(
    pool: asyncpg.Pool,
    start_time: str | datetime | None = None,
    end_time: str | datetime | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    start_dt = _parse_iso_datetime(start_time)
    end_dt = _parse_iso_datetime(end_time)

    async with pool.acquire() as conn:
        conditions = []
        params = []

        if start_dt:
            params.append(start_dt)
            conditions.append(f"created_at >= ${len(params)}")
        if end_dt:
            params.append(end_dt)
            conditions.append(f"created_at <= ${len(params)}")
        if model and model != "all":
            params.append(f"%{model}%")
            conditions.append(f"model ILIKE ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        row = await conn.fetchrow(
            f"""
            SELECT
                COUNT(*) AS total_requests,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(DISTINCT session_id) AS total_sessions,
                COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(estimated_cost_usd), 0) AS total_cost_usd,
                COALESCE(AVG(latency_s), 0) AS avg_latency_s,
                COUNT(*) FILTER (WHERE rejected = TRUE) AS total_rejected
            FROM audit_logs
            {where_clause}
            """,
            *params,
        )
        data = dict(row)
        total_req = data["total_requests"]
        data["rejection_rate_percent"] = (
            round((data["total_rejected"] / total_req * 100), 2) if total_req > 0 else 0.0
        )
        data["total_cost_usd"] = float(data["total_cost_usd"])
        data["total_cost_idr"] = round(data["total_cost_usd"] * get_usd_to_idr(), 2)
        data["avg_latency_s"] = round(float(data["avg_latency_s"]), 2)

        # Breakdown per model (menghormati filter rentang waktu)
        time_conditions = []
        time_params = []
        if start_dt:
            time_params.append(start_dt)
            time_conditions.append(f"created_at >= ${len(time_params)}")
        if end_dt:
            time_params.append(end_dt)
            time_conditions.append(f"created_at <= ${len(time_params)}")
        time_where = f"WHERE {' AND '.join(time_conditions)}" if time_conditions else ""

        model_rows = await conn.fetch(
            f"""
            SELECT 
                model, 
                COUNT(*) AS requests, 
                COALESCE(SUM(total_tokens), 0) AS tokens,
                COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                COALESCE(SUM(estimated_cost_usd), 0) AS cost_usd,
                COALESCE(AVG(latency_s), 0) AS avg_latency_s,
                COUNT(*) FILTER (WHERE rejected = TRUE) AS errors
            FROM audit_logs
            {time_where}
            GROUP BY model ORDER BY requests DESC
            """,
            *time_params,
        )
        data["models"] = [
            {
                "model": r["model"],
                "requests": r["requests"],
                "tokens": r["tokens"],
                "prompt_tokens": r["prompt_tokens"],
                "completion_tokens": r["completion_tokens"],
                "cost_usd": float(r["cost_usd"]),
                "cost_idr": round(float(r["cost_usd"]) * get_usd_to_idr(), 2),
                "avg_latency_s": round(float(r["avg_latency_s"]), 2),
                "errors": r["errors"],
            }
            for r in model_rows
        ]
        return data


async def query_audit_logs(
    pool: asyncpg.Pool,
    user_id: str | uuid.UUID | None = None,
    model: str | None = None,
    start_time: str | datetime | None = None,
    end_time: str | datetime | None = None,
    limit: int = 500,
    offset: int = 0,
    return_total: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], int]:
    start_dt = _parse_iso_datetime(start_time)
    end_dt = _parse_iso_datetime(end_time)

    async with pool.acquire() as conn:
        conditions = []
        params = []

        if user_id:
            params.append(uuid.UUID(str(user_id)))
            conditions.append(f"user_id = ${len(params)}")

        if model and model != "all":
            params.append(f"%{model}%")
            conditions.append(f"model ILIKE ${len(params)}")

        if start_dt:
            params.append(start_dt)
            conditions.append(f"created_at >= ${len(params)}")

        if end_dt:
            params.append(end_dt)
            conditions.append(f"created_at <= ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total_count = 0
        if return_total:
            count_query = f"SELECT COUNT(*) FROM audit_logs {where_clause}"
            total_count = await conn.fetchval(count_query, *params)

        params.append(limit)
        limit_param = f"${len(params)}"
        params.append(offset)
        offset_param = f"${len(params)}"

        query = f"""
            SELECT id, created_at, user_id, user_email, session_id, message_id, endpoint, model,
                   question, answer, user_prompt_tokens, system_prompt_tokens, context_tokens,
                   prompt_tokens, completion_tokens, total_tokens,
                   estimated_cost_usd, latency_s, steps, tool_calls, system_prompt, user_prompt,
                   timing_breakdown, feedback, rejected, reason
            FROM audit_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """

        rows = await conn.fetch(query, *params)
        res = []
        for r in rows:
            d = dict(r)
            d["estimated_cost_usd"] = float(d["estimated_cost_usd"])
            d["estimated_cost_idr"] = round(d["estimated_cost_usd"] * get_usd_to_idr(), 2)
            d["id"] = str(d["id"])
            if d.get("user_id"):
                d["user_id"] = str(d["user_id"])
            if d.get("session_id"):
                d["session_id"] = str(d["session_id"])
            if d.get("message_id"):
                d["message_id"] = str(d["message_id"])
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()

            # Decode JSONB jika string
            if isinstance(d.get("tool_calls"), str):
                try:
                    d["tool_calls"] = json.loads(d["tool_calls"])
                except Exception:
                    d["tool_calls"] = []
            if isinstance(d.get("timing_breakdown"), str):
                try:
                    d["timing_breakdown"] = json.loads(d["timing_breakdown"])
                except Exception:
                    d["timing_breakdown"] = {}

            res.append(d)

        if return_total:
            return res, total_count
        return res


async def export_audit_csv(
    pool: asyncpg.Pool,
    model: str | None = None,
    start_time: str | datetime | None = None,
    end_time: str | datetime | None = None,
) -> str:
    logs = await query_audit_logs(
        pool,
        model=model,
        start_time=start_time,
        end_time=end_time,
        limit=10000,
        offset=0,
        return_total=False,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "timestamp", "user_email", "endpoint", "model",
        "question", "prompt_tokens", "completion_tokens", "total_tokens",
        "cost_usd", "cost_idr", "latency_s", "steps", "feedback", "rejected", "reason"
    ])
    for l in logs:
        writer.writerow([
            l["id"], l["created_at"], l.get("user_email") or "-", l["endpoint"], l["model"],
            l["question"].replace("\n", " "), l["prompt_tokens"], l["completion_tokens"], l["total_tokens"],
            l["estimated_cost_usd"], l["estimated_cost_idr"], l["latency_s"], l["steps"], l.get("feedback") or "-", l["rejected"], l.get("reason") or "-"
        ])
    return output.getvalue()
