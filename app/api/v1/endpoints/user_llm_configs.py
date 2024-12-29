"""
User LLM Configuration Endpoints Module

This module manages user-specific LLM (Language Model) configurations.
It provides endpoints for:
- Listing supported LLM models and their capabilities
- Creating and managing user LLM configurations
- Setting and retrieving default configurations
- Updating configuration parameters

The module supports various LLM providers:
- OpenAI (GPT models)
- Google (Gemini models)
- Mistral (Mistral models)
- Anthropic (Claude models)
- Meta (Llama models)
- OpenRouter (various models through the OpenRouter API)

It also handles different types of configurations:
- Default configurations
- Provider-specific configurations (e.g., API keys, base URLs)
- Model-specific parameters (e.g., temperature, max_tokens)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user_llm_config import (
    SupportedModel,
    UserLLMConfig,
    UserLLMConfigCreate,
    UserLLMConfigUpdate,
)
from app.crud.crud_user_llm_config import (
    create_user_llm_config,
    get_user_llm_config,
    get_user_llm_configs,
    update_user_llm_config,
    delete_user_llm_config,
    get_default_user_llm_config,
)

router = APIRouter()

# Define supported models with their capabilities
# Each model specifies:
# - name: Model identifier
# - type: Provider/family of the model
# - image_support: Whether it can process images
# - web_search_support: Whether it can perform web searches
SUPPORTED_MODELS = [
    # OpenAI Models
    SupportedModel(name="gpt-3.5-turbo", type="openai", image_support=False, web_search_support=False),
    SupportedModel(name="gpt-4-turbo-preview", type="openai", image_support=False, web_search_support=False),
    SupportedModel(name="gpt-4-turbo", type="openai", image_support=False, web_search_support=False),
    # Google Gemini Models
    SupportedModel(name="gemini-pro", type="gemini", image_support=False, web_search_support=True),
    SupportedModel(name="gemini-1.5-flash-8b", type="gemini", image_support=False, web_search_support=True),
    SupportedModel(name="gemini-2.0-flash-thinking", type="gemini", image_support=False, web_search_support=True),
    SupportedModel(name="gemini-pro-vision", type="gemini", image_support=True, web_search_support=False),
    # Mistral Models
    SupportedModel(name="mistral-tiny", type="mistral", image_support=False, web_search_support=False),
    SupportedModel(name="mistral-small", type="mistral", image_support=False, web_search_support=False),
    SupportedModel(name="mistral-medium", type="mistral", image_support=False, web_search_support=False),
    # Anthropic Claude Models
    SupportedModel(name="claude-3.5-sonnet", type="claude", image_support=False, web_search_support=False),
    # Meta Models
    SupportedModel(name="llama-3.2", type="llama", image_support=False, web_search_support=False),
    # OpenRouter Models
    SupportedModel(
        name="mistralai/mixtral-8x7b-instruct",
        type="openrouter",
        image_support=False,
        web_search_support=False
    ),
    SupportedModel(
        name="anthropic/claude-3-sonnet",
        type="openrouter",
        image_support=True,
        web_search_support=False
    ),
    SupportedModel(
        name="openai/gpt-4-turbo",
        type="openrouter",
        image_support=True,
        web_search_support=False
    ),
    SupportedModel(
        name="google/gemini-pro",
        type="openrouter",
        image_support=False,
        web_search_support=True
    ),
]

@router.get("/models/", response_model=List[SupportedModel])
async def list_models():
    """
    List all supported LLM models and their capabilities.

    Returns:
        List[SupportedModel]: List of supported models with their features
            - name: Model identifier
            - type: Provider/family
            - image_support: Image processing capability
            - web_search_support: Web search integration
    """
    return SUPPORTED_MODELS

@router.post("/", response_model=UserLLMConfig)
async def create_config(
    user_llm_config_create: UserLLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new LLM configuration for the current user.

    Args:
        user_llm_config_create: Configuration parameters, including:
            - model_name: Name of the LLM model (e.g., "gpt-3.5-turbo", "gemini-pro").
            - api_key: (Optional) API key for the model provider.
            - base_url: (Optional) Base URL for the model API endpoint.
            - model_type: Type of the model service (e.g., "openai", "gemini", "mistral", "openrouter").
            - max_tokens: (Optional) Maximum number of tokens to generate.
            - top_k: (Optional) Top-k sampling parameter.
            - top_p: (Optional) Top-p (nucleus) sampling parameter.
            - temperature: (Optional) Temperature parameter for controlling randomness.
            - repetition_penalty: (Optional) Repetition penalty parameter.
            - seed: (Optional) Seed for reproducibility.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        UserLLMConfig: Created configuration details.

    Note:
        Users can have multiple configurations for different use cases
        (e.g., different models for different types of tasks).
    """
    return create_user_llm_config(db, user_llm_config_create, current_user.id)

@router.get("/{user_llm_config_id}", response_model=UserLLMConfig)
async def get_config(
    user_llm_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific LLM configuration by its ID.

    Args:
        user_llm_config_id: ID of the LLM configuration to retrieve.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        UserLLMConfig: Details of the requested LLM configuration.

    Raises:
        HTTPException 404: If the configuration is not found or does not belong to the user.
    """
    user_llm_config = get_user_llm_config(db, user_llm_config_id)
    if not user_llm_config or user_llm_config.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="LLM configuration not found")
    return user_llm_config

@router.get("/", response_model=List[UserLLMConfig])
async def get_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all LLM configurations for the current user.

    Args:
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        List[UserLLMConfig]: List of LLM configurations belonging to the user.
    """
    return get_user_llm_configs(db, current_user.id)

@router.put("/{user_llm_config_id}", response_model=UserLLMConfig)
async def update_config(
    user_llm_config_id: int,
    user_llm_config_update: UserLLMConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing LLM configuration.

    Args:
        user_llm_config_id: ID of the LLM configuration to update.
        user_llm_config_update: Updated configuration parameters, including:
            - model_name: (Optional) Updated name of the LLM model.
            - api_key: (Optional) Updated API key for the model provider.
            - base_url: (Optional) Updated base URL for the model API endpoint.
            - model_type: (Optional) Updated type of the model service.
            - max_tokens: (Optional) Updated maximum number of tokens to generate.
            - top_k: (Optional) Updated top-k sampling parameter.
            - top_p: (Optional) Updated top-p (nucleus) sampling parameter.
            - temperature: (Optional) Updated temperature parameter.
            - repetition_penalty: (Optional) Updated repetition penalty parameter.
            - seed: (Optional) Updated seed for reproducibility.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        UserLLMConfig: Updated configuration details.

    Raises:
        HTTPException 404: If the configuration is not found or does not belong to the user.
    """
    db_user_llm_config = get_user_llm_config(db, user_llm_config_id)
    if not db_user_llm_config or db_user_llm_config.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="LLM configuration not found")
    return update_user_llm_config(db, db_user_llm_config, user_llm_config_update)

@router.delete("/{user_llm_config_id}", status_code=204)
async def delete_config(
    user_llm_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific LLM configuration.

    Args:
        user_llm_config_id: ID of the LLM configuration to delete.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        None

    Raises:
        HTTPException 404: If the configuration is not found or does not belong to the user.
    """
    if not delete_user_llm_config(db, user_llm_config_id):
        raise HTTPException(status_code=404, detail="LLM configuration not found")

@router.post("/{user_llm_config_id}/set-default", response_model=UserLLMConfig)
async def set_default_config(
    user_llm_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a specific LLM configuration as the default for the current user.

    Args:
        user_llm_config_id: ID of the LLM configuration to set as default.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        UserLLMConfig: Details of the default LLM configuration.

    Raises:
        HTTPException 404: If the configuration is not found or does not belong to the user.
    """
    user_llm_config = get_user_llm_config(db, user_llm_config_id)
    if not user_llm_config or user_llm_config.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="LLM configuration not found")

    # Set all other configurations to not be the default
    for config in get_user_llm_configs(db, current_user.id):
        if config.id != user_llm_config_id:
            update_user_llm_config(db, config, UserLLMConfigUpdate(is_default=False))

    # Set the specified configuration as the default
    updated_config = update_user_llm_config(db, user_llm_config, UserLLMConfigUpdate(is_default=True))
    return updated_config

@router.get("/default/", response_model=UserLLMConfig)
async def get_default_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the default LLM configuration for the current user.

    Args:
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        UserLLMConfig: Details of the default LLM configuration.

    Raises:
        HTTPException 404: If no default configuration is found for the user.
    """
    default_config = get_default_user_llm_config(db, current_user.id)
    if not default_config:
        raise HTTPException(status_code=404, detail="Default LLM configuration not found")
    return default_config

