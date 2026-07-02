from __future__ import annotations
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.schemas import (
    AskRequest, AskResponse, HealthResponse,
    IngestRequest, IngestResponse,
    ProposalRequest, ProposalResponse, UploadResponse,
)
from app.rag.pipeline import answer_question, generate_proposal
from app.rag.vector_store import VectorStore
from app.services.ingest_service import ingest_file
from app.services.proposal_exporter import export_proposal_to_pdf
from app.utils.config import get_settings
from app.utils.logger import logger

router = APIRouter()

_UPLOAD_DIR = Path("data/raw")
_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}

# VectorStore partagé entre tous les endpoints
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


@router.get("/health", response_model=HealthResponse, tags=["Système"])
def health(vs: VectorStore = Depends(get_vector_store)) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        vector_store="chromadb",
        llm_model=settings.openai_model,
        embedding_model=settings.openai_embedding_model,
        documents_indexed=vs.count_documents(),
    )


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Format '{suffix}' non supporté. Acceptés : {sorted(_SUPPORTED_EXTENSIONS)}")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = _UPLOAD_DIR / file.filename

    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as exc:
        logger.error("Échec upload : %s", exc)
        raise HTTPException(status_code=500, detail="Impossible de sauvegarder le fichier.") from exc

    size = dest.stat().st_size
    logger.info("Uploadé : '%s' (%d octets)", file.filename, size)

    return UploadResponse(
        filename=file.filename,
        document_type=suffix.lstrip("."),  # type: ignore[arg-type]
        size_bytes=size,
        message=f"'{file.filename}' uploadé. Lance POST /ingest pour l'indexer.",
    )


@router.post("/ingest", response_model=IngestResponse, tags=["Documents"])
def ingest_document(request: IngestRequest, vs: VectorStore = Depends(get_vector_store)) -> IngestResponse:
    try:
        n_chunks = ingest_file(request.file_path, vs, metadata=request.metadata)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erreur ingestion '%s'", request.file_path)
        raise HTTPException(status_code=500, detail=f"Ingestion échouée : {exc}") from exc

    settings = get_settings()
    return IngestResponse(
        file_path=request.file_path,
        chunks_created=n_chunks,
        collection_name=settings.chroma_collection_name,
        message=f"{n_chunks} chunks ingérés dans '{settings.chroma_collection_name}'.",
    )


@router.post("/generate-proposal", response_model=ProposalResponse, tags=["Propositions"])
def create_proposal(
    request: ProposalRequest,
    export_pdf: bool = False,
    vs: VectorStore = Depends(get_vector_store),
) -> ProposalResponse:
    try:
        proposal = generate_proposal(
            company_name=request.company_name,
            client_name=request.client_name,
            project_description=request.project_description,
            requirements=request.requirements,
            budget_range=request.budget_range,
            deadline=request.deadline,
            vector_store=vs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erreur génération proposition")
        raise HTTPException(status_code=500, detail=f"Génération échouée : {exc}") from exc

    if export_pdf:
        try:
            export_proposal_to_pdf(proposal)
        except Exception as exc:
            logger.warning("Export PDF échoué (non bloquant) : %s", exc)

    return proposal


@router.post("/ask", response_model=AskResponse, tags=["Q&A"])
def ask_question(request: AskRequest, vs: VectorStore = Depends(get_vector_store)) -> AskResponse:
    try:
        return answer_question(
            question=request.question,
            vector_store=vs,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erreur Q&A")
        raise HTTPException(status_code=500, detail=f"Erreur : {exc}") from exc
