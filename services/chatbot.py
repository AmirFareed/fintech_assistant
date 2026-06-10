import time

from services.language_utils import detect_response_language
from services.router import detect_intent, find_best_service
from services.retrieval import search_chunks, search_chunks_debug
from services.response_generator import (
    PAYMENT_OPTIONS,
    GUARD_RAIL_RESPONSE,
    generate_greeting_response,
    generate_chat_response,
    get_suggested_questions,
    is_injection_attempt,
)
from services.supabase_client import supabase


SERVICE_NAME_BY_INTENT = {
    "easypaisa_payment": "Easypaisa PSID Payment",
    "jazzcash_payment": "JazzCash PSID Payment",
    "other_banks_payment": "Other Banks PSID Payment",
    "psid_verify": "How to Verify PSID",
    "psid_generate": "How to Generate PSID",
    "psid_format": "PSID Format and Details",
    "psid_security": "PSID Payment Security",
    "psid_troubleshooting": "PSID Payment Troubleshooting",
    "general_help": "General Help",
}

SEARCH_MATCH_COUNT = 6
SUPPORTED_RESPONSE_LANGUAGES = {"en", "ur", "ps"}
MAX_QUERY_LENGTH = 500


def merge_chunk_lists(*chunk_lists: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for chunk_list in chunk_lists:
        for chunk in chunk_list:
            chunk_id = chunk.get("id")
            if chunk_id and chunk_id in seen:
                continue
            if chunk_id:
                seen.add(chunk_id)
            merged.append(chunk)
    return merged[:SEARCH_MATCH_COUNT]


def resolve_response_language(user_query: str, preferred_language: str | None = None) -> str:
    if preferred_language in SUPPORTED_RESPONSE_LANGUAGES:
        return preferred_language
    return detect_response_language(user_query)


def store_query(
    query: str,
    intent: str,
    service: str = None,
    session_id: str = None,
    response_language: str = None,
    had_result: bool = None,
    response_time_ms: int = None,
) -> None:
    try:
        supabase.table("user_queries").insert({
            "query_text": query,
            "intent": intent,
            "service": service,
            "session_id": session_id,
            "response_language": response_language,
            "had_result": had_result,
            "response_time_ms": response_time_ms,
        }).execute()
    except Exception:
        pass


def log_token_usage(session_id: str, usage: dict, model: str) -> None:
    try:
        supabase.table("token_usage").insert({
            "session_id": session_id,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": model,
        }).execute()
    except Exception:
        pass


def get_service_by_name(service_name: str) -> dict | None:
    res = (
        supabase.table("services")
        .select("id, department_id, service_name, service_slug, summary, official_link, fee_link, keywords")
        .eq("is_active", True)
        .ilike("service_name", service_name)
        .limit(1)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


def resolve_service(user_query: str, intent: str) -> dict | None:
    preferred_service_name = SERVICE_NAME_BY_INTENT.get(intent)
    if preferred_service_name:
        service = get_service_by_name(preferred_service_name)
        if service:
            return service
    best_service, _ = find_best_service(user_query)
    return best_service


def retrieve_chunks(user_query: str, intent: str, service: dict | None) -> list[dict]:
    if not service:
        return []

    if intent == "psid_payment":
        return search_chunks(
            query=user_query,
            match_count=SEARCH_MATCH_COUNT,
            department_id=service["department_id"],
            service_id=None,
        )

    primary_chunks = search_chunks(
        query=user_query,
        match_count=SEARCH_MATCH_COUNT,
        department_id=service["department_id"],
        service_id=service["id"],
    )
    if primary_chunks:
        return primary_chunks

    fallback_chunks = search_chunks(
        query=user_query,
        match_count=SEARCH_MATCH_COUNT,
        department_id=service["department_id"],
        service_id=None,
    )
    return merge_chunk_lists(primary_chunks, fallback_chunks)


def retrieve_chunks_debug(user_query: str, intent: str, service: dict | None) -> dict:
    if not service:
        return {"mode": "none", "chunks": []}

    if intent == "psid_payment":
        return search_chunks_debug(
            query=user_query,
            match_count=SEARCH_MATCH_COUNT,
            department_id=service["department_id"],
            service_id=None,
        )

    primary_result = search_chunks_debug(
        query=user_query,
        match_count=SEARCH_MATCH_COUNT,
        department_id=service["department_id"],
        service_id=service["id"],
    )
    if primary_result["chunks"]:
        return primary_result

    fallback_result = search_chunks_debug(
        query=user_query,
        match_count=SEARCH_MATCH_COUNT,
        department_id=service["department_id"],
        service_id=None,
    )
    return {
        "mode": f"{primary_result['mode']}+fallback",
        "chunks": merge_chunk_lists(primary_result["chunks"], fallback_result["chunks"]),
    }


def debug_chat_query(user_query: str) -> dict:
    intent = detect_intent(user_query)
    service = resolve_service(user_query, intent)
    retrieval = retrieve_chunks_debug(user_query, intent, service)
    return {
        "query": user_query,
        "intent": intent,
        "service": service,
        "retrieval_mode": retrieval["mode"],
        "chunk_count": len(retrieval["chunks"]),
        "chunks": retrieval["chunks"],
    }


def handle_chat_query(
    user_query: str,
    preferred_language: str | None = None,
    history: list[dict] | None = None,
    session_id: str | None = None,
) -> dict:
    t_start = time.monotonic()

    # Guard rail: block injection attempts before anything else
    if is_injection_attempt(user_query):
        response_language = resolve_response_language(user_query, preferred_language)
        return {
            "answer": GUARD_RAIL_RESPONSE.get(response_language, GUARD_RAIL_RESPONSE["en"]),
            "service": None,
            "intent": "guard_rail",
            "response_language": response_language,
            "suggested_questions": get_suggested_questions(response_language),
            "payment_options": None,
        }

    intent = detect_intent(user_query)
    response_language = resolve_response_language(user_query, preferred_language)

    if intent == "greeting":
        store_query(user_query, intent, session_id=session_id, response_language=response_language, had_result=True)
        return {
            "answer": generate_greeting_response(response_language),
            "service": None,
            "intent": "greeting",
            "response_language": response_language,
            "suggested_questions": get_suggested_questions(response_language),
            "payment_options": None,
        }

    best_service = resolve_service(user_query, intent)
    chunks = retrieve_chunks(user_query, intent, best_service)
    had_result = bool(chunks)

    if not chunks:
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        store_query(user_query, intent, session_id=session_id, response_language=response_language, had_result=False, response_time_ms=elapsed_ms)

        if response_language == "ps":
            fallback_answer = (
                "زه د **PSID-based digital payments** په اړه مرسته کوم. "
                "ستاسو د پوښتنې لپاره مې ځانګړي معلومات ونه موندل.\n\n"
                "مهرباني وکړئ پوښتنه په بل ډول ولیکئ یا له لاندې موضوعاتو څخه یوه وټاکئ:"
            )
        elif response_language == "ur":
            fallback_answer = (
                "میں **PSID-based digital payments** کے بارے میں مدد کے لیے حاضر ہوں۔ "
                "مجھے آپ کے سوال کے لیے مخصوص معلومات نہیں مل سکیں۔\n\n"
                "براہ کرم سوال کو دوسرے انداز میں لکھیں یا نیچے دیے گئے موضوعات میں سے ایک منتخب کریں:"
            )
        else:
            fallback_answer = (
                "I'm here to help with **PSID-based digital payments**. "
                "I couldn't find specific information for your query.\n\n"
                "Please try rephrasing your question or select a topic below:"
            )
        return {
            "answer": fallback_answer,
            "service": None,
            "intent": intent,
            "response_language": response_language,
            "suggested_questions": get_suggested_questions(response_language),
            "payment_options": None,
        }

    answer, usage = generate_chat_response(
        user_query=user_query,
        service=best_service,
        chunks=chunks,
        intent=intent,
        response_language=response_language,
        history=history,
    )

    elapsed_ms = int((time.monotonic() - t_start) * 1000)
    service_name = best_service["service_name"] if best_service else None

    store_query(
        user_query, intent, service=service_name,
        session_id=session_id, response_language=response_language,
        had_result=had_result, response_time_ms=elapsed_ms,
    )

    if usage.get("total_tokens", 0) > 0 and session_id:
        from services.llm_client import GROQ_MODEL
        log_token_usage(session_id, usage, GROQ_MODEL)

    return {
        "answer": answer,
        "service": service_name,
        "intent": intent,
        "response_language": response_language,
        "suggested_questions": get_suggested_questions(response_language)[:3],
        "payment_options": PAYMENT_OPTIONS if intent == "psid_payment" else None,
    }
