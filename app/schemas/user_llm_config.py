from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
import json

# Load OpenRouter models from a JSON file
with open("openrouter_models.json", "r") as f:
    OPENROUTER_MODELS = json.load(f)

class SupportedModel(BaseModel):
    name: str = Field(..., description="Name of the supported model")
    type: str = Field(..., description="Type of the model (e.g., gemini, openai, mistral)")
    image_support: bool = Field(..., description="Whether the model supports image processing")
    web_search_support: bool = Field(..., description="Whether the model supports web search capabilities")

class UserLLMConfigBase(BaseModel):
    model_name: str = Field(..., description="Name of the LLM model (e.g., gemini-pro, gpt-4-turbo)")
    api_key: Optional[str] = Field(None, description="API key for accessing the model service")
    base_url: Optional[str] = Field(None, description="Base URL for the model API endpoint")
    model_type: str = Field(..., description="Type of the model service (e.g., gemini, openai, mistral)")
    callback_manager: Optional[Any] = Field(
        None, description="Callback manager for handling streaming and events"
    )
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    top_k: Optional[int] = Field(None, description="Top-k sampling parameter")
    top_p: Optional[float] = Field(None, description="Top-p (nucleus) sampling parameter")
    temperature: Optional[float] = Field(None, description="Temperature parameter for controlling randomness")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty parameter")
    seed: Optional[int] = Field(None, description="Seed for reproducibility")

    @field_validator("model_name")
    def validate_model_name(cls, value, values):
        """Validates the model name based on the model type."""
        model_type = values.get("model_type")
        if model_type == "gemini" and value not in ["gemini-pro", "gemini-1.5-flash-8b", "gemini-2.0-flash-thinking", "gemini-pro-vision"]:
            raise ValueError(f"Invalid Gemini model name: {value}")
        elif model_type == "openai" and value not in ["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4-turbo"]:
            raise ValueError(f"Invalid OpenAI model name: {value}")
        elif model_type == "mistral" and value not in ["mistral-tiny", "mistral-small", "mistral-medium"]:
            raise ValueError(f"Invalid Mistral model name: {value}")
        elif model_type == "claude" and value not in ["claude-3.5-sonnet"]:
            raise ValueError(f"Invalid Claude model name: {value}")
        elif model_type == "llama" and value not in ["llama-3.2"]:
            raise ValueError(f"Invalid Llama model name: {value}")
        elif model_type == "openrouter" and value not in OPENROUTER_MODELS:
            raise ValueError(f"Invalid OpenRouter model name: {value}")
        return value

class UserLLMConfigCreate(UserLLMConfigBase):
    pass

class UserLLMConfigUpdate(BaseModel):
    model_name: Optional[str] = Field(None, description="Updated name of the LLM model")
    api_key: Optional[str] = Field(None, description="Updated API key for the model service")
    base_url: Optional[str] = Field(None, description="Updated base URL for the model API endpoint")
    model_type: Optional[str] = Field(None, description="Updated type of the model service")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    top_k: Optional[int] = Field(None, description="Top-k sampling parameter")
    top_p: Optional[float] = Field(None, description="Top-p (nucleus) sampling parameter")
    temperature: Optional[float] = Field(None, description="Temperature parameter for controlling randomness")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty parameter")
    seed: Optional[int] = Field(None, description="Seed for reproducibility")

    @field_validator("model_name")
    def validate_model_name_update(cls, value, values):
        """Validates the model name based on the model type."""
        model_type = values.get("model_type")
        if model_type == "gemini" and value not in ["gemini-pro", "gemini-1.5-flash-8b", "gemini-2.0-flash-thinking", "gemini-pro-vision"]:
            raise ValueError(f"Invalid Gemini model name: {value}")
        elif model_type == "openai" and value not in ["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4-turbo"]:
            raise ValueError(f"Invalid OpenAI model name: {value}")
        elif model_type == "mistral" and value not in ["mistral-tiny", "mistral-small", "mistral-medium"]:
            raise ValueError(f"Invalid Mistral model name: {value}")
        elif model_type == "claude" and value not in ["claude-3.5-sonnet"]:
            raise ValueError(f"Invalid Claude model name: {value}")
        elif model_type == "llama" and value not in ["llama-3.2"]:
            raise ValueError(f"Invalid Llama model name: {value}")
        elif model_type == "openrouter" and value not in OPENROUTER_MODELS:
            raise ValueError(f"Invalid OpenRouter model name: {value}")
        return value

class UserLLMConfig(UserLLMConfigBase):
    id: int = Field(..., description="Unique identifier for the user's LLM configuration")
    user_id: int = Field(..., description="ID of the user who owns this configuration")

    class Config:
        from_attributes = True 