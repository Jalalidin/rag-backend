"""
Configuration Module

This module manages all application-wide settings and configurations using Pydantic's BaseSettings.
It handles environment variables, database connections, security settings, and external service configurations.
The Settings class is designed to be loaded once and cached for performance.
"""

import os
from typing import Optional, Any, Dict
from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import Field, PostgresDsn, validator

class Settings(BaseSettings):
    """
    Application settings and configuration management.
    
    This class uses Pydantic's BaseSettings to handle:
    - Environment variable loading
    - Type validation
    - Default values
    - Configuration file (.env) integration
    """
    
    # API Settings
    API_V1_STR: str = "/api/v1"  # Base path for API v1 endpoints
    PROJECT_NAME: str = "Document RAG API"  # Project name used in documentation and logging
    
    # Database Settings
    POSTGRES_SERVER: str  # PostgreSQL server hostname
    POSTGRES_USER: str  # Database user for authentication
    POSTGRES_PASSWORD: str  # Database password for authentication
    POSTGRES_DB: str = "rag_chat_db"  # Name of the application database
    DATABASE_URL: Optional[str] = None  # Full database connection URL (constructed in __init__)
    SQLALCHEMY_DATABASE_URI: Optional[str] = None  # SQLAlchemy-specific connection string
    
    # Redis Settings
    REDIS_HOST: str = "localhost"  # Redis server hostname for caching and session management
    REDIS_PORT: int = 6379  # Default Redis port
    
    # Vector DB Settings
    QDRANT_HOST: str = "qdrant"  # Qdrant vector database hostname
    QDRANT_PORT: int = 6333  # Default Qdrant port
    QDRANT_COLLECTION_NAME: str = "documents"  # Collection name for storing document embeddings
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "XD9Tgmh8tZ03Ox4GeOZl_I5MHDMzWCqj-P7uRqx5zNU")  # JWT signing key
    ALGORITHM: str = "HS256"  # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # JWT token expiration time
    
    # Upload Directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")  # Directory for storing uploaded files
    
    # Embedding Model Settings
    EMBEDDING_MODEL: str = "huggingface:BAAI/bge-small-en"  # Model used for text embeddings
    
    # OpenRouter Settings
    OPENROUTER_API_KEY: str = Field(..., env="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    SITE_URL: str = Field(default="http://localhost:8000")
    SITE_NAME: str = Field(default="RAG Chat")
    
    # Add Celery settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Optional Celery configuration
    CELERY_TASK_ALWAYS_EAGER: bool = False  # Set to True for testing/development
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    
    class Config:
        """Pydantic configuration class"""
        case_sensitive = True  # Environment variables are case-sensitive
        env_file = ".env"  # Load configuration from .env file
    
    def __init__(self, **kwargs):
        """
        Initialize settings with dynamic database URL construction.
        
        This method:
        1. Calls parent class initialization
        2. Constructs DATABASE_URL if not provided
        3. Sets up SQLAlchemy URI
        """
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL

@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache a Settings instance.
    
    Uses functools.lru_cache to ensure settings are only loaded once
    and reused across the application lifecycle.
    
    Returns:
        Settings: Cached application settings instance
    """
    return Settings()

# Global settings instance for import and use across the application
settings = get_settings()