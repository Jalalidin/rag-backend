from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.exceptions import ResourceNotFoundError

def create_document(db: Session, document: DocumentCreate, user_id: int, file_path: str, mime_type: str) -> Document:
    db_document = Document(
        filename=document.filename,
        file_path=file_path,
        mime_type=mime_type,
        user_id=user_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id).first()

def get_user_documents(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
    return db.query(Document)\
        .filter(Document.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_document_status(db: Session, document_id: int, status: DocumentStatus) -> Document:
    """Update the status of a document."""
    document = get_document(db, document_id)
    if not document:
        raise ResourceNotFoundError(f"Document {document_id} not found")
    
    document.status = status
    db.commit()
    db.refresh(document)
    return document

def delete_document(db: Session, document_id: int) -> bool:
    document = get_document(db, document_id)
    if document:
        db.delete(document)
        db.commit()
        return True
    return False 

def update_document(
    db: Session,
    document_id: int,
    document: DocumentUpdate,
    file_path: str,
    mime_type: str
) -> Optional[Document]:
    db_document = get_document(db, document_id)
    if db_document:
        db_document.filename = document.filename
        db_document.file_path = file_path
        db_document.mime_type = mime_type
        db_document.status = DocumentStatus.QUEUED  # Reset status for re-processing
        db_document.error_message = None
        db.commit()
        db.refresh(db_document)
    return db_document 