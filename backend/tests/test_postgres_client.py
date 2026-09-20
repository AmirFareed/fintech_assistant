from unittest.mock import patch

import pytest

from vectordb import postgres
from vectordb.postgres import Database


def capture(build):
    """Run a query builder against a fake Database and return (sql_text, params)."""
    db = Database()
    seen = {}

    def fake_run(query, params=None):
        seen["sql"] = query.as_string(None)
        seen["params"] = params
        return [{"n": 3}] if "COUNT(*)" in seen["sql"] else []

    with patch.object(db, "run", side_effect=fake_run):
        build(db).execute()
    return seen["sql"], seen["params"]


def test_select_with_filters_order_and_range():
    sql_text, params = capture(
        lambda db: db.table("chunks").select("id, chunk_text").eq("department_id", "d1").is_("service_id", "null")
        .order("chunk_index").range(10, 19)
    )
    assert sql_text == (
        'SELECT "id", "chunk_text" FROM "chunks" WHERE "department_id" = %s AND "service_id" IS NULL '
        'ORDER BY "chunk_index" ASC LIMIT 10 OFFSET 10'
    )
    assert params == ["d1"]


def test_insert_embeds_vectors_as_pgvector_text():
    sql_text, params = capture(
        lambda db: db.table("chunks").insert([{"chunk_text": "a", "embedding": [0.5, 0.25]}, {"chunk_text": "b", "embedding": None}])
    )
    assert '("chunk_text", "embedding") VALUES (%s, %s::vector), (%s, %s)' in sql_text
    assert params == ["a", "[0.5,0.25]", "b", None]


def test_update_and_delete_return_rows():
    sql_text, _ = capture(lambda db: db.table("chunks").update({"service_id": "s"}).eq("id", "c"))
    assert sql_text == 'UPDATE "chunks" SET "service_id" = %s WHERE "id" = %s RETURNING *'
    sql_text, _ = capture(lambda db: db.table("chunks").delete().eq("id", "c"))
    assert sql_text == 'DELETE FROM "chunks" WHERE "id" = %s RETURNING *'


def test_ilike_and_in_and_bool_filters():
    sql_text, params = capture(
        lambda db: db.table("services").select("*").ilike("service_name", "%pay%").is_("is_active", True).in_("id", ["a", "b"])
    )
    assert '"service_name"::text ILIKE %s' in sql_text
    assert '"is_active" IS TRUE' in sql_text
    assert '"id" = ANY(%s)' in sql_text
    assert params == ["%pay%", ["a", "b"]]


def test_exact_count_runs_separate_count_query():
    db = Database()
    calls = []

    def fake_run(query, params=None):
        text = query.as_string(None)
        calls.append(text)
        return [{"n": 7}] if "COUNT(*)" in text else [{"id": "1"}]

    with patch.object(db, "run", side_effect=fake_run):
        result = db.table("feedback").select("id", count="exact").eq("rating", 1).range(0, 24).execute()
    assert result.count == 7
    assert result.data == [{"id": "1"}]
    assert calls[1] == 'SELECT COUNT(*) AS n FROM "feedback" WHERE "rating" = %s'


def test_single_requires_exactly_one_row():
    db = Database()
    with patch.object(db, "run", return_value=[]):
        with pytest.raises(LookupError):
            db.table("departments").select("id").eq("slug", "x").single().execute()
    with patch.object(db, "run", return_value=[{"id": "1"}]):
        assert db.table("departments").select("id").single().execute().data == {"id": "1"}


def test_rpc_passes_named_args_and_vector_cast():
    db = Database()
    seen = {}

    def fake_run(query, params=None):
        seen["sql"], seen["params"] = query.as_string(None), params
        return []

    with patch.object(db, "run", side_effect=fake_run):
        db.rpc("match_chunks", {"query_embedding": [0.1, 0.2], "match_count": 6, "filter_service_id": None}).execute()
    assert seen["sql"] == 'SELECT * FROM "match_chunks"("query_embedding" => %s::vector, "match_count" => %s, "filter_service_id" => %s)'
    assert seen["params"] == ["[0.1,0.2]", 6, None]


@pytest.mark.parametrize("bad", ["chunks; DROP TABLE x", "a b", "", "1abc", 'x"y'])
def test_invalid_identifiers_are_rejected(bad):
    with pytest.raises(ValueError):
        postgres.Query(Database(), bad)
    with pytest.raises(ValueError):
        Database().table("chunks").eq(bad, 1)


def test_rows_are_json_friendly():
    import datetime as dt
    import uuid

    row = postgres._clean_row({"id": uuid.UUID(int=1), "at": dt.datetime(2026, 1, 2, 3, 4, tzinfo=dt.timezone.utc), "n": 1})
    assert row == {"id": "00000000-0000-0000-0000-000000000001", "at": "2026-01-02T03:04:00+00:00", "n": 1}
