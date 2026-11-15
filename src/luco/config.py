from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import secrets


def _load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    # Hindari fallback rahasia statis di kode. Buat kunci acak aman untuk sesi ini bila tidak diset di .env
    gen = secrets.token_hex(32)
    os.environ["JWT_SECRET"] = gen
    return gen


@dataclass(frozen=True)
class Settings:
    llm_api_base: str = os.getenv("LLM_API_BASE", "http://127.0.0.1:3000/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "antigravity-gemini-3-flash")
    llm_fallback_api_base: str = os.getenv("LLM_FALLBACK_API_BASE", "")
    llm_fallback_api_key: str = os.getenv("LLM_FALLBACK_API_KEY", "")
    llm_fallback_model: str = os.getenv("LLM_FALLBACK_MODEL", "")
    backend: str = os.getenv("LUCO_BACKEND", "viking")
    viking_url: str = os.getenv("OPENVIKING_URL", "http://127.0.0.1:1933")
    viking_api_key: str = os.getenv("OPENVIKING_API_KEY", "")
    viking_root: str = os.getenv("VIKING_ROOT", "viking://resources/luco").rstrip("/")
    vault_dir: Path = Path(os.getenv("VAULT_DIR", "vault"))
    lookup_json: Path = Path(os.getenv("LOOKUP_JSON", "vault/lookup.json"))
    max_steps: int = int(os.getenv("MAX_AGENT_STEPS", "12"))
    trajectory_log: Path = Path(os.getenv("TRAJECTORY_LOG", "logs/trajectory.jsonl"))
    database_url: str = os.getenv("DATABASE_URL", "postgresql://luco:lucopass123@localhost:5432/lucodb")
    jwt_secret: str = field(default_factory=_get_jwt_secret)
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    usd_to_idr: float = float(os.getenv("USD_TO_IDR", "16200.0"))
    # Konfigurasi pembatasan laju (RPM, TPM, TPD) per identitas user (anti ban IP)
    rate_limit_rpm: int = int(os.getenv("RATE_LIMIT_RPM", "20"))
    rate_limit_tpm: int = int(os.getenv("RATE_LIMIT_TPM", "40000"))
    rate_limit_daily_tokens: int = int(os.getenv("RATE_LIMIT_DAILY_TOKENS", "200000"))
    # Google OAuth 2.0 Credentials
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/v1/auth/google/callback")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    # Admin emails yang berhak mengakses monitoring & audit (3 mahasiswa pengembang)
    admin_emails: tuple[str, ...] = tuple(
        e.strip().lower()
        for e in os.getenv(
            "ADMIN_EMAILS",
            "d1041241069@student.untan.ac.id,d1041241027@student.untan.ac.id,d1041241038@student.untan.ac.id,ragilamirzaky@gmail.com,lapness21@gmail.com,tenutyquwil1@gmail.com",
        ).split(",")
        if e.strip()
    )
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    )


def get_settings() -> Settings:
    return Settings()
