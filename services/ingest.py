import uuid
import re
from pathlib import Path
from services.supabase_client import supabase
from services.file_parser import extract_text
from services.chunker import chunk_text
from services.embeddings import embed_text
from config import Config


SERVICE_NAME_ALIASES = {
    "psid verification": "How to Verify PSID",
    "verify psid": "How to Verify PSID",
    "psid generation": "How to Generate PSID",
    "generate psid": "How to Generate PSID",
}


def get_content_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()

    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".txt":
        return "text/plain"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    raise ValueError("Unsupported file type. Only PDF, TXT, and DOCX are supported.")


def upload_file_to_storage(local_file_path: str, storage_name: str, original_file_name: str):
    content_type = get_content_type(original_file_name)

    with open(local_file_path, "rb") as f:
        supabase.storage.from_(Config.SUPABASE_BUCKET).upload(
            path=storage_name,
            file=f,
            file_options={"content-type": content_type}
        )


def create_department_file_record(department_id: str, file_name: str, storage_path: str):
    result = supabase.table("department_files").insert({
        "department_id": department_id,
        "file_name": file_name,
        "storage_path": storage_path,
        "version": "v1",
        "is_active": True
    }).execute()

    return result.data[0]


def split_by_service(text: str) -> list[dict]:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return []

    matches = list(re.finditer(r"(?im)^\s*service name\s*:\s*(.+?)\s*$", text))
    if matches:
        service_blocks = []

        leading_text = re.sub(r"(?im)^\s*=+\s*service start\s*=+\s*$", "", text[:matches[0].start()]).strip()
        if leading_text:
            service_blocks.append({
                "service_name": None,
                "text": leading_text,
            })

        for index, match in enumerate(matches):
            block_start = match.start()
            block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block_text = text[block_start:block_end].strip()
            if not block_text:
                continue

            service_blocks.append({
                "service_name": match.group(1).strip(),
                "text": block_text,
            })

        return service_blocks

    parts = [part.strip() for part in text.split("=== Service Start ===") if part.strip()]
    if parts:
        return [{
            "service_name": None,
            "text": part,
        } for part in parts]

    return [{
        "service_name": None,
        "text": text.strip(),
    }]


def normalize_service_name(service_name: str | None) -> str | None:
    if not service_name:
        return None

    normalized = " ".join(service_name.split()).strip()
    alias = SERVICE_NAME_ALIASES.get(normalized.lower())
    return alias or normalized


def clean_block_text(block_text: str, service_name: str | None) -> str:
    cleaned = (block_text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"(?im)^\s*=+\s*service start\s*=+\s*$", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*service name\s*:\s*.+?\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if not cleaned:
        return ""

    normalized_service_name = normalize_service_name(service_name)
    if normalized_service_name:
        escaped = re.escape(normalized_service_name)
        cleaned = re.sub(rf"(?im)^\s*{escaped}\s*:?\s*$", "", cleaned).strip()

    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def merge_block_parts(parts: list[str]) -> str:
    seen = set()
    merged_parts = []

    for part in parts:
        normalized = re.sub(r"\s+", " ", (part or "").strip()).lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged_parts.append(part.strip())

    return "\n\n".join(merged_parts).strip()


def get_service_by_name(department_id: str, service_name: str):
    service_name = normalize_service_name(service_name)
    if not service_name:
        return None

    exact_res = (
        supabase.table("services")
        .select("*")
        .eq("department_id", department_id)
        .ilike("service_name", service_name)
        .execute()
    )
    exact_data = exact_res.data or []
    if exact_data:
        return exact_data[0]

    partial_res = (
        supabase.table("services")
        .select("*")
        .eq("department_id", department_id)
        .ilike("service_name", f"%{service_name}%")
        .execute()
    )
    partial_data = partial_res.data or []
    if partial_data:
        return partial_data[0]

    all_res = (
        supabase.table("services")
        .select("*")
        .eq("department_id", department_id)
        .execute()
    )
    services = all_res.data or []

    service_name_tokens = {
        token for token in re.findall(r"[a-z0-9]+", service_name.lower())
        if len(token) > 2
    }
    best_match = None
    best_score = 0

    for service in services:
        candidate_text = " ".join([
            service.get("service_name", "") or "",
            " ".join(service.get("keywords") or []),
        ]).lower()
        candidate_tokens = {
            token for token in re.findall(r"[a-z0-9]+", candidate_text)
            if len(token) > 2
        }
        score = len(service_name_tokens & candidate_tokens)
        if score > best_score:
            best_score = score
            best_match = service

    if best_match and best_score >= 2:
        return best_match

    return None


def save_service_chunks(
    department_id: str,
    department_file_id: str,
    service_id: str,
    service_name: str,
    chunks: list[str]
):
    rows = []

    for idx, chunk in enumerate(chunks):
        rows.append({
            "department_id": department_id,
            "department_file_id": department_file_id,
            "service_id": service_id,
            "section_name": service_name,
            "chunk_text": chunk,
            "chunk_index": idx,
            "embedding": embed_text(chunk),
        })

    if rows:
        supabase.table("chunks").insert(rows).execute()


def save_unmatched_chunks(
    department_id: str,
    department_file_id: str,
    block_name: str,
    chunks: list[str]
):
    rows = []

    for idx, chunk in enumerate(chunks):
        rows.append({
            "department_id": department_id,
            "department_file_id": department_file_id,
            "service_id": None,
            "section_name": block_name or "general",
            "chunk_text": chunk,
            "chunk_index": idx,
            "embedding": embed_text(chunk),
        })

    if rows:
        supabase.table("chunks").insert(rows).execute()


def ingest_department_file(local_file_path: str, department_id: str, original_file_name: str):
    unique_name = f"{uuid.uuid4()}_{original_file_name}"

    upload_file_to_storage(local_file_path, unique_name, original_file_name)

    department_file = create_department_file_record(
        department_id=department_id,
        file_name=original_file_name,
        storage_path=unique_name
    )

    extracted_text = extract_text(local_file_path)

    if not extracted_text.strip():
        raise ValueError("No text could be extracted from the uploaded file.")

    service_blocks = split_by_service(extracted_text)

    total_chunks = 0
    matched_services = 0
    unmatched_blocks = 0

    if service_blocks:
        grouped_blocks: dict[tuple[str, str], dict] = {}

        for block in service_blocks:
            raw_service_name = block["service_name"]
            block_text = clean_block_text(block["text"], raw_service_name)

            if not block_text:
                continue

            service = get_service_by_name(department_id, raw_service_name)
            if service:
                group_key = ("service", service["id"])
                bucket = grouped_blocks.setdefault(group_key, {
                    "kind": "service",
                    "service": service,
                    "section_name": service["service_name"],
                    "parts": [],
                })
            else:
                section_name = normalize_service_name(raw_service_name) or "general"
                group_key = ("unmatched", section_name.lower())
                bucket = grouped_blocks.setdefault(group_key, {
                    "kind": "unmatched",
                    "service": None,
                    "section_name": section_name,
                    "parts": [],
                })

            bucket["parts"].append(block_text)

        for block in grouped_blocks.values():
            merged_text = merge_block_parts(block["parts"])
            if not merged_text:
                continue

            chunks = chunk_text(merged_text)
            if block["kind"] == "service":
                save_service_chunks(
                    department_id=department_id,
                    department_file_id=department_file["id"],
                    service_id=block["service"]["id"],
                    service_name=block["section_name"],
                    chunks=chunks
                )
                matched_services += 1
            else:
                save_unmatched_chunks(
                    department_id=department_id,
                    department_file_id=department_file["id"],
                    block_name=block["section_name"],
                    chunks=chunks
                )
                unmatched_blocks += 1
                print(f"Warning: service not found in database for block: {block['section_name']}")

            total_chunks += len(chunks)
    else:
        chunks = chunk_text(extracted_text)
        save_unmatched_chunks(
            department_id=department_id,
            department_file_id=department_file["id"],
            block_name="general",
            chunks=chunks
        )
        total_chunks = len(chunks)
        unmatched_blocks = 1

    return {
        "department_file_id": department_file["id"],
        "file_name": original_file_name,
        "storage_path": unique_name,
        "chunk_count": total_chunks,
        "matched_services": matched_services,
        "unmatched_blocks": unmatched_blocks
    }
