from __future__ import annotations

from app.services.rag import RAGEngine


def test_stats_and_query_history(engine: RAGEngine, policy_text: str) -> None:
    engine.ingest_bytes(policy_text.encode(), "policy.txt")
    engine.answer("What approvals apply above $25,000?", channel="telegram")
    stats = engine.repository.stats()
    history = engine.repository.list_queries()
    assert stats.documents == 1
    assert stats.chunks >= 1
    assert stats.queries == 1
    assert history[0].channel == "telegram"


def test_document_listing(engine: RAGEngine, policy_text: str) -> None:
    engine.ingest_bytes(policy_text.encode(), "policy.txt", source="Google Drive")
    documents = engine.repository.list_documents()
    assert documents[0].name == "policy.txt"
    assert documents[0].source == "Google Drive"
