from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user_llm_config import UserLLMConfig
from app.schemas.user_llm_config import UserLLMConfigCreate, UserLLMConfigUpdate

def create_user_llm_config(db: Session, user_llm_config_create: UserLLMConfigCreate, user_id: int) -> UserLLMConfig:
    """
    Creates a new LLM configuration for a user.
    """
    db_user_llm_config = UserLLMConfig(
        **user_llm_config_create.model_dump(),
        user_id=user_id
    )
    db.add(db_user_llm_config)
    db.commit()
    db.refresh(db_user_llm_config)
    return db_user_llm_config

def get_user_llm_config(db: Session, user_llm_config_id: int) -> Optional[UserLLMConfig]:
    return db.query(UserLLMConfig).filter(UserLLMConfig.id == user_llm_config_id).first()

def get_user_llm_configs(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[UserLLMConfig]:
    return db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user_id).offset(skip).limit(limit).all()

def update_user_llm_config(
    db: Session, db_user_llm_config: UserLLMConfig, user_llm_config_update: UserLLMConfigUpdate
) -> UserLLMConfig:
    """
    Updates an existing LLM configuration.
    """
    update_data = user_llm_config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user_llm_config, key, value)
    db.commit()
    db.refresh(db_user_llm_config)
    return db_user_llm_config

def delete_user_llm_config(db: Session, user_llm_config_id: int) -> bool:
    user_llm_config = get_user_llm_config(db, user_llm_config_id)
    if user_llm_config:
        db.delete(user_llm_config)
        db.commit()
        return True
    return False

def get_default_user_llm_config(db: Session, user_id: int) -> Optional[UserLLMConfig]:
    return db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user_id).order_by(UserLLMConfig.id).first() 