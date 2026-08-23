from __future__ import annotations

from fastapi import FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.models import (
    DocumentSummary,
    DriveIngestionPayload,
    HealthResponse,
    IngestionResult,
    IntegrationStatus,
    QueryHistoryItem,
    QueryRequest,
    QueryResponse,
    TelegramWebhookResponse,
    WorkspaceStats,
)
from app.services.integrations import integration_statuses
from app.services.parser import DocumentParseError
from app.services.rag import bootstrap_demo


engine = bootstrap_demo()
app = FastAPI(
    title="PrismRAG Document Intelligence API",
    version=__version__,
    description="Grounded document ingestion, semantic retrieval, citations, and automation webhooks.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Workflow-Secret"],
)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"name": "PrismRAG API", "docs": "/docs", "health": "/api/v1/health"}


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    statuses = integration_statuses()
    return HealthResponse(
        status="healthy",
        version=__version__,
        vector_backend=engine.pinecone.backend_name,
        document_count=engine.repository.stats().documents,
        integrations_ready=sum(item.status in {"ready", "connected"} for item in statuses),
    )


@app.get("/api/v1/stats", response_model=WorkspaceStats)
async def stats() -> WorkspaceStats:
    return engine.repository.stats()


@app.get("/api/v1/documents", response_model=list[DocumentSummary])
async def documents(namespace: str = "workspace", limit: int = Query(50, ge=1, le=200)) -> list[DocumentSummary]:
    return engine.repository.list_documents(namespace, limit)


@app.post("/api/v1/documents/ingest", response_model=IngestionResult)
async def ingest_document(document: UploadFile = File(...), namespace: str = "workspace") -> IngestionResult:
    try:
        return engine.ingest_bytes(await document.read(), document.filename or "document.txt", namespace=namespace)
    except (DocumentParseError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await document.close()


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    return engine.answer(request.question, request.namespace, request.top_k, request.channel)


@app.get("/api/v1/queries", response_model=list[QueryHistoryItem])
async def query_history(limit: int = Query(12, ge=1, le=100)) -> list[QueryHistoryItem]:
    return engine.repository.list_queries(limit)


@app.get("/api/v1/integrations", response_model=list[IntegrationStatus])
async def integrations() -> list[IntegrationStatus]:
    return integration_statuses()


@app.post("/webhooks/n8n/google-drive", response_model=IngestionResult)
async def n8n_drive_ingestion(payload: DriveIngestionPayload, x_workflow_secret: str = Header(default="")) -> IngestionResult:
    if settings.n8n_webhook_secret != "replace-this-secret" and x_workflow_secret != settings.n8n_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid workflow secret.")
    return engine.ingest_text(payload.text, payload.file_name, source=f"Google Drive · {payload.file_id}", namespace=payload.namespace)


@app.post("/webhooks/telegram", response_model=TelegramWebhookResponse)
async def telegram_webhook(update: dict) -> TelegramWebhookResponse:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    question = str(message.get("text") or "").strip()
    chat_id = chat.get("id", "unknown")
    if not question:
        return TelegramWebhookResponse(chat_id=chat_id, text="Send a question and I’ll search the indexed document library.")
    result = engine.answer(question, channel="telegram")
    sources = "\n".join(f"• {item.document_name}, page {item.page}" for item in result.citations[:3])
    text = f"<b>PrismRAG answer</b>\n\n{result.answer}"
    if sources:
        text += f"\n\n<b>Sources</b>\n{sources}"
    return TelegramWebhookResponse(chat_id=chat_id, text=text[:4000])
