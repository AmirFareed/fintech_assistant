"""
Ingests all 4 FinTech RAG files into Supabase under the Digital Payments department.
Run AFTER reset_and_setup_fintech.py
Usage: python -m scripts.ingest_fintech
"""
import os
from dotenv import load_dotenv
load_dotenv()

from ingestion.pipeline import ingest_department_file
from vectordb.supabase import supabase

FILES = [
    "psid_info.txt",
    "easypaisa_jazzcash.txt",
    "other_banks.txt",
    "other_questions.txt",
]

def main():
    res = supabase.table("departments").select("id").eq("slug", "digital-payments").single().execute()
    if not res.data:
        print("ERROR: 'digital-payments' department not found. Run reset_and_setup_fintech.py first.")
        return

    dept_id = res.data["id"]
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    total   = 0

    for fname in FILES:
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            print(f"[SKIP] {fname} not found")
            continue
        print(f"[INGESTING] {fname}")
        try:
            result = ingest_department_file(
                local_file_path=path,
                department_id=dept_id,
                original_file_name=fname,
            )
            n = result.get("chunk_count", 0)
            total += n
            print(f"  OK  {n} chunks\n")
        except Exception as e:
            print(f"  FAIL  {e}\n")

    print(f"Done. Total chunks: {total}")

if __name__ == "__main__":
    main()
