from __future__ import annotations
from pathlib import Path
from typing import Any

from app.rag.vector_store import VectorStore
from app.services.chunker import chunk_documents
from app.services.document_loader import load_document
from app.utils.logger import logger


def ingest_file(
    file_path: str | Path,
    vector_store: VectorStore,
    metadata: dict[str, Any] | None = None,
) -> int:
    path = Path(file_path)
    logger.info("Ingestion : %s", path.name)

    documents = load_document(path, metadata=metadata)
    if not documents:
        raise ValueError(f"Rien extrait de '{path.name}'.")

    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError(f"Découpage vide pour '{path.name}'.")

    vector_store.add_documents(chunks)
    logger.info("Terminé : %s → %d chunks", path.name, len(chunks))
    return len(chunks)
