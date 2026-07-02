from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = "sk-placeholder"
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    chroma_persist_dir: str = "./vector_store"
    chroma_collection_name: str = "tender_docs"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # si on veut tester avec un LLM local via Ollama
    ollama_base_url: str | None = None
    ollama_model: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
