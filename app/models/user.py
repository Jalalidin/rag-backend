from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Relationships
    documents = relationship("Document", back_populates="user") 
    chat_sessions = relationship("ChatSession", back_populates="user") 
    llm_configs = relationship("UserLLMConfig", back_populates="user") 