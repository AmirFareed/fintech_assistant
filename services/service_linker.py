from services.supabase_client import supabase


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().split())


def score_service_match(chunk_text: str, service: dict) -> int:
    score = 0
    chunk_text = normalize_text(chunk_text)

    service_name = normalize_text(service.get("service_name", ""))
    keywords = service.get("keywords", []) or []

    if service_name and service_name in chunk_text:
        score += 5

    for keyword in keywords:
        keyword = normalize_text(keyword)
        if keyword and keyword in chunk_text:
            score += 3

    # extra loose matching by service name words
    for word in service_name.split():
        if len(word) > 3 and word in chunk_text:
            score += 1

    return score


def link_chunks_to_services(department_id: str):
    chunks_res = (
        supabase.table("chunks")
        .select("id, chunk_text, service_id")
        .eq("department_id", department_id)
        .is_("service_id", "null")
        .order("chunk_index")
        .execute()
    )
    chunks = chunks_res.data or []

    services_res = (
        supabase.table("services")
        .select("id, service_name, service_slug, keywords")
        .eq("department_id", department_id)
        .eq("is_active", True)
        .execute()
    )
    services = services_res.data or []

    linked_count = 0
    unmatched_count = 0

    for chunk in chunks:
        best_service = None
        best_score = 0

        for service in services:
            score = score_service_match(chunk["chunk_text"], service)
            if score > best_score:
                best_score = score
                best_service = service

        if best_service and best_score > 0:
            (
                supabase.table("chunks")
                .update({"service_id": best_service["id"]})
                .eq("id", chunk["id"])
                .execute()
            )
            linked_count += 1
            print(
                f"Linked chunk {chunk['id']} -> {best_service['service_name']} (score={best_score})"
            )
        else:
            unmatched_count += 1
            print(f"No service match for chunk {chunk['id']}")

    return {
        "total_chunks_checked": len(chunks),
        "linked_count": linked_count,
        "unmatched_count": unmatched_count,
    }