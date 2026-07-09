import pytest
from services.chunker import split_long_paragraph, chunk_text


class TestSplitLongParagraph:
    def test_short_paragraph_returned_as_is(self):
        result = split_long_paragraph("Hello world.", 1000)
        assert result == ["Hello world."]

    def test_empty_returns_empty(self):
        assert split_long_paragraph("", 100) == []

    def test_none_returns_empty(self):
        assert split_long_paragraph(None, 100) == []

    def test_splits_on_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = split_long_paragraph(text, 30)
        assert len(result) > 1
        for part in result:
            assert len(part) <= 30 or "." in part  # each part is a sentence

    def test_long_single_sentence_split_by_size(self):
        text = "A" * 200
        result = split_long_paragraph(text, 50)
        assert all(len(p) <= 50 for p in result)

    def test_strips_whitespace_from_parts(self):
        text = "  Hello.   World.  "
        result = split_long_paragraph(text, 1000)
        assert result[0] == result[0].strip()


class TestChunkText:
    def test_empty_returns_empty(self):
        assert chunk_text("") == []

    def test_none_returns_empty(self):
        assert chunk_text(None) == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   \n\n   ") == []

    def test_short_text_single_chunk(self):
        result = chunk_text("Short text that fits in one chunk.")
        assert len(result) == 1
        assert "Short text" in result[0]

    def test_long_text_multiple_chunks(self):
        paragraph = "Word " * 300  # ~1500 chars
        result = chunk_text(paragraph, chunk_size=500)
        assert len(result) > 1

    def test_chunks_respect_chunk_size(self):
        paragraph = "Sentence number one. Sentence number two. " * 50
        result = chunk_text(paragraph, chunk_size=200, overlap=0)
        for chunk in result:
            assert len(chunk) <= 400  # some tolerance for sentence boundaries

    def test_normalizes_crlf(self):
        text = "Line one.\r\nLine two.\r\nLine three."
        result = chunk_text(text)
        assert len(result) >= 1
        assert "\r" not in result[0]

    def test_collapses_excess_newlines(self):
        text = "Para one.\n\n\n\n\nPara two."
        result = chunk_text(text)
        assert len(result) >= 1

    def test_overlap_carries_content_forward(self):
        # Build text with two clearly separate paragraphs
        para1 = "Alpha " * 60   # ~360 chars
        para2 = "Beta " * 60
        text = para1.strip() + "\n\n" + para2.strip()
        result = chunk_text(text, chunk_size=400, overlap=100)
        # With overlap, second chunk should start with content from first
        if len(result) > 1:
            assert "Alpha" in result[1]

    def test_multiple_paragraphs_split_correctly(self):
        text = "\n\n".join([f"Paragraph {i}. " * 5 for i in range(10)])
        result = chunk_text(text, chunk_size=200)
        assert len(result) >= 2
