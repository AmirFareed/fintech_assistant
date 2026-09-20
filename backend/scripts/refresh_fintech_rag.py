"""
Replace the FinTech RAG files in the database with the current local copies.

This script removes prior records for the known FinTech files from:
- chunks
- department_files
- storage bucket objects

It then re-ingests the updated local files for the Digital Payments department.

Usage: python -m scripts.refresh_fintech_rag
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from utils.config import Config
from ingestion.pipeline import ingest_department_file
from vectordb.postgres import db
from vectordb.file_store import remove_file


FILES = [
    "psid_info.txt",
    "easypaisa_jazzcash.txt",
    "other_banks.txt",
    "other_questions.txt",
]


FINTECH_SERVICES = [
    {
        "service_name": "What is PSID",
        "service_slug": "what-is-psid",
        "summary": "Explanation of PSID, its purpose, and how it connects a payment to an institution.",
        "keywords": ["psid", "payment slip id", "what is psid", "psid meaning", "psid definition"],
    },
    {
        "service_name": "How to Generate PSID",
        "service_slug": "generate-psid",
        "summary": "How an issuing institution generates a PSID and where the user can find it.",
        "keywords": ["generate psid", "create psid", "get psid", "psid generation", "obtain psid"],
    },
    {
        "service_name": "How to Verify PSID",
        "service_slug": "verify-psid",
        "summary": "How to verify PSID bill details before confirming a payment.",
        "keywords": ["verify psid", "check psid", "validate psid", "psid verification", "psid status"],
    },
    {
        "service_name": "PSID Format and Details",
        "service_slug": "psid-format",
        "summary": "PSID number format and the details that should be checked on a payment slip.",
        "keywords": ["psid format", "psid number", "17 digit psid", "psid structure", "psid details"],
    },
    {
        "service_name": "PSID Payment Security",
        "service_slug": "psid-security",
        "summary": "Security checks and fraud-prevention guidance for PSID payments.",
        "keywords": ["psid security", "safe payment", "secure psid", "payment safety", "psid fraud"],
    },
    {
        "service_name": "PSID Payment Troubleshooting",
        "service_slug": "psid-troubleshooting",
        "summary": "Troubleshooting failed, deducted, expired, mismatched, or unconfirmed PSID payments.",
        "keywords": ["payment failed", "money deducted", "psid error", "payment not working", "psid issue"],
    },
    {
        "service_name": "Easypaisa PSID Payment",
        "service_slug": "easypaisa-psid-payment",
        "summary": "How to pay an official PSID through the Easypaisa app.",
        "keywords": ["easypaisa", "easypaisa payment", "pay via easypaisa", "easypaisa psid"],
    },
    {
        "service_name": "JazzCash PSID Payment",
        "service_slug": "jazzcash-psid-payment",
        "summary": "How to pay an official PSID through the JazzCash app.",
        "keywords": ["jazzcash", "jazz cash", "jazzcash payment", "pay via jazzcash", "jazzcash psid"],
    },
    {
        "service_name": "Bank of Khyber PSID Payment",
        "service_slug": "bank-of-khyber-psid-payment",
        "summary": "How to pay an official PSID through the Bank of Khyber app.",
        "keywords": ["bank of khyber", "bok", "pay via bank of khyber", "bank of khyber psid"],
    },
    {
        "service_name": "HBL PSID Payment",
        "service_slug": "hbl-psid-payment",
        "summary": "How to pay an official PSID through the HBL app.",
        "keywords": ["hbl", "habib bank", "pay via hbl", "hbl psid"],
    },
    {
        "service_name": "Bank Al Habib PSID Payment",
        "service_slug": "bank-al-habib-psid-payment",
        "summary": "How to pay an official PSID through the Bank Al Habib app.",
        "keywords": ["bank al habib", "bah", "pay via bank al habib", "bank al habib psid"],
    },
    {
        "service_name": "Meezan Bank PSID Payment",
        "service_slug": "meezan-bank-psid-payment",
        "summary": "How to pay an official PSID through the Meezan Bank app.",
        "keywords": ["meezan", "meezan bank", "pay via meezan", "meezan bank psid"],
    },
    {
        "service_name": "Other Banks PSID Payment",
        "service_slug": "other-banks-psid-payment",
        "summary": "How to pay an official PSID through supported mobile and internet banking channels.",
        "keywords": ["other bank", "bank payment", "internet banking psid", "bank psid", "1bill payment"],
    },
    {
        "service_name": "General Help",
        "service_slug": "general-help",
        "summary": "General PSID assistance, payment destination guidance, and support escalation.",
        "keywords": ["help", "support", "payment destination", "where does money go", "general question"],
    },
]


def get_department_id() -> str:
    response = (
        db.table("departments")
        .select("id")
        .eq("slug", "digital-payments")
        .single()
        .execute()
    )
    if not response.data:
        raise RuntimeError("Department 'digital-payments' not found.")
    return response.data["id"]


def ensure_fintech_services(department_id: str) -> int:
    """Create missing services and refresh metadata used by routing."""
    ensured = 0

    for service in FINTECH_SERVICES:
        payload = {
            **service,
            "department_id": department_id,
            "is_active": True,
        }
        existing = (
            db.table("services")
            .select("id")
            .eq("department_id", department_id)
            .eq("service_slug", service["service_slug"])
            .limit(1)
            .execute()
        ).data or []

        if existing:
            (
                db.table("services")
                .update(payload)
                .eq("id", existing[0]["id"])
                .execute()
            )
        else:
            db.table("services").insert(payload).execute()

        ensured += 1
        print(f"  Ready: {service['service_name']}")

    return ensured


def fetch_existing_files(department_id: str) -> list[dict]:
    response = (
        db.table("department_files")
        .select("id, file_name, storage_path")
        .eq("department_id", department_id)
        .execute()
    )
    rows = response.data or []
    return [row for row in rows if row.get("file_name") in FILES]


def delete_existing_files(department_id: str) -> int:
    existing_files = fetch_existing_files(department_id)
    if not existing_files:
        print("No previous FinTech RAG files found in the database.")
        return 0

    print(f"Found {len(existing_files)} existing FinTech RAG file record(s). Removing old data...")

    removed_chunks = 0
    storage_paths: list[str] = []

    for row in existing_files:
        department_file_id = row["id"]
        storage_path = row.get("storage_path")

        chunk_response = (
            db.table("chunks")
            .delete()
            .eq("department_file_id", department_file_id)
            .execute()
        )
        removed_chunks += len(chunk_response.data or [])

        (
            db.table("department_files")
            .delete()
            .eq("id", department_file_id)
            .execute()
        )

        if storage_path:
            storage_paths.append(storage_path)

        print(f"  Removed {row['file_name']}")

    if storage_paths:
        for storage_path in storage_paths:
            try:
                remove_file(storage_path)
            except Exception as exc:
                print(f"Warning: failed to remove stored file {storage_path}: {exc}")
        print(f"Removed {len(storage_paths)} stored file(s).")

    print(f"Removed {removed_chunks} old chunk record(s).")
    return len(existing_files)


def ingest_updated_files(department_id: str) -> int:
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    total_chunks = 0

    for file_name in FILES:
        local_path = os.path.join(base_dir, file_name)
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Required file not found: {local_path}")

        print(f"Ingesting {file_name}...")
        result = ingest_department_file(
            local_file_path=local_path,
            department_id=department_id,
            original_file_name=file_name,
        )
        chunk_count = result.get("chunk_count", 0)
        total_chunks += chunk_count
        print(f"  Uploaded and indexed {chunk_count} chunk(s).")

    return total_chunks


def verify_chunk_links(department_id: str) -> None:
    response = (
        db.table("chunks")
        .select("id", count="exact")
        .eq("department_id", department_id)
        .is_("service_id", "null")
        .execute()
    )
    unmatched_count = response.count or 0
    if unmatched_count:
        raise RuntimeError(
            f"Refresh created {unmatched_count} unlinked chunk(s). "
            "Check that every 'Service Name:' matches FINTECH_SERVICES."
        )


def main() -> None:
    print("=" * 56)
    print(" Paymir AI Assistant - RAG Refresh")
    print("=" * 56)

    department_id = get_department_id()
    print("Ensuring FinTech service records...")
    service_count = ensure_fintech_services(department_id)
    print(f"Prepared {service_count} service record(s).")
    delete_existing_files(department_id)
    total_chunks = ingest_updated_files(department_id)
    verify_chunk_links(department_id)

    print()
    print(f"Refresh complete. Total new chunks: {total_chunks}")


if __name__ == "__main__":
    main()
