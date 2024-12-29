"""
Error Handler Middleware Module

This module provides centralized error handling for the application.
"""

from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.exceptions import (
    AppBaseException,
    DatabaseError,
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    AuthorizationError,
    LLMError,
    OpenRouterError
)
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.exceptions import HTTPException as StarletteHTTPException
import json

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except AppBaseException as e:
            logger.error(f"Application error: {str(e)}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.status_code,
                        "message": str(e),
                        "type": e.__class__.__name__
                    }
                }
            )
        except OpenRouterError as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.status_code,
                        "message": str(e),
                        "metadata": e.metadata
                    }
                }
            )
        # ... rest of your error handlers ...

async def handle_openrouter_error(exc: Exception) -> JSONResponse:
    """
    Handle OpenRouter-specific errors based on their documentation.
    https://openrouter.ai/docs/errors
    """
    error_mapping = {
        400: "Bad Request (invalid or missing params, CORS)",
        401: "Invalid credentials (OAuth session expired, disabled/invalid API key)",
        402: "Insufficient credits. Add more credits and retry the request.",
        403: "Input was flagged by content moderation",
        408: "Request timed out",
        429: "Rate limit exceeded",
        502: "Model provider is down or invalid response",
        503: "No available model provider meets routing requirements"
    }
    
    status_code = getattr(exc, 'status_code', 500)
    message = error_mapping.get(status_code, str(exc))
    metadata = getattr(exc, 'metadata', None)
    
    # Convert to our custom OpenRouterError
    raise OpenRouterError(message, status_code, metadata) 