from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DocumentSummary(BaseModel):
    id: str
    name: str
    source: str = "Manual upload"
    file_type: str
    pages: int = 1
    size_kb: float = 0
    chunks: int = 0
    status: Literal["indexed", "processing", "failed"] = "indexed"
    namespace: str = "workspace"
    created_at: str = Field(default_factory=utc_now)


class IngestionResult(BaseModel):
    document: DocumentSummary
    chunks_created: int
    embedding_model: str
    vector_backend: str
    deduplicated: bool = False


class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    page: int
    score: float = Field(ge=0, le=1)
    excerpt: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    namespace: str = "workspace"
    top_k: int = Field(default=4, ge=1, le=10)
    channel: Literal["web", "telegram", "api"] = "web"


class QueryResponse(BaseModel):
    id: str
    question: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[SourceCitation]
    retrieval_ms: int
    model_used: str
    grounded: bool
    created_at: str = Field(default_factory=utc_now)


class QueryHistoryItem(BaseModel):
    id: str
    question: str
    answer_preview: str
    channel: str
    confidence: float
    citation_count: int
    created_at: str


class WorkspaceStats(BaseModel):
    documents: int
    chunks: int
    queries: int
    average_confidence: float
    vector_backend: str
    automation_status: str


class IntegrationStatus(BaseModel):
    name: str
    status: Literal["connected", "ready", "configuration-needed"]
    detail: str
    accent: str


class HealthResponse(BaseModel):
    status: str
    version: str
    vector_backend: str
    document_count: int
    integrations_ready: int


class DriveIngestionPayload(BaseModel):
    file_id: str
    file_name: str
    text: str = Field(min_length=1)
    mime_type: str = "application/pdf"
    namespace: str = "workspace"


class TelegramWebhookResponse(BaseModel):
    method: str = "sendMessage"
    chat_id: int | str
    text: str
    parse_mode: str = "HTML"
