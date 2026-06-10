import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from httpx import RequestError
from werkzeug.utils import secure_filename
from config import Config
from user import user_bp
from admin import admin_bp
from services.supabase_client import supabase
from services.ingest import ingest_department_file
from services.chatbot import handle_chat_query, debug_chat_query, MAX_QUERY_LENGTH

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(admin_bp)

# ── Rate limiting ─────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def format_backend_error(exc):
    if isinstance(exc, RequestError):
        return "The knowledge base is currently unavailable. Check your Supabase connection and try again."
    return str(exc)


def build_cors_headers():
    allowed_origins = app.config.get("WIDGET_ALLOWED_ORIGINS", "*")
    request_origin = request.headers.get("Origin", "")
    allowed_origin_list = [o.strip() for o in allowed_origins.split(",") if o.strip()]
    allow_origin = "*"
    if allowed_origin_list and "*" not in allowed_origin_list:
        allow_origin = request_origin if request_origin in allowed_origin_list else allowed_origin_list[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
    }


@app.after_request
def apply_widget_cors_headers(response):
    for key, value in build_cors_headers().items():
        response.headers[key] = value
    return response


def is_admin():
    return bool(session.get("admin_logged_in"))


def get_public_chat_user_key():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        session_id = (data.get("session_id") or "").strip()
        if session_id:
            return f"chat-user:{session_id}"
    return f"chat-ip:{get_remote_address()}"


def get_departments():
    try:
        res = supabase.table("departments").select("*").order("name").execute()
        return res.data or [], None
    except Exception as exc:
        app.logger.exception("Failed to load departments")
        return [], format_backend_error(exc)


def process_department_upload(department_id, file):
    if not department_id or not file:
        return False, "Department and file are required."
    filename = secure_filename(file.filename)
    if not filename:
        return False, "Please choose a file."
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Only PDF, TXT, and DOCX files are supported right now."
    local_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(local_path)
    try:
        result = ingest_department_file(
            local_file_path=local_path,
            department_id=department_id,
            original_file_name=filename,
        )
        return True, {
            "message": f"Upload successful. {result['chunk_count']} chunks created.",
            "chunk_count": result["chunk_count"],
            "file_name": filename,
        }
    except Exception as exc:
        app.logger.exception("Department upload failed")
        return False, f"Error: {format_backend_error(exc)}"


# ── Public routes (User Panel) ────────────────────────────────────────────────

@app.route("/")
def home():
    # Root always goes to the user panel
    return redirect(url_for("user_widget.user_widget_demo"))


@app.route("/health")
def health():
    status = {"status": "ok", "supabase": "ok", "version": "2.0"}
    try:
        supabase.table("departments").select("id").limit(1).execute()
    except Exception as exc:
        status["supabase"] = f"error: {exc}"
        status["status"] = "degraded"
    code = 200 if status["status"] == "ok" else 503
    return jsonify(status), code


# ── Public API (used by the widget) ──────────────────────────────────────────

@app.route("/api/chat", methods=["POST", "OPTIONS"])
@limiter.limit("30 per minute; 50 per day", key_func=get_public_chat_user_key)
def api_chat():
    if request.method == "OPTIONS":
        response = make_response("", 204)
        for key, value in build_cors_headers().items():
            response.headers[key] = value
        return response

    data = request.get_json(silent=True) or {}
    user_query = (data.get("user_query") or "").strip()
    preferred_language = (data.get("preferred_language") or "").strip().lower() or None
    history = data.get("history") or None
    session_id = (data.get("session_id") or "").strip() or None

    if not user_query:
        return jsonify({"error": "Empty query"}), 400

    if len(user_query) > MAX_QUERY_LENGTH:
        return jsonify({"error": f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed."}), 400

    clean_history = None
    if isinstance(history, list):
        clean_history = [
            {"role": h["role"], "content": str(h["content"])[:2000]}
            for h in history
            if isinstance(h, dict) and h.get("role") in {"user", "assistant"} and h.get("content")
        ][-10:]

    try:
        result = handle_chat_query(
            user_query,
            preferred_language=preferred_language,
            history=clean_history,
            session_id=session_id,
        )
        service = result.get("service")
        if isinstance(service, dict):
            service = service.get("service_name")
        return jsonify({
            "answer":              result.get("answer", ""),
            "service":             service,
            "intent":              result.get("intent"),
            "response_language":   result.get("response_language"),
            "suggested_questions": result.get("suggested_questions"),
            "payment_options":     result.get("payment_options"),
        })
    except Exception as exc:
        app.logger.exception("Chat request failed")
        return jsonify({"error": format_backend_error(exc)}), 500


@app.route("/api/feedback", methods=["POST"])
@limiter.limit("60 per minute")
def api_feedback():
    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    if rating not in (1, -1):
        return jsonify({"error": "rating must be 1 or -1"}), 400
    try:
        supabase.table("feedback").insert({
            "query_text": (data.get("query_text") or "")[:1000],
            "rating": rating,
            "comment": (data.get("comment") or "")[:500] or None,
            "intent": data.get("intent") or None,
            "service": data.get("service") or None,
            "session_id": data.get("session_id") or None,
        }).execute()
        return jsonify({"ok": True})
    except Exception as exc:
        app.logger.exception("Feedback save failed")
        return jsonify({"error": str(exc)}), 500


# ── Admin-only API ────────────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
@limiter.limit("10 per minute")
def api_upload():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    department_id = request.form.get("department_id")
    file = request.files.get("file")
    ok, result = process_department_upload(department_id, file)
    if ok:
        return jsonify(result)
    if isinstance(result, str) and result.startswith("Error:"):
        return jsonify({"error": result}), 500
    return jsonify({"error": result}), 400


@app.route("/debug/retrieval", methods=["GET", "POST"])
def debug_retrieval():
    if not is_admin():
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        user_query = (data.get("user_query") or "").strip()
    else:
        user_query = (request.args.get("q") or "").strip()

    if not user_query:
        return jsonify({"error": "Provide a query with ?q=... or POST {\"user_query\": \"...\"}"}), 400

    try:
        result = debug_chat_query(user_query)
        service = result.get("service")
        return jsonify({
            "query": result["query"],
            "intent": result["intent"],
            "service": {
                "id": service.get("id"),
                "department_id": service.get("department_id"),
                "service_name": service.get("service_name"),
                "service_slug": service.get("service_slug"),
            } if isinstance(service, dict) else None,
            "retrieval_mode": result["retrieval_mode"],
            "chunk_count": result["chunk_count"],
            "chunks": [
                {
                    "id": chunk.get("id"),
                    "service_id": chunk.get("service_id"),
                    "section_name": chunk.get("section_name"),
                    "chunk_index": chunk.get("chunk_index"),
                    "similarity": chunk.get("similarity"),
                    "chunk_text": chunk.get("chunk_text"),
                }
                for chunk in result["chunks"]
            ],
        })
    except Exception as exc:
        app.logger.exception("Debug retrieval failed")
        return jsonify({"error": format_backend_error(exc)}), 500


# ── Legacy redirects (old /chat and /upload URLs) ─────────────────────────────

@app.route("/chat")
def chat_redirect():
    return redirect(url_for("admin.test_chatbot"), 301)


@app.route("/upload")
def upload_redirect():
    return redirect(url_for("admin.knowledge"), 301)


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"error": "Too many requests. Please wait a moment before trying again."}), 429


@app.errorhandler(403)
def forbidden_handler(e):
    return jsonify({"error": "Access forbidden."}), 403


if __name__ == "__main__":
    app.run(debug=True)
