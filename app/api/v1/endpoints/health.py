"""
Health Check Endpoints Module

This module provides system health monitoring endpoints.
It performs comprehensive health checks on all critical system components:
- API server status
- Database connectivity
- Celery worker availability
- Redis connection
- Vector store (Qdrant) accessibility

The health check returns detailed status for each component and an overall
system health status. This is useful for monitoring and alerting systems.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.celery_app import celery_app
from qdrant_client import QdrantClient
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Perform comprehensive health check of all system components.
    
    Args:
        db: Database session for checking database connectivity
        
    Returns:
        dict: Health status of all services with structure:
            {
                "status": "healthy" | "unhealthy",
                "services": {
                    "api": "healthy" | "unhealthy",
                    "database": "healthy" | "unhealthy",
                    "celery": "healthy" | "unhealthy",
                    "redis": "healthy" | "unhealthy",
                    "vector_store": "healthy" | "unhealthy"
                }
            }
            
    The endpoint checks:
    1. Database connection by executing a simple query
    2. Celery workers by pinging the cluster
    3. Redis connection by sending a ping command
    4. Vector store by attempting to list collections
    
    If any service is unhealthy, the overall status is marked as unhealthy.
    """
    health_status = {
        "status": "healthy",
        "services": {
            "api": "healthy",  # API is running if we can process this request
            "database": "unhealthy",
            "celery": "unhealthy",
            "redis": "unhealthy",
            "vector_store": "unhealthy"
        }
    }
    
    # Check database connectivity with a simple query
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"
    
    # Check Celery worker availability
    try:
        celery_app.control.ping()
        health_status["services"]["celery"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis_client = celery_app.backend.client
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"
    
    # Check Vector Store (Qdrant) accessibility
    try:
        client = QdrantClient(
            url=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        client.get_collections()  # Verify we can communicate with Qdrant
        health_status["services"]["vector_store"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"
    
    return health_status 