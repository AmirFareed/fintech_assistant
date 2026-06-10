from services.supabase_client import supabase
from services.embeddings import embed_text


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


GREETING_WORDS = [
    "hi", "hello", "hey", "salam", "assalam", "aoa", "aslam",
    "good morning", "good afternoon", "good evening", "howdy",
    "greetings", "sup", "whats up", "what's up", "helo", "hii", "hiii",
    "asslam", "assalamualaikum", "walaikum",
    "سلام", "اسلام عليکم", "اسلام علیکم", "وعليکم سلام", "وعلیکم سلام",
]

EASYPAISA_WORDS = ["easypaisa", "easy paisa"]
JAZZCASH_WORDS = ["jazzcash", "jazz cash", "jcash"]
OTHER_BANK_WORDS = [
    "other bank", "other banks", "hbl", "ubl", "mcb", "alfalah",
    "meezan", "allied bank", "askari", "faysal", "standard chartered",
    "internet banking", "bank of punjab", "conventional bank",
    "what banks support", "banks support psid", "which banks support",
    "supported banks", "banks support payment",
]

PSID_VERIFY_PHRASES = [
    "verify psid", "check psid", "validate psid", "psid status",
    "psid valid", "is my psid", "confirm psid", "how to verify",
    "psid verification", "psid check",
    "psid تصدیق", "psid چک", "psid څنګه تصدیق", "psid څنګه چک",
]
PSID_GENERATE_PHRASES = [
    "generate psid", "create psid", "get psid", "how to get psid",
    "psid generate", "new psid", "how to generate", "psid kaise banaye",
    "psid جوړ", "psid څنګه جوړ", "psid ترلاسه", "psid څنګه ترلاسه",
]
PSID_FORMAT_PHRASES = [
    "psid format", "psid number", "24 digit", "24-digit", "psid structure",
]
PSID_INFO_PHRASES = [
    "what is psid", "what's psid", "psid mean", "psid stands",
    "define psid", "explain psid", "tell me about psid",
    "psid kya", "what does psid", "psid ka matlab",
    "psid څه شی دی", "psid څه دی", "psid په اړه", "psid معلومات",
]
PSID_SECURITY_WORDS = ["secure", "safe", "security", "fraud", "scam", "خوندي", "محفوظ", "فراډ"]
PSID_TROUBLESHOOTING_WORDS = [
    "fail", "failed", "error", "problem", "issue", "stuck",
    "wrong", "not working", "expired", "accepted", "already paid",
    "ناکام", "غلط", "ستونزه", "مسئله", "کار نه کوي",
]

PSID_PAYMENT_PHRASES = [
    "pay through psid", "payment through psid", "digital payment psid",
    "pay using psid", "pay with psid", "payment via psid",
    "make payment psid", "pay psid", "psid payment method",
    "how to pay", "make a payment", "online payment", "digital payment",
    "pay online", "make digital payment",
    "psid پیمنټ", "psid payment", "د psid له لارې پیسې", "د psid له لارې ادایګي",
    "څنګه پیسې ورکړم", "څنګه پیمنټ وکړم",
]

PAYMENT_DESTINATION_PHRASES = [
    "where does my money go",
    "where does the money go",
    "where does payment go",
    "where is my payment sent",
    "where is the payment sent",
    "payment destination",
]


def detect_intent(query: str) -> str:
    q = normalize(query)
    words = q.split()

    if q in GREETING_WORDS:
        return "greeting"
    if len(words) <= 3 and any(greeting in q for greeting in GREETING_WORDS):
        return "greeting"

    if any(word in q for word in EASYPAISA_WORDS):
        return "easypaisa_payment"

    if any(word in q for word in JAZZCASH_WORDS):
        return "jazzcash_payment"

    if any(word in q for word in OTHER_BANK_WORDS):
        return "other_banks_payment"

    if any(phrase in q for phrase in PSID_VERIFY_PHRASES):
        return "psid_verify"

    if any(phrase in q for phrase in PSID_GENERATE_PHRASES):
        return "psid_generate"

    if any(phrase in q for phrase in PSID_FORMAT_PHRASES):
        return "psid_format"

    if "psid" in q and any(word in q for word in PSID_SECURITY_WORDS):
        return "psid_security"

    if "psid" in q and any(word in q for word in PSID_TROUBLESHOOTING_WORDS):
        return "psid_troubleshooting"

    if any(word in q for word in ["payment problem", "payment issue", "payment error"]):
        return "psid_troubleshooting"

    if any(phrase in q for phrase in PSID_INFO_PHRASES):
        return "psid_info"

    if any(phrase in q for phrase in PAYMENT_DESTINATION_PHRASES):
        return "psid_payment"

    if "psid" in q and any(word in q for word in ["pay", "payment"]):
        return "psid_payment"

    if any(phrase in q for phrase in PSID_PAYMENT_PHRASES):
        return "psid_payment"

    if "psid" in q:
        return "psid_info"

    return "general_help"


def find_best_service(user_query: str, top_k: int = 5):
    res = supabase.table("services").select(
        "id, department_id, service_name, service_slug, summary, official_link, fee_link, keywords"
    ).eq("is_active", True).execute()

    services = res.data or []
    if not services:
        return None, []

    q = normalize(user_query)
    scored = []

    for svc in services:
        score = 0.0
        name = normalize(svc.get("service_name", ""))
        summary = normalize(svc.get("summary", ""))
        keywords = [normalize(keyword) for keyword in (svc.get("keywords") or [])]

        if name and name in q:
            score += 8.0
        for keyword in keywords:
            if keyword and keyword in q:
                score += 5.0
        for word in name.split():
            if len(word) > 3 and word in q:
                score += 1.0
        for word in summary.split():
            if len(word) > 4 and word in q:
                score += 0.5

        scored.append((svc, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    top_matches = [item[0] for item in scored[:top_k]]

    if scored and scored[0][1] > 0:
        return scored[0][0], top_matches

    try:
        query_vec = embed_text(user_query)
        best_service = None
        best_similarity = -1.0

        for svc in services:
            text = " ".join([
                svc.get("service_name", "") or "",
                svc.get("summary", "") or "",
                " ".join(svc.get("keywords") or []),
            ]).strip()
            if not text:
                continue

            svc_vec = embed_text(text)
            similarity = sum(a * b for a, b in zip(query_vec, svc_vec))
            if similarity > best_similarity:
                best_similarity = similarity
                best_service = svc

        if best_service:
            return best_service, top_matches
    except Exception:
        pass

    return (top_matches[0] if top_matches else None), top_matches
