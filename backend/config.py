"""
Configuration & Settings — loaded from .env
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_secret_key: str = "change-me-in-production"

    # App
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:8000,http://localhost:8000,null"

    @property
    def cors_origins(self) -> List[str]:
        # Filter blank entries and return unique origins
        return list(dict.fromkeys(
            o.strip() for o in self.allowed_origins.split(",") if o.strip()
        ))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
