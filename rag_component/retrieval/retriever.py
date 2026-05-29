"""
retrieval/retriever.py
─────────────────────────────────────────────────────────────────────
Step 5: Load the existing vector store from Neon and build a retriever.

The retriever is what converts a question into a search:
1. Embeds the incoming question using the same model used during ingestion
2. Searches Neon pgvector for the most similar chunks
3. Returns the top K chunks to be passed to the LLM

Optional filtering:
    Pass a filter dict to narrow the search to a specific manual
    or section type. This improves precision when the device is known.
─────────────────────────────────────────────────────────────────────
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from config import (
    NEON_CONNECTION_STRING,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    TOP_K_RESULTS,
    MANUAL_KEYWORDS,
)

# ── Module-level cache ────────────────────────────────────────────
# The embedding model is heavy (~90MB). We load it once and reuse it
# across all queries in the same session.
_embeddings_cache = None
_vectorstore_cache = None


def get_embeddings():
    """Return cached embedding model (loads once per session)."""
    global _embeddings_cache
    if _embeddings_cache is None:
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_cache


def get_vectorstore() -> PGVector:
    """
    Connect to the Neon pgvector store.
    Uses a module-level cache to avoid reconnecting on every query.
    """
    global _vectorstore_cache
    if _vectorstore_cache is None:
        _vectorstore_cache = PGVector(
            embeddings=get_embeddings(),
            collection_name=COLLECTION_NAME,
            connection=NEON_CONNECTION_STRING,
        )
    return _vectorstore_cache


def get_retriever(filter: dict = None):
    """
    Build and return a LangChain retriever with optional metadata filtering.

    Args:
        filter: optional dict to narrow the search scope.

        Examples:
            None                              → search ALL manuals (default)
            {"source_manual": "Fresenius_4008S"}  → only Fresenius manual
            {"source_manual": "BeneFusion_VP3"}   → only infusion pump manual
            {"source_manual": "MAC_2000"}          → only ECG manual
            {"section_type": "maintenance"}        → only maintenance sections
            {"section_type": "alarms"}             → only alarm/error sections

    Returns:
        LangChain BaseRetriever ready to use in a chain.
    """
    vectorstore   = get_vectorstore()
    search_kwargs = {"k": TOP_K_RESULTS}

    if filter:
        search_kwargs["filter"] = filter

    return vectorstore.as_retriever(search_kwargs=search_kwargs)


def detect_manual_from_query(query: str) -> dict | None:
    """
    Analyze the query text and return a metadata filter if a specific
    device is clearly mentioned. Returns None if no device is detected
    (which causes the retriever to search all 3 manuals).

    Args:
        query: the engineer's natural language question

    Returns:
        A filter dict, e.g. {"source_manual": "Fresenius_4008S"}
        or None if no specific device detected.
    """
    query_lower = query.lower()

    for manual_name, keywords in MANUAL_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return {"source_manual": manual_name}

    return None   # No specific device detected → search all manuals


def search(query: str, filter: dict = None, k: int = None) -> list:
    """
    Direct similarity search (without LLM — just retrieval).
    Useful for testing what chunks are being retrieved.

    Args:
        query  : search query
        filter : optional metadata filter
        k      : number of results (defaults to TOP_K_RESULTS from config)

    Returns:
        List of (Document, score) tuples
    """
    vectorstore = get_vectorstore()
    k = k or TOP_K_RESULTS

    search_kwargs = {}
    if filter:
        search_kwargs["filter"] = filter

    results = vectorstore.similarity_search_with_score(
        query=query,
        k=k,
        **search_kwargs,
    )
    return results
