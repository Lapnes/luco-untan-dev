"""API Luco: Single Active Session with Archiving, JWT Auth, CORS, Rate Limiting, & OpenAI-compatible endpoint."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import logging
import time
from typing import Any
from urllib.parse import quote, urlencode
import uuid

import httpx
logger = logging.getLogger("luco.api")

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import jwt
from pydantic import BaseModel, EmailStr

from .agent import Luco
from .auth import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from .config import get_settings
from .db import (
    add_message,
    clear_and_create_active_session,
    close_db,
    count_session_messages,
    create_active_session,
    create_session,
    create_user,
    delete_session,
    get_active_session,
    get_or_create_active_session,
    get_pool,
    get_session,
    get_session_messages,
    get_user_by_email,
    get_user_by_id,
    init_db,
    list_sessions,
    set_message_feedback,
    switch_active_session,
    update_session_title,
)
from .monitoring import count_tokens, export_audit_csv, get_audit_summary, query_audit_logs, record_audit_log
from .ratelimit import get_rate_limiter

_luco: Luco | None = None
_background_tasks: set[asyncio.Task] = set()


def get_luco() -> Luco:
    global _luco
    if _luco is None:
        _luco = Luco()
    return _luco


def _run_background(coro) -> None:
    # Simpan referensi kuat pada set agar task tidak di-garbage-collect sebelum selesai
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"[warning] Database connection skipped or failed: {e}")
    yield
    await close_db()


app = FastAPI(title="Luco API", lifespan=lifespan)

# CORS middleware agar browser frontend pada port berbeda tidak diblokir
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|.*\.ragilamirzaky\.com)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Request Models ---


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    nim_or_nip: str | None = None
    angkatan: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CreateSessionRequest(BaseModel):
    title: str = "Percakapan Baru"


class SessionChatRequest(BaseModel):
    content: str
    mode: str | None = None


class SimpleChatRequest(BaseModel):
    content: str
    mode: str | None = None


class GoogleVerifyRequest(BaseModel):
    credential: str | None = None
    access_token: str | None = None


# --- Auth Dependency ---


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization Bearer dibutuhkan",
        )
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token tidak valid: {e}")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipe token salah")

    user = await get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User tidak ditemukan")
    return user


def is_admin(email: str | None) -> bool:
    if not email:
        return False
    admins = [a.lower().strip() for a in get_settings().admin_emails]
    return email.lower().strip() in admins


async def get_current_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not is_admin(user.get("email")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: Hanya tim pengembang/admin (NIM terdaftar) yang berhak mengakses monitoring & audit.",
        )
    return user


# --- Background Helper: Auto-Generate Title ---


async def _generate_title_background(session_id: str, query: str):
    try:
        llm = get_luco().llm
        prompt = (
            "Buat judul percakapan yang sangat singkat (maksimal 3-5 kata, tanpa tanda kutip) "
            f"berdasarkan pertanyaan pengguna berikut:\n\nPertanyaan: {query}\n\nJudul:"
        )
        resp = await llm.acomplete(prompt)
        title = str(resp).strip().strip('"').strip("'")
        if title:
            if len(title) > 60:
                title = title[:60]
            await update_session_title(session_id, title)
    except Exception as e:
        logger.warning("Background title generation failed for session %s: %s", session_id, e)


# --- System & Auth Endpoints ---


@app.get("/")
def root():
    return {
        "name": "Luco API Backend",
        "description": "API Backend Chatbot Asisten Informasi Prodi Informatika UNTAN",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    existing = await get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah terdaftar")
    pw_hash = hash_password(req.password)
    user = await create_user(
        email=req.email,
        password_hash=pw_hash,
        full_name=req.full_name,
        nim_or_nip=req.nim_or_nip,
        angkatan=req.angkatan,
    )
    await create_active_session(user["id"], title="Percakapan Baru")

    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])
    return {
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "nim_or_nip": user.get("nim_or_nip"),
            "angkatan": user.get("angkatan"),
            "created_at": user.get("created_at"),
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/v1/auth/login")
async def login(req: LoginRequest):
    # Rate limit login per target email untuk mencegah credential stuffing tanpa memblokir IP bersama
    await get_rate_limiter().check_and_reserve(f"login:{req.email.lower()}", estimated_tokens=0)

    user = await get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau kata sandi salah")
    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])
    return {
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "nim_or_nip": user.get("nim_or_nip"),
            "angkatan": user.get("angkatan"),
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/v1/auth/refresh")
async def refresh(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Refresh token tidak valid: {e}")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipe token harus refresh")
    user = await get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User tidak ditemukan")
    new_access_token = create_access_token(user["id"], user["email"])
    return {"access_token": new_access_token, "token_type": "bearer"}


@app.get("/v1/auth/me")
async def get_me(user: dict[str, Any] = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "nim_or_nip": user.get("nim_or_nip"),
        "angkatan": user.get("angkatan"),
        "is_admin": is_admin(user.get("email")),
        "created_at": user.get("created_at"),
    }


# --- Google OAuth 2.0 Endpoints ---


def _resolve_google_redirect_uri(request: Request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    if "ragilamirzaky.com" in host:
        return "https://uas-ai-be.ragilamirzaky.com/v1/auth/google/callback"
    return get_settings().google_redirect_uri


def _resolve_frontend_url(request: Request, state: str | None) -> str:
    if state and state.startswith("http"):
        return state
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    if "ragilamirzaky.com" in host:
        return "https://uas-ai.ragilamirzaky.com"
    return get_settings().frontend_url


@app.get("/v1/auth/google/login")
async def google_login(request: Request, redirect_to: str | None = None):
    """Mengarahkan pengguna ke halaman persetujuan Google OAuth 2.0."""
    settings = get_settings()
    redirect_uri = _resolve_google_redirect_uri(request)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    if redirect_to:
        params["state"] = redirect_to
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=url)


@app.get("/v1/auth/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
):
    """Menangani callback dari Google OAuth, menukar code dengan token, dan membuat sesi user."""
    import secrets
    settings = get_settings()
    target_frontend = _resolve_frontend_url(request, state)
    redirect_uri = _resolve_google_redirect_uri(request)

    if error or not code:
        err_msg = error or "Kode otorisasi Google tidak ditemukan"
        return RedirectResponse(url=f"{target_frontend}/?auth_error={quote(err_msg)}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Tukar authorization code dengan Google tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            return RedirectResponse(url=f"{target_frontend}/?auth_error=Gagal+tukar+token+Google")

        token_data = token_resp.json()
        access_tok = token_data.get("access_token")

        # 2. Ambil profil pengguna dari Google UserInfo endpoint
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_tok}"},
        )
        if userinfo_resp.status_code != 200:
            return RedirectResponse(url=f"{target_frontend}/?auth_error=Gagal+ambil+profil+Google")

        userinfo = userinfo_resp.json()
        email = userinfo.get("email")
        full_name = userinfo.get("name") or (email.split("@")[0] if email else "Mahasiswa UNTAN")
        picture = userinfo.get("picture") or ""

        if not email:
            return RedirectResponse(url=f"{target_frontend}/?auth_error=Email+Google+tidak+tersedia")

        # 3. Cari atau buat user baru di PostgreSQL
        user = await get_user_by_email(email)
        if not user:
            random_pw = secrets.token_urlsafe(24)
            pw_hash = hash_password(random_pw)
            user = await create_user(
                email=email,
                password_hash=pw_hash,
                full_name=full_name,
            )
            await create_active_session(user["id"], title="Percakapan Baru")

        # 4. Buat JWT tokens Luco
        access_token = create_access_token(user["id"], user["email"])
        refresh_token = create_refresh_token(user["id"])
        user_is_admin = is_admin(user["email"])

        # 5. Redirect kembali ke frontend web dengan parameter autentikasi
        redirect_url = (
            f"{target_frontend}/?token={quote(access_token)}"
            f"&refresh_token={quote(refresh_token)}"
            f"&user_id={quote(str(user['id']))}"
            f"&email={quote(user['email'])}"
            f"&name={quote(user['full_name'])}"
            f"&picture={quote(picture)}"
            f"&is_admin={'true' if user_is_admin else 'false'}"
        )
        return RedirectResponse(url=redirect_url)


@app.post("/v1/auth/google/verify")
async def google_verify(req: GoogleVerifyRequest):
    """Verifikasi token Google credential dari frontend (Google Identity Services)."""
    import secrets
    if not req.credential and not req.access_token:
        raise HTTPException(status_code=400, detail="credential atau access_token dibutuhkan")

    async with httpx.AsyncClient(timeout=10.0) as client:
        if req.credential:
            # Verifikasi ID token via Google tokeninfo
            resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}")
        else:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {req.access_token}"},
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Token Google tidak valid")

        data = resp.json()
        email = data.get("email")
        full_name = data.get("name") or (email.split("@")[0] if email else "Mahasiswa UNTAN")
        picture = data.get("picture") or ""

        if not email:
            raise HTTPException(status_code=400, detail="Email tidak ditemukan pada profil Google")

        user = await get_user_by_email(email)
        if not user:
            random_pw = secrets.token_urlsafe(24)
            pw_hash = hash_password(random_pw)
            user = await create_user(
                email=email,
                password_hash=pw_hash,
                full_name=full_name,
            )
            await create_active_session(user["id"], title="Percakapan Baru")

        access_token = create_access_token(user["id"], user["email"])
        refresh_token = create_refresh_token(user["id"])

        return {
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "full_name": user["full_name"],
                "picture": picture,
                "is_admin": is_admin(user["email"]),
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


# --- Single Active Session with Archiving Endpoints ---


@app.get("/v1/session/active")
async def get_current_active_session(user: dict[str, Any] = Depends(get_current_user)):
    session = await get_or_create_active_session(user["id"])
    messages = await get_session_messages(session["id"], limit=50)
    return {
        "session": {
            "id": str(session["id"]),
            "title": session["title"],
            "is_active": session["is_active"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
        },
        "messages": [
            {
                "id": str(m["id"]),
                "role": m["role"],
                "content": m["content"],
                "citations": m.get("citations") or [],
                "clarification": m.get("clarification"),
                "created_at": m["created_at"].isoformat() if hasattr(m.get("created_at"), "isoformat") else str(m.get("created_at", "")),
            }
            for m in messages
        ],
    }


@app.post("/v1/chat")
async def chat_active_session(
    req: SimpleChatRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    rate_key = f"user:{user['id']}"
    est_tokens = count_tokens(req.content) + 500
    await get_rate_limiter().check_and_reserve(rate_key, estimated_tokens=est_tokens)

    session = await get_or_create_active_session(user["id"])
    session_id = str(session["id"])
    msg_count = await count_session_messages(session["id"])

    # 1. Ambil 6 pesan terakhir untuk konteks ringkas LLM
    history_rows = await get_session_messages(session["id"], limit=6)
    history = [{"role": m["role"], "content": m["content"]} for m in history_rows]

    # 2. Simpan pesan user
    await add_message(
        session_id=session["id"],
        user_id=user["id"],
        role="user",
        content=req.content,
    )

    # 3. Panggil agen Luco
    mode = req.mode or "viking_indobert"
    r = await get_luco().ask(
        question=req.content,
        history=history,
        use_router=True,
        mode=mode,
    )

    # 4. Simpan jawaban dan sitasi
    verified_citations = r["citations"].get("verified", [])
    clarification = r.get("clarification")
    asst_msg = await add_message(
        session_id=session["id"],
        user_id=user["id"],
        role="assistant",
        content=r["answer"],
        citations=verified_citations,
        clarification=clarification,
    )

    # 5. Background task penamaan judul otomatis jika pesan pertama
    if msg_count == 0:
        _run_background(_generate_title_background(session_id, req.content))

    # 6. Audit log dan rekonsiliasi token
    db_pool = None
    try:
        db_pool = await get_pool()
    except Exception:
        pass
    audit_rec = await record_audit_log(
        endpoint="/v1/chat",
        model=f"{get_luco().settings.llm_model} ({mode})",
        question=req.content,
        answer=r["answer"],
        latency_s=r["latency_s"],
        user_id=user["id"],
        user_email=user.get("email"),
        session_id=session["id"],
        message_id=asst_msg["id"],
        user_prompt_tokens=r.get("user_prompt_tokens"),
        system_prompt_tokens=r.get("system_prompt_tokens"),
        context_tokens=r.get("context_tokens"),
        prompt_tokens=r.get("prompt_tokens"),
        completion_tokens=r.get("completion_tokens"),
        steps=r["steps"],
        tool_calls=r["trajectory"],
        system_prompt=r.get("system_prompt"),
        user_prompt=r.get("user_prompt", req.content),
        timing_breakdown=r.get("timing_breakdown"),
        rejected=r.get("rejected", False),
        reason=r.get("reason"),
        pool=db_pool,
    )

    await get_rate_limiter().record_tokens(rate_key, audit_rec["total_tokens"])

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "luco",
        "session_id": session_id,
        "answer": r["answer"],
        "clarification": clarification,
        "choices": [
            {
                "index": 0,
                "message": {
                    "id": str(asst_msg["id"]),
                    "role": "assistant",
                    "content": r["answer"],
                    "clarification": clarification,
                },
                "finish_reason": "stop",
            }
        ],
        "luco": {
            "steps": r["steps"],
            "citations": r["citations"],
            "trajectory": r["trajectory"],
            "rejected": r.get("rejected", False),
            "reason": r.get("reason"),
            "clarification": clarification,
        },
        "usage": {
            "prompt_tokens": audit_rec["prompt_tokens"],
            "completion_tokens": audit_rec["completion_tokens"],
            "total_tokens": audit_rec["total_tokens"],
            "estimated_cost_usd": audit_rec["estimated_cost_usd"],
            "estimated_cost_idr": audit_rec["estimated_cost_idr"],
            "latency_s": audit_rec.get("latency_s", r.get("latency_s", 0.0)),
        },
    }


@app.post("/v1/session/clear")
async def clear_active_session(user: dict[str, Any] = Depends(get_current_user)):
    new_session = await clear_and_create_active_session(user["id"])
    return {
        "status": "cleared",
        "session": {
            "id": str(new_session["id"]),
            "title": new_session["title"],
            "is_active": new_session["is_active"],
            "created_at": new_session["created_at"],
            "updated_at": new_session["updated_at"],
        },
        "messages": [],
    }


@app.post("/v1/session/{session_id}/switch")
async def switch_session(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    switched = await switch_active_session(session_id, user["id"])
    if not switched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")
    messages = await get_session_messages(switched["id"], limit=50)
    return {
        "status": "switched",
        "session": {
            "id": str(switched["id"]),
            "title": switched["title"],
            "is_active": switched["is_active"],
            "created_at": switched["created_at"],
            "updated_at": switched["updated_at"],
        },
        "messages": [
            {
                "id": str(m["id"]),
                "role": m["role"],
                "content": m["content"],
                "citations": m.get("citations") or [],
                "clarification": m.get("clarification"),
                "created_at": m["created_at"].isoformat() if hasattr(m.get("created_at"), "isoformat") else str(m.get("created_at", "")),
            }
            for m in messages
        ],
    }


# --- Sesi Riwayat & Kompatibilitas ---


@app.get("/v1/sessions")
async def get_sessions(user: dict[str, Any] = Depends(get_current_user)):
    sessions = await list_sessions(user["id"])
    return [
        {
            "id": str(s["id"]),
            "title": s["title"],
            "is_active": s["is_active"],
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
        }
        for s in sessions
    ]


@app.post("/v1/sessions", status_code=status.HTTP_201_CREATED)
async def create_new_session_legacy(req: CreateSessionRequest, user: dict[str, Any] = Depends(get_current_user)):
    session = await create_active_session(user["id"], title=req.title)
    return {
        "id": str(session["id"]),
        "title": session["title"],
        "is_active": session["is_active"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
    }


@app.get("/v1/sessions/{session_id}")
async def get_session_detail(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    session = await get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")
    messages = await get_session_messages(session_id, limit=50)
    return {
        "session": {
            "id": str(session["id"]),
            "title": session["title"],
            "is_active": session["is_active"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
        },
        "messages": [
            {
                "id": str(m["id"]),
                "role": m["role"],
                "content": m["content"],
                "citations": m.get("citations") or [],
                "clarification": m.get("clarification"),
                "created_at": m["created_at"].isoformat() if hasattr(m.get("created_at"), "isoformat") else str(m.get("created_at", "")),
            }
            for m in messages
        ],
    }


@app.get("/v1/sessions/{session_id}/export.md")
async def export_session_markdown(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    """Ekspor riwayat sesi percakapan menjadi dokumen Markdown (.md) resmi."""
    session = await get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")
    messages = await get_session_messages(session_id, limit=200)

    now_str = time.strftime("%d %B %Y, %H:%M WIB")
    lines = [
        f"# Percakapan Luco: {session.get('title', 'Informasi Akademik UNTAN')}",
        "",
        f"> **Tanggal Ekspor**: {now_str}  ",
        f"> **Pengguna**: {user.get('full_name', 'Mahasiswa')} ({user.get('email', '-')})  ",
        "> **Sistem**: Luco — Asisten Cerdas Prodi Informatika Universitas Tanjungpura  ",
        "> **Sumber**: Dokumen Resmi Knowledge Vault Prodi Informatika UNTAN  ",
        "",
        "---",
        "",
    ]
    for msg in messages:
        is_user = msg["role"] == "user"
        role_label = f"👤 **{user.get('full_name', 'Mahasiswa')}**" if is_user else "🐦 **Luco (Asisten Prodi)**"
        lines.append(f"### {role_label}:")
        lines.append(msg["content"])
        lines.append("")
        if msg.get("citations"):
            lines.append("**Rujukan Dokumen Resmi:**")
            for c in msg["citations"]:
                title = c if isinstance(c, str) else c.get("text") or c.get("title") or c.get("target") or "Dokumen Resmi"
                target = c.get("target", "") if isinstance(c, dict) else ""
                lines.append(f"- [{title}]({target})")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("*Dokumen ini diekspor otomatis dari Luco — Asisten Informasi Informatika UNTAN.*")
    md_text = "\n".join(lines)
    filename = f"luco-chat-{session_id[:8]}.md"
    return Response(
        content=md_text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/v1/share/{session_id}")
async def get_shared_session(session_id: str):
    """Membuka sesi bersama (read-only snapshot) untuk link share mahasiswa."""
    try:
        s_uuid = uuid.UUID(str(session_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="ID sesi tidak valid")
    pool = await get_pool()
    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = $1",
            s_uuid,
        )
        if not session:
            raise HTTPException(status_code=404, detail="Sesi obrolan tidak ditemukan")
        rows = await conn.fetch(
            """
            SELECT id, role, content, citations, clarification, created_at
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT 100
            """,
            s_uuid,
        )
        messages = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("citations"), str):
                d["citations"] = json.loads(d["citations"])
            if isinstance(d.get("clarification"), str):
                d["clarification"] = json.loads(d["clarification"])
            messages.append({
                "id": str(d["id"]),
                "role": d["role"],
                "content": d["content"],
                "citations": d.get("citations", []),
                "clarification": d.get("clarification"),
                "created_at": d["created_at"].isoformat() if d.get("created_at") else "",
            })
        return {
            "session": {
                "id": str(session["id"]),
                "title": session["title"],
                "created_at": session["created_at"].isoformat() if session.get("created_at") else "",
            },
            "messages": messages,
        }


@app.delete("/v1/sessions/{session_id}")
async def remove_session(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    deleted = await delete_session(session_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")
    return {"status": "deleted", "session_id": session_id}


@app.post("/v1/sessions/{session_id}/chat")
async def chat_in_session(
    session_id: str,
    req: SessionChatRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    session = await get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")

    rate_key = f"user:{user['id']}"
    est_tokens = count_tokens(req.content) + 500
    await get_rate_limiter().check_and_reserve(rate_key, estimated_tokens=est_tokens)

    msg_count = await count_session_messages(session["id"])
    history_rows = await get_session_messages(session_id, limit=6)
    history = [{"role": m["role"], "content": m["content"]} for m in history_rows]

    await add_message(
        session_id=session_id,
        user_id=user["id"],
        role="user",
        content=req.content,
    )

    mode = req.mode or "viking_indobert"
    r = await get_luco().ask(
        question=req.content,
        history=history,
        use_router=True,
        mode=mode,
    )

    verified_citations = r["citations"].get("verified", [])
    clarification = r.get("clarification")
    await add_message(
        session_id=session_id,
        user_id=user["id"],
        role="assistant",
        content=r["answer"],
        citations=verified_citations,
        clarification=clarification,
    )

    if msg_count == 0:
        _run_background(_generate_title_background(session_id, req.content))

    db_pool = None
    try:
        db_pool = await get_pool()
    except Exception:
        pass
    audit_rec = await record_audit_log(
        endpoint=f"/v1/sessions/{session_id}/chat",
        model=f"{get_luco().settings.llm_model} ({mode})",
        question=req.content,
        answer=r["answer"],
        latency_s=r["latency_s"],
        user_id=user["id"],
        user_email=user.get("email"),
        session_id=session_id,
        steps=r["steps"],
        tool_calls=r["trajectory"],
        rejected=r.get("rejected", False),
        reason=r.get("reason"),
        pool=db_pool,
    )

    await get_rate_limiter().record_tokens(rate_key, audit_rec["total_tokens"])

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "luco",
        "session_id": session_id,
        "answer": r["answer"],
        "clarification": clarification,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": r["answer"], "clarification": clarification},
                "finish_reason": "stop",
            }
        ],
        "luco": {
            "steps": r["steps"],
            "citations": r["citations"],
            "trajectory": r["trajectory"],
            "rejected": r.get("rejected", False),
            "reason": r.get("reason"),
            "clarification": clarification,
        },
        "usage": {
            "prompt_tokens": audit_rec["prompt_tokens"],
            "completion_tokens": audit_rec["completion_tokens"],
            "total_tokens": audit_rec["total_tokens"],
            "estimated_cost_usd": audit_rec["estimated_cost_usd"],
            "estimated_cost_idr": audit_rec["estimated_cost_idr"],
            "latency_s": audit_rec.get("latency_s", r.get("latency_s", 0.0)),
        },
    }


# --- OpenAI-Compatible Endpoint (Stateless / Open Access) ---


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    users = [m for m in req.messages if m.role == "user"]
    if not users:
        raise HTTPException(400, "butuh minimal satu pesan user")
    last = req.messages[-1]
    if last.role != "user":
        raise HTTPException(400, "pesan terakhir harus dari user")

    rate_key = "guest:completions"
    est_tokens = sum(count_tokens(m.content) for m in req.messages) + 500
    await get_rate_limiter().check_and_reserve(rate_key, estimated_tokens=est_tokens)

    history = [m.model_dump() for m in req.messages[:-1] if m.role in ("user", "assistant")]
    r = await get_luco().ask(last.content, history=history, use_router=True)

    db_pool = None
    try:
        db_pool = await get_pool()
    except Exception:
        pass
    audit_rec = await record_audit_log(
        endpoint="/v1/chat/completions",
        model=req.model or get_luco().settings.llm_model or "luco",
        question=last.content,
        answer=r["answer"],
        latency_s=r["latency_s"],
        steps=r["steps"],
        tool_calls=r["trajectory"],
        rejected=r.get("rejected", False),
        reason=r.get("reason"),
        pool=db_pool,
    )

    await get_rate_limiter().record_tokens(rate_key, audit_rec["total_tokens"])

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or "luco",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": r["answer"], "clarification": r.get("clarification")},
                "finish_reason": "stop",
            }
        ],
        "clarification": r.get("clarification"),
        "luco": {
            "steps": r["steps"],
            "citations": r["citations"],
            "trajectory": r["trajectory"],
            "rejected": r.get("rejected", False),
            "reason": r.get("reason"),
            "clarification": r.get("clarification"),
        },
        "usage": {
            "prompt_tokens": audit_rec["prompt_tokens"],
            "completion_tokens": audit_rec["completion_tokens"],
            "total_tokens": audit_rec["total_tokens"],
            "estimated_cost_usd": audit_rec["estimated_cost_usd"],
            "estimated_cost_idr": audit_rec["estimated_cost_idr"],
            "latency_s": audit_rec.get("latency_s", r.get("latency_s", 0.0)),
        },
    }


# --- Monitoring & Audit Analytics Endpoints ---


class MessageFeedbackRequest(BaseModel):
    feedback: str  # "like" | "dislike" | "none"


@app.post("/v1/messages/{message_id}/feedback")
async def submit_message_feedback(
    message_id: str,
    req: MessageFeedbackRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Mencatat reaksi Like/Dislike pengguna pada jawaban asisten sebagai data mentah riset."""
    if req.feedback not in ("like", "dislike", "none"):
        raise HTTPException(status_code=400, detail="Feedback harus salah satu dari: 'like', 'dislike', 'none'")
    try:
        pool = await get_pool()
        val = None if req.feedback == "none" else req.feedback
        ok = await set_message_feedback(message_id, val, pool=pool)
        if not ok:
            raise HTTPException(status_code=404, detail="Pesan tidak ditemukan atau gagal diperbarui")
        return {"status": "ok", "message_id": message_id, "feedback": val}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mencatat feedback: {e}")


@app.get("/v1/monitoring/summary")
async def get_summary(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    model: str | None = Query(None),
    admin: dict[str, Any] = Depends(get_current_admin),
):
    try:
        pool = await get_pool()
        return await get_audit_summary(
            pool,
            start_time=start_time,
            end_time=end_time,
            model=model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil ringkasan monitoring: {e}")


@app.get("/v1/monitoring/logs")
async def get_logs(
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    model: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    admin: dict[str, Any] = Depends(get_current_admin),
):
    try:
        pool = await get_pool()
        logs, total = await query_audit_logs(
            pool,
            limit=limit,
            offset=offset,
            model=model,
            start_time=start_time,
            end_time=end_time,
            return_total=True,
        )
        return {"total": total, "offset": offset, "limit": limit, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil audit logs: {e}")


@app.get("/v1/monitoring/export")
async def export_logs_csv(
    model: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    admin: dict[str, Any] = Depends(get_current_admin),
):
    try:
        pool = await get_pool()
        csv_data = await export_audit_csv(
            pool,
            model=model,
            start_time=start_time,
            end_time=end_time,
        )
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=luco_audit_dataset.csv"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal export CSV: {e}")


# --- Vault Official Documents Endpoints ---

import pathlib
import yaml

VAULT_DIR = (pathlib.Path(__file__).parent.parent.parent / "vault").resolve()

VAULT_CATEGORY_MAP = {
    "kp-ta": "Tugas Akhir & Kerja Praktik",
    "akademik": "Akademik & Kurikulum",
    "dosen": "Direktori Dosen & Riset",
    "kemahasiswaan": "Kemahasiswaan & Alumni",
    "fasilitas-lab": "Laboratorium & Fasilitas",
    "profil": "Profil Prodi & Akreditasi",
}


def _extract_doc_info(file_path: pathlib.Path) -> dict[str, Any]:
    rel_path = file_path.relative_to(VAULT_DIR).as_posix()
    cat_key = rel_path.split("/")[0] if "/" in rel_path else "umum"
    category = VAULT_CATEGORY_MAP.get(cat_key, cat_key.capitalize())

    text = file_path.read_text(encoding="utf-8")
    title = file_path.stem.replace("-", " ").title()
    summary = ""
    frontmatter = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                content = parts[2]
            except Exception:
                pass

    if frontmatter.get("title"):
        title = frontmatter["title"]
    elif frontmatter.get("nama"):
        title = frontmatter["nama"]
    else:
        import re
        m = re.search(r"^#\s+(.+)$", content, re.M)
        if m:
            title = m.group(1).strip()

    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("```") and not line.startswith("---"):
            summary = line[:200] + ("..." if len(line) > 200 else "")
            break

    return {
        "path": rel_path,
        "title": title,
        "category": category,
        "category_id": cat_key,
        "summary": summary,
        "metadata": frontmatter,
        "content": content,
    }


def _resolve_vault_file(query_path: str) -> pathlib.Path | None:
    q = query_path.strip().replace("\\", "/").strip("/")
    if "://" in q:
        q = q.split("://", 1)[-1].strip("/")
    if q.startswith("resources/luco/"):
        q = q[len("resources/luco/"):]
    elif q.startswith("luco/"):
        q = q[len("luco/"):]
    elif q.startswith("vault/"):
        q = q[6:]
    if "#" in q:
        q = q.split("#")[0]
    if "?" in q:
        q = q.split("?")[0]
    q = q.strip("/")
    if not q or q in ("~", ".", ".."):
        return None

    # 1. Exact path & prefix-path matching for OpenViking hierarchical URIs
    cand = (VAULT_DIR / q).resolve()
    if cand.is_file() and cand.is_relative_to(VAULT_DIR):
        return cand
    if cand.is_dir() and cand.is_relative_to(VAULT_DIR):
        for idx in ["README.md", "index.md"]:
            if (cand / idx).is_file():
                return cand / idx

    cand_md = (VAULT_DIR / (q + ".md")).resolve()
    if cand_md.is_file() and cand_md.is_relative_to(VAULT_DIR):
        return cand_md

    # Prefix scan from full path downwards (resolves OpenViking nested paths like folder/file/section.md -> folder/file.md)
    parts = [p for p in q.split("/") if p]
    for i in range(len(parts), 0, -1):
        sub = "/".join(parts[:i])
        c1 = (VAULT_DIR / sub).resolve()
        if c1.is_file() and c1.is_relative_to(VAULT_DIR):
            return c1
        c2 = (VAULT_DIR / f"{sub}.md").resolve()
        if c2.is_file() and c2.is_relative_to(VAULT_DIR):
            return c2
        if c1.is_dir() and c1.is_relative_to(VAULT_DIR):
            for idx in ["README.md", "index.md"]:
                if (c1 / idx).is_file():
                    return c1 / idx

    # 2. Fuzzy search against all .md files in vault
    all_files = [f for f in VAULT_DIR.rglob("*.md") if not f.name.startswith("_")]
    parts = [p for p in q.split("/") if p]
    stems_to_try = [p.removesuffix(".md").lower() for p in reversed(parts)]

    for stem in stems_to_try:
        # direct stem match
        for f in all_files:
            if f.stem.lower() == stem:
                return f
        # directory match with README / index
        for f in all_files:
            if f.parent.name.lower() == stem and f.name in ("README.md", "index.md"):
                return f
        # path substring match
        normalized_stem = stem.replace(" ", "-").replace("_", "-")
        for f in all_files:
            rel_str = str(f.relative_to(VAULT_DIR)).lower().replace("_", "-")
            if normalized_stem in rel_str:
                return f

    # 3. Match against document title (frontmatter title / name / headings)
    clean_q = q.lower().replace("-", " ").replace("_", " ").strip()
    for f in all_files:
        try:
            info = _extract_doc_info(f)
            doc_title = info.get("title", "").lower()
            if doc_title and (clean_q in doc_title or doc_title in clean_q):
                return f
            # Match subheadings or manifest sections (e.g., "Tahapan Menuju Kelulusan")
            if len(clean_q) >= 6:
                content_low = f.read_text(encoding="utf-8").lower()
                for line in content_low.splitlines():
                    if line.startswith("#") and clean_q in line:
                        return f
        except Exception:
            continue

    # 4. Fallback for content phrase match if query is specific (> 10 chars)
    if len(clean_q) >= 10:
        for f in all_files:
            try:
                content_low = f.read_text(encoding="utf-8").lower()
                if clean_q in content_low:
                    return f
            except Exception:
                continue

    # 4. Fallback for generic queries like "pedoman" / "pedoman resmi" / "panduan"
    if any(k in clean_q for k in ["pedoman", "panduan", "aturan", "syarat"]):
        for f in all_files:
            if "panduan-ta.md" in f.name or "peraturan-akademik-krs.md" in f.name:
                return f

    return None


@app.get("/v1/vault/documents")
async def list_vault_documents():
    """Mengembalikan daftar seluruh dokumen resmi yang terindeks di knowledge vault."""
    docs = []
    if not VAULT_DIR.exists():
        return {"total": 0, "documents": []}

    all_files = sorted([f for f in VAULT_DIR.rglob("*.md") if not f.name.startswith("_")])
    for f in all_files:
        try:
            info = _extract_doc_info(f)
            info.pop("content", None)
            docs.append(info)
        except Exception as e:
            logger.warning(f"Gagal parse dokumen {f}: {e}")

    return {"total": len(docs), "documents": docs}


@app.get("/v1/vault/document")
async def get_vault_document(path: str = Query(..., description="Path dokumen vault atau kata kunci fuzzy")):
    """Mengambil isi konten lengkap markdown dokumen resmi dari vault."""
    target_file = _resolve_vault_file(path)
    if not target_file or not target_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dokumen resmi '{path}' tidak ditemukan di knowledge vault Informatika UNTAN.",
        )

    try:
        doc_info = _extract_doc_info(target_file)
        return {"status": "success", "document": doc_info}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membaca dokumen '{path}': {e}",
        )


DOKUMEN_RAW_DIR = (pathlib.Path(__file__).parent.parent.parent / "data" / "dokumen_raw").resolve()
VAULT_DOKUMEN_DIR = (VAULT_DIR / "dokumen").resolve()


@app.get("/v1/dokumen")
async def list_official_documents():
    """Mengembalikan daftar 26 dokumen resmi prodi dengan opsi naskah Markdown (.md) atau unduh berkas asli (PDF/DOCX)."""
    if not VAULT_DOKUMEN_DIR.exists():
        return {"total": 0, "documents": []}

    docs = []
    for f in sorted(VAULT_DOKUMEN_DIR.glob("[0-9][0-9]-*.md")):
        try:
            info = _extract_doc_info(f)
            meta = info.get("frontmatter", {})
            doc_id = meta.get("id", f.stem[:2])
            docs.append({
                "id": doc_id,
                "title": info.get("title", f.stem),
                "format": meta.get("format", "PDF"),
                "ukuran_byte": meta.get("ukuran_byte", 0),
                "tanggal_upload": meta.get("tanggal_upload", ""),
                "slug": f.stem,
                "path_markdown": f"dokumen/{f.name}",
                "url_markdown_export": f"/v1/dokumen/{f.stem}/export.md",
                "url_raw_download": meta.get("url_asli", f"/v1/dokumen/{f.stem}/raw"),
            })
        except Exception as e:
            logger.warning(f"Gagal parse dokumen {f}: {e}")

    return {"total": len(docs), "documents": docs}


@app.get("/v1/dokumen/{doc_slug}/export.md")
async def export_official_document_md(doc_slug: str):
    """Mengunduh berkas naskah markdown hasil ekstraksi resmi."""
    clean_slug = doc_slug.removesuffix(".md").strip()
    matched = list(VAULT_DOKUMEN_DIR.glob(f"*{clean_slug}*.md"))
    if not matched:
        raise HTTPException(status_code=404, detail="Dokumen markdown tidak ditemukan.")

    file_path = matched[0]
    return FileResponse(
        path=file_path,
        media_type="text/markdown; charset=utf-8",
        filename=file_path.name,
    )


@app.get("/v1/dokumen/{doc_slug}/raw")
async def download_official_document_raw(doc_slug: str):
    """Mengunduh berkas biner asli (.pdf / .docx) dari arsip resmi prodi."""
    clean_slug = doc_slug.removesuffix(".md").strip()
    prefix = clean_slug[:2] if clean_slug[:2].isdigit() else ""

    if prefix and DOKUMEN_RAW_DIR.exists():
        matched_raw = list(DOKUMEN_RAW_DIR.glob(f"{prefix}_*"))
        if matched_raw:
            raw_file = matched_raw[0]
            ext = raw_file.suffix.lower()
            media_type = (
                "application/pdf"
                if ext == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            return FileResponse(
                path=raw_file,
                media_type=media_type,
                filename=raw_file.name[3:],
            )

    # Fallback: Redirect ke URL CDN Directus jika file lokal belum tersinkron
    matched_md = list(VAULT_DOKUMEN_DIR.glob(f"*{clean_slug}*.md"))
    if matched_md:
        info = _extract_doc_info(matched_md[0])
        url_asli = info.get("frontmatter", {}).get("url_asli")
        if url_asli:
            return RedirectResponse(url=url_asli)

    raise HTTPException(status_code=404, detail="Berkas biner asli tidak ditemukan.")


