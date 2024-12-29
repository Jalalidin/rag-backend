from typing import Optional, List, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.core.config import settings
from app.crud.crud_chat import get_chat_history
from app.crud.crud_user_llm_config import get_default_user_llm_config
from app.models.user import User
from sqlalchemy.orm import Session
from app.schemas.chat import ChatMessageCreate, ChatMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper
from app.utils.langchain_utils import get_async_callback_manager, get_callback_manager
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from openai import OpenAI

from app.utils.llm_utils import get_openrouter_llm

logger = logging.getLogger(__name__)

def format_vision_message(model_type: str, text: str, image_base64: str) -> HumanMessage:
    """Format vision message based on model type."""
    if model_type == "openai":
        return HumanMessage(content=[
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
        ])
    elif model_type == "gemini":
        return HumanMessage(content={
            "text": text,
            "images": [image_base64]
        })
    elif model_type == "claude":
        return HumanMessage(content=f"""
            {text}
            <image>{image_base64}</image>
        """)
    else:
        raise ValueError(f"Unsupported vision model type: {model_type}")

def get_llm(user: User, db: Session, streaming: bool = False) -> BaseChatModel:
    """Initializes and returns the appropriate language model based on user configuration."""
    try:
        user_llm_config = get_default_user_llm_config(db, user.id)
        callback_manager = get_callback_manager()
        async_callback_manager = get_async_callback_manager()

        if user_llm_config:
            if user_llm_config.model_type == "openai":
                return ChatOpenAI(
                    model=user_llm_config.model_name,
                    openai_api_key=user_llm_config.api_key,
                    openai_api_base=user_llm_config.base_url,
                    temperature=0.7,
                    streaming=streaming,
                    callbacks=async_callback_manager if streaming else callback_manager,
                )
            elif user_llm_config.model_type == "gemini":
                return ChatGoogleGenerativeAI(
                    model=user_llm_config.model_name,
                    google_api_key=user_llm_config.api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True,
                    streaming=streaming,
                    callbacks=async_callback_manager if streaming else callback_manager,
                )
            elif user_llm_config.model_type == "claude":
                return ChatAnthropic(
                    model_name=user_llm_config.model_name,
                    anthropic_api_key=user_llm_config.api_key,
                    temperature=0.7,
                    max_tokens=4096,
                    anthropic_version="2024-01-01",
                    callbacks=callback_manager
                )
            elif user_llm_config.model_type == "mistral":
                return ChatMistralAI(
                    model=user_llm_config.model_name,
                    mistral_api_key=user_llm_config.api_key,
                    temperature=0.7,
                    callbacks=callback_manager
                )
            elif user_llm_config.model_type == "huggingface":
                return HuggingFaceEndpoint(
                    endpoint_url=user_llm_config.base_url,
                    huggingfacehub_api_token=user_llm_config.api_key,
                    task="text-generation",
                    model_kwargs={
                        "max_new_tokens": user_llm_config.max_tokens,
                        "top_k": user_llm_config.top_k,
                        "top_p": user_llm_config.top_p,
                        "temperature": user_llm_config.temperature,
                        "repetition_penalty": user_llm_config.repetition_penalty,
                        "seed": user_llm_config.seed,
                    },
                    callbacks=callback_manager
                )
            elif user_llm_config.model_type == "openrouter":
                return get_openrouter_llm(user_llm_config)
        else:
            # Use default model from config.py
            if settings.EMBEDDING_MODEL.startswith("huggingface:"):
                model_name = settings.EMBEDDING_MODEL.split(":")[1]
                return HuggingFaceEndpoint(
                    endpoint_url=f"https://api-inference.huggingface.co/models/{model_name}",  # Replace with the actual endpoint if different
                    task="text-generation",
                    model_kwargs={
                        "max_new_tokens": 512,  # Example value, adjust as needed
                        "top_k": 50,
                        "temperature": 0.7,
                        "repetition_penalty": 1.1,
                    },
                    callbacks=callback_manager,
                )
            else:
                raise ValueError(f"Unsupported default embedding model: {settings.EMBEDDING_MODEL}")

    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise

def setup_web_search_agent(llm: BaseChatModel):
    """Setup a web search agent using LCEL."""
    try:
        search = GoogleSearchAPIWrapper()
        tools = [
            Tool(
                name="Google Search",
                func=search.run,
                description="useful for when you need to answer questions about current events. You should ask targeted questions",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. Use the provided tools to answer questions.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_react_agent(llm, tools, prompt)
        memory = ConversationSummaryMemory(
            llm=llm, memory_key="chat_history", return_messages=True
        )
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=memory,
            handle_parsing_errors="Check your output and make sure it conforms!",
        )

        return agent_executor
    except ValueError as e:
        logger.error(f"Google Search API Wrapper initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to setup web search agent: {e}")
        raise

def setup_web_search_chain(llm: BaseChatModel):
    """Setup a web search chain using LCEL."""
    try:
        search = GoogleSearchAPIWrapper()
        template = """Answer the following question based only on the provided context:

        Question: {question}

        Context: {context}
        """
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            {
                "context": lambda x: search.run(x["question"]),
                "question": lambda x: x["question"],
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain
    except ValueError as e:
        logger.error(f"Google Search API Wrapper initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to setup web search chain: {e}")
        raise

async def generate_streaming_chat_response(
    db: Session,
    user: User,
    chat_id: int,
    message_create: ChatMessageCreate,
    image_base64: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Generates a streaming chat response using the user's selected LLM."""
    try:
        llm = get_llm(user, db, streaming=True)
        user_llm_config = get_default_user_llm_config(db, user.id)
        messages: List[BaseMessage] = []

        if image_base64 and user_llm_config:
            messages.append(format_vision_message(
                user_llm_config.model_type,
                message_create.message,
                image_base64
            ))
        else:
            chat_history = get_chat_history(db, chat_id)
            for msg in chat_history:
                if msg.message:
                    messages.append(HumanMessage(content=msg.message))
                if msg.response:
                    messages.append(AIMessage(content=msg.response))
            messages.append(HumanMessage(content=message_create.message))

        async for chunk in llm.astream(messages):
            yield chunk.content

        # Save the message to the database after the stream is finished
        message_create.response = ""  # Initialize response
        async for chunk in llm.astream(messages):
            message_create.response += chunk.content
            yield chunk.content

        # Save the message to the database after the stream is finished
        from app.crud.crud_chat import create_message
        create_message(db, message_create, chat_id, user.id)

    except Exception as e:
        logger.error(f"Failed to generate streaming chat response: {e}")
        raise

async def generate_chat_response(
    db: Session,
    user: User,
    chat_id: int,
    message_create: ChatMessageCreate,
    image_base64: Optional[str] = None,
) -> ChatMessage:
    """Generates a chat response using the user's selected LLM."""
    try:
        llm = get_llm(user, db, streaming=False)
        user_llm_config = get_default_user_llm_config(db, user.id)
        messages: List[BaseMessage] = []
        
        if image_base64 and user_llm_config:
            messages.append(format_vision_message(
                user_llm_config.model_type,
                message_create.message,
                image_base64
            ))
        else:
            messages.append(HumanMessage(content=message_create.message))

        if user_llm_config and user_llm_config.model_type == "gemini" and user_llm_config.model_name != "gemini-pro-vision":
            search_chain = setup_web_search_chain(llm)
            search_result = search_chain.invoke({"question": message_create.message})
            messages.append(AIMessage(content=search_result))

        response = llm.invoke(messages)
        message_create.response = response.content

        # Save the message to the database
        from app.crud.crud_chat import create_message
        db_message = create_message(db, message_create, chat_id, user.id)

        return db_message

    except Exception as e:
        logger.error(f"Failed to generate chat response: {e}")
        raise 