import re


PASHTO_SPECIFIC_CHARS = set("ځښڼګټډړږۍې")
ARABIC_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

PASHTO_HINT_WORDS = {
    "سلام",
    "اسلام",
    "عليکم",
    "علیکم",
    "څه",
    "شی",
    "دی",
    "ده",
    "دي",
    "څنګه",
    "ولې",
    "زما",
    "ستاسو",
    "تاسو",
    "مونږ",
    "موږ",
    "راسره",
    "مهرباني",
    "لطفا",
    "ووایه",
    "راکړه",
    "کړم",
    "وکړم",
    "کوم",
    "پوښتنه",
    "پیسې",
    "رسید",
    "د",
}


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def contains_arabic_script(text: str) -> bool:
    return bool(ARABIC_SCRIPT_RE.search(text or ""))


def is_pashto_text(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False

    if any(char in PASHTO_SPECIFIC_CHARS for char in normalized):
        return True

    words = {word for word in re.findall(r"[\u0600-\u06FF]+", normalized)}
    hint_matches = words & PASHTO_HINT_WORDS
    if len(hint_matches) >= 2:
        return True
    return contains_arabic_script(normalized) and len(hint_matches) >= 1 and len(words) <= 3


def detect_response_language(text: str) -> str:
    return "ps" if is_pashto_text(text) else "en"
