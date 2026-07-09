import pytest
from services.router import normalize, detect_intent


class TestNormalize:
    def test_lowercases(self):
        assert normalize("HELLO") == "hello"

    def test_strips_edges(self):
        assert normalize("  hi  ") == "hi"

    def test_collapses_spaces(self):
        assert normalize("how  to  pay") == "how to pay"

    def test_empty(self):
        assert normalize("") == ""

    def test_none(self):
        assert normalize(None) == ""


class TestDetectIntentGreeting:
    def test_hi(self):
        assert detect_intent("hi") == "greeting"

    def test_hello(self):
        assert detect_intent("hello") == "greeting"

    def test_salam(self):
        assert detect_intent("salam") == "greeting"

    def test_aoa(self):
        assert detect_intent("aoa") == "greeting"

    def test_short_greeting_phrase(self):
        assert detect_intent("hi there") == "greeting"

    def test_arabic_salam(self):
        assert detect_intent("سلام") == "greeting"


class TestDetectIntentEasypaisa:
    def test_easypaisa_word(self):
        assert detect_intent("how to pay via easypaisa") == "easypaisa_payment"

    def test_easy_paisa_spaced(self):
        assert detect_intent("easy paisa payment steps") == "easypaisa_payment"


class TestDetectIntentJazzcash:
    def test_jazzcash(self):
        assert detect_intent("jazzcash payment") == "jazzcash_payment"

    def test_jazz_cash_spaced(self):
        assert detect_intent("jazz cash guide") == "jazzcash_payment"


class TestDetectIntentOtherBanks:
    def test_hbl(self):
        assert detect_intent("pay via hbl") == "other_banks_payment"

    def test_internet_banking(self):
        assert detect_intent("internet banking psid") == "other_banks_payment"

    def test_which_banks_support(self):
        assert detect_intent("which banks support psid") == "other_banks_payment"


class TestDetectIntentPsidVerify:
    def test_verify_psid(self):
        assert detect_intent("how to verify psid") == "psid_verify"

    def test_check_psid(self):
        assert detect_intent("check psid") == "psid_verify"

    def test_psid_status(self):
        assert detect_intent("psid status") == "psid_verify"


class TestDetectIntentPsidGenerate:
    def test_generate_psid(self):
        assert detect_intent("how to generate psid") == "psid_generate"

    def test_create_psid(self):
        assert detect_intent("create psid") == "psid_generate"

    def test_get_psid(self):
        assert detect_intent("how to get psid") == "psid_generate"


class TestDetectIntentPsidFormat:
    def test_psid_format(self):
        assert detect_intent("psid format") == "psid_format"

    def test_24_digit(self):
        assert detect_intent("what is the 24 digit psid number") == "psid_format"


class TestDetectIntentPsidSecurity:
    def test_psid_secure(self):
        assert detect_intent("is psid secure") == "psid_security"

    def test_psid_fraud(self):
        assert detect_intent("psid fraud prevention") == "psid_security"


class TestDetectIntentPsidTroubleshooting:
    def test_psid_failed(self):
        assert detect_intent("psid payment failed") == "psid_troubleshooting"

    def test_psid_error(self):
        assert detect_intent("psid error") == "psid_troubleshooting"

    def test_payment_problem(self):
        assert detect_intent("payment problem") == "psid_troubleshooting"


class TestDetectIntentPsidInfo:
    def test_what_is_psid(self):
        assert detect_intent("what is psid") == "psid_info"

    def test_psid_standalone(self):
        assert detect_intent("psid") == "psid_info"


class TestDetectIntentPsidPayment:
    def test_how_to_pay(self):
        assert detect_intent("how to pay") == "psid_payment"

    def test_online_payment(self):
        assert detect_intent("online payment") == "psid_payment"

    def test_psid_pay(self):
        assert detect_intent("psid pay") == "psid_payment"

    def test_where_does_money_go(self):
        assert detect_intent("where does my money go") == "psid_payment"


class TestDetectIntentGeneralHelp:
    def test_unrelated_query(self):
        assert detect_intent("what is the weather today") == "general_help"

    def test_random_text(self):
        assert detect_intent("tell me a joke") == "general_help"
