from __future__ import annotations

import pytest

from app.services.chunker import chunk_document
from app.services.parser import DocumentParseError, parse_document


def test_text_document_is_parsed_and_chunked(policy_text: str) -> None:
    parsed = parse_document(policy_text.encode(), "policy.txt")
    chunks = chunk_document(parsed, chunk_size=120, overlap=20)
    assert parsed.file_type == "txt"
    assert len(chunks) >= 2
    assert all(chunk.content for chunk in chunks)


def test_rejects_unknown_file_type(policy_text: str) -> None:
    with pytest.raises(DocumentParseError, match="Supported formats"):
        parse_document(policy_text.encode(), "policy.csv")


def test_rejects_empty_document() -> None:
    with pytest.raises(DocumentParseError, match="empty"):
        parse_document(b"", "empty.txt")
