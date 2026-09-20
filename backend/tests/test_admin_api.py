from unittest.mock import MagicMock, patch

import pytest

from utils.config import Config


@pytest.fixture
def client():
    from api.application import app

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        yield c


@pytest.fixture
def admin_headers(client):
    from api.auth import issue_token

    with client.application.app_context():
        return {"Authorization": f"Bearer {issue_token()}"}


class TestLogin:
    def test_valid_credentials_return_token(self, client):
        res = client.post("/api/admin/login", json={"username": Config.ADMIN_USERNAME, "password": Config.ADMIN_PASSWORD})
        assert res.status_code == 200
        assert res.get_json()["token"]

    def test_invalid_credentials_return_401(self, client):
        res = client.post("/api/admin/login", json={"username": "x", "password": "y"})
        assert res.status_code == 401

    def test_issued_token_authenticates(self, client):
        token = client.post(
            "/api/admin/login", json={"username": Config.ADMIN_USERNAME, "password": Config.ADMIN_PASSWORD}
        ).get_json()["token"]
        assert client.get("/api/admin/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


class TestAuthRequired:
    @pytest.mark.parametrize("path", ["/api/admin/me", "/api/admin/dashboard", "/api/admin/queries",
                                      "/api/admin/feedback", "/api/admin/knowledge"])
    def test_missing_token_returns_401(self, client, path):
        assert client.get(path).status_code == 401

    def test_tampered_token_returns_401(self, client):
        res = client.get("/api/admin/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert res.status_code == 401

    def test_delete_requires_auth(self, client):
        assert client.delete("/api/admin/files/abc").status_code == 401

    def test_debug_retrieval_requires_auth(self, client):
        assert client.get("/debug/retrieval?q=hi").status_code == 401

    def test_preflight_allows_authorization_header(self, client):
        res = client.options("/api/admin/dashboard")
        assert "Authorization" in res.headers["Access-Control-Allow-Headers"]
        assert "DELETE" in res.headers["Access-Control-Allow-Methods"]


class TestAdminData:
    @patch("api.admin.routes.db")
    def test_queries_returns_json_page(self, mock_sb, client, admin_headers):
        chain = mock_sb.table.return_value.select.return_value
        chain.order.return_value.range.return_value.execute.return_value = MagicMock(data=[{"query_text": "hi"}])
        chain.execute.return_value = MagicMock(count=1)
        res = client.get("/api/admin/queries", headers=admin_headers)
        assert res.status_code == 200
        body = res.get_json()
        assert body["rows"] == [{"query_text": "hi"}]
        assert body["total_pages"] == 1
        assert "greeting" in body["intents"]

    @patch("api.admin.routes.db")
    def test_delete_file_removes_record(self, mock_sb, client, admin_headers):
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"storage_path": None}
        )
        res = client.delete("/api/admin/files/abc", headers=admin_headers)
        assert res.status_code == 200
        assert res.get_json()["success"] is True


class TestLoginRateLimit:
    def test_repeated_bad_logins_are_throttled(self, client):
        from api.application import limiter

        limiter.reset()
        codes = [client.post("/api/admin/login", json={"username": "x", "password": "y"}).status_code for _ in range(12)]
        limiter.reset()
        assert codes[:10] == [401] * 10
        assert 429 in codes[10:]
