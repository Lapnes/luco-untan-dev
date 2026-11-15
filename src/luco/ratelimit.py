"""Sistem pembatasan laju (Rate Limiting & Token Budget) berbasis identitas pengguna.

Anti Ban IP: Di lingkungan produksi (CGNAT ISP / WiFi kampus), ribuan pengguna sah
berbagi 1 IP publik yang sama. Pembatasan dilakukan pada user_id (JWT), bukan IP.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import time
from typing import Any

from fastapi import HTTPException, status

from .config import Settings, get_settings


@dataclass
class UsageEntry:
    timestamp: float
    tokens: int = 0


@dataclass
class UserQuotaBucket:
    # Riwayat request dalam sliding window
    requests: list[float] = field(default_factory=list)
    # Riwayat token dalam sliding window 1 menit
    tokens_minute: list[UsageEntry] = field(default_factory=list)
    # Total akumulasi token harian
    daily_tokens: int = 0
    daily_reset_at: float = field(default_factory=time.time)


class IdentityRateLimiter:
    """Rate limiter berbasis identitas (User ID / Akun target) dengan algoritma sliding window."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._buckets: dict[str, UserQuotaBucket] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup: float = time.time()

    def _cleanup_inactive(self, now: float) -> None:
        # Bersihkan bucket yang tidak aktif setiap 5 menit agar memori tidak tumbuh tak terbatas
        if now - self._last_cleanup < 300.0:
            return
        self._last_cleanup = now
        stale_keys = [
            k
            for k, b in self._buckets.items()
            if now >= b.daily_reset_at and not b.requests and not b.tokens_minute
        ]
        for k in stale_keys:
            self._buckets.pop(k, None)

    def _get_bucket(self, key: str, now: float) -> UserQuotaBucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = UserQuotaBucket(daily_reset_at=now + 86400.0)
            self._buckets[key] = bucket
        # Reset kuota harian jika window 24 jam telah lewat
        if now >= bucket.daily_reset_at:
            bucket.daily_tokens = 0
            bucket.daily_reset_at = now + 86400.0
        return bucket

    def _prune(self, bucket: UserQuotaBucket, now: float) -> None:
        # Bersihkan entri yang lebih tua dari 60 detik
        cutoff = now - 60.0
        bucket.requests = [t for t in bucket.requests if t > cutoff]
        bucket.tokens_minute = [e for e in bucket.tokens_minute if e.timestamp > cutoff]

    async def check_and_reserve(
        self,
        key: str,
        estimated_tokens: int = 0,
    ) -> dict[str, str]:
        """Periksa apakah request diperbolehkan berdasarkan limit RPM, TPM, dan TPD."""
        now = time.time()
        async with self._lock:
            self._cleanup_inactive(now)
            bucket = self._get_bucket(key, now)
            self._prune(bucket, now)

            rpm_limit = self.settings.rate_limit_rpm
            tpm_limit = self.settings.rate_limit_tpm
            daily_limit = self.settings.rate_limit_daily_tokens

            # 1. Cek Request Per Minute (RPM)
            if len(bucket.requests) >= rpm_limit:
                earliest = bucket.requests[0]
                retry_after = max(1, int(60.0 - (now - earliest)))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Batas laju permintaan terlampaui ({rpm_limit} req/menit). Coba lagi dalam {retry_after} detik.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit-Requests": str(rpm_limit),
                        "X-RateLimit-Remaining-Requests": "0",
                    },
                )

            # 2. Cek Token Per Minute (TPM) pre-flight
            current_minute_tokens = sum(e.tokens for e in bucket.tokens_minute)
            if current_minute_tokens + estimated_tokens > tpm_limit:
                earliest_token = bucket.tokens_minute[0].timestamp if bucket.tokens_minute else now
                retry_after = max(1, int(60.0 - (now - earliest_token)))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Batas kuota token per menit terlampaui ({tpm_limit} token/menit). Coba lagi dalam {retry_after} detik.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit-Tokens": str(tpm_limit),
                        "X-RateLimit-Remaining-Tokens": str(max(0, tpm_limit - current_minute_tokens)),
                    },
                )

            # 3. Cek Batas Harian (TPD)
            if bucket.daily_tokens + estimated_tokens > daily_limit:
                seconds_to_reset = max(1, int(bucket.daily_reset_at - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Batas kuota harian akun terlampaui ({daily_limit} token/hari). Kuota di-reset dalam {seconds_to_reset // 3600} jam.",
                    headers={
                        "Retry-After": str(seconds_to_reset),
                        "X-RateLimit-Limit-Daily": str(daily_limit),
                        "X-RateLimit-Remaining-Daily": "0",
                    },
                )

            # Catat request
            bucket.requests.append(now)

            remaining_req = max(0, rpm_limit - len(bucket.requests))
            remaining_tpm = max(0, tpm_limit - current_minute_tokens)
            return {
                "X-RateLimit-Limit-Requests": str(rpm_limit),
                "X-RateLimit-Remaining-Requests": str(remaining_req),
                "X-RateLimit-Limit-Tokens": str(tpm_limit),
                "X-RateLimit-Remaining-Tokens": str(remaining_tpm),
            }

    async def record_tokens(self, key: str, actual_tokens: int) -> None:
        """Rekonsiliasi penggunaan token aktual setelah respon LLM selesai."""
        if actual_tokens <= 0:
            return
        now = time.time()
        async with self._lock:
            self._cleanup_inactive(now)
            bucket = self._get_bucket(key, now)
            bucket.tokens_minute.append(UsageEntry(timestamp=now, tokens=actual_tokens))
            bucket.daily_tokens += actual_tokens


_limiter: IdentityRateLimiter | None = None


def get_rate_limiter() -> IdentityRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = IdentityRateLimiter()
    return _limiter

