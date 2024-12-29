import os
from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentCreate
from app.crud.crud_document import create_document, update_document_status
from app.core.config import settings
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import (
    TitleExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor,
    KeywordExtractor,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.schema import TextNode, ImageNode, BaseNode
from llama_index.readers.file import CSVReader, PandasExcelReader
from qdrant_client import QdrantClient, models
from langchain_community.vectorstores import Qdrant
from PIL import Image
import io
import base64
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredImageLoader,
    UnstructuredExcelLoader
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter
)
import logging
from langchain_community.document_transformers import Html2TextTransformer
from langchain_openai import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
import json
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

def get_embedding_model():
    """Initializes and returns the embedding model."""
    if settings.EMBEDDING_MODEL == "openai":
        return OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=settings.OPENAI_API_KEY  # Assuming users will set this if they use OpenAI
        )
    elif settings.EMBEDDING_MODEL.startswith("huggingface:"):
        # Handle Hugging Face models (you might need to install a different library)
        # Example using Sentence Transformers:
        from sentence_transformers import SentenceTransformer
        model_name = settings.EMBEDDING_MODEL.split(":")[1]
        return SentenceTransformer(model_name)
    else:
        raise ValueError(f"Unsupported embedding model: {settings.EMBEDDING_MODEL}")

def get_text_splitter(mime_type: str):
    """Get appropriate text splitter based on content type."""
    if mime_type == "text/markdown":
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        return MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    elif mime_type == "text/html":
        return HTMLHeaderTextSplitter()
    else:
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.TEXT_SPLITTER_CHUNK_SIZE,
            chunk_overlap=settings.TEXT_SPLITTER_CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

def get_metadata_extractors():
    """Initializes and returns the metadata extractors."""
    return [
        TitleExtractor(nodes=5, llm=OpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)),
        QuestionsAnsweredExtractor(questions=3, llm=OpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)),
        SummaryExtractor(summaries=["prev", "self"], llm=OpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)),
        KeywordExtractor(keywords=5, llm=OpenAI(model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)),
    ]

def save_file(file: UploadFile, directory: str) -> str:
    """Saves the uploaded file to the specified directory."""
    file_path = os.path.join(directory, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    return file_path

def get_document_loader(file_path: str, mime_type: str):
    """Get appropriate document loader based on mime type."""
    loaders = {
        "application/pdf": PyPDFLoader,
        "application/msword": Docx2txtLoader,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": Docx2txtLoader,
        "text/csv": CSVLoader,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": UnstructuredExcelLoader,
    }
    
    if mime_type.startswith("image/"):
        return UnstructuredImageLoader(file_path, mode="elements")
    
    loader_class = loaders.get(mime_type)
    if loader_class:
        return loader_class(file_path)
    
    raise ValueError(f"Unsupported mime type: {mime_type}")

async def generate_embeddings_and_store(db: Session, document_id: int, nodes: List[Document]):
    """Generates embeddings for document chunks and stores them in Qdrant."""
    try:
        client = QdrantClient(
            url=settings.QDRANT_HOST, 
            port=settings.QDRANT_PORT,
        )

        # Create collection if it doesn't exist
        try:
            client.get_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
        except Exception:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)
            )

        vector_store = Qdrant(
            client=client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=get_embedding_model()
        )
        
        for node in nodes:
            metadata = {
                "document_id": document_id,
                "image_support": isinstance(node, ImageNode),
                "mime_type": node.metadata.get("mime_type", "text/plain"),
                "chunk_type": "image" if isinstance(node, ImageNode) else "text"
            }
            node.metadata.update(metadata)
        
        vector_store.add_documents(nodes)
        
        # Update document status to completed
        update_document_status(db, document_id, DocumentStatus.COMPLETED)

    except Exception as e:
        logger.error(f"Failed to generate embeddings and store: {e}")
        update_document_status(db, document_id, DocumentStatus.FAILED, str(e))
        raise

def get_metadata_extraction_chain(llm):
    """Creates an LLMChain for extracting additional metadata."""
    response_schemas = [
        ResponseSchema(name="title", description="What is the main title of the document?"),
        ResponseSchema(name="summary", description="Provide a brief summary of the document."),
        ResponseSchema(name="keywords", description="What are the main keywords of the document?"),
        ResponseSchema(name="questions", description="What are some questions that this document answers?")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt_template = """
    Extract the following information from the text:

    {format_instructions}

    Text: {text}
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["text"],
        partial_variables={"format_instructions": format_instructions}
    )
    return LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)

async def process_document(db: Session, document: Document):
    """Processes the document: loads, chunks, generates embeddings, and stores in Qdrant."""
    try:
        # Load document using appropriate loader
        loader = get_document_loader(document.file_path, document.mime_type)
        pages = loader.load()

        # Get appropriate text splitter
        text_splitter = get_text_splitter(document.mime_type)
        chunks = text_splitter.split_documents(pages)

        # Optionally transform HTML content to plain text
        if document.mime_type == "text/html":
            transformer = Html2TextTransformer()
            chunks = transformer.transform_documents(chunks)

        # Enhance metadata with LLM
        llm = OpenAI(
            model="gpt-3.5-turbo",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
        metadata_chain = get_metadata_extraction_chain(llm)
        for chunk in chunks:
            try:
                metadata = metadata_chain.invoke({"text": chunk.page_content})
                chunk.metadata.update(metadata)
            except Exception as e:
                logger.error(f"Failed to extract metadata: {e}")

        # Generate embeddings and store in Qdrant
        await generate_embeddings_and_store(db, document.id, chunks)

    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        update_document_status(
            db, 
            document.id, 
            DocumentStatus.FAILED,
            str(e)
        )
        raise 