"""Create the pgvector extension, tables, indexes and match_chunks() from database/schema.sql.

Usage: python -m scripts.init_db
"""
from pathlib import Path

import psycopg

from utils.config import Config

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "database" / "schema.sql"


def apply_schema() -> None:
    with psycopg.connect(Config.DATABASE_URL, autocommit=True, connect_timeout=int(Config.DB_TIMEOUT_SECONDS)) as conn:
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def main() -> None:
    apply_schema()
    print("Database schema is up to date.")


if __name__ == "__main__":
    main()
