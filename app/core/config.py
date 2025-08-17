import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:yourpassword@localhost:5432/queryiq"
    database_url_async: str = "postgresql+asyncpg://postgres:yourpassword@localhost:5432/queryiq"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    
    # Query monitoring
    slow_query_threshold_ms: int = 1000  # 1 second
    max_suggestions_per_query: int = 10

    # AI integration (optional, will load from GEMINI_API_KEY in .env if present)
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
