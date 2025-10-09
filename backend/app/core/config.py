"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Redis (In-Memory Database)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_DB_INDEX: int = 0
    REDIS_PERSISTENCE_ENABLED: bool = True
    
    # Security
    JWT_SECRET: str = "your-secret-key-here"
    CACHE_KEY_SECRET: str = "your-cache-secret-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cache Settings
    DEFAULT_CACHE_TTL: int = 3600  # 1 hour
    
    # External Provider APIs
    PROVIDER_A_API_KEY: str = ""
    PROVIDER_B_API_KEY: str = ""
    
    # Chatbot
    CHATBOT_PROVIDER: str = "LANGCHAIN"
    OPENAI_API_KEY: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5175"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
