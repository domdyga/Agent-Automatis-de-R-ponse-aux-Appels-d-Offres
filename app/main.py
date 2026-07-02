from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.utils.config import get_settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("=== reponse agent — Démarrage ===")
    logger.info("Modèle LLM  : %s", settings.openai_model)
    logger.info("Embeddings  : %s", settings.openai_embedding_model)
    logger.info("Vector store : %s", settings.chroma_persist_dir)
    yield
    logger.info("=== Response Agent — Arrêt ===")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Response automatique Agent",
        description=(
            "Agent IA pour répondre automatiquement aux appels d'offres (RFP) "
            "grâce au Retrieval-Augmented Generation (RAG)."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # En développement on accepte toutes les origines.
    # En production il faudrait restreindre ça.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
