"""Stateless bearer-token auth for the admin API (the frontend is served from a separate origin)."""

import hmac
from functools import wraps

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from utils.config import Config

TOKEN_MAX_AGE_SECONDS = 12 * 60 * 60
_SALT = "admin-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def credentials_valid(username, password):
    return hmac.compare_digest(str(username or "").strip(), Config.ADMIN_USERNAME) & hmac.compare_digest(
        str(password or "").strip(), Config.ADMIN_PASSWORD
    )


def issue_token():
    return _serializer().dumps({"role": "admin"})


def is_admin():
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return False
    try:
        data = _serializer().loads(token.strip(), max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    return data.get("role") == "admin"


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method != "OPTIONS" and not is_admin():
            return jsonify({"error": "Admin authentication required."}), 401
        return f(*args, **kwargs)

    return decorated
