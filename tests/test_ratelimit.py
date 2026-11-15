import pytest
from fastapi import HTTPException
from luco.config import Settings
from luco.ratelimit import IdentityRateLimiter


@pytest.mark.asyncio
async def test_rpm_rate_limiting():
    # Konfigurasi uji: limit 3 request per menit
    s = Settings(rate_limit_rpm=3, rate_limit_tpm=10000, rate_limit_daily_tokens=50000)
    limiter = IdentityRateLimiter(settings=s)

    # 3 request awal harus lolos
    h1 = await limiter.check_and_reserve("user:123", estimated_tokens=10)
    assert h1["X-RateLimit-Limit-Requests"] == "3"
    assert h1["X-RateLimit-Remaining-Requests"] == "2"

    await limiter.check_and_reserve("user:123", estimated_tokens=10)
    await limiter.check_and_reserve("user:123", estimated_tokens=10)

    # Request ke-4 harus ditolak dengan 429
    with pytest.raises(HTTPException) as exc:
        await limiter.check_and_reserve("user:123", estimated_tokens=10)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers
    assert exc.value.headers["X-RateLimit-Remaining-Requests"] == "0"


@pytest.mark.asyncio
async def test_anti_ip_ban_independent_users():
    # Menjamin bahwa 2 user pada jaringan / IP yang sama (CGNAT/Kampus) tidak saling memblokir
    s = Settings(rate_limit_rpm=2, rate_limit_tpm=10000, rate_limit_daily_tokens=50000)
    limiter = IdentityRateLimiter(settings=s)

    # User 1 menghabiskan kuotanya
    await limiter.check_and_reserve("user:mahasiswa_a", estimated_tokens=10)
    await limiter.check_and_reserve("user:mahasiswa_a", estimated_tokens=10)

    with pytest.raises(HTTPException):
        await limiter.check_and_reserve("user:mahasiswa_a", estimated_tokens=10)

    # User 2 pada IP yang sama tetap dapat mengakses tanpa hambatan
    h_b = await limiter.check_and_reserve("user:mahasiswa_b", estimated_tokens=10)
    assert h_b["X-RateLimit-Remaining-Requests"] == "1"


@pytest.mark.asyncio
async def test_tpm_and_daily_token_limiting():
    # Batas 100 token per menit, 300 token per hari
    s = Settings(rate_limit_rpm=10, rate_limit_tpm=100, rate_limit_daily_tokens=300)
    limiter = IdentityRateLimiter(settings=s)

    # Alokasi awal 80 token
    await limiter.check_and_reserve("user:bob", estimated_tokens=50)
    await limiter.record_tokens("user:bob", actual_tokens=80)

    # Pre-flight check: mencoba mengirim prompt dengan estimasi 30 token (total 110 > 100 TPM)
    with pytest.raises(HTTPException) as exc:
        await limiter.check_and_reserve("user:bob", estimated_tokens=30)
    assert exc.value.status_code == 429
    assert "token/menit" in exc.value.detail


@pytest.mark.asyncio
async def test_login_rate_limiting_per_account():
    # Limit login percobaan per akun target (mencegah brute force credential stuffing)
    s = Settings(rate_limit_rpm=2, rate_limit_tpm=10000, rate_limit_daily_tokens=50000)
    limiter = IdentityRateLimiter(settings=s)

    await limiter.check_and_reserve("login:korban@untan.ac.id", estimated_tokens=0)
    await limiter.check_and_reserve("login:korban@untan.ac.id", estimated_tokens=0)

    # Percobaan ke-3 ditolak
    with pytest.raises(HTTPException) as exc:
        await limiter.check_and_reserve("login:korban@untan.ac.id", estimated_tokens=0)
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_inactive_bucket_cleanup():
    limiter = IdentityRateLimiter(settings=Settings())
    # Buat entri aktif
    await limiter.check_and_reserve("user:active", estimated_tokens=10)
    # Buat entri kedaluwarsa tanpa riwayat tersisa
    limiter._buckets["user:stale"] = limiter._get_bucket("user:stale", now=0.0)
    limiter._buckets["user:stale"].daily_reset_at = 100.0
    limiter._buckets["user:stale"].requests = []
    limiter._buckets["user:stale"].tokens_minute = []

    # Paksa cleanup dengan memajukan waktu
    limiter._last_cleanup = 0.0
    limiter._cleanup_inactive(now=500.0)

    assert "user:stale" not in limiter._buckets
    assert "user:active" in limiter._buckets

