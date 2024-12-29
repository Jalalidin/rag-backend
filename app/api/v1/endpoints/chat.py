"""
Chat Endpoints Module

This module handles all chat-related API endpoints including:
- Chat session management (create, update, delete)
- Message handling (create, stream)
- WebSocket connections for real-time chat
- Chat history retrieval
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, WebSocket, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.core.exceptions import ResourceNotFoundError
from app.schemas.chat import (
    ChatMessage, 
    ChatMessageCreate, 
    ChatHistory, 
    ChatSessionUpdate, 
    ChatSessionCreate, 
    ChatSessionResponse
)
from app.crud.crud_chat import (
    get_chat_history, 
    create_chat, 
    create_message, 
    get_chat_session,
    update_chat_session,
    delete_chat_session,
    get_user_chat_sessions
)
from app.llm_manager import generate_chat_response, generate_streaming_chat_response
from app.utils.websocket_manager import WebSocketManager
import json
import logging
import asyncio

# Initialize logging and router
logger = logging.getLogger(__name__)
router = APIRouter()
ws_manager = WebSocketManager()

@router.post("/", response_model=ChatSessionResponse)
async def create_new_chat(
    chat_create: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session for the current user.
    
    Args:
        chat_create: Chat session creation parameters
        db: Database session
        current_user: Authenticated user making the request
        
    Returns:
        ChatSessionResponse: Newly created chat session details
    """
    return create_chat(db, user_id=current_user.id, chat_create=chat_create)

@router.get("/tree", response_model=List[ChatSessionResponse])
async def get_chat_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get hierarchical chat session tree."""
    return get_user_chat_sessions(db, current_user.id)

@router.put("/{chat_id}", response_model=ChatSessionResponse)
async def update_chat(
    chat_id: int,
    chat_update: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update chat session details."""
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")
    return update_chat_session(db, chat_id, chat_update)

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (archive) chat session."""
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")
    delete_chat_session(db, chat_id)
    return {"message": "Chat session archived"}

@router.get("/{chat_id}/history", response_model=List[ChatMessage])
async def read_chat_history(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve chat history for a specific chat."""
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")
    return get_chat_history(db, chat_id)

@router.websocket("/{chat_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for real-time chat communication.
    
    Handles:
    - Real-time message streaming
    - Typing indicators
    - Message broadcasting to connected clients
    
    Args:
        websocket: WebSocket connection instance
        chat_id: ID of the chat session
        db: Database session
        current_user: Authenticated user making the connection
    """
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")

    await ws_manager.connect(websocket, chat_id, current_user.id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types (typing indicators and actual messages)
            if data["type"] == "typing":
                await ws_manager.broadcast_typing(chat_id, current_user.id, data["is_typing"])
            elif data["type"] == "message":
                message_create = ChatMessageCreate(**data["content"])
                # Set typing indicator while generating response
                await ws_manager.broadcast_typing(chat_id, current_user.id, True)
                
                # Stream response chunks to all connected clients
                async for chunk in generate_chat_response(db, current_user, chat_id, message_create):
                    await ws_manager.broadcast_message(chat_id, {
                        "type": "chunk",
                        "content": chunk,
                        "user_id": current_user.id
                    })
                
                # Clear typing indicator after response is complete
                await ws_manager.broadcast_typing(chat_id, current_user.id, False)
                
                # Send final complete message notification
                await ws_manager.broadcast_message(chat_id, {
                    "type": "message_complete",
                    "content": message_create.dict(),
                    "user_id": current_user.id
                })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, chat_id, current_user.id)

@router.post("/{chat_id}/messages", response_model=ChatMessage)
async def create_new_message(
    chat_id: int,
    message: ChatMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new message in a chat session with background processing.
    
    Args:
        chat_id: ID of the chat session
        message: Message content and metadata
        background_tasks: FastAPI background tasks handler
        db: Database session
        current_user: Authenticated user creating the message
        
    Returns:
        ChatMessage: Created message details
        
    Note:
        Response generation happens in the background to avoid blocking
    """
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")
    
    # Create initial message with typing indicator
    message.is_typing = True
    db_message = create_message(db, message, chat_id, current_user.id)
    
    # Generate response asynchronously
    background_tasks.add_task(
        generate_chat_response,
        db,
        current_user,
        chat_id,
        message
    )
    
    return db_message

@router.post("/{chat_id}/messages/stream")
async def create_streaming_message(
    chat_id: int,
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new message with streaming response.
    
    Args:
        chat_id: ID of the chat session
        message: Message content and metadata
        db: Database session
        current_user: Authenticated user creating the message
        
    Returns:
        StreamingResponse: Server-sent events stream of response chunks
    """
    chat = get_chat_session(db, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise ResourceNotFoundError(detail="Chat session not found")
    
    return StreamingResponse(
        generate_streaming_chat_response(db, current_user, chat_id, message),
        media_type="text/event-stream"
    ) 