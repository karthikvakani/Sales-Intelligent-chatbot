"""
config/settings.py
Centralised, validated configuration loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
FAISS_INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", str(BASE_DIR / "faiss_indices")))
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(BASE_DIR / "cache")))
EXPORT_DIR = Path(os.getenv("EXPORT_DIR", str(BASE_DIR / "exports")))

for _p in [FAISS_INDEX_PATH, CACHE_DIR, EXPORT_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

# ── API Keys ─────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_MODEL: str = "llama-3.3-70b-versatile"
LLM_TEMPERATURE: float = 0.2
LLM_MAX_TOKENS: int = 4096

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

# ── Retrieval ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL: str = os.getenv(
    "CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)
TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "10"))
TOP_K_RERANK: int = int(os.getenv("TOP_K_RERANK", "5"))

# ── Cache ────────────────────────────────────────────────────────────────────
CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "24"))

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def validate_keys() -> dict[str, bool]:
    """Return which API keys are configured (without revealing values)."""
    return {
        "groq": bool(GROQ_API_KEY),
        "tavily": bool(TAVILY_API_KEY),
        "newsapi": bool(NEWS_API_KEY),
        "serpapi": bool(SERP_API_KEY),
    }
