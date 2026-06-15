"""
agents/llm_client.py
Thin wrapper around the Groq API using langchain-groq.
Returns a ready-to-use ChatGroq instance used by all agents.
"""

from functools import lru_cache
from langchain_groq import ChatGroq

from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from utils.logger import logger


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Return a cached ChatGroq LLM instance."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example → .env and add your key."
        )
    logger.info(f"Initialising LLM: {LLM_MODEL}")
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )
