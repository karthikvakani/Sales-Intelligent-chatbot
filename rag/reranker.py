"""
rag/reranker.py
Cross-encoder reranking step applied after FAISS cosine retrieval.
Uses sentence-transformers cross-encoder (ms-marco-MiniLM-L-6-v2 by default).
Cross-encoders jointly encode (query, passage) for more accurate relevance
scoring than bi-encoder cosine similarity.
"""

from langchain_core.documents import Document

from config.settings import CROSS_ENCODER_MODEL, TOP_K_RERANK
from utils.state import SourceDocument
from utils.logger import logger

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading cross-encoder: {CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
    return _cross_encoder


def rerank(
    query: str,
    candidates: list[tuple[Document, float]],
    top_k: int = TOP_K_RERANK,
) -> list[SourceDocument]:
    """
    Rerank FAISS candidates using a cross-encoder.

    Args:
        query: The user/agent query string.
        candidates: List of (Document, cosine_score) from FAISS.
        top_k: Number of top results to return after reranking.

    Returns:
        List of SourceDocument TypedDicts sorted by rerank_score descending.
    """
    if not candidates:
        return []

    cross_encoder = _get_cross_encoder()

    pairs = [(query, doc.page_content) for doc, _ in candidates]
    logger.info(f"Cross-encoder reranking {len(pairs)} candidates…")

    try:
        scores = cross_encoder.predict(pairs)
    except Exception as exc:
        logger.warning(f"Cross-encoder failed: {exc}. Falling back to cosine scores.")
        scores = [cos_score for _, cos_score in candidates]

    # Combine original doc, cosine score, and rerank score
    ranked: list[SourceDocument] = []
    for (doc, cos_score), rerank_score in zip(candidates, scores):
        ranked.append(SourceDocument(
            content=doc.page_content,
            source=doc.metadata.get("url", ""),
            source_type=doc.metadata.get("source_type", "unknown"),
            score=float(cos_score),
            rerank_score=float(rerank_score),
            chunk_index=doc.metadata.get("chunk_index", 0),
        ))

    ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    top = ranked[:top_k]

    logger.info(
        f"Reranking complete: top chunk score={top[0]['rerank_score']:.4f} "
        f"(source={top[0]['source_type']})" if top else "No results after reranking"
    )
    return top
