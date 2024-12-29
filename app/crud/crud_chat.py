from typing import List, Optional, Dict
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatSessionUpdate
import json

def create_chat(db: Session, user_id: int, chat_create: ChatSessionCreate) -> ChatSession:
    """Create a new chat session."""
    db_chat = ChatSession(
        title=chat_create.title,
        user_id=user_id,
        parent_id=chat_create.parent_id
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chat_session(db: Session, chat_id: int) -> Optional[ChatSession]:
    """Get a chat session by ID."""
    return db.query(ChatSession)\
        .filter(ChatSession.id == chat_id)\
        .filter(ChatSession.is_deleted == False)\
        .first()

def update_chat_session(db: Session, chat_id: int, chat_update: ChatSessionUpdate) -> ChatSession:
    """Update a chat session."""
    db_chat = get_chat_session(db, chat_id)
    if not db_chat:
        return None
    
    update_data = chat_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chat, field, value)
    
    db.commit()
    db.refresh(db_chat)
    return db_chat

def delete_chat_session(db: Session, chat_id: int):
    """Soft delete a chat session."""
    db_chat = get_chat_session(db, chat_id)
    if db_chat:
        db_chat.is_deleted = True
        db.commit()

def get_user_chat_sessions(db: Session, user_id: int) -> List[ChatSession]:
    """Get all chat sessions for a user in a tree structure."""
    # Get root level chats (no parent)
    root_chats = db.query(ChatSession)\
        .filter(ChatSession.user_id == user_id)\
        .filter(ChatSession.parent_id == None)\
        .filter(ChatSession.is_deleted == False)\
        .options(joinedload(ChatSession.children))\
        .order_by(desc(ChatSession.updated_at))\
        .all()
    
    # Add last message to each chat
    for chat in root_chats:
        _add_last_message(db, chat)
        _process_children(db, chat)
    
    return root_chats

def _process_children(db: Session, chat: ChatSession):
    """Recursively process children of a chat session."""
    for child in chat.children:
        if not child.is_deleted:
            _add_last_message(db, child)
            _process_children(db, child)

def _add_last_message(db: Session, chat: ChatSession):
    """Add the last message to a chat session."""
    last_message = db.query(ChatMessage)\
        .filter(ChatMessage.chat_session_id == chat.id)\
        .order_by(desc(ChatMessage.created_at))\
        .first()
    setattr(chat, 'last_message', last_message)

def create_message(db: Session, message: ChatMessageCreate, chat_id: int, user_id: int) -> ChatMessage:
    """Create a new chat message."""
    # Convert source documents to JSON string if present
    source_docs_json = json.dumps(message.source_documents) if message.source_documents else None
    
    db_message = ChatMessage(
        message=message.message,
        response=message.response,
        chat_session_id=chat_id,
        user_id=user_id,
        is_typing=message.is_typing,
        source_documents=source_docs_json
    )
    db.add(db_message)
    
    # Update chat session's updated_at timestamp
    chat_session = get_chat_session(db, chat_id)
    if chat_session:
        chat_session.updated_at = db_message.created_at
    
    db.commit()
    db.refresh(db_message)
    
    # Convert source documents back to list for response
    if db_message.source_documents:
        db_message.source_documents = json.loads(db_message.source_documents)
    
    return db_message

def get_chat_history(db: Session, chat_id: int) -> List[ChatMessage]:
    """Get chat history for a specific chat."""
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.chat_session_id == chat_id)\
        .order_by(ChatMessage.created_at)\
        .all()
    
    # Convert source documents from JSON string to list for each message
    for message in messages:
        if message.source_documents:
            message.source_documents = json.loads(message.source_documents)
        else:
            message.source_documents = []
    
    return messages 