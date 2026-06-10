from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)

    return "\n\n".join(pages)


def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = []

    for para in doc.paragraphs:
        text = (para.text or "").strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError("Unsupported file type. Only PDF, TXT, and DOCX are supported.")