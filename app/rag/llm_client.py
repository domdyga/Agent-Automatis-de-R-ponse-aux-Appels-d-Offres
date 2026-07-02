from __future__ import annotations
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.utils.config import get_settings
from app.utils.logger import logger


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    settings = get_settings()

    # si OLLAMA_BASE_URL est défini dans le .env, on utilise un modèle local
    if settings.ollama_base_url and settings.ollama_model:
        try:
            from langchain_community.chat_models import ChatOllama  # type: ignore
            logger.info("LLM local Ollama : %s", settings.ollama_model)
            return ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model, temperature=0.3)
        except ImportError:
            logger.warning("langchain-community absent, bascule sur OpenAI")

    logger.info("LLM OpenAI : %s", settings.openai_model)
    return ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        temperature=0.3,
        max_retries=3,
    )
