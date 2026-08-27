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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()