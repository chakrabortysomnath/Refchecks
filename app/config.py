"""
Configuration module for RefChecks backend.
Handles environment variables, database setup, and OAuth configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from .env file and environment variables.
    Pydantic automatically validates and converts types.
    """
    
    # ===== DATABASE =====
    database_url: str = "postgresql://postgres:password@localhost:5432/refchecks_db"
    
    # ===== GOOGLE OAUTH =====
    # google_client_id: str = "267372237255-o2460qj6aru70lvo7is9q8f7t0btoa71.apps.googleusercontent.com"
    # google_client_secret: str = "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"
    google_client_id: str = "YOUR_GOOGLE_CLIENT_ID_HERE"
    google_client_secret: str = "YOUR_GOOGLE_CLIENT_SECRET_HERE"
    
    # ===== JWT & SECURITY =====
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ===== ENVIRONMENT =====
    environment: str = "development"
    
    # ===== STATSBOMB =====
    statsbomb_data_repo: str = "https://github.com/statsbomb/StatsBombOpenData"
    
    # ===== API =====
    api_title: str = "RefChecks - Football Bias Analysis"
    api_version: str = "1.0.0"
    api_description: str = "Analyze refereeing bias using Statsbomb data"
    
    # ===== CORS =====
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    
    class Config:
        """Load from .env file"""
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"


# Create global settings instance
settings = Settings()


# ===== GOOGLE OAUTH CONFIGURATION =====

GOOGLE_OAUTH_CONFIG = {
    "client_id": settings.google_client_id,
    "client_secret": settings.google_client_secret,
    "redirect_uri": None,  # Will be set at runtime based on request
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "scopes": [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
}


# ===== DATABASE CONFIGURATION =====

# SQLAlchemy connection string
SQLALCHEMY_DATABASE_URL = settings.database_url

# SQLAlchemy engine options
SQLALCHEMY_KWARGS = {
    "echo": not settings.is_production,  # Log SQL in development
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,  # Verify connection before using
}
