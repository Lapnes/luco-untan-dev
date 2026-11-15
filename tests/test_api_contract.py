from fastapi.testclient import TestClient
from luco.api import app
from luco.citations import check_citations

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_cors_headers():
    res = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_image_links_not_treated_as_citations():
    # Gambar Markdown ![alt](url) tidak boleh dianggap sebagai sitasi dokumen
    answer = "Berikut ilustrasi diagram: ![Diagram KP](https://example.com/diagram.png)"
    res = check_citations(answer, ["Hanya dokumen teks biasa"])
    assert res["links"] == 0
    assert res["has_citations"] is False
    assert len(res["verified"]) == 0
    assert len(res["unverified"]) == 0


def test_chat_completions_validation():
    # Empty messages
    r1 = client.post("/v1/chat/completions", json={"messages": []})
    assert r1.status_code == 400

    # Last message not from user
    r2 = client.post("/v1/chat/completions", json={"messages": [{"role": "assistant", "content": "Halo"}]})
    assert r2.status_code == 400


def test_fast_reject_payload_contract():
    # Testing Fast Redirect for saran/kritik/kerjasama
    res = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Saya ingin menyampaikan saran dan kritik untuk lab prodi"}]},
    )
    assert res.status_code == 200
    data = res.json()

    # Pastikan kontrak payload konsisten
    assert "id" in data
    assert data["object"] == "chat.completion"
    assert "created" in data
    assert "choices" in data and len(data["choices"]) == 1
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert "kontak resmi" in choice["message"]["content"].lower()

    # Metadata luco
    assert "luco" in data
    assert data["luco"]["rejected"] is True
    assert data["luco"]["reason"] == "contact_redirect"
    assert data["luco"]["steps"] == 0

    # Metadata audit token & cost
    assert "usage" in data
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    assert "estimated_cost_usd" in data["usage"]
    assert "estimated_cost_idr" in data["usage"]


def test_protected_routes_require_auth():
    # Calling protected endpoint without token must return 401
    res = client.get("/v1/sessions")
    assert res.status_code == 401

    res2 = client.get("/v1/auth/me")
    assert res2.status_code == 401

    # Endpoint sesi aktif baru juga wajib auth
    res3 = client.get("/v1/session/active")
    assert res3.status_code == 401

    res4 = client.post("/v1/session/clear")
    assert res4.status_code == 401

    res5 = client.post("/v1/chat", json={"content": "Halo"})
    assert res5.status_code == 401

    # Calling with malformed authorization header
    res6 = client.get("/v1/sessions", headers={"Authorization": "Basic 12345"})
    assert res6.status_code == 401

    # Calling with invalid token string
    res7 = client.get("/v1/sessions", headers={"Authorization": "Bearer token.palsu.rusak"})
    assert res7.status_code == 401


def test_google_oauth_login_redirect():
    res = client.get("/v1/auth/google/login", follow_redirects=False)
    assert res.status_code in (302, 307)
    loc = res.headers.get("location", "")
    assert "accounts.google.com" in loc
    assert "client_id=" in loc
    assert "response_type=code" in loc


def test_google_oauth_callback_error_handling():
    res = client.get("/v1/auth/google/callback?error=access_denied", follow_redirects=False)
    assert res.status_code in (302, 307)
    loc = res.headers.get("location", "")
    assert "auth_error=" in loc


def test_vault_documents_list():
    res = client.get("/v1/vault/documents")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] >= 50
    assert len(data["documents"]) == data["total"]
    doc0 = data["documents"][0]
    assert "path" in doc0
    assert "title" in doc0
    assert "category" in doc0


def test_vault_document_detail_exact_and_fuzzy():
    # Exact path
    res = client.get("/v1/vault/document?path=kp-ta/panduan-ta.md")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    doc = data["document"]
    assert doc["path"] == "kp-ta/panduan-ta.md"
    assert "Panduan Tugas Akhir" in doc["title"]
    assert "Persyaratan Pengajuan Tugas Akhir" in doc["content"]

    # Fuzzy stem
    res2 = client.get("/v1/vault/document?path=panduan-ta")
    assert res2.status_code == 200
    assert res2.json()["document"]["path"] == "kp-ta/panduan-ta.md"

    # Fuzzy with long markdown citation path
    res3 = client.get("/v1/vault/document?path=kp-ta/panduan-ta/Panduan_Tugas_Akhir_Skripsi_Informatika_UNTAN/kp-ta/panduan-ta/Panduan_Tugas_Akhir_Skripsi_Informatika_UNTAN.md")
    assert res3.status_code == 200
    assert res3.json()["document"]["path"] == "kp-ta/panduan-ta.md"

    # Not found
    res4 = client.get("/v1/vault/document?path=dokumen-palsu-ngawur-123.md")
    assert res4.status_code == 404


def test_shared_session_endpoint_contract():
    # Invalid UUID string
    r1 = client.get("/v1/share/not-a-valid-uuid")
    assert r1.status_code == 400
    assert "tidak valid" in r1.json()["detail"].lower()

    # Valid UUID but not found in DB
    r2 = client.get("/v1/share/00000000-0000-0000-0000-000000000000")
    assert r2.status_code == 404
    assert "tidak ditemukan" in r2.json()["detail"].lower()


def test_export_markdown_contract():
    # Requires authentication
    r1 = client.get("/v1/sessions/00000000-0000-0000-0000-000000000000/export.md")
    assert r1.status_code == 401


def test_official_dokumen_endpoints_contract():
    # 1. List official dokumen
    res = client.get("/v1/dokumen")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] >= 26
    docs = data["documents"]
    first = docs[0]
    assert "slug" in first
    assert "url_markdown_export" in first
    assert "url_raw_download" in first

    slug = first["slug"]

    # 2. Export markdown
    res_md = client.get(f"/v1/dokumen/{slug}/export.md")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers.get("content-type", "")
    assert len(res_md.text) > 0

    # 3. Download raw file
    res_raw = client.get(f"/v1/dokumen/{slug}/raw")
    assert res_raw.status_code == 200
    assert len(res_raw.content) > 0

    # 4. Not found cases
    res_md_404 = client.get("/v1/dokumen/dokumen-tidak-ada/export.md")
    assert res_md_404.status_code == 404
    res_raw_404 = client.get("/v1/dokumen/dokumen-tidak-ada/raw")
    assert res_raw_404.status_code == 404


def test_message_feedback_contract():
    # 1. Unauthenticated request -> 401
    r_unauth = client.post(
        "/v1/messages/00000000-0000-0000-0000-000000000000/feedback",
        json={"feedback": "like"},
    )
    assert r_unauth.status_code == 401

    # 2. Authenticated request with invalid feedback choice
    from luco.api import get_current_user
    mock_user = {"id": "00000000-0000-0000-0000-000000000001", "email": "tester@untan.ac.id"}
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        r_invalid = client.post(
            "/v1/messages/00000000-0000-0000-0000-000000000000/feedback",
            headers={"Authorization": "Bearer dummy"},
            json={"feedback": "superlike"},
        )
        assert r_invalid.status_code == 400
        assert "feedback harus salah satu" in r_invalid.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


