from typing import Optional
from langchain.callbacks.base import BaseCallbackManager
from langchain.callbacks.manager import AsyncCallbackManager, CallbackManager
from langchain_community.cache import SQLAlchemyCache
from sqlalchemy.engine import Engine

def get_callback_manager() -> CallbackManager:
    """
    Get a synchronous callback manager for LangChain.
    
    Returns:
        CallbackManager: A callback manager instance
    """
    return CallbackManager([])

def get_async_callback_manager() -> AsyncCallbackManager:
    """
    Get an asynchronous callback manager for LangChain.
    
    Returns:
        AsyncCallbackManager: An async callback manager instance
    """
    return AsyncCallbackManager([])

def setup_langchain_cache(engine: Engine) -> None:
    """
    Setup SQLAlchemy cache for LangChain.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    from langchain.globals import set_llm_cache
    set_llm_cache(SQLAlchemyCache(engine)) 