import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    REDIS_URL: str | None = os.getenv("REDIS_URL")
    CACHE_KEY_SECRET: str | None = os.getenv("CACHE_KEY_SECRET")
    DEFAULT_CACHE_TTL: int = int(os.getenv("DEFAULT_CACHE_TTL", "300"))

    PROVIDER_A_API_KEY: str | None = os.getenv("PROVIDER_A_API_KEY")

    SENTRY_DSN: str | None = os.getenv("SENTRY_DSN")
    JWT_SECRET: str | None = os.getenv("JWT_SECRET")

    CHATBOT_PROVIDER: str | None = os.getenv("CHATBOT_PROVIDER")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")


settings = Settings()


