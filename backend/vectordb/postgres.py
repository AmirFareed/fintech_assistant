"""PostgreSQL (pgvector) access layer.

Exposes a small chainable query builder (``db.table("chunks").select(...).eq(...).execute()``)
plus ``db.rpc(...)`` for SQL functions such as ``match_chunks``. All values are sent as bound
parameters and identifiers are validated, so callers never build SQL strings themselves.
"""

from __future__ import annotations

import datetime as dt
import decimal
import re
import threading
import uuid
from typing import Any

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from utils.config import Config

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(name: str) -> sql.Identifier:
    if not isinstance(name, str) or not _IDENT.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return sql.Identifier(name)


def _is_vector(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and bool(value)
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    )


def _param(value: Any) -> Any:
    """Convert a Python value into a bindable parameter (vectors become pgvector text)."""
    if _is_vector(value):
        return "[" + ",".join(repr(float(v)) for v in value) + "]"
    if isinstance(value, dict):
        return Jsonb(value)
    return value


def _placeholder(value: Any) -> sql.Composable:
    return sql.SQL("%s::vector") if _is_vector(value) else sql.SQL("%s")


def _clean(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


def _clean_row(row: dict) -> dict:
    return {key: _clean(value) for key, value in row.items()}


class Result:
    def __init__(self, data: Any, count: int | None = None) -> None:
        self.data = data
        self.count = count


class Database:
    """Lazily-opened connection pool so importing the app never touches the network."""

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._lock = threading.Lock()

    def _get_pool(self) -> ConnectionPool:
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    pool = ConnectionPool(
                        Config.DATABASE_URL,
                        min_size=1,
                        max_size=Config.DB_POOL_MAX,
                        kwargs={
                            "autocommit": True,
                            "row_factory": dict_row,
                            "connect_timeout": int(Config.DB_TIMEOUT_SECONDS),
                        },
                        open=False,
                    )
                    pool.open(wait=True, timeout=Config.DB_TIMEOUT_SECONDS)
                    self._pool = pool
        return self._pool

    def run(self, query: sql.Composable, params: list[Any] | None = None) -> list[dict]:
        with self._get_pool().connection() as conn:
            cur = conn.execute(query, params or [])
            rows = cur.fetchall() if cur.description else []
        return [_clean_row(row) for row in rows]

    def table(self, name: str) -> "Query":
        return Query(self, name)

    def rpc(self, function: str, params: dict[str, Any] | None = None) -> "Rpc":
        return Rpc(self, function, params or {})

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None


class Rpc:
    def __init__(self, db: Database, function: str, params: dict[str, Any]) -> None:
        self._db, self._function, self._params = db, function, params

    def execute(self) -> Result:
        args = sql.SQL(", ").join(
            sql.SQL("{} => {}").format(_ident(key), _placeholder(value)) for key, value in self._params.items()
        )
        query = sql.SQL("SELECT * FROM {}({})").format(_ident(self._function), args)
        return Result(self._db.run(query, [_param(v) for v in self._params.values()]))


class Query:
    def __init__(self, db: Database, table: str) -> None:
        self._db = db
        self._table = _ident(table)
        self._action = "select"
        self._columns: list[sql.Composable] | None = None
        self._count: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[sql.Composable, list[Any]]] = []
        self._order: list[sql.Composable] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._single = False

    # ── actions ───────────────────────────────────────────────────────────────
    def select(self, columns: str = "*", count: str | None = None) -> "Query":
        self._action = "select"
        self._count = count
        cols = [c.strip() for c in columns.split(",") if c.strip()]
        self._columns = None if cols == ["*"] else [_ident(c) for c in cols]
        return self

    def insert(self, rows: dict | list[dict]) -> "Query":
        self._action, self._payload = "insert", rows
        return self

    def update(self, values: dict) -> "Query":
        self._action, self._payload = "update", values
        return self

    def delete(self) -> "Query":
        self._action = "delete"
        return self

    # ── filters ───────────────────────────────────────────────────────────────
    def _filter(self, template: str, column: str, value: Any) -> "Query":
        self._filters.append((sql.SQL(template).format(_ident(column)), [_param(value)]))
        return self

    def eq(self, column: str, value: Any) -> "Query":
        return self._filter("{} = %s", column, value)

    def neq(self, column: str, value: Any) -> "Query":
        return self._filter("{} <> %s", column, value)

    def ilike(self, column: str, pattern: str) -> "Query":
        # Compare as text so the pattern also works against non-text columns.
        return self._filter("{}::text ILIKE %s", column, pattern)

    def in_(self, column: str, values: list[Any]) -> "Query":
        return self._filter("{} = ANY(%s)", column, list(values))

    def is_(self, column: str, value: Any) -> "Query":
        if value is None or str(value).lower() == "null":
            clause = sql.SQL("{} IS NULL").format(_ident(column))
        elif str(value).lower() == "true":
            clause = sql.SQL("{} IS TRUE").format(_ident(column))
        else:
            clause = sql.SQL("{} IS FALSE").format(_ident(column))
        self._filters.append((clause, []))
        return self

    # ── modifiers ─────────────────────────────────────────────────────────────
    def order(self, column: str, desc: bool = False) -> "Query":
        self._order.append(sql.SQL("{} {}").format(_ident(column), sql.SQL("DESC" if desc else "ASC")))
        return self

    def limit(self, n: int) -> "Query":
        self._limit = int(n)
        return self

    def range(self, start: int, end: int) -> "Query":
        """Inclusive row range, like PostgREST."""
        self._offset, self._limit = int(start), int(end) - int(start) + 1
        return self

    def single(self) -> "Query":
        self._single = True
        return self

    # ── execution ─────────────────────────────────────────────────────────────
    def _where(self) -> tuple[sql.Composable, list[Any]]:
        if not self._filters:
            return sql.SQL(""), []
        clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(f for f, _ in self._filters)
        return clause, [p for _, params in self._filters for p in params]

    def execute(self) -> Result:
        where, params = self._where()
        if self._action == "select":
            return self._execute_select(where, params)
        if self._action == "insert":
            return self._execute_insert()
        if self._action == "update":
            values = self._payload or {}
            if not values:
                return Result([])
            sets = sql.SQL(", ").join(
                sql.SQL("{} = {}").format(_ident(k), _placeholder(v)) for k, v in values.items()
            )
            query = sql.SQL("UPDATE {} SET {}").format(self._table, sets) + where + sql.SQL(" RETURNING *")
            return Result(self._db.run(query, [_param(v) for v in values.values()] + params))
        query = sql.SQL("DELETE FROM {}").format(self._table) + where + sql.SQL(" RETURNING *")
        return Result(self._db.run(query, params))

    def _execute_select(self, where: sql.Composable, params: list[Any]) -> Result:
        cols = sql.SQL(", ").join(self._columns) if self._columns else sql.SQL("*")
        query = sql.SQL("SELECT {} FROM {}").format(cols, self._table) + where
        if self._order:
            query += sql.SQL(" ORDER BY ") + sql.SQL(", ").join(self._order)
        if self._limit is not None:
            query += sql.SQL(" LIMIT {}").format(sql.Literal(self._limit))
        if self._offset:
            query += sql.SQL(" OFFSET {}").format(sql.Literal(self._offset))
        rows = self._db.run(query, params)

        count = None
        if self._count == "exact":
            count_query = sql.SQL("SELECT COUNT(*) AS n FROM {}").format(self._table) + where
            count = int(self._db.run(count_query, params)[0]["n"])

        if self._single:
            if len(rows) != 1:
                raise LookupError(f"Expected exactly one row, got {len(rows)}")
            return Result(rows[0], count)
        return Result(rows, count)

    def _execute_insert(self) -> Result:
        rows = self._payload if isinstance(self._payload, list) else [self._payload]
        if not rows:
            return Result([])
        columns = list(dict.fromkeys(key for row in rows for key in row))
        row_sql, params = [], []
        for row in rows:
            values = [row.get(col) for col in columns]
            row_sql.append(sql.SQL("({})").format(sql.SQL(", ").join(_placeholder(v) for v in values)))
            params.extend(_param(v) for v in values)
        query = sql.SQL("INSERT INTO {} ({}) VALUES {} RETURNING *").format(
            self._table,
            sql.SQL(", ").join(_ident(c) for c in columns),
            sql.SQL(", ").join(row_sql),
        )
        return Result(self._db.run(query, params))


db = Database()
