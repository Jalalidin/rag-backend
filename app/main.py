import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.api import api_router
from app.core.errors import validation_exception_handler
from app.database.session import Base, engine
from app.utils.langchain_utils import setup_langchain_cache
import logging
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.core.monitoring import MetricsMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for lifespan events."""
    try:
        # Startup
        setup_langchain_cache(engine)
        logger.info("LangChain cache initialized")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize LangChain cache: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application")

# Create database tables
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document RAG API",
    description="API for document management and chat with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add error handler middleware first
app.add_middleware(ErrorHandlerMiddleware)

# Add monitoring middleware
app.add_middleware(MetricsMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Delay startup if STARTUP_DELAY is set
startup_delay = int(os.environ.get("STARTUP_DELAY", 0))
if startup_delay > 0:
    print(f"Delaying startup by {startup_delay} seconds...")
    time.sleep(startup_delay)

app.add_exception_handler(RequestValidationError, validation_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 