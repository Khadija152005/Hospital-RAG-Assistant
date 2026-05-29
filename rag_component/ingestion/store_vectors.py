"""
ingestion/store_vectors.py
─────────────────────────────────────────────────────────────────────
Step 4: Embed all chunks using HuggingFace and store in Neon pgvector.

What happens here:
1. Load the embedding model (all-MiniLM-L6-v2) - runs locally, free
2. For each chunk, convert its text to a 384-dimensional vector
3. Store (vector + original text + metadata) in Neon pgvector table
   called 'langchain_pg_embedding'

This step runs ONCE. After it's done, the vectors live in Neon
and are accessible to the entire team.

NOTE: First run downloads ~90MB model from HuggingFace. 
      Subsequent runs use the cached model.
─────────────────────────────────────────────────────────────────────
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from tqdm import tqdm
from config import (
    NEON_CONNECTION_STRING,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)


def get_embeddings():
    """
    Load the HuggingFace embedding model.
    Model: all-MiniLM-L6-v2
    - 384 dimensions
    - ~90MB download on first use
    - Runs locally on CPU
    - No API key needed
    """
    print(f"\n  Loading embedding model: {EMBEDDING_MODEL}")
    print("  (First time: will download ~90MB from HuggingFace)")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("  ✓ Embedding model ready")
    return embeddings


def store_in_neon(chunks: list, rebuild: bool = False) -> PGVector:
    """
    Embed all chunks and store them in Neon pgvector.

    Args:
        chunks  : list of Document chunks from chunk_documents.py
        rebuild : if True, deletes and rebuilds the entire collection.
                  Use rebuild=True only when you update the manuals.
                  Default is False (safe - won't overwrite existing data).

    Returns:
        PGVector vectorstore object (can be used directly for search)
    """
    print("\n" + "="*60)
    print("STEP 4 — Embedding and Storing Vectors in Neon")
    print("="*60)

    if not NEON_CONNECTION_STRING:
        raise ValueError(
            "\n[ERROR] NEON_CONNECTION_STRING not found in .env file."
            "\nPlease copy .env.example to .env and fill in your Neon connection string."
        )

    embeddings = get_embeddings()

    if rebuild:
        print("\n  ⚠ rebuild=True: Deleting existing collection and rebuilding...")
    else:
        print("\n  rebuild=False: Adding to existing collection (safe mode)")

    print(f"\n  Connecting to Neon...")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Chunks to store: {len(chunks)}")
    print(f"\n  Embedding and storing... (this takes a few minutes)")

    # PGVector.from_documents handles:
    # 1. Connecting to Neon
    # 2. Creating the table if it doesn't exist
    # 3. Embedding each chunk
    # 4. Storing vector + text + metadata
    vectorstore = PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        connection=NEON_CONNECTION_STRING,
        pre_delete_collection=rebuild,
    )

    print(f"\n  ✓ Successfully stored {len(chunks)} chunks in Neon!")
    print(f"  Table: langchain_pg_embedding")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"\n  To verify in Neon SQL editor run:")
    print(f"  SELECT COUNT(*) FROM langchain_pg_embedding;")
    print(f"\n{'='*60}\n")

    return vectorstore


def verify_storage() -> int:
    """
    Quick check: connect to Neon and count stored vectors.
    Returns the count of stored chunks.
    """
    import psycopg2

    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        print(f"\n  ✓ Neon verification: {count} vectors stored in langchain_pg_embedding")
        return count

    except Exception as e:
        print(f"\n  ✗ Verification failed: {e}")
        return 0
