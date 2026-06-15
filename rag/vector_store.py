"""
rag/vector_store.py
FAISS vector store with cosine similarity.
Embeddings are generated using sentence-transformers (all-MiniLM-L6-v2).
Cosine similarity is achieved by L2-normalising vectors before indexing
with IndexFlatIP (inner product = cosine similarity on unit vectors).
"""

import numpy as np
from langchain_core.documents import Document

from config.settings import EMBEDDING_MODEL, TOP_K_RETRIEVAL
from utils.logger import logger

# ── Lazy-load heavy deps ──────────────────────────────────────────────────────
_embedder = None
_faiss = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss as faiss_lib
        _faiss = faiss_lib
    return _faiss


class FAISSVectorStore:
    """
    Thin FAISS wrapper supporting cosine similarity retrieval.
    Inner product on L2-normalised vectors equals cosine similarity.
    """

    def __init__(self):
        self.index = None
        self.documents: list[Document] = []
        self.embeddings: np.ndarray | None = None

    def build(self, chunks: list[Document]) -> None:
        """Embed chunks and build a FAISS flat index (cosine similarity)."""
        if not chunks:
            logger.warning("No chunks to index — vector store is empty")
            return

        embedder = _get_embedder()
        faiss = _get_faiss()

        texts = [c.page_content for c in chunks]
        logger.info(f"Embedding {len(texts)} chunks…")
        vectors = embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)

        # L2-normalise so inner product == cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)
        vectors = (vectors / norms).astype(np.float32)

        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)   # inner product = cosine on unit vecs
        self.index.add(vectors)

        self.documents = chunks
        self.embeddings = vectors
        logger.info(f"FAISS index built: {self.index.ntotal} vectors, dim={dim}")

    def similarity_search(
        self, query: str, top_k: int = TOP_K_RETRIEVAL
    ) -> list[tuple[Document, float]]:
        """
        Returns (document, cosine_similarity_score) tuples,
        sorted descending by score.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty — returning no results")
            return []

        embedder = _get_embedder()
        faiss = _get_faiss()

        q_vec = embedder.encode([query], convert_to_numpy=True)
        norm = np.linalg.norm(q_vec)
        q_vec = (q_vec / (norm if norm > 0 else 1e-10)).astype(np.float32)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            doc = self.documents[idx]
            results.append((doc, float(score)))

        logger.debug(f"FAISS retrieved {len(results)} chunks for query='{query[:60]}'")
        return results

    @property
    def size(self) -> int:
        return self.index.ntotal if self.index else 0
