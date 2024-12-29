"""
Main API Router Module

This module serves as the central routing configuration for the API.
It aggregates all endpoint routers and configures them with appropriate:
- URL prefixes
- Tags for API documentation
- Version prefixing

The router structure:
/api/v1/
  ├── /health        - System health monitoring
  ├── /auth          - Authentication and user management
  ├── /documents     - Document management and processing
  ├── /chats         - Chat sessions and messaging
  └── /user-llm-configs - User-specific LLM configurations
"""

from fastapi import APIRouter
from app.core.config import get_settings
from app.api.v1.endpoints import health, auth, documents, chat, user_llm_configs

# Load application settings
settings = get_settings()

# Create main API router with version prefix
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include sub-routers with appropriate prefixes and tags
api_router.include_router(
    health.router,
    tags=["health"]  # Health check endpoints
)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]  # Authentication endpoints
)
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]  # Document management endpoints
)
api_router.include_router(
    chat.router,
    prefix="/chats",
    tags=["chats"]  # Chat functionality endpoints
)
api_router.include_router(
    user_llm_configs.router,
    prefix="/user-llm-configs",
    tags=["user_llm_configs"]  # User LLM configuration endpoints
)