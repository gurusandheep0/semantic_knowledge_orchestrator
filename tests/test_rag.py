from __future__ import annotations

from app.services.rag import RAGEngine


def test_ingestion_and_deduplication(engine: RAGEngine, policy_text: str) -> None:
    first = engine.ingest_bytes(policy_text.encode(), "vendor-policy.txt")
    second = engine.ingest_bytes(policy_text.encode(), "vendor-policy.txt")
    assert first.chunks_created >= 1
    assert first.document.status == "indexed"
    assert second.deduplicated is True
    assert engine.repository.stats().documents == 1


def test_grounded_answer_contains_citation(engine: RAGEngine, policy_text: str) -> None:
    engine.ingest_bytes(policy_text.encode(), "vendor-policy.txt")
    result = engine.answer("Who must approve a purchase over $25,000?")
    assert result.grounded is True
    assert result.confidence > 0
    assert result.citations
    assert result.citations[0].document_name == "vendor-policy.txt"
    assert "[1]" in result.answer


def test_unknown_question_is_not_forced(engine: RAGEngine, policy_text: str) -> None:
    engine.ingest_bytes(policy_text.encode(), "vendor-policy.txt")
    result = engine.answer("What is the lunar launch schedule for Europa?")
    assert result.confidence < 0.5
