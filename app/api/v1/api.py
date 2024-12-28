from fastapi import APIRouter
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter(prefix=settings.API_V1_STR)

# Import and include routers here as they are created
# Example:
# from .endpoints import documents, chats
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(chats.router, prefix="/chats", tags=["chats"]) 