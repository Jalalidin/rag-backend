"""
Database Session Management Module

This module handles SQLAlchemy session management for the application.
It provides:
- Database engine configuration
- Session factory setup
- Dependency injection for database sessions
- Automatic session cleanup

The module ensures proper connection handling and resource cleanup
through FastAPI's dependency injection system.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.base_class import Base

# Create database engine with connection URL from settings
engine = create_engine(
    settings.DATABASE_URL,
    # Add engine configuration here if needed:
    # pool_size=5,
    # max_overflow=10,
    # pool_timeout=30,
)

# Create session factory
# autocommit=False: Transactions must be committed explicitly
# autoflush=False: Changes are not automatically flushed to DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency for database session management.
    
    This function:
    1. Creates a new database session
    2. Yields it for route usage
    3. Ensures proper cleanup after request completion
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        The session is automatically closed after the request
        is completed, even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Ensure session is closed after request 