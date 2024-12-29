from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator

class ChatSessionBase(BaseModel):
    title: str = Field(..., description="Title of the chat session")
    parent_id: Optional[int] = Field(None, description="ID of the parent chat session, if this is a child session")

    @field_validator('parent_id')
    def validate_parent_id(cls, v):
        if v == 0:  # Convert 0 to None
            return None
        return v

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title of the chat session")
    parent_id: Optional[int] = Field(None, description="Updated parent chat session ID")
    is_archived: Optional[bool] = Field(None, description="Whether the chat session is archived")

class ChatMessageBase(BaseModel):
    message: str = Field(..., description="User's input message")
    response: Optional[str] = Field(None, description="AI's response to the user's message")
    is_typing: Optional[bool] = Field(False, description="Indicates if the AI is currently generating a response")
    source_documents: Optional[List[Dict]] = Field(default_factory=list, description="List of reference documents used in generating the response")

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int = Field(..., description="Unique identifier for the chat message")
    chat_session_id: int = Field(..., description="ID of the chat session this message belongs to")
    user_id: int = Field(..., description="ID of the user who sent the message")
    created_at: datetime = Field(..., description="Timestamp when the message was created")

    class Config:
        from_attributes = True

class ChatSessionResponse(ChatSessionBase):
    id: int = Field(..., description="Unique identifier for the chat session")
    user_id: int = Field(..., description="ID of the user who owns this chat session")
    created_at: datetime = Field(..., description="Timestamp when the session was created")
    updated_at: datetime = Field(..., description="Timestamp when the session was last updated")
    is_deleted: bool = Field(..., description="Whether the chat session has been deleted")
    is_archived: bool = Field(..., description="Whether the chat session is archived")
    children: List['ChatSessionResponse'] = Field(default_factory=list, description="List of child chat sessions")
    last_message: Optional[ChatMessage] = Field(None, description="Most recent message in this chat session")

    class Config:
        from_attributes = True

# Needed for self-referencing model
ChatSessionResponse.model_rebuild()

class ChatHistory(BaseModel):
    chat_id: int = Field(..., description="ID of the chat session")
    messages: List[ChatMessage] = Field(..., description="List of messages in the chat session")
    
    class Config:
        from_attributes = True 