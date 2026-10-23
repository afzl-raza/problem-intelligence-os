from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str

    HOST: str
    PORT: int

    DEBUG: bool

    DATABASE_URL: str

    SECRET_KEY: str

    REDIS_URL: str

    OPENAI_API_KEY: str = ""

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Semantic search. Embeddings run locally (no paid API). Provider "none" disables
    # semantic search entirely; hybrid requests then fall back to keyword results.
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_CACHE_DIR: str = ".model_cache"
    # Minimum cosine similarity (bge-small-en-v1.5) for a query to match a problem, and for one
    # problem to count as related to another. Calibrated with scripts/eval_semantic.py against
    # eval/semantic_queries.json (see Engineering_Log.md, Sprint 3.4): query->problem at 0.60 gives
    # recall 0.96 / precision 0.55 and rejects off-topic queries; problem->problem similarities run
    # higher (same-domain pairs 0.70-0.85), so related problems need a stricter 0.70.
    # Changing the model means re-running the evaluation and re-setting both.
    SEMANTIC_MIN_SIMILARITY: float = 0.60
    RELATED_MIN_SIMILARITY: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()