from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.config import settings
from app.models import DocumentSummary, QueryHistoryItem, WorkspaceStats
from app.services.embeddings import cosine_similarity


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL, file_type TEXT NOT NULL,
    pages INTEGER NOT NULL, size_kb REAL NOT NULL, chunks INTEGER NOT NULL, status TEXT NOT NULL,
    namespace TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_hash_namespace ON documents(content_hash, namespace);
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY, document_id TEXT NOT NULL, document_name TEXT NOT NULL, page INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL, content TEXT NOT NULL, vector TEXT NOT NULL, namespace TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON chunks(namespace);
CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY, question TEXT NOT NULL, answer_preview TEXT NOT NULL, channel TEXT NOT NULL,
    confidence REAL NOT NULL, citation_count INTEGER NOT NULL, created_at TEXT NOT NULL
);
"""


class KnowledgeRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.database_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def find_by_hash(self, content_hash: str, namespace: str) -> DocumentSummary | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE content_hash = ? AND namespace = ?", (content_hash, namespace)
            ).fetchone()
        return DocumentSummary(**dict(row)) if row else None

    def save_document(self, document: DocumentSummary, content_hash: str, chunks: list[dict]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO documents (id, name, source, file_type, pages, size_kb, chunks, status, namespace, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (document.id, document.name, document.source, document.file_type, document.pages, document.size_kb,
                 document.chunks, document.status, document.namespace, content_hash, document.created_at),
            )
            connection.executemany(
                """INSERT INTO chunks (id, document_id, document_name, page, chunk_index, content, vector, namespace)
                VALUES (:id, :document_id, :document_name, :page, :chunk_index, :content, :vector, :namespace)""",
                chunks,
            )

    def list_documents(self, namespace: str = "workspace", limit: int = 50) -> list[DocumentSummary]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents WHERE namespace = ? ORDER BY created_at DESC LIMIT ?", (namespace, limit)
            ).fetchall()
        return [DocumentSummary(**dict(row)) for row in rows]

    def search(self, query_vector: list[float], namespace: str, limit: int) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM chunks WHERE namespace = ?", (namespace,)).fetchall()
        matches = []
        for row in rows:
            item = dict(row)
            item["score"] = max(0.0, cosine_similarity(query_vector, json.loads(item.pop("vector"))))
            matches.append(item)
        return sorted(matches, key=lambda item: item["score"], reverse=True)[:limit]

    def record_query(self, item: QueryHistoryItem) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO queries (id, question, answer_preview, channel, confidence, citation_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item.id, item.question, item.answer_preview, item.channel, item.confidence, item.citation_count, item.created_at),
            )

    def list_queries(self, limit: int = 12) -> list[QueryHistoryItem]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM queries ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [QueryHistoryItem(**dict(row)) for row in rows]

    def stats(self) -> WorkspaceStats:
        with self.connect() as connection:
            documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            query_row = connection.execute("SELECT COUNT(*), COALESCE(AVG(confidence), 0) FROM queries").fetchone()
        return WorkspaceStats(
            documents=documents,
            chunks=chunks,
            queries=query_row[0],
            average_confidence=round(query_row[1] * 100, 1),
            vector_backend="Pinecone" if settings.use_pinecone and settings.pinecone_api_key else "Local vector index",
            automation_status="Ready",
        )
