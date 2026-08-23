from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.rag import RAGEngine
from app.services.store import KnowledgeRepository


@pytest.fixture()
def engine(tmp_path: Path) -> RAGEngine:
    return RAGEngine(KnowledgeRepository(tmp_path / "test.sqlite3"))


@pytest.fixture()
def policy_text() -> str:
    return (
        "Vendor Purchase Policy. Department managers approve purchases up to $10,000. "
        "Purchases between $10,001 and $25,000 require director approval. "
        "Purchases over $25,000 require approval from both the vice president and Finance. "
        "All new vendors must complete security and sanctions screening before onboarding."
    )


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"
