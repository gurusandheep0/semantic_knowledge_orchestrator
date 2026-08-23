from __future__ import annotations

from app.config import settings
from app.models import IntegrationStatus


def integration_statuses() -> list[IntegrationStatus]:
    return [
        IntegrationStatus(
            name="Google Drive",
            status="ready",
            detail="n8n trigger template included",
            accent="cyan",
        ),
        IntegrationStatus(
            name="Pinecone",
            status="connected" if settings.use_pinecone and settings.pinecone_api_key else "configuration-needed",
            detail="Integrated embeddings" if settings.pinecone_api_key else "Add PINECONE_API_KEY",
            accent="violet",
        ),
        IntegrationStatus(
            name="Groq LLM",
            status="connected" if settings.groq_api_key else "configuration-needed",
            detail=settings.groq_model if settings.groq_api_key else "Local synthesis active",
            accent="magenta",
        ),
        IntegrationStatus(
            name="Telegram",
            status="connected" if settings.telegram_bot_token else "ready",
            detail="Webhook response route ready" if not settings.telegram_bot_token else "Bot token configured",
            accent="blue",
        ),
        IntegrationStatus(
            name="n8n Automation",
            status="ready",
            detail="Import workflow/prismrag-workflow.json",
            accent="amber",
        ),
    ]
