"""
API Dependencies Module

This module provides common dependencies for the FastAPI application.
It handles:
- Database session management
- Authentication and authorization
- User token validation
- Current user retrieval

These dependencies can be injected into API endpoints using FastAPI's
dependency injection system.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.crud.crud_user import get_user_by_username
from app.database.session import SessionLocal
from app.models.user import User

# Configure OAuth2 password bearer scheme for token handling
# tokenUrl specifies the endpoint for token acquisition
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db() -> Generator:
    """
    FastAPI dependency for database session management.
    
    This function creates a new SQLAlchemy session for each request
    and ensures it's properly closed after the request is completed.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        The session is automatically closed in the finally block,
        ensuring proper cleanup even if an exception occurs.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    This function:
    1. Extracts and validates the JWT token
    2. Decodes the token payload
    3. Retrieves the user from the database
    
    Args:
        db: Database session (injected)
        token: JWT token from request (injected)
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
            - 401 Unauthorized: Invalid or expired token
            - 401 Unauthorized: User not found in database
            
    Usage:
        @app.get("/users/me")
        def read_users_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT token and extract username
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        # Handle JWT decode errors and validation errors
        raise credentials_exception
    
    # Verify user exists in database
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user 