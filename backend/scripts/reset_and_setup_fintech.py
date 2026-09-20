"""
Applies the database schema, clears ALL existing knowledge-base data and sets up
the FinTech / Digital Payments department and services.

Run: python -m scripts.reset_and_setup_fintech
"""
from dotenv import load_dotenv
load_dotenv()

from scripts.init_db import apply_schema
from vectordb.postgres import db

DEPARTMENT = {
    "name":        "Digital Payments",
    "slug":        "digital-payments",
    "description": "PSID-based digital payment services for Pakistan"
}

SERVICES = [
    {
        "service_name": "What is PSID",
        "service_slug": "what-is-psid",
        "summary":      "Explanation of PSID (Payment Slip ID), its purpose and format",
        "keywords":     ["psid", "payment slip id", "what is psid", "psid meaning", "psid definition"],
        "is_active":    True,
    },
    {
        "service_name": "How to Generate PSID",
        "service_slug": "generate-psid",
        "summary":      "Steps to generate a PSID for digital payment",
        "keywords":     ["generate psid", "create psid", "get psid", "psid generation"],
        "is_active":    True,
    },
    {
        "service_name": "How to Verify PSID",
        "service_slug": "verify-psid",
        "summary":      "How to verify or check the validity of a PSID",
        "keywords":     ["verify psid", "check psid", "validate psid", "psid verification", "psid status"],
        "is_active":    True,
    },
    {
        "service_name": "PSID Format and Details",
        "service_slug": "psid-format",
        "summary":      "PSID number format, structure and technical details",
        "keywords":     ["psid format", "psid number", "24 digit psid", "psid structure"],
        "is_active":    True,
    },
    {
        "service_name": "PSID Payment Security",
        "service_slug": "psid-security",
        "summary":      "Security features and safety of PSID-based digital payments",
        "keywords":     ["psid security", "safe payment", "secure psid", "payment safety"],
        "is_active":    True,
    },
    {
        "service_name": "PSID Payment Troubleshooting",
        "service_slug": "psid-troubleshooting",
        "summary":      "Troubleshooting failed or stuck PSID payments",
        "keywords":     ["payment failed", "psid error", "payment not working", "payment problem", "psid issue"],
        "is_active":    True,
    },
    {
        "service_name": "Easypaisa PSID Payment",
        "service_slug": "easypaisa-psid-payment",
        "summary":      "How to pay using PSID through the Easypaisa app",
        "keywords":     ["easypaisa", "easypaisa payment", "pay via easypaisa", "easypaisa psid"],
        "is_active":    True,
    },
    {
        "service_name": "JazzCash PSID Payment",
        "service_slug": "jazzcash-psid-payment",
        "summary":      "How to pay using PSID through the JazzCash app",
        "keywords":     ["jazzcash", "jazz cash", "jazzcash payment", "pay via jazzcash", "jazzcash psid"],
        "is_active":    True,
    },
    {
        "service_name": "Bank of Khyber PSID Payment",
        "service_slug": "bank-of-khyber-psid-payment",
        "summary":      "How to pay using PSID through the Bank of Khyber app",
        "keywords":     ["bank of khyber", "bok", "pay via bank of khyber", "bank of khyber psid"],
        "is_active":    True,
    },
    {
        "service_name": "HBL PSID Payment",
        "service_slug": "hbl-psid-payment",
        "summary":      "How to pay using PSID through the HBL app",
        "keywords":     ["hbl", "habib bank", "pay via hbl", "hbl psid"],
        "is_active":    True,
    },
    {
        "service_name": "Bank Al Habib PSID Payment",
        "service_slug": "bank-al-habib-psid-payment",
        "summary":      "How to pay using PSID through the Bank Al Habib app",
        "keywords":     ["bank al habib", "bah", "pay via bank al habib", "bank al habib psid"],
        "is_active":    True,
    },
    {
        "service_name": "Meezan Bank PSID Payment",
        "service_slug": "meezan-bank-psid-payment",
        "summary":      "How to pay using PSID through the Meezan Bank app",
        "keywords":     ["meezan", "meezan bank", "pay via meezan", "meezan bank psid"],
        "is_active":    True,
    },
    {
        "service_name": "Other Banks PSID Payment",
        "service_slug": "other-banks-psid-payment",
        "summary":      "How to pay using PSID through conventional and other banks",
        "keywords":     ["other bank", "bank payment", "internet banking psid", "bank psid", "conventional bank"],
        "is_active":    True,
    },
    {
        "service_name": "General Help",
        "service_slug": "general-help",
        "summary":      "General assistance and handling of irrelevant or off-topic questions",
        "keywords":     ["help", "support", "general", "question", "other"],
        "is_active":    True,
    },
]


def clear_database():
    print("Clearing existing data...")
    try:
        db.table("chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  [OK] chunks cleared")
    except Exception as e:
        print(f"  [WARN] chunks: {e}")

    try:
        db.table("department_files").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  [OK] department_files cleared")
    except Exception as e:
        print(f"  [WARN] department_files: {e}")

    try:
        db.table("services").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  [OK] services cleared")
    except Exception as e:
        print(f"  [WARN] services: {e}")

    try:
        db.table("departments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  [OK] departments cleared")
    except Exception as e:
        print(f"  [WARN] departments: {e}")

    print()


def setup_fintech():
    print("Creating Digital Payments department...")
    dept_res = db.table("departments").insert(DEPARTMENT).execute()
    dept_id = dept_res.data[0]["id"]
    print(f"  [OK] department id: {dept_id}\n")

    print("Inserting services...")
    ok = err = 0
    for svc in SERVICES:
        try:
            db.table("services").insert({**svc, "department_id": dept_id}).execute()
            print(f"  [OK] {svc['service_name']}")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {svc['service_name']}: {e}")
            err += 1

    print(f"\nDone. Services inserted: {ok} | Errors: {err}")
    return dept_id


def main():
    print("=" * 55)
    print("  Paymir AI Assistant - DB Reset & Setup")
    print("=" * 55)
    print()

    apply_schema()
    print("Schema applied.\n")

    clear_database()
    dept_id = setup_fintech()

    print(f"\nAll done! Department ID: {dept_id}")
    print("Next: run  python -m scripts.ingest_fintech")


if __name__ == "__main__":
    main()
