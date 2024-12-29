from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.document import DocumentStatus
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    filename: str = Field(..., description="Name of the uploaded document file")

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    filename: str = Field(..., description="Updated name of the document file")

class Document(DocumentBase):
    id: int = Field(..., description="Unique identifier for the document")
    status: DocumentStatus = Field(..., description="Current processing status of the document")
    mime_type: str = Field(..., description="MIME type of the document file")
    created_at: datetime = Field(..., description="Timestamp when the document was created")
    updated_at: datetime = Field(..., description="Timestamp when the document was last updated")
    error_message: Optional[str] = Field(None, description="Error message if document processing failed")
    user_id: int = Field(..., description="ID of the user who owns this document")

    class Config:
        from_attributes = True 