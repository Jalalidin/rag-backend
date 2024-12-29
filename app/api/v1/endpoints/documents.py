"""
Document Management Endpoints Module

This module handles all document-related operations including:
- Document upload and processing
- Document retrieval (single and batch)
- Document deletion
- Document status management

The module integrates with:
- Celery for asynchronous document processing
- File system for document storage
- Database for document metadata
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.document import Document, DocumentCreate, DocumentStatus
from app.crud.crud_document import get_document, get_user_documents, update_document_status, create_document
from app.document_processing import process_document, save_file
from app.core.config import settings
from app.utils.file_utils import get_mime_type
from app.worker import process_document_task

router = APIRouter()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and initiate processing of a new document.
    
    This endpoint:
    1. Creates a database record for the document
    2. Queues an asynchronous processing task
    3. Returns immediately with processing status
    
    Args:
        file: The uploaded file (multipart/form-data)
        db: Database session (injected)
        current_user: Authenticated user (injected)
        
    Returns:
        dict: Document ID and processing status
            {
                "document_id": int,
                "status": "queued",
                "message": str
            }
            
    Raises:
        HTTPException: If document processing fails
            - 500 Internal Server Error: Processing failure
    """
    try:
        # Create document record in database
        document = create_document(
            db=db,
            user_id=current_user.id,
            filename=file.filename,
            mime_type=file.content_type
        )
        
        # Queue asynchronous processing task
        process_document_task.delay(document.id)
        
        return {
            "document_id": document.id,
            "status": "queued",
            "message": "Document processing started"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@router.get("/", response_model=List[Document])
async def read_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve paginated list of user's documents.
    
    Args:
        skip: Number of records to skip (pagination offset)
        limit: Maximum number of records to return
        db: Database session (injected)
        current_user: Authenticated user (injected)
        
    Returns:
        List[Document]: List of document records
        
    Note:
        Results are paginated and only include documents
        owned by the authenticated user.
    """
    documents = get_user_documents(db, current_user.id, skip=skip, limit=limit)
    return documents

@router.get("/{document_id}", response_model=Document)
async def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific document by ID.
    
    Args:
        document_id: ID of the document to retrieve
        db: Database session (injected)
        current_user: Authenticated user (injected)
        
    Returns:
        Document: Document record if found and authorized
        
    Raises:
        HTTPException:
            - 404 Not Found: Document doesn't exist
            - 403 Forbidden: User not authorized to access document
    """
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific document and its associated file.
    
    This endpoint:
    1. Verifies document exists and user has permission
    2. Deletes the physical file from storage
    3. Removes the database record
    
    Args:
        document_id: ID of the document to delete
        db: Database session (injected)
        current_user: Authenticated user (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException:
            - 404 Not Found: Document doesn't exist
            - 403 Forbidden: User not authorized to delete document
            - 500 Internal Server Error: File deletion failure
    """
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    # Delete physical file from storage
    try:
        os.remove(document.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    # Remove database record
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"} 