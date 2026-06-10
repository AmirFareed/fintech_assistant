import os
from functools import wraps

from flask import render_template, request, redirect, url_for, session
from admin import admin_bp
from services.supabase_client import supabase

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")
PER_PAGE = 25


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
def index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        if (request.form.get("username", "").strip() == ADMIN_USERNAME and
                request.form.get("password", "").strip() == ADMIN_PASSWORD):
            session["admin_logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        error = "Invalid username or password."
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@login_required
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
        r = supabase.table("user_queries").select("id", count="exact").execute()
        stats["total_queries"] = r.count or 0
    except Exception:
        pass

    try:
        r = supabase.table("user_queries").select("id", count="exact").eq("had_result", False).execute()
        stats["no_result_count"] = r.count or 0
    except Exception:
        pass

    try:
        r = supabase.table("feedback").select("rating").execute()
        fb = r.data or []
        stats["total_feedback"] = len(fb)
        stats["positive_feedback"] = sum(1 for f in fb if f.get("rating") == 1)
        stats["negative_feedback"] = sum(1 for f in fb if f.get("rating") == -1)
        if stats["total_feedback"]:
            stats["satisfaction_rate"] = round(stats["positive_feedback"] / stats["total_feedback"] * 100)
    except Exception:
        pass

    try:
        r = supabase.table("token_usage").select("total_tokens").execute()
        stats["total_tokens"] = sum(t.get("total_tokens", 0) for t in (r.data or []))
    except Exception:
        pass

    try:
        r = supabase.table("user_queries").select("intent").execute()
        counts: dict[str, int] = {}
        for row in (r.data or []):
            k = row.get("intent") or "unknown"
            counts[k] = counts.get(k, 0) + 1
        stats["top_intents"] = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        pass

    try:
        r = (supabase.table("user_queries")
             .select("query_text, intent, service, response_language, had_result, created_at")
             .order("created_at", desc=True).limit(10).execute())
        stats["recent_queries"] = r.data or []
    except Exception:
        pass

    return render_template("admin/dashboard.html", stats=stats)


# ── Queries ───────────────────────────────────────────────────────────────────

@admin_bp.route("/queries")
@login_required
def queries():
    page = max(1, int(request.args.get("page", 1)))
    intent_filter = request.args.get("intent", "").strip()
    result_filter = request.args.get("result", "").strip()
    offset = (page - 1) * PER_PAGE

    try:
        q = supabase.table("user_queries").select(
            "query_text, intent, service, response_language, had_result, response_time_ms, created_at"
        ).order("created_at", desc=True)
        if intent_filter:
            q = q.eq("intent", intent_filter)
        if result_filter == "found":
            q = q.eq("had_result", True)
        elif result_filter == "not_found":
            q = q.eq("had_result", False)
        rows = q.range(offset, offset + PER_PAGE - 1).execute().data or []

        cq = supabase.table("user_queries").select("id", count="exact")
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
    return render_template(
        "admin/queries.html",
        rows=rows, page=page, total_pages=total_pages, total=total,
        intent_filter=intent_filter, result_filter=result_filter,
    )


# ── Feedback ──────────────────────────────────────────────────────────────────

@admin_bp.route("/feedback")
@login_required
def feedback():
    page = max(1, int(request.args.get("page", 1)))
    rating_filter = request.args.get("rating", "").strip()
    offset = (page - 1) * PER_PAGE

    try:
        q = supabase.table("feedback").select("*").order("created_at", desc=True)
        if rating_filter == "positive":
            q = q.eq("rating", 1)
        elif rating_filter == "negative":
            q = q.eq("rating", -1)
        rows = q.range(offset, offset + PER_PAGE - 1).execute().data or []

        cq = supabase.table("feedback").select("id", count="exact")
        if rating_filter == "positive":
            cq = cq.eq("rating", 1)
        elif rating_filter == "negative":
            cq = cq.eq("rating", -1)
        total = cq.execute().count or len(rows)
    except Exception:
        rows, total = [], 0

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    return render_template(
        "admin/feedback.html",
        rows=rows, page=page, total_pages=total_pages, total=total,
        rating_filter=rating_filter,
    )


# ── Test chatbot ──────────────────────────────────────────────────────────────

@admin_bp.route("/test")
@login_required
def test_chatbot():
    return render_template("admin/test.html")


# ── Knowledge base ────────────────────────────────────────────────────────────

@admin_bp.route("/knowledge")
@login_required
def knowledge():
    departments, files = [], []
    try:
        departments = supabase.table("departments").select("*").order("name").execute().data or []
    except Exception:
        pass
    try:
        files = (supabase.table("department_files")
                 .select("id, original_file_name, created_at, department_id")
                 .order("created_at", desc=True).limit(50).execute().data or [])
        dept_map = {d["id"]: d["name"] for d in departments}
        for f in files:
            f["department_name"] = dept_map.get(f.get("department_id"), "—")
    except Exception:
        pass
    return render_template("admin/knowledge.html", departments=departments, files=files)
