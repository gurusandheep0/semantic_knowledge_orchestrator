import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.rag import RAGEngine, bootstrap_demo


engine = bootstrap_demo(RAGEngine())
stats = engine.repository.stats()
result = engine.answer("What approvals are needed for a vendor purchase of $40,000?", channel="api")

print("PrismRAG demo pipeline")
print("-" * 48)
print(f"Documents:  {stats.documents}")
print(f"Chunks:     {stats.chunks}")
print(f"Backend:    {stats.vector_backend}")
print(f"Confidence: {round(result.confidence * 100)}%")
print(f"Answer:     {result.answer}")
print("Sources:")
for citation in result.citations:
    print(f"  - {citation.document_name} · page {citation.page} · {round(citation.score * 100)}%")

Path("outputs").mkdir(exist_ok=True)
Path("outputs/demo-answer.txt").write_text(
    result.answer + "\n\n" + "\n".join(f"- {item.document_name}, page {item.page}" for item in result.citations),
    encoding="utf-8",
)
