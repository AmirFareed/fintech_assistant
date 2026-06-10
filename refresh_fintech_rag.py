"""
Replace the FinTech RAG files in Supabase with the current local copies.

This script removes prior records for the known FinTech files from:
- chunks
- department_files
- storage bucket objects

It then re-ingests the updated local files for the Digital Payments department.

Usage: python refresh_fintech_rag.py
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from config import Config
from services.ingest import ingest_department_file
from services.supabase_client import supabase


FILES = [
    "psid_info.txt",
    "easypaisa_jazzcash.txt",
    "other_banks.txt",
    "irrelevant_questions.txt",
]


def get_department_id() -> str:
    response = (
        supabase.table("departments")
        .select("id")
        .eq("slug", "digital-payments")
        .single()
        .execute()
    )
    if not response.data:
        raise RuntimeError("Department 'digital-payments' not found.")
    return response.data["id"]


def fetch_existing_files(department_id: str) -> list[dict]:
    response = (
        supabase.table("department_files")
        .select("id, file_name, storage_path")
        .eq("department_id", department_id)
        .execute()
    )
    rows = response.data or []
    return [row for row in rows if row.get("file_name") in FILES]


def delete_existing_files(department_id: str) -> int:
    existing_files = fetch_existing_files(department_id)
    if not existing_files:
        print("No previous FinTech RAG files found in Supabase.")
        return 0

    print(f"Found {len(existing_files)} existing FinTech RAG file record(s). Removing old data...")

    removed_chunks = 0
    storage_paths: list[str] = []

    for row in existing_files:
        department_file_id = row["id"]
        storage_path = row.get("storage_path")

        chunk_response = (
            supabase.table("chunks")
            .delete()
            .eq("department_file_id", department_file_id)
            .execute()
        )
        removed_chunks += len(chunk_response.data or [])

        (
            supabase.table("department_files")
            .delete()
            .eq("id", department_file_id)
            .execute()
        )

        if storage_path:
            storage_paths.append(storage_path)

        print(f"  Removed {row['file_name']}")

    if storage_paths:
        try:
            supabase.storage.from_(Config.SUPABASE_BUCKET).remove(storage_paths)
            print(f"Removed {len(storage_paths)} storage object(s) from bucket '{Config.SUPABASE_BUCKET}'.")
        except Exception as exc:
            print(f"Warning: failed to remove one or more storage objects: {exc}")

    print(f"Removed {removed_chunks} old chunk record(s).")
    return len(existing_files)


def ingest_updated_files(department_id: str) -> int:
    base_dir = os.path.dirname(os.path.abspath(__file__))
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


def main() -> None:
    print("=" * 56)
    print(" FinTech AI Assistant - RAG Refresh")
    print("=" * 56)

    department_id = get_department_id()
    delete_existing_files(department_id)
    total_chunks = ingest_updated_files(department_id)

    print()
    print(f"Refresh complete. Total new chunks: {total_chunks}")


if __name__ == "__main__":
    main()
