from app.core.celery_app import celery_app
from typing import Dict, Any, List
from celery import Task
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.document import Document
from app.crud.crud_document import get_document, update_document_status
from app.schemas.document import DocumentStatus
from app.core.exceptions import DatabaseError, LLMError
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
import logging

logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    """Base task that provides database session management."""
    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Clean up the database session after the task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None

@celery_app.task(bind=True, base=DatabaseTask, name="app.worker.generate_embeddings")
def generate_embeddings_task(self, document_id: int) -> Dict[str, Any]:
    """
    Generate embeddings for document chunks and store them in Qdrant.
    
    Args:
        document_id: ID of the document to process
        
    Returns:
        Dict containing task status and any error messages
    """
    try:
        # Get document from database
        document = get_document(self.db, document_id)
        if not document:
            raise DatabaseError(f"Document {document_id} not found")

        # Update document status to processing
        update_document_status(self.db, document_id, DocumentStatus.PROCESSING)

        # Initialize embedding model based on settings
        if settings.EMBEDDING_MODEL.startswith("openai:"):
            embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL.split(":")[1],
                openai_api_key=settings.OPENAI_API_KEY
            )
        elif settings.EMBEDDING_MODEL.startswith("huggingface:"):
            embeddings = OllamaEmbeddings(
                model=settings.EMBEDDING_MODEL.split(":")[1]
            )
        else:
            raise ValueError(f"Unsupported embedding model: {settings.EMBEDDING_MODEL}")

        # Initialize Qdrant client
        client = QdrantClient(
            url=settings.QDRANT_URL,
            port=settings.QDRANT_PORT
        )

        # Create Qdrant vector store
        vectorstore = Qdrant(
            client=client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=embeddings
        )

        # Prepare documents for embedding
        texts = []
        metadatas = []
        for chunk in document.chunks:
            texts.append(chunk.content)
            metadatas.append({
                "chunk_id": chunk.id,
                "document_id": document_id,
                "user_id": document.user_id,
                "page_number": chunk.page_number,
                "chunk_number": chunk.chunk_number
            })

        # Generate embeddings and store in Qdrant
        try:
            vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas
            )
        except Exception as e:
            raise LLMError(f"Failed to generate embeddings: {str(e)}")

        # Update document status to completed
        update_document_status(self.db, document_id, DocumentStatus.COMPLETED)

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_processed": len(texts)
        }

    except Exception as e:
        logger.error(f"Error generating embeddings for document {document_id}: {str(e)}")
        # Update document status to failed
        try:
            update_document_status(self.db, document_id, DocumentStatus.FAILED)
        except Exception as db_error:
            logger.error(f"Failed to update document status: {str(db_error)}")

        return {
            "status": "error",
            "document_id": document_id,
            "message": str(e)
        }

@celery_app.task(bind=True, base=DatabaseTask, name="app.worker.process_document")
def process_document_task(self, document_id: int) -> Dict[str, Any]:
    """
    Process a document by splitting it into chunks and preparing it for embedding generation.
    
    Args:
        document_id: ID of the document to process
        
    Returns:
        Dict containing task status and any error messages
    """
    try:
        # Get document from database
        document = get_document(self.db, document_id)
        if not document:
            raise DatabaseError(f"Document {document_id} not found")

        # Update document status to processing
        update_document_status(self.db, document_id, DocumentStatus.PROCESSING)

        # TODO: Implement document processing logic  (already done in the document_manager.py, but we need to add the chunking logic here)
        # 1. Read the document file
        # 2. Split into chunks
        # 3. Store chunks in database
        # 4. Queue embedding generation task

        # Queue embedding generation task
        generate_embeddings_task.delay(document_id)

        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document processing started"
        }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        # Update document status to failed
        try:
            update_document_status(self.db, document_id, DocumentStatus.FAILED)
        except Exception as db_error:
            logger.error(f"Failed to update document status: {str(db_error)}")

        return {
            "status": "error",
            "document_id": document_id,
            "message": str(e)
        } 