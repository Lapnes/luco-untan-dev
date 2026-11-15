import tempfile
from pathlib import Path
import pytest
from luco.monitoring import calculate_cost_usd, count_tokens, record_audit_log


def test_count_tokens():
    assert count_tokens("") == 0
    cnt = count_tokens("Halo Luco, asisten Informatika UNTAN")
    assert cnt > 0


def test_calculate_cost_usd():
    # Gemini pricing: $0.10 / 1M prompt, $0.40 / 1M completion
    cost_gemini = calculate_cost_usd("gemini-3.8-flash-high", 1000, 500)
    # (1000 / 1M) * 0.10 + (500 / 1M) * 0.40 = 0.000100 + 0.000200 = 0.000300
    assert cost_gemini == 0.0003

    # DeepSeek pricing: $0.14 / 1M prompt, $0.28 / 1M completion
    cost_ds = calculate_cost_usd("deepseek-v4.1-flash", 1000, 1000)
    assert cost_ds == 0.00042


@pytest.mark.asyncio
async def test_record_audit_log_file():
    with tempfile.TemporaryDirectory() as d:
        log_file = Path(d) / "audit.jsonl"
        rec = await record_audit_log(
            endpoint="/v1/chat/completions",
            model="gemini-3.8-flash-high",
            question="Berapa SKS syarat KP?",
            answer="Syarat KP adalah minimal 80 SKS.",
            latency_s=0.45,
            steps=1,
            tool_calls=[{"tool": "find_docs", "args": {"query": "syarat KP"}}],
            log_file=log_file,
        )
        assert rec["prompt_tokens"] > 0
        assert rec["completion_tokens"] > 0
        assert rec["total_tokens"] == rec["prompt_tokens"] + rec["completion_tokens"]
        assert rec["estimated_cost_usd"] > 0
        assert rec["estimated_cost_idr"] > 0

        # Verifikasi file ditulis
        assert log_file.exists()
        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert "estimated_cost_idr" in lines[0]


@pytest.mark.asyncio
async def test_monitor_script_functions():
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from monitor import check_service_health, fetch_audit_summary, export_audit_to_csv

    services = await check_service_health()
    assert "PostgreSQL" in services
    assert "OpenViking" in services
    assert "IndoBERT Embedder" in services

    summary = await fetch_audit_summary()
    assert "total_requests" in summary
    assert "total_tokens" in summary
    assert "total_cost_idr" in summary
