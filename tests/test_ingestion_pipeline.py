from ingestion.pipeline import normalize_service_name, service_keywords, service_slug


def test_supported_banks_block_uses_generic_other_banks_service():
    assert normalize_service_name("Supported Banks PSID Payment") == "Other Banks PSID Payment"


def test_named_bank_service_metadata_is_routable():
    assert service_slug("Meezan Bank PSID Payment") == "meezan-bank-psid-payment"
    assert "meezan bank" in service_keywords("Meezan Bank PSID Payment")
    assert "pay via meezan bank" in service_keywords("Meezan Bank PSID Payment")
