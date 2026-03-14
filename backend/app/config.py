from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Linea 1 Metro - Sistema de Gestion Energetica"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:12345@localhost:5432/linea1metro"

    # Supabase
    SUPABASE_URL: str = "http://localhost:8000"
    SUPABASE_ANON_KEY: str = "your-anon-key-here"
    SUPABASE_SERVICE_ROLE_KEY: str = "your-service-role-key-here"
    SUPABASE_JWT_SECRET: str = "your-jwt-secret-here"

    # Storage
    STORAGE_PATH: str = "storage"
    MAX_IMAGE_SIZE_MB: int = 10

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
