"""
Core Exceptions Module

This module defines custom exceptions used throughout the application.
"""

class AppBaseException(Exception):
    """Base exception class for all application-specific exceptions."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(AppBaseException):
    """Exception raised for database-related errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class ValidationError(AppBaseException):
    """Exception raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

class ResourceNotFoundError(AppBaseException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class AuthenticationError(AppBaseException):
    """Exception raised for authentication failures."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class AuthorizationError(AppBaseException):
    """Exception raised for authorization failures."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)

class LLMError(AppBaseException):
    """Exception raised for LLM-related errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code=status_code)

class OpenRouterError(AppBaseException):
    """Exception raised for OpenRouter-specific errors."""
    def __init__(self, message: str, status_code: int, metadata: dict = None):
        super().__init__(message, status_code=status_code)
        self.metadata = metadata 