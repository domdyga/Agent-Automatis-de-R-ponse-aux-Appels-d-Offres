from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    csv = "csv"


# /upload
class UploadResponse(BaseModel):
    filename: str
    document_type: DocumentType
    size_bytes: int
    message: str


# /ingest
class IngestRequest(BaseModel):
    file_path: str = Field(..., description="Chemin vers le fichier à indexer")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    file_path: str
    chunks_created: int
    collection_name: str
    message: str


# /generate-proposal
class ProposalRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    project_description: str = Field(..., min_length=10)
    requirements: list[str] = Field(..., min_length=1)
    budget_range: str | None = None
    deadline: str | None = None


class SourceDocument(BaseModel):
    source: str
    relevance_score: float
    excerpt: str


class ProposalResponse(BaseModel):
    company_name: str
    client_name: str
    project_title: str
    executive_summary: str
    technical_approach: str
    methodology: str
    project_organization: str
    conclusion: str
    sources: list[SourceDocument]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    generation_model: str


# /ask
class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    conversation_id: str | None = None
    top_k: int = Field(5, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: list[SourceDocument]
    confidence_score: float


# /health
class HealthResponse(BaseModel):
    status: str
    vector_store: str
    llm_model: str
    embedding_model: str
    documents_indexed: int
