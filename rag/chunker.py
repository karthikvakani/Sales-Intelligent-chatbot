"""
rag/chunker.py
Converts raw tool results into LangChain Documents and chunks them
using RecursiveCharacterTextSplitter.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from utils.logger import logger


def build_documents(raw_results: list[dict]) -> list[Document]:
    """
    Convert heterogeneous tool result dicts into LangChain Document objects
    with rich metadata for citation traceability.
    """
    docs: list[Document] = []
    for i, item in enumerate(raw_results):
        content = item.get("content", "").strip()
        if not content:
            continue
        docs.append(Document(
            page_content=content,
            metadata={
                "title": item.get("title", f"Document {i}"),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", "unknown"),
                "score": item.get("score", 0.0),
                "raw_index": i,
            }
        ))
    return docs


def chunk_documents(docs: list[Document]) -> list[Document]:
    """
    Split documents into chunks using RecursiveCharacterTextSplitter.
    Metadata is propagated to every chunk so citations remain traceable.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = []
    for doc_idx, doc in enumerate(docs):
        split_docs = splitter.split_documents([doc])
        for chunk_idx, chunk in enumerate(split_docs):
            chunk.metadata["doc_index"] = doc_idx
            chunk.metadata["chunk_index"] = chunk_idx
            chunks.append(chunk)

    logger.info(f"Chunking: {len(docs)} docs → {len(chunks)} chunks "
                f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks
