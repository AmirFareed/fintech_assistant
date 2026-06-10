import re

from services.supabase_client import supabase
from services.embeddings import embed_text


CHUNK_COLUMNS = "id, department_id, department_file_id, service_id, section_name, chunk_text, chunk_index"


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(text))


def load_chunks(
    department_id: str | None = None,
    service_id: str | None = None,
) -> list[dict]:
    query = supabase.table("chunks").select(CHUNK_COLUMNS).order("department_file_id").order("chunk_index")
    if department_id:
        query = query.eq("department_id", department_id)
    if service_id:
        query = query.eq("service_id", service_id)
    response = query.execute()
    return response.data or []


def build_query_phrases(query: str) -> list[str]:
    tokens = tokenize(query)
    phrases = []

    for size in (3, 2):
        if len(tokens) < size:
            continue
        for index in range(len(tokens) - size + 1):
            phrases.append(" ".join(tokens[index:index + size]))

    return phrases


def score_chunk(query: str, chunk: dict) -> float:
    query_norm = normalize(query)
    query_tokens = set(tokenize(query))
    query_phrases = build_query_phrases(query)

    section_name = normalize(chunk.get("section_name", ""))
    chunk_text = normalize(chunk.get("chunk_text", ""))
    haystack = f"{section_name} {chunk_text}".strip()
    haystack_tokens = set(tokenize(haystack))

    score = 0.0

    if section_name and section_name in query_norm:
        score += 10.0
    if query_norm and query_norm in haystack:
        score += 8.0

    overlap = query_tokens & haystack_tokens
    score += len(overlap) * 2.0
    score += (len(overlap) / max(len(query_tokens), 1)) * 4.0

    for token in query_tokens:
        if len(token) > 3 and token in section_name:
            score += 2.5

    for phrase in query_phrases:
        if phrase in haystack:
            score += 2.5

    return score


def score_rows(rows: list[dict], query: str, limit: int) -> list[dict]:
    scored = []

    for row in rows:
        score = score_chunk(query, row)
        if score <= 0:
            continue
        scored.append({**row, "similarity": score, "keyword_score": score, "vector_score": 0.0})

    scored.sort(key=lambda item: item["similarity"], reverse=True)
    return scored[:limit]


def merge_ranked_results(
    query: str,
    rows: list[dict],
    keyword_results: list[dict],
    vector_results: list[dict],
) -> list[dict]:
    rows_by_id = {row["id"]: row for row in rows if row.get("id")}
    merged: dict[str, dict] = {}

    for item in keyword_results:
        item_id = item.get("id")
        if not item_id:
            continue
        merged[item_id] = {**rows_by_id.get(item_id, {}), **item}

    for item in vector_results:
        item_id = item.get("id")
        if not item_id:
            continue

        base = merged.setdefault(item_id, {**rows_by_id.get(item_id, {}), **item})
        for key, value in item.items():
            if value is not None:
                base[key] = value
        base["vector_score"] = max(float(item.get("similarity") or 0.0), base.get("vector_score", 0.0))

    ranked = []
    for item_id, item in merged.items():
        keyword_score = float(item.get("keyword_score") or score_chunk(query, item))
        vector_score = float(item.get("vector_score") or 0.0)
        hybrid_score = keyword_score + (max(vector_score, 0.0) * 4.0)
        ranked.append({
            **rows_by_id.get(item_id, {}),
            **item,
            "keyword_score": keyword_score,
            "vector_score": vector_score,
            "similarity": hybrid_score,
        })

    ranked.sort(key=lambda item: item["similarity"], reverse=True)
    return ranked


def expand_with_neighbors(ranked_chunks: list[dict], rows: list[dict], limit: int) -> list[dict]:
    if not ranked_chunks:
        return []

    rows_by_file: dict[str, list[dict]] = {}
    row_positions: dict[str, int] = {}

    for row in rows:
        row_id = row.get("id")
        if not row_id:
            continue
        file_id = row.get("department_file_id") or "__unknown__"
        bucket = rows_by_file.setdefault(file_id, [])
        row_positions[row_id] = len(bucket)
        bucket.append(row)

    expanded = []
    seen = set()

    for seed in ranked_chunks[: min(3, len(ranked_chunks))]:
        seed_id = seed.get("id")
        file_id = seed.get("department_file_id") or "__unknown__"
        siblings = rows_by_file.get(file_id, [])
        position = row_positions.get(seed_id, 0)

        start = max(position - 1, 0)
        end = min(position + 2, len(siblings))

        for sibling in siblings[start:end]:
            sibling_id = sibling.get("id")
            if not sibling_id or sibling_id in seen:
                continue

            distance = abs((sibling.get("chunk_index") or 0) - (seed.get("chunk_index") or 0))
            expanded.append({
                **sibling,
                "similarity": max(float(seed.get("similarity") or 0.0) - (distance * 0.25), 0.0),
            })
            seen.add(sibling_id)

            if len(expanded) >= limit:
                return expanded

    for item in ranked_chunks:
        item_id = item.get("id")
        if not item_id or item_id in seen:
            continue
        expanded.append(item)
        seen.add(item_id)
        if len(expanded) >= limit:
            break

    return expanded


def fallback_search_chunks(
    query: str,
    match_count: int = 5,
    department_id: str | None = None,
    service_id: str | None = None,
):
    rows = load_chunks(department_id=department_id, service_id=service_id)
    return score_rows(rows=rows, query=query, limit=match_count)


def search_chunks_debug(
    query: str,
    match_count: int = 5,
    department_id: str | None = None,
    service_id: str | None = None,
):
    rows = load_chunks(department_id=department_id, service_id=service_id)
    keyword_limit = max(match_count * 4, 12)
    keyword_results = score_rows(rows=rows, query=query, limit=keyword_limit)

    try:
        query_vector = embed_text(query)

        response = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": query_vector,
                "match_count": keyword_limit,
                "filter_department_id": department_id,
                "filter_service_id": service_id,
            },
        ).execute()

        results = response.data or []
        if results:
            ranked = merge_ranked_results(
                query=query,
                rows=rows,
                keyword_results=keyword_results,
                vector_results=results,
            )
            return {
                "mode": "hybrid_vector_keyword",
                "chunks": expand_with_neighbors(ranked_chunks=ranked, rows=rows, limit=match_count),
            }
    except Exception:
        pass

    return {
        "mode": "keyword_fallback",
        "chunks": expand_with_neighbors(ranked_chunks=keyword_results, rows=rows, limit=match_count),
    }


def search_chunks(
    query: str,
    match_count: int = 5,
    department_id: str | None = None,
    service_id: str | None = None,
):
    return search_chunks_debug(
        query=query,
        match_count=match_count,
        department_id=department_id,
        service_id=service_id,
    )["chunks"]
