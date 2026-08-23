from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.services.parser import ParsedDocument


@dataclass(frozen=True)
class TextChunk:
    page: int
    index: int
    content: str


def _windows(text: str, target: int, overlap: int) -> list[str]:
    if len(text) <= target:
        return [text]
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]
    windows: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > target:
            windows.append(current.strip())
            carry = current[-overlap:].lstrip() if overlap else ""
            current = f"{carry} {sentence}".strip()
        else:
            current = f"{current} {sentence}".strip()
    if current:
        windows.append(current.strip())
    return windows


def chunk_document(document: ParsedDocument, chunk_size: int | None = None, overlap: int | None = None) -> list[TextChunk]:
    target = chunk_size or settings.chunk_size
    carry = overlap if overlap is not None else settings.chunk_overlap
    chunks: list[TextChunk] = []
    for page in document.pages:
        for content in _windows(page.text, target, carry):
            if len(content.split()) >= 5:
                chunks.append(TextChunk(page=page.number, index=len(chunks), content=content))
    return chunks
