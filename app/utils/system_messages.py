from app.models.user_llm_config import UserLLMConfig

def get_openrouter_system_message(llm_config: UserLLMConfig):
    """
    Returns the system message for OpenRouter models.
    """
    return """You are an AI assistant that can answer questions based on provided documents.
    If the question cannot be answered from the documents, respond with "I don't know".
    """

def get_default_system_message(llm_config: UserLLMConfig):
    """
    Returns the default system message based on the LLM configuration.
    """
    if llm_config.model_type == "openrouter":
        return get_openrouter_system_message(llm_config)
    else:
        return """You are an AI assistant that can answer questions based on provided documents.
        If the question cannot be answered from the documents, respond with "I don't know".
        """

def get_image_system_message(llm_config: UserLLMConfig):
    """
    Returns the system message for image-related queries based on the LLM configuration.
    """
    if llm_config.model_type == "openrouter":
        return get_openrouter_system_message(llm_config)
    else:
        return """You are an AI assistant that can describe images and answer questions based on provided documents.
        If the question cannot be answered from the documents, respond with "I don't know".
        """

def get_web_search_system_message(llm_config: UserLLMConfig):
    """
    Returns the system message for web search-related queries based on the LLM configuration.
    """
    if llm_config.model_type == "openrouter":
        return get_openrouter_system_message(llm_config)
    else:
        return """You are an AI assistant that can answer questions based on provided documents and web search results.
        If the question cannot be answered from the documents or web search results, respond with "I don't know".
        """ 