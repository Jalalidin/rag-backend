from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserLLMConfig(Base):
    __tablename__ = "user_llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_name = Column(String, index=True)
    api_key = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    model_type = Column(String)  # e.g., "openai", "huggingface", "custom"

    user = relationship("User", back_populates="llm_configs") 