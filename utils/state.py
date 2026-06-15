"""
utils/state.py
Shared LangGraph state schema passed between all agents.
Using TypedDict so LangGraph can serialise/checkpoint it.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class SourceDocument(TypedDict):
    content: str
    source: str          # URL or label
    source_type: str     # "web", "news", "wikipedia", "crm", "yfinance"
    score: float         # cosine similarity score after retrieval
    rerank_score: float  # cross-encoder score after reranking
    chunk_index: int


class AgentState(TypedDict):
    # ── Inputs ───────────────────────────────────────────────────────────────
    company_name: str
    country: str

    # ── Raw collected data (per tool) ────────────────────────────────────────
    web_results: list[dict]
    news_results: list[dict]
    wiki_results: list[dict]
    financial_results: list[dict]
    crm_results: list[dict]

    # ── RAG layer ────────────────────────────────────────────────────────────
    all_documents: list[dict]        # flat list of all raw docs before chunking
    retrieved_chunks: list[SourceDocument]   # post-retrieval + reranked

    # ── Agent outputs ────────────────────────────────────────────────────────
    research_summary: str            # Research Agent output
    analysis_output: dict            # Analysis & Sales Agent structured output

    # ── Final report ─────────────────────────────────────────────────────────
    report: dict                     # Section-keyed report dict
    export_path: Optional[str]

    # ── Control ──────────────────────────────────────────────────────────────
    errors: list[str]
    warnings: list[str]
    confidence: str                  # "high" | "medium" | "low"
    status: str                      # pipeline status message
