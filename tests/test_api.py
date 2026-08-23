from __future__ import annotations

import httpx
import pytest

from app.api import app


@pytest.fixture()
async def client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client


@pytest.mark.anyio
async def test_health_and_documents(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert (await client.get("/api/v1/documents")).status_code == 200


@pytest.mark.anyio
async def test_query_endpoint_returns_sources(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/query", json={"question": "What is the emissions target for 2030?", "channel": "api"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"]
    assert payload["grounded"] is True


@pytest.mark.anyio
async def test_telegram_webhook_returns_direct_reply(client: httpx.AsyncClient) -> None:
    response = await client.post("/webhooks/telegram", json={"message": {"chat": {"id": 88}, "text": "How much annual learning allowance is available?"}})
    assert response.status_code == 200
    assert response.json()["chat_id"] == 88
    assert "PrismRAG answer" in response.json()["text"]
