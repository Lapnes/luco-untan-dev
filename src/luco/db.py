from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
import uuid

import asyncpg

from .config import get_settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    current_loop = asyncio.get_running_loop()
    if _pool is None or _pool._loop.is_closed() or _pool._loop is not current_loop:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=1,
            max_size=10,
        )
    return _pool


async def set_pool(pool: asyncpg.Pool | None) -> None:
    global _pool
    _pool = pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db(pool: asyncpg.Pool | None = None) -> None:
    p = pool or await get_pool()
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    async with p.acquire() as conn:
        await conn.execute(sql)
        # Migrasi safe untuk database yang sudah running sebelumnya
        await conn.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_session_per_user ON chat_sessions(user_id) WHERE (is_active = true);")
        await conn.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS clarification JSONB;")
        await conn.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS feedback VARCHAR(10);")
        await conn.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS system_prompt TEXT;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_prompt TEXT;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS timing_breakdown JSONB DEFAULT '{}'::jsonb;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS feedback VARCHAR(10);")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_prompt_tokens INT DEFAULT 0;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS system_prompt_tokens INT DEFAULT 0;")
        await conn.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS context_tokens INT DEFAULT 0;")


# --- User Operations ---


async def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    nim_or_nip: str | None = None,
    angkatan: int | None = None,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, full_name, nim_or_nip, angkatan)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, email, full_name, nim_or_nip, angkatan, created_at
            """,
            email,
            password_hash,
            full_name,
            nim_or_nip,
            angkatan,
        )
        return dict(row)


async def get_user_by_email(email: str, pool: asyncpg.Pool | None = None) -> dict[str, Any] | None:
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return dict(row) if row else None


async def get_user_by_id(user_id: str | uuid.UUID, pool: asyncpg.Pool | None = None) -> dict[str, Any] | None:
    try:
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return None
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email, full_name, nim_or_nip, angkatan, created_at FROM users WHERE id = $1", u_uuid)
        return dict(row) if row else None


# --- Session Operations (Single Active Session with Archiving) ---


async def get_active_session(
    user_id: str | uuid.UUID,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any] | None:
    """Ambil satu-satunya sesi yang berstatus is_active = true untuk user ini."""
    try:
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return None
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, title, is_active, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = $1 AND is_active = true
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            u_uuid,
        )
        return dict(row) if row else None


async def create_active_session(
    user_id: str | uuid.UUID,
    title: str = "Percakapan Baru",
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Arsipkan sesi aktif saat ini (is_active = false) dan buat sesi baru dengan is_active = true."""
    try:
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid user_id UUID: {user_id}")
    p = pool or await get_pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            # Nonaktifkan semua sesi aktif sebelumnya milik user ini
            await conn.execute(
                "UPDATE chat_sessions SET is_active = false WHERE user_id = $1 AND is_active = true",
                u_uuid,
            )
            row = await conn.fetchrow(
                """
                INSERT INTO chat_sessions (user_id, title, is_active)
                VALUES ($1, $2, true)
                RETURNING id, user_id, title, is_active, created_at, updated_at
                """,
                u_uuid,
                title,
            )
            return dict(row)


async def get_or_create_active_session(
    user_id: str | uuid.UUID,
    title: str = "Percakapan Baru",
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Kembalikan sesi aktif pengguna. Jika belum ada, otomatis buat sesi baru."""
    active = await get_active_session(user_id, pool=pool)
    if active is not None:
        return active
    return await create_active_session(user_id, title=title, pool=pool)


async def clear_and_create_active_session(
    user_id: str | uuid.UUID,
    title: str = "Percakapan Baru",
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Clear chat: Arsipkan sesi aktif saat ini dan mulai kanvas bersih yang baru."""
    return await create_active_session(user_id, title=title, pool=pool)


async def switch_active_session(
    session_id: str | uuid.UUID,
    user_id: str | uuid.UUID,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any] | None:
    """Ubah status sesi lama menjadi aktif (is_active = true) dan nonaktifkan sesi lainnya."""
    try:
        s_uuid = uuid.UUID(str(session_id))
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return None
    p = pool or await get_pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            # Verifikasi keberadaan sesi
            target = await conn.fetchrow(
                "SELECT id FROM chat_sessions WHERE id = $1 AND user_id = $2",
                s_uuid,
                u_uuid,
            )
            if not target:
                return None
            # Nonaktifkan semua sesi aktif milik user ini
            await conn.execute(
                "UPDATE chat_sessions SET is_active = false WHERE user_id = $1",
                u_uuid,
            )
            # Aktifkan sesi target
            row = await conn.fetchrow(
                """
                UPDATE chat_sessions
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND user_id = $2
                RETURNING id, user_id, title, is_active, created_at, updated_at
                """,
                s_uuid,
                u_uuid,
            )
            return dict(row) if row else None


async def create_session(
    user_id: str | uuid.UUID,
    title: str = "Percakapan Baru",
    is_active: bool = True,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Helper kompatibilitas untuk membuat sesi baru."""
    if is_active:
        return await create_active_session(user_id, title, pool=pool)
    try:
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid user_id UUID: {user_id}")
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO chat_sessions (user_id, title, is_active)
            VALUES ($1, $2, false)
            RETURNING id, user_id, title, is_active, created_at, updated_at
            """,
            u_uuid,
            title,
        )
        return dict(row)


async def list_sessions(user_id: str | uuid.UUID, pool: asyncpg.Pool | None = None) -> list[dict[str, Any]]:
    """Daftar seluruh sesi percakapan milik pengguna (aktif maupun arsip)."""
    try:
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return []
    p = pool or await get_pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, title, is_active, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = $1
            ORDER BY is_active DESC, updated_at DESC
            """,
            u_uuid,
        )
        return [dict(r) for r in rows]


async def get_session(
    session_id: str | uuid.UUID,
    user_id: str | uuid.UUID,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any] | None:
    try:
        s_uuid = uuid.UUID(str(session_id))
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return None
    p = pool or await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, title, is_active, created_at, updated_at
            FROM chat_sessions
            WHERE id = $1 AND user_id = $2
            """,
            s_uuid,
            u_uuid,
        )
        return dict(row) if row else None


async def update_session_title(
    session_id: str | uuid.UUID,
    title: str,
    pool: asyncpg.Pool | None = None,
) -> bool:
    try:
        s_uuid = uuid.UUID(str(session_id))
    except (ValueError, AttributeError):
        return False
    p = pool or await get_pool()
    async with p.acquire() as conn:
        res = await conn.execute(
            """
            UPDATE chat_sessions
            SET title = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """,
            title,
            s_uuid,
        )
        return "UPDATE 1" in res


async def delete_session(
    session_id: str | uuid.UUID,
    user_id: str | uuid.UUID,
    pool: asyncpg.Pool | None = None,
) -> bool:
    try:
        s_uuid = uuid.UUID(str(session_id))
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return False
    p = pool or await get_pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "DELETE FROM chat_sessions WHERE id = $1 AND user_id = $2 RETURNING is_active",
                s_uuid,
                u_uuid,
            )
            if not row:
                return False
            # Jika sesi yang dihapus adalah sesi aktif, aktifkan sesi terbaru lainnya (jika ada)
            if row["is_active"]:
                latest = await conn.fetchrow(
                    """
                    SELECT id FROM chat_sessions
                    WHERE user_id = $1
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    u_uuid,
                )
                if latest:
                    await conn.execute(
                        "UPDATE chat_sessions SET is_active = true WHERE id = $1",
                        latest["id"],
                    )
            return True


# --- Message Operations ---


async def add_message(
    session_id: str | uuid.UUID,
    user_id: str | uuid.UUID,
    role: str,
    content: str,
    citations: list[dict] | None = None,
    clarification: dict | None = None,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    try:
        s_uuid = uuid.UUID(str(session_id))
        u_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        raise ValueError("Invalid UUID for session_id or user_id")
    p = pool or await get_pool()
    citations_json = json.dumps(citations or [])
    clarification_json = json.dumps(clarification) if clarification else None
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO chat_messages (session_id, user_id, role, content, citations, clarification)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)
            RETURNING id, session_id, user_id, role, content, citations, clarification, created_at
            """,
            s_uuid,
            u_uuid,
            role,
            content,
            citations_json,
            clarification_json,
        )
        # Update timestamp session
        await conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            s_uuid,
        )
        res = dict(row)
        if isinstance(res.get("citations"), str):
            res["citations"] = json.loads(res["citations"])
        if isinstance(res.get("clarification"), str):
            res["clarification"] = json.loads(res["clarification"])
        return res


async def get_session_messages(
    session_id: str | uuid.UUID,
    limit: int = 50,
    pool: asyncpg.Pool | None = None,
) -> list[dict[str, Any]]:
    """Ambil N pesan terakhir dalam urutan kronologis (default 50 untuk display UI, atau 4-6 untuk konteks LLM)."""
    try:
        s_uuid = uuid.UUID(str(session_id))
    except (ValueError, AttributeError):
        return []
    p = pool or await get_pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM (
                SELECT id, session_id, user_id, role, content, citations, clarification, feedback, created_at
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ) sub ORDER BY created_at ASC
            """,
            s_uuid,
            limit,
        )
        result = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("citations"), str):
                d["citations"] = json.loads(d["citations"])
            if isinstance(d.get("clarification"), str):
                d["clarification"] = json.loads(d["clarification"])
            result.append(d)
        return result


async def count_session_messages(
    session_id: str | uuid.UUID,
    pool: asyncpg.Pool | None = None,
) -> int:
    try:
        s_uuid = uuid.UUID(str(session_id))
    except (ValueError, AttributeError):
        return 0
    p = pool or await get_pool()
    async with p.acquire() as conn:
        val = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_messages WHERE session_id = $1",
            s_uuid,
        )
        return int(val or 0)


async def set_message_feedback(
    message_id: str | uuid.UUID,
    feedback: str,
    pool: asyncpg.Pool | None = None,
) -> bool:
    try:
        m_uuid = uuid.UUID(str(message_id))
    except (ValueError, AttributeError):
        return False
    p = pool or await get_pool()
    async with p.acquire() as conn:
        res = await conn.execute(
            """
            UPDATE chat_messages
            SET feedback = $1, feedback_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """,
            feedback,
            m_uuid,
        )
        # Sync juga ke audit_logs jika tercatat
        await conn.execute(
            """
            UPDATE audit_logs
            SET feedback = $1
            WHERE message_id = $2
            """,
            feedback,
            m_uuid,
        )
        return "UPDATE" in res
