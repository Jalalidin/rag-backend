from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)

    # Relationships (Corrected)
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")
    children = relationship("ChatSession", back_populates="parent")
    parent = relationship("ChatSession", back_populates="children", remote_side=[id])

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    response = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_typing = Column(Boolean, default=False)
    source_documents = Column(JSON, nullable=True)

    # Relationships (Corrected)
    chat_session = relationship("ChatSession", back_populates="messages") 