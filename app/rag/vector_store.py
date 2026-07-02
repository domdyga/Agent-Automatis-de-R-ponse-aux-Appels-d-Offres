from __future__ import annotations
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.utils.config import get_settings
from app.utils.logger import logger


class VectorStore:

    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings

        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )

        self._store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self._embeddings,
            persist_directory=str(persist_dir),
        )

        logger.info("VectorStore prêt — collection='%s'", settings.chroma_collection_name)

    def add_documents(self, documents: list[Document]) -> list[str]:
        if not documents:
            raise ValueError("Liste de documents vide.")
        ids = self._store.add_documents(documents)
        logger.info("%d chunks ajoutés.", len(ids))
        return ids

    def similarity_search(
        self, query: str, k: int | None = None, filter: dict[str, Any] | None = None
    ) -> list[tuple[Document, float]]:
        top_k = k or self._settings.top_k_results
        results = self._store.similarity_search_with_score(query, k=top_k, filter=filter)
        # on convertit la distance cosinus en score de pertinence (plus c'est haut, mieux c'est)
        return [(doc, max(0.0, 1.0 - score)) for doc, score in results]

    def count_documents(self) -> int:
        try:
            return self._store._collection.count()
        except Exception:
            return 0

    def get_retriever(self, k: int | None = None):
        return self._store.as_retriever(search_kwargs={"k": k or self._settings.top_k_results})
