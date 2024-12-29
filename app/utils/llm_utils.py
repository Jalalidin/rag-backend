import logging
from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Ollama
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from app.core.config import settings
from app.models.user_llm_config import UserLLMConfig
from app.utils.system_messages import get_default_system_message, get_image_system_message, get_web_search_system_message
from app.core.exceptions import OpenRouterError, LLMError

logger = logging.getLogger(__name__)

def get_openrouter_llm(llm_config: UserLLMConfig):
    """
    Creates an OpenRouter LLM instance using LangChain's ChatOpenAI.
    Based on OpenRouter documentation: https://openrouter.ai/docs
    """
    try:
        return ChatOpenAI(
            model=llm_config.model_name,
            temperature=llm_config.temperature or 0.7,
            openai_api_key=settings.OPENROUTER_API_KEY,
            max_tokens=llm_config.max_tokens,
            top_p=llm_config.top_p,
            streaming=True,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.SITE_URL,
                "X-Title": settings.SITE_NAME,
            },
            model_kwargs={
                "route": "fallback",
                "models": [
                    llm_config.model_name,
                    "anthropic/claude-2.1",
                    "mistralai/mixtral-8x7b-instruct",
                ],
                "provider": {
                    "order": ["OpenAI", "Anthropic", "Together"],
                    "allow_fallbacks": True,
                    "data_collection": "deny"
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize OpenRouter LLM: {str(e)}")
        if hasattr(e, 'status_code'):
            raise OpenRouterError(str(e), getattr(e, 'status_code'), getattr(e, 'metadata', None))
        raise LLMError(f"Failed to initialize OpenRouter LLM: {str(e)}")

def get_llm(llm_config: UserLLMConfig):
    """
    Returns the appropriate language model based on the configuration.
    """
    model_name = llm_config.model_name
    model_type = llm_config.model_type
    temperature = llm_config.temperature
    max_tokens = llm_config.max_tokens
    top_p = llm_config.top_p
    frequency_penalty = llm_config.frequency_penalty
    presence_penalty = llm_config.presence_penalty
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    try:
        if model_type == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                openai_api_key=settings.OPENAI_API_KEY,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                streaming=True,
                callback_manager=callback_manager,
            )
        elif model_type == "gemini":
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=settings.GOOGLE_API_KEY,
                max_output_tokens=max_tokens,
                top_p=top_p,
                convert_system_message_to_human=True,
                streaming=True,
                callback_manager=callback_manager,
            )
        elif model_type == "mistral":
            return ChatMistralAI(
                model=model_name,
                temperature=temperature,
                mistral_api_key=settings.MISTRAL_API_KEY,
                max_tokens=max_tokens,
                top_p=top_p,
                streaming=True,
                callback_manager=callback_manager,
            )
        elif model_type == "claude":
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                max_tokens_to_sample=max_tokens,
                top_p=top_p,
                streaming=True,
                callback_manager=callback_manager,
            )
        elif model_type == "llama":
            return Ollama(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                streaming=True,
                callback_manager=callback_manager,
            )
        elif model_type == "openrouter":
            return get_openrouter_llm(llm_config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    except Exception as e:
        logger.error(f"Error creating LLM instance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating LLM instance: {e}",
        )

def get_prompt_template(llm_config: UserLLMConfig, image_support: bool = False, web_search_support: bool = False):
    """
    Returns the appropriate prompt template based on the configuration.
    """
    if image_support:
        system_message = get_image_system_message(llm_config)
    elif web_search_support:
        system_message = get_web_search_system_message(llm_config)
    else:
        system_message = get_default_system_message(llm_config)

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            ("user", "{input}"),
        ]
    )

def get_retriever(user_id: int):
    """
    Returns a Qdrant retriever for the given user.
    """
    try:
        client = QdrantClient(
            url=settings.QDRANT_URL,
        )

        embedding = get_embedding_model()

        vectorstore = Qdrant(
            client=client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=embedding,
        )

        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "filter": {
                    "must": [
                        {
                            "key": "metadata.user_id",
                            "match": {"value": user_id},
                        }
                    ]
                },
            },
        )
    except Exception as e:
        logger.error(f"Error creating retriever: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating retriever: {e}",
        )

def get_retrieval_chain(retriever, llm_config: UserLLMConfig):
    """
    Returns a retrieval chain for the given retriever and LLM configuration.
    """
    llm = get_llm(llm_config)
    prompt = get_prompt_template(llm_config)

    return (
        {
            "input": lambda x: x["input"],
            "context": retriever,
        }
        | prompt
        | llm
    )

def get_embedding_model():
    """
    Returns the appropriate embedding model based on the configuration.
    """
    model_name = settings.EMBEDDING_MODEL
    model_type = model_name.split(":")[0]

    if model_type == "openai":
        return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    elif model_type == "huggingface":
        return OllamaEmbeddings(model=model_name.split(":")[1])
    else:
        raise ValueError(f"Unsupported embedding model type: {model_type}") 