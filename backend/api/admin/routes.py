from flask import jsonify, request

from api.admin import admin_bp
from api.auth import admin_required, credentials_valid, issue_token
from vectordb.postgres import db

PER_PAGE = 25

QUERY_INTENTS = [
    "greeting", "psid_info", "psid_generate", "psid_verify", "psid_format", "psid_security",
    "psid_troubleshooting", "psid_payment", "easypaisa_payment", "jazzcash_payment",
    "other_banks_payment", "general_help", "guard_rail",
]


def _page_arg():
    try:
        return max(1, int(request.args.get("page", 1)))
    except ValueError:
        return 1


# ── Auth ──────────────────────────────────────────────────────────────────────

@admin_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    if not credentials_valid(data.get("username"), data.get("password")):
        return jsonify({"error": "Invalid username or password."}), 401
    return jsonify({"token": issue_token()})


@admin_bp.get("/me")
@admin_required
def me():
    return jsonify({"ok": True})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    stats = {
        "total_queries": 0,
        "total_feedback": 0,
        "positive_feedback": 0,
        "negative_feedback": 0,
        "satisfaction_rate": 0,
        "total_tokens": 0,
        "top_intents": [],
        "recent_queries": [],
        "no_result_count": 0,
    }

    try:
        r = db.table("user_queries").select("id", count="exact").execute()
        stats["total_queries"] = r.count or 0
    except Exception:
        pass

    try:
        r = db.table("user_queries").select("id", count="exact").eq("had_result", False).execute()
        stats["no_result_count"] = r.count or 0
    except Exception:
        pass

    try:
        r = db.table("feedback").select("rating").execute()
        fb = r.data or []
        stats["total_feedback"] = len(fb)
        stats["positive_feedback"] = sum(1 for f in fb if f.get("rating") == 1)
        stats["negative_feedback"] = sum(1 for f in fb if f.get("rating") == -1)
        if stats["total_feedback"]:
            stats["satisfaction_rate"] = round(stats["positive_feedback"] / stats["total_feedback"] * 100)
    except Exception:
        pass

    try:
        r = db.table("token_usage").select("total_tokens").execute()
        stats["total_tokens"] = sum(t.get("total_tokens", 0) for t in (r.data or []))
    except Exception:
        pass

    try:
        r = db.table("user_queries").select("intent").execute()
        counts: dict[str, int] = {}
        for row in (r.data or []):
            k = row.get("intent") or "unknown"
            counts[k] = counts.get(k, 0) + 1
        stats["top_intents"] = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        pass

    try:
        r = (db.table("user_queries")
             .select("query_text, intent, service, response_language, had_result, created_at")
             .order("created_at", desc=True).limit(10).execute())
        stats["recent_queries"] = r.data or []
    except Exception:
        pass

    return jsonify(stats)


# ── Queries ───────────────────────────────────────────────────────────────────

@admin_bp.get("/queries")
@admin_required
def queries():
    page = _page_arg()
    intent_filter = request.args.get("intent", "").strip()
    result_filter = request.args.get("result", "").strip()
    offset = (page - 1) * PER_PAGE

    try:
        q = db.table("user_queries").select(
            "query_text, intent, service, response_language, had_result, response_time_ms, created_at"
        ).order("created_at", desc=True)
        if intent_filter:
            q = q.eq("intent", intent_filter)
        if result_filter == "found":
            q = q.eq("had_result", True)
        elif result_filter == "not_found":
            q = q.eq("had_result", False)
        rows = q.range(offset, offset + PER_PAGE - 1).execute().data or []

        cq = db.table("user_queries").select("id", count="exact")
        if intent_filter:
            cq = cq.eq("intent", intent_filter)
        if result_filter == "found":
            cq = cq.eq("had_result", True)
        elif result_filter == "not_found":
            cq = cq.eq("had_result", False)
        total = cq.execute().count or len(rows)
    except Exception:
        rows, total = [], 0

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    return jsonify(rows=rows, page=page, total_pages=total_pages, total=total, intents=QUERY_INTENTS)


# ── Feedback ──────────────────────────────────────────────────────────────────

@admin_bp.get("/feedback")
@admin_required
def feedback():
    page = _page_arg()
    rating_filter = request.args.get("rating", "").strip()
    offset = (page - 1) * PER_PAGE

    try:
        q = db.table("feedback").select("*").order("created_at", desc=True)
        if rating_filter == "positive":
            q = q.eq("rating", 1)
        elif rating_filter == "negative":
            q = q.eq("rating", -1)
        rows = q.range(offset, offset + PER_PAGE - 1).execute().data or []

        cq = db.table("feedback").select("id", count="exact")
        if rating_filter == "positive":
            cq = cq.eq("rating", 1)
        elif rating_filter == "negative":
            cq = cq.eq("rating", -1)
        total = cq.execute().count or len(rows)
    except Exception:
        rows, total = [], 0

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    return jsonify(rows=rows, page=page, total_pages=total_pages, total=total)


# ── Knowledge base ────────────────────────────────────────────────────────────

@admin_bp.get("/knowledge")
@admin_required
def knowledge():
    departments, files = [], []
    try:
        departments = db.table("departments").select("*").order("name").execute().data or []
    except Exception:
        pass
    try:
        resp = db.table("department_files").select("id, file_name, department_id, uploaded_at").limit(50).execute()
        files = resp.data or []
        dept_map = {d["id"]: d["name"] for d in departments}
        for f in files:
            f["department_name"] = dept_map.get(f.get("department_id"), "—")
            f["original_file_name"] = f.get("file_name", "—")
            f["created_at"] = f.get("uploaded_at")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[KB ERROR] {e}")
    return jsonify(departments=departments, files=files)


@admin_bp.delete("/files/<file_id>")
@admin_required
def delete_file(file_id):
    try:
        # Get storage_path before deleting the record
        rec = db.table("department_files").select("storage_path").eq("id", file_id).single().execute()
        storage_path = rec.data.get("storage_path") if rec.data else None

        # Delete associated chunks first
        db.table("chunks").delete().eq("department_file_id", file_id).execute()

        # Delete the department_files record
        db.table("department_files").delete().eq("id", file_id).execute()

        # Delete the stored original (best-effort)
        if storage_path:
            try:
                remove_file(storage_path)
            except Exception:
                pass

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
