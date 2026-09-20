"""Application configuration loaded from config.yaml with environment overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _load_yaml() -> dict[str, Any]:
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def _value(config: dict[str, Any], section: str, key: str, default: Any) -> Any:
    return config.get(section, {}).get(key, default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


_CONFIG = _load_yaml()


class Config:
    PROJECT_ROOT = PROJECT_ROOT
    SECRET_KEY = os.getenv("SECRET_KEY", _value(_CONFIG, "app", "secret_key", "dev-secret-key"))
    PORT = int(os.getenv("PORT", _value(_CONFIG, "app", "port", 5000)))
    UPLOAD_FOLDER = str(PROJECT_ROOT / _value(_CONFIG, "app", "upload_folder", "uploads"))
    # Set when running behind a reverse proxy (Caddy/nginx) so client IPs come from X-Forwarded-For.
    TRUST_PROXY = _env_bool("TRUST_PROXY", False)
    WIDGET_ALLOWED_ORIGINS = os.getenv(
        "WIDGET_ALLOWED_ORIGINS", _value(_CONFIG, "app", "allowed_origins", "*")
    )

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", _value(_CONFIG, "admin", "username", "admin"))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", _value(_CONFIG, "admin", "password", "changeme123"))

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        _value(_CONFIG, "database", "url", "postgresql://fintech:fintech@localhost:5432/fintech"),
    )
    DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", _value(_CONFIG, "database", "pool_max", 5)))
    DB_TIMEOUT_SECONDS = float(os.getenv("DB_TIMEOUT_SECONDS", _value(_CONFIG, "database", "timeout_seconds", 10)))
    FILE_STORAGE_DIR = os.getenv(
        "FILE_STORAGE_DIR",
        str(PROJECT_ROOT / _value(_CONFIG, "database", "file_storage_dir", "uploads/knowledge_base")),
    )

    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", _value(_CONFIG, "chunking", "size", 1000)))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", _value(_CONFIG, "chunking", "overlap", 150)))
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", _value(_CONFIG, "embeddings", "model", "BAAI/bge-small-en-v1.5")
    )
    ENABLE_VECTOR_RETRIEVAL = _env_bool(
        "ENABLE_VECTOR_RETRIEVAL", bool(_value(_CONFIG, "retrieval", "enable_vector", True))
    )
    RETRIEVAL_MATCH_COUNT = int(
        os.getenv("RETRIEVAL_MATCH_COUNT", _value(_CONFIG, "retrieval", "match_count", 6))
    )

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", _value(_CONFIG, "llm", "provider", "auto")).strip().lower()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", _value(_CONFIG, "llm", "groq_model", "openai/gpt-oss-120b"))
    QEHWA_MODEL_ID = os.getenv(
        "QEHWA_MODEL_ID", _value(_CONFIG, "llm", "qehwa_model", "junaid008/qehwa-pashto-llm")
    )
    QEHWA_DEVICE = os.getenv("QEHWA_DEVICE", _value(_CONFIG, "llm", "qehwa_device", "auto")).strip().lower()
    QEHWA_MAX_NEW_TOKENS = int(
        os.getenv("QEHWA_MAX_NEW_TOKENS", _value(_CONFIG, "llm", "max_new_tokens", 300))
    )
    QEHWA_TEMPERATURE = float(
        os.getenv("QEHWA_TEMPERATURE", _value(_CONFIG, "llm", "temperature", 0.3))
    )
