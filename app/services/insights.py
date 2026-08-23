from __future__ import annotations

from app.config import settings


SYSTEM_PROMPT = """You are PrismRAG, a precise document intelligence assistant.
Answer only from the supplied context. Never add unsupported facts. If evidence is incomplete, say so.
Keep citation markers such as [1] and [2] attached to the claims they support. Return plain text only."""


def enhance_answer(question: str, context: str, fallback: str) -> tuple[str, str]:
    if not settings.groq_api_key:
        return fallback, "local-grounded-synthesis-v1"
    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.1,
            max_tokens=700,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nRetrieved context:\n{context}"},
            ],
        )
        answer = (completion.choices[0].message.content or "").strip()
        return (answer or fallback), settings.groq_model
    except Exception:
        return fallback, "local-grounded-synthesis-v1"
