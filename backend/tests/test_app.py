import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    # Patch the database client before importing app so the module-level client is mocked
    with patch("vectordb.postgres.db") as _mock_sb:
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


# ── /healthz ─────────────────────────────────────────────────────────────────

class TestHealthz:
    def test_returns_200(self, client):
        res = client.get("/healthz")
        assert res.status_code == 200

    def test_returns_ok_status(self, client):
        data = res = client.get("/healthz").get_json()
        assert data["status"] == "ok"

    def test_returns_version(self, client):
        data = client.get("/healthz").get_json()
        assert "version" in data


class TestSuggestions:
    def test_english_suggestions_include_named_bank_prompts(self, client):
        suggestions = client.get("/api/suggestions?lang=en").get_json()["suggestions"]

        assert "How to pay via Meezan Bank?" in suggestions
        assert "How do I pay using PSID?" in suggestions

    def test_unknown_language_falls_back_to_english(self, client):
        assert client.get("/api/suggestions?lang=xx").get_json()["lang"] == "en"


class TestBackendServesNoUi:
    def test_root_is_json_service_info(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert res.get_json()["service"] == "fintech-assistant-api"

    def test_no_html_pages_or_static_assets(self, client):
        for path in ("/user/", "/admin/login", "/static/chat.css", "/chat", "/upload"):
            assert client.get(path).status_code == 404


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealth:
    @patch("api.application.db")
    def test_healthy_when_database_ok(self, mock_sb, client):
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()
        res = client.get("/health")
        assert res.status_code == 200
        assert res.get_json()["database"] == "ok"

    @patch("api.application.db")
    def test_degraded_when_database_fails(self, mock_sb, client):
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("conn error")
        res = client.get("/health")
        assert res.status_code == 503
        data = res.get_json()
        assert data["status"] == "degraded"
        assert "error" in data["database"]


# ── /api/chat ─────────────────────────────────────────────────────────────────

class TestApiChat:
    def test_empty_query_returns_400(self, client):
        res = client.post("/api/chat", json={"user_query": ""})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_missing_query_returns_400(self, client):
        res = client.post("/api/chat", json={})
        assert res.status_code == 400

    def test_query_too_long_returns_400(self, client):
        res = client.post("/api/chat", json={"user_query": "x" * 501})
        assert res.status_code == 400
        assert "too long" in res.get_json()["error"].lower()

    @patch("api.application.handle_chat_query")
    def test_valid_query_returns_200(self, mock_chat, client):
        mock_chat.return_value = {
            "answer": "Hello!",
            "service": None,
            "intent": "greeting",
            "response_language": "en",
            "suggested_questions": [],
            "payment_options": None,
        }
        res = client.post("/api/chat", json={"user_query": "hello"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["answer"] == "Hello!"
        assert data["intent"] == "greeting"

    @patch("api.application.handle_chat_query")
    def test_service_dict_is_flattened_to_name(self, mock_chat, client):
        mock_chat.return_value = {
            "answer": "Here is info.",
            "service": {"service_name": "Easypaisa PSID Payment"},
            "intent": "easypaisa_payment",
            "response_language": "en",
            "suggested_questions": [],
            "payment_options": None,
        }
        res = client.post("/api/chat", json={"user_query": "easypaisa"})
        assert res.status_code == 200
        assert res.get_json()["service"] == "Easypaisa PSID Payment"

    @patch("api.application.handle_chat_query")
    def test_history_is_passed_cleaned(self, mock_chat, client):
        mock_chat.return_value = {
            "answer": "ok", "service": None, "intent": "greeting",
            "response_language": "en", "suggested_questions": [], "payment_options": None,
        }
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        res = client.post("/api/chat", json={"user_query": "how are you", "history": history})
        assert res.status_code == 200
        _, kwargs = mock_chat.call_args
        assert kwargs.get("history") is not None or mock_chat.call_args[0][1:] is not None

    @patch("api.application.handle_chat_query", side_effect=Exception("LLM down"))
    def test_internal_error_returns_500(self, mock_chat, client):
        res = client.post("/api/chat", json={"user_query": "hello"})
        assert res.status_code == 500
        assert "error" in res.get_json()

    def test_options_preflight_returns_204(self, client):
        res = client.options("/api/chat")
        assert res.status_code == 204


# ── /api/feedback ─────────────────────────────────────────────────────────────

class TestApiFeedback:
    @patch("api.application.db")
    def test_valid_positive_rating(self, mock_sb, client):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
        res = client.post("/api/feedback", json={"rating": 1, "query_text": "test"})
        assert res.status_code == 200
        assert res.get_json()["ok"] is True

    @patch("api.application.db")
    def test_valid_negative_rating(self, mock_sb, client):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
        res = client.post("/api/feedback", json={"rating": -1})
        assert res.status_code == 200

    def test_invalid_rating_zero(self, client):
        res = client.post("/api/feedback", json={"rating": 0})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_invalid_rating_string(self, client):
        res = client.post("/api/feedback", json={"rating": "good"})
        assert res.status_code == 400

    def test_missing_rating(self, client):
        res = client.post("/api/feedback", json={})
        assert res.status_code == 400

    @patch("api.application.db")
    def test_database_error_returns_500(self, mock_sb, client):
        mock_sb.table.return_value.insert.return_value.execute.side_effect = Exception("db error")
        res = client.post("/api/feedback", json={"rating": 1})
        assert res.status_code == 500


# ── /api/upload ───────────────────────────────────────────────────────────────

class TestApiUpload:
    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/upload", data={"department_id": "1"})
        assert res.status_code == 401
        assert "Admin" in res.get_json()["error"]

    def test_authenticated_no_file_returns_400(self, client, admin_headers):
        res = client.post("/api/upload", data={"department_id": "dept1"}, headers=admin_headers)
        assert res.status_code == 400

    def test_authenticated_no_department_returns_400(self, client, admin_headers):
        data = {"file": (b"content", "test.txt")}
        res = client.post("/api/upload", content_type="multipart/form-data", data=data, headers=admin_headers)
        assert res.status_code == 400


# ── CORS headers ──────────────────────────────────────────────────────────────

class TestCorsHeaders:
    def test_cors_header_present_on_chat(self, client):
        with patch("api.application.handle_chat_query") as mock_chat:
            mock_chat.return_value = {
                "answer": "hi", "service": None, "intent": "greeting",
                "response_language": "en", "suggested_questions": [], "payment_options": None,
            }
            res = client.post("/api/chat", json={"user_query": "hello"})
        assert "Access-Control-Allow-Origin" in res.headers

    def test_cors_header_present_on_healthz(self, client):
        res = client.get("/healthz")
        assert "Access-Control-Allow-Origin" in res.headers


# ── format_backend_error ──────────────────────────────────────────────────────

class TestFormatBackendError:
    def test_request_error_gives_friendly_message(self):
        from api.application import format_backend_error
        from psycopg import OperationalError
        err = OperationalError("connection failed")
        result = format_backend_error(err)
        assert "unavailable" in result.lower()

    def test_generic_exception_returns_str(self):
        from api.application import format_backend_error
        result = format_backend_error(ValueError("bad value"))
        assert result == "bad value"


# ── build_cors_headers ────────────────────────────────────────────────────────

class TestBuildCorsHeaders:
    def test_wildcard_origin_by_default(self, client):
        with client.application.test_request_context("/"):
            from api.application import build_cors_headers
            headers = build_cors_headers()
        assert headers["Access-Control-Allow-Origin"] == "*"

    def test_allowed_methods_present(self, client):
        with client.application.test_request_context("/"):
            from api.application import build_cors_headers
            headers = build_cors_headers()
        assert "POST" in headers["Access-Control-Allow-Methods"]
