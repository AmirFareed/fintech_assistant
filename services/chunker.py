import re


def split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    paragraph = (paragraph or "").strip()
    if not paragraph:
        return []
    if len(paragraph) <= chunk_size:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) == 1:
        sentences = re.split(r"(?<=[:;])\s+", paragraph)
    if len(sentences) == 1:
        return [paragraph[index:index + chunk_size].strip() for index in range(0, len(paragraph), chunk_size)]

    parts = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > chunk_size:
            parts.append(current.strip())
            current = sentence
        else:
            current = candidate

    if current:
        parts.append(current.strip())

    return parts


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150):
    text = text or ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraphs.extend(split_long_paragraph(paragraph, chunk_size))

    chunks = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        separator_length = 2 if current_parts else 0
        if current_parts and current_length + separator_length + len(paragraph) > chunk_size:
            chunks.append("\n\n".join(current_parts).strip())

            overlap_parts = []
            overlap_length = 0
            for part in reversed(current_parts):
                extra = len(part) + (2 if overlap_parts else 0)
                if overlap_parts and overlap_length + extra > overlap:
                    break
                overlap_parts.insert(0, part)
                overlap_length += extra

            current_parts = overlap_parts[:]
            current_length = sum(len(part) for part in current_parts) + max(0, (len(current_parts) - 1) * 2)

        current_parts.append(paragraph)
        current_length += len(paragraph) + (2 if len(current_parts) > 1 else 0)

    if current_parts:
        chunks.append("\n\n".join(current_parts).strip())

    return chunks
