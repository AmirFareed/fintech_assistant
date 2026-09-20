import pytest
from utils.language import (
    normalize_text,
    contains_arabic_script,
    is_pashto_text,
    detect_response_language,
)


class TestNormalizeText:
    def test_strips_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapses_inner_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_none_like_empty(self):
        assert normalize_text(None) == ""


class TestContainsArabicScript:
    def test_arabic_text(self):
        assert contains_arabic_script("سلام") is True

    def test_english_text(self):
        assert contains_arabic_script("hello") is False

    def test_mixed_text(self):
        assert contains_arabic_script("hello سلام") is True

    def test_empty(self):
        assert contains_arabic_script("") is False


class TestIsPashtoText:
    def test_pashto_specific_char(self):
        # ځ is in PASHTO_SPECIFIC_CHARS
        assert is_pashto_text("ځای") is True

    def test_pashto_hint_words(self):
        # "څه" and "دی" are both Pashto hint words
        assert is_pashto_text("PSID څه دی") is True

    def test_english_is_not_pashto(self):
        assert is_pashto_text("how do I pay via PSID") is False

    def test_empty_string(self):
        assert is_pashto_text("") is False

    def test_single_hint_word_among_many_arabic_words_not_enough(self):
        # 1 hint word across >3 Arabic words: the short-text shortcut doesn't apply
        assert is_pashto_text("ده الله محمد رسول کتاب") is False


class TestDetectResponseLanguage:
    def test_english_query(self):
        assert detect_response_language("How do I pay via PSID?") == "en"

    def test_pashto_query(self):
        assert detect_response_language("PSID څه دی") == "ps"

    def test_empty_defaults_to_english(self):
        assert detect_response_language("") == "en"
