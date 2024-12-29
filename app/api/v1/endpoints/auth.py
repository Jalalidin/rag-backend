"""
Authentication Endpoints Module

This module handles user authentication and registration endpoints.
It provides:
- User login with JWT token generation
- New user registration
- Password verification
- Token management

The module uses OAuth2 with Password flow and JWT tokens for secure
authentication. All passwords are hashed before storage.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import create_access_token, verify_password
from app.api.deps import get_db
from app.crud.crud_user import create_user, get_user_by_username
from app.schemas.auth import UserCreate, UserInDB
from app.schemas.auth import Token
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Authenticate user and generate access token.
    
    Args:
        db: Database session
        form_data: OAuth2 form containing username and password
        
    Returns:
        Token: JWT access token for authenticated user
        
    Raises:
        HTTPException: If authentication fails due to invalid credentials
        
    The endpoint:
    1. Verifies username exists
    2. Validates password hash
    3. Generates timed JWT token
    4. Returns token with bearer type
    """
    user = get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserInDB)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user: User creation data including username and password
        db: Database session
        
    Returns:
        UserInDB: Created user information (excluding password)
        
    Raises:
        HTTPException: If username is already taken
        
    The endpoint:
    1. Checks username availability
    2. Hashes the password
    3. Creates new user record
    4. Returns user data without sensitive information
    """
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user) 