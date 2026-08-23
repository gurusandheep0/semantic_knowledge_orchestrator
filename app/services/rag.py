from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path

from app.config import ROOT_DIR, settings
from app.models import DocumentSummary, IngestionResult, QueryHistoryItem, QueryResponse, SourceCitation, utc_now
from app.services.chunker import chunk_document
from app.services.embeddings import LocalEmbeddingModel, tokenize
from app.services.insights import enhance_answer
from app.services.parser import parse_document, parse_text
from app.services.pinecone_store import PineconeMirror
from app.services.store import KnowledgeRepository


def _clean_excerpt(text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


class RAGEngine:
    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository or KnowledgeRepository()
        self.embedder = LocalEmbeddingModel()
        self.pinecone = PineconeMirror()

    def ingest_bytes(self, payload: bytes, file_name: str, source: str = "Manual upload", namespace: str = "workspace") -> IngestionResult:
        return self._persist(parse_document(payload, file_name), payload, source, namespace)

    def _persist(self, parsed, payload: bytes, source: str, namespace: str) -> IngestionResult:
        content_hash = hashlib.sha256(payload).hexdigest()
        existing = self.repository.find_by_hash(content_hash, namespace)
        if existing:
            return IngestionResult(
                document=existing,
                chunks_created=existing.chunks,
                embedding_model=self.embedder.name,
                vector_backend=self.pinecone.backend_name,
                deduplicated=True,
            )

        text_chunks = chunk_document(parsed)
        if not text_chunks:
            raise ValueError("No retrieval-ready chunks could be created from the document.")
        document_id = uuid.uuid4().hex[:12]
        created_at = utc_now()
        document = DocumentSummary(
            id=document_id,
            name=parsed.file_name,
            source=source,
            file_type=parsed.file_type,
            pages=len(parsed.pages),
            size_kb=parsed.size_kb,
            chunks=len(text_chunks),
            namespace=namespace,
            created_at=created_at,
        )
        vectors = self.embedder.embed_many([chunk.content for chunk in text_chunks])
        records = [
            {
                "id": f"{document_id}-{chunk.index:04d}",
                "document_id": document_id,
                "document_name": parsed.file_name,
                "page": chunk.page,
                "chunk_index": chunk.index,
                "content": chunk.content,
                "vector": json.dumps(vector),
                "namespace": namespace,
            }
            for chunk, vector in zip(text_chunks, vectors)
        ]
        self.repository.save_document(document, content_hash, records)
        self.pinecone.upsert(namespace, records)
        return IngestionResult(
            document=document,
            chunks_created=len(records),
            embedding_model=self.embedder.name,
            vector_backend=self.pinecone.backend_name,
        )

    def ingest_text(self, text: str, file_name: str, source: str = "n8n · Google Drive", namespace: str = "workspace") -> IngestionResult:
        parsed = parse_text(text, file_name)
        return self._persist(parsed, parsed.text.encode("utf-8"), source, namespace)

    def retrieve(self, question: str, namespace: str = "workspace", top_k: int | None = None) -> list[dict]:
        question_tokens = set(tokenize(question))
        candidates = self.repository.search(
            self.embedder.embed(question), namespace, max((top_k or settings.retrieval_top_k) * 3, 8)
        )
        for item in candidates:
            content_tokens = set(tokenize(item["content"]))
            lexical = len(question_tokens & content_tokens) / max(len(question_tokens), 1)
            item["lexical"] = lexical
            item["score"] = min(1.0, (item["score"] * 0.58) + (min(1.0, lexical * 2.2) * 0.42))
        return sorted(candidates, key=lambda item: item["score"], reverse=True)[: top_k or settings.retrieval_top_k]

    def answer(self, question: str, namespace: str = "workspace", top_k: int | None = None, channel: str = "web") -> QueryResponse:
        started = time.perf_counter()
        matches = self.retrieve(question, namespace, top_k)
        relative_floor = max(0.12, (matches[0]["score"] * 0.55) if matches else 0.12)
        usable = [item for item in matches if item["score"] >= relative_floor and item.get("lexical", 0) > 0]
        citations = [
            SourceCitation(
                document_id=item["document_id"],
                document_name=item["document_name"],
                page=item["page"],
                score=round(item["score"], 3),
                excerpt=_clean_excerpt(item["content"]),
            )
            for item in usable
        ]

        if not citations:
            fallback = "I could not find enough evidence in the indexed documents to answer that confidently. Try a more specific question or add a relevant source."
            confidence = 0.0
            grounded = False
            context = "No relevant context retrieved."
        else:
            question_tokens = set(tokenize(question))
            evidence: list[tuple[float, str, int]] = []
            for index, item in enumerate(usable, start=1):
                for sentence in re.split(r"(?<=[.!?])\s+|\n+", item["content"]):
                    sentence = sentence.strip()
                    if len(sentence) < 35:
                        continue
                    overlap = len(question_tokens & set(tokenize(sentence)))
                    evidence.append((overlap + item["score"], sentence, index))
            selected: list[tuple[str, int]] = []
            seen: set[str] = set()
            for _, sentence, citation_index in sorted(evidence, reverse=True):
                key = sentence.lower()[:80]
                if key not in seen:
                    selected.append((sentence, citation_index))
                    seen.add(key)
                if len(selected) == 3:
                    break
            if not selected:
                selected = [(usable[0]["content"], 1)]
            statements = " ".join(f"{_clean_excerpt(sentence, 360)} [{citation_index}]" for sentence, citation_index in selected)
            fallback = f"Based on the indexed knowledge, {statements}"
            confidence = min(0.98, round(sum(item["score"] for item in usable[:3]) / min(len(usable), 3) + 0.18, 3))
            grounded = True
            context = "\n\n".join(f"[{index}] {item['document_name']} · page {item['page']}\n{item['content']}" for index, item in enumerate(usable, start=1))

        answer, model_used = enhance_answer(question, context, fallback)
        result = QueryResponse(
            id=uuid.uuid4().hex[:12],
            question=question,
            answer=answer,
            confidence=confidence,
            citations=citations,
            retrieval_ms=max(1, int((time.perf_counter() - started) * 1000)),
            model_used=model_used,
            grounded=grounded,
        )
        self.repository.record_query(QueryHistoryItem(
            id=result.id,
            question=question,
            answer_preview=_clean_excerpt(answer, 170),
            channel=channel,
            confidence=result.confidence,
            citation_count=len(result.citations),
            created_at=result.created_at,
        ))
        return result


def bootstrap_demo(engine: RAGEngine | None = None) -> RAGEngine:
    engine = engine or RAGEngine()
    sample_dir = ROOT_DIR / "sample_data"
    if not engine.repository.list_documents() and sample_dir.exists():
        for path in sorted(sample_dir.glob("*.txt")):
            engine.ingest_bytes(path.read_bytes(), path.name, source="Google Drive · Demo")
    if not engine.repository.list_queries() and engine.repository.list_documents():
        for question, channel in [
            ("What is the 2030 emissions reduction target?", "telegram"),
            ("How quickly are critical security incidents acknowledged?", "web"),
            ("What approval is required for vendor purchases over $25,000?", "api"),
        ]:
            engine.answer(question, channel=channel)
    return engine
