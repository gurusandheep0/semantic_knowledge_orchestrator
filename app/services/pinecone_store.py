from __future__ import annotations

from app.config import settings


class PineconeMirror:
    """Optional Pinecone integrated-embedding mirror.

    Local retrieval remains available when credentials or the SDK are absent.
    """

    def __init__(self) -> None:
        self.enabled = bool(settings.use_pinecone and settings.pinecone_api_key)

    @property
    def backend_name(self) -> str:
        return "Pinecone integrated embeddings" if self.enabled else "Local vector index"

    def upsert(self, namespace: str, records: list[dict]) -> bool:
        if not self.enabled or not records:
            return False
        try:
            from pinecone import Pinecone

            client = Pinecone(api_key=settings.pinecone_api_key)
            if not client.has_index(settings.pinecone_index):
                client.create_index_for_model(
                    name=settings.pinecone_index,
                    cloud=settings.pinecone_cloud,
                    region=settings.pinecone_region,
                    embed={"model": "llama-text-embed-v2", "field_map": {"text": "chunk_text"}},
                )
            index = client.Index(settings.pinecone_index)
            index.upsert_records(
                namespace=namespace,
                records=[
                    {
                        "_id": item["id"],
                        "chunk_text": item["content"],
                        "document_id": item["document_id"],
                        "document_name": item["document_name"],
                        "page": item["page"],
                    }
                    for item in records
                ],
            )
            return True
        except Exception:
            return False
