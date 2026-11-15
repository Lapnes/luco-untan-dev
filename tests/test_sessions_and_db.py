from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from luco.api import app, get_current_user
from luco import db

client = TestClient(app)


@pytest.mark.asyncio
async def test_db_uuid_safety_returns_safe_fallbacks():
    # Menguji bahwa fungsi-fungsi db tidak melempar unhandled ValueError jika UUID cacat
    assert await db.get_user_by_id("bukan-uuid") is None
    assert await db.get_session("bukan-uuid", "bukan-uuid") is None
    assert await db.get_active_session("bukan-uuid") is None
    assert await db.switch_active_session("bukan-uuid", "bukan-uuid") is None
    assert await db.update_session_title("bukan-uuid", "Judul") is False
    assert await db.count_session_messages("bukan-uuid") == 0
    assert await db.list_sessions("bukan-uuid") == []
    assert await db.delete_session("bukan-uuid", "bukan-uuid") is False
    assert await db.get_session_messages("bukan-uuid") == []


def test_api_invalid_session_id_returns_404_not_500():
    # Pastikan bahwa session_id cacat di URL menghasilkan 404 Not Found (BUKAN 500 Server Crash)
    mock_user = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "mahasiswa@untan.ac.id",
        "full_name": "Mahasiswa Uji",
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        # GET /v1/sessions/bukan-uuid-valid
        r1 = client.get("/v1/sessions/bukan-uuid-valid")
        assert r1.status_code == 404
        assert "Sesi tidak ditemukan" in r1.json()["detail"]

        # DELETE /v1/sessions/bukan-uuid-valid
        r2 = client.delete("/v1/sessions/bukan-uuid-valid")
        assert r2.status_code == 404
        assert "Sesi tidak ditemukan" in r2.json()["detail"]

        # POST /v1/session/bukan-uuid-valid/switch
        r3 = client.post("/v1/session/bukan-uuid-valid/switch")
        assert r3.status_code == 404
        assert "Sesi tidak ditemukan" in r3.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_api_active_session_lifecycle():
    mock_user = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "mahasiswa@untan.ac.id",
        "full_name": "Mahasiswa Uji",
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_active = {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "user_id": mock_user["id"],
            "title": "Percakapan Aktif",
            "is_active": True,
            "created_at": "2026-11-13T10:00:00",
            "updated_at": "2026-11-13T10:00:00",
        }
        mock_msgs = [
            {"id": "msg-1", "role": "user", "content": "Halo", "citations": [], "created_at": "2026-11-13T10:00:00"},
            {"id": "msg-2", "role": "assistant", "content": "Halo! Ada yang bisa dibantu?", "citations": [], "created_at": "2026-11-13T10:00:01"},
        ]

        with patch("luco.api.get_or_create_active_session", new_callable=AsyncMock) as m_active, \
             patch("luco.api.get_session_messages", new_callable=AsyncMock) as m_msgs:
            m_active.return_value = mock_active
            m_msgs.return_value = mock_msgs

            # Test GET /v1/session/active
            res = client.get("/v1/session/active")
            assert res.status_code == 200
            data = res.json()
            assert data["session"]["id"] == mock_active["id"]
            assert data["session"]["is_active"] is True
            assert len(data["messages"]) == 2

        with patch("luco.api.clear_and_create_active_session", new_callable=AsyncMock) as m_clear:
            new_active = {
                "id": "333e4567-e89b-12d3-a456-426614174000",
                "user_id": mock_user["id"],
                "title": "Percakapan Baru",
                "is_active": True,
                "created_at": "2026-11-13T10:05:00",
                "updated_at": "2026-11-13T10:05:00",
            }
            m_clear.return_value = new_active

            # Test POST /v1/session/clear
            res_clear = client.post("/v1/session/clear")
            assert res_clear.status_code == 200
            data_clear = res_clear.json()
            assert data_clear["status"] == "cleared"
            assert data_clear["session"]["id"] == new_active["id"]
            assert data_clear["messages"] == []
    finally:
        app.dependency_overrides.clear()


def test_api_chat_active_session_flow():
    mock_user = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "mahasiswa@untan.ac.id",
        "full_name": "Mahasiswa Uji",
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_active = {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "user_id": mock_user["id"],
            "title": "Percakapan Baru",
            "is_active": True,
        }
        mock_luco_resp = {
            "question": "Berapa SKS untuk KP?",
            "answer": "Syarat KP adalah minimal 80 SKS sesuai [panduan-kp.md](file:///vault/kp-ta/panduan-kp.md).",
            "steps": 1,
            "trajectory": [{"tool": "telusuri_direktori_prodi", "input": {"kategori": "kp-ta"}, "output": "found"}],
            "citations": {"links": 1, "has_citations": True, "all_verified": True, "verified": ["panduan-kp.md"], "unverified": []},
            "latency_s": 0.45,
            "backend": "local",
            "error": None,
            "rejected": False,
            "reason": None,
        }
        mock_audit = {
            "id": "aud-1",
            "prompt_tokens": 150,
            "completion_tokens": 30,
            "total_tokens": 180,
            "estimated_cost_usd": 0.00003,
            "estimated_cost_idr": 0.5,
        }

        with patch("luco.api.get_or_create_active_session", new_callable=AsyncMock) as m_active, \
             patch("luco.api.count_session_messages", new_callable=AsyncMock) as m_count, \
             patch("luco.api.get_session_messages", new_callable=AsyncMock) as m_msgs, \
             patch("luco.api.add_message", new_callable=AsyncMock) as m_add, \
             patch("luco.api.record_audit_log", new_callable=AsyncMock) as m_audit, \
             patch("luco.api.get_luco") as m_luco, \
             patch("luco.api.get_pool", new_callable=AsyncMock) as m_pool:
            m_active.return_value = mock_active
            m_count.return_value = 0
            m_msgs.return_value = []
            m_audit.return_value = mock_audit
            m_pool.return_value = None
            m_luco.return_value.ask = AsyncMock(return_value=mock_luco_resp)
            m_luco.return_value.settings.llm_model = "test-model"

            res = client.post("/v1/chat", json={"content": "Berapa SKS untuk KP?"})
            assert res.status_code == 200
            data = res.json()
            assert data["object"] == "chat.completion"
            assert data["session_id"] == mock_active["id"]
            assert "80 SKS" in data["choices"][0]["message"]["content"]
            assert data["luco"]["steps"] == 1
            assert data["usage"]["total_tokens"] == 180
            assert m_add.call_count == 2  # 1 user message, 1 assistant message
    finally:
        app.dependency_overrides.clear()


def test_api_chat_in_session_flow():
    mock_user = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "mahasiswa@untan.ac.id",
        "full_name": "Mahasiswa Uji",
    }
    target_session_id = "555e4567-e89b-12d3-a456-426614174000"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_session = {
            "id": target_session_id,
            "user_id": mock_user["id"],
            "title": "Sesi Spesifik",
            "is_active": False,
        }
        mock_luco_resp = {
            "question": "Siapa kaprodi?",
            "answer": "Ketua Jurusan / Kaprodi tercantum di struktur organisasi.",
            "steps": 1,
            "trajectory": [],
            "citations": {"links": 0, "has_citations": False, "all_verified": True, "verified": [], "unverified": []},
            "latency_s": 0.3,
            "backend": "local",
            "error": None,
            "rejected": False,
            "reason": None,
        }
        mock_audit = {
            "id": "aud-2",
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": 0.00002,
            "estimated_cost_idr": 0.3,
        }

        with patch("luco.api.get_session", new_callable=AsyncMock) as m_get_sess, \
             patch("luco.api.get_session_messages", new_callable=AsyncMock) as m_msgs, \
             patch("luco.api.add_message", new_callable=AsyncMock) as m_add, \
             patch("luco.api.record_audit_log", new_callable=AsyncMock) as m_audit, \
             patch("luco.api.get_luco") as m_luco, \
             patch("luco.api.get_pool", new_callable=AsyncMock) as m_pool:
            m_get_sess.return_value = mock_session
            m_msgs.return_value = []
            m_audit.return_value = mock_audit
            m_pool.return_value = None
            m_luco.return_value.ask = AsyncMock(return_value=mock_luco_resp)
            m_luco.return_value.settings.llm_model = "test-model"

            res = client.post(f"/v1/sessions/{target_session_id}/chat", json={"content": "Siapa kaprodi?"})
            assert res.status_code == 200
            data = res.json()
            assert data["session_id"] == target_session_id
            assert "struktur organisasi" in data["choices"][0]["message"]["content"]
            assert data["usage"]["total_tokens"] == 120
    finally:
        app.dependency_overrides.clear()

