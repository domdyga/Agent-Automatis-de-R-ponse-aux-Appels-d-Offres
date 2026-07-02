from __future__ import annotations

from app.models.schemas import SourceDocument
from app.rag.vector_store import VectorStore
from app.utils.logger import logger

_EXCERPT_MAX_LEN = 300


def retrieve(
    query: str,
    vector_store: VectorStore,
    top_k: int | None = None,
) -> tuple[list[SourceDocument], float]:
    if not query.strip():
        raise ValueError("La requête ne peut pas être vide.")

    results = vector_store.similarity_search(query, k=top_k)

    if not results:
        logger.warning("Aucun résultat pour : '%s'", query[:80])
        return [], 0.0

    sources: list[SourceDocument] = []
    for doc, score in results:
        excerpt = doc.page_content[:_EXCERPT_MAX_LEN].replace("\n", " ")
        if len(doc.page_content) > _EXCERPT_MAX_LEN:
            excerpt += "…"
        sources.append(SourceDocument(
            source=doc.metadata.get("source", "inconnu"),
            relevance_score=round(score, 4),
            excerpt=excerpt,
        ))

    confidence = round(sum(s.relevance_score for s in sources) / len(sources), 4)
    logger.info("%d source(s) trouvée(s), confiance=%.3f", len(sources), confidence)
    return sources, confidence


def build_context_string(sources: list[SourceDocument]) -> str:
    if not sources:
        return ""
    parts = [
        f"[Source {i}] {src.source} (pertinence : {src.relevance_score:.2f})\n{src.excerpt}"
        for i, src in enumerate(sources, start=1)
    ]
    return "\n\n---\n\n".join(parts)
