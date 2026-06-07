"""
reindex_mac.py
Re-ingests only the MAC 2000 manual using PyMuPDF.
Run this ONCE after installing pymupdf.
"""

import psycopg2
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from dotenv import load_dotenv
import os

load_dotenv()

NEON  = os.getenv("NEON_CONNECTION_STRING")
MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLL  = os.getenv("COLLECTION_NAME", "hospital_manuals")

# ── Step 1: Delete existing MAC_2000 chunks from Neon ────────────
print("Deleting existing MAC_2000 chunks...")
conn = psycopg2.connect(NEON)
cur  = conn.cursor()
cur.execute("""
    DELETE FROM langchain_pg_embedding
    WHERE cmetadata->>'source_manual' = 'MAC_2000';
""")
deleted = cur.rowcount
conn.commit()
cur.close()
conn.close()
print(f"  ✓ Deleted {deleted} old MAC_2000 chunks")

# ── Step 2: Load with PyMuPDF ─────────────────────────────────────
print("\nLoading MAC_2000 with PyMuPDF...")
loader = PyMuPDFLoader("data/manuals/MAC_2000.pdf")
docs   = loader.load()
print(f"  ✓ Loaded {len(docs)} pages")

# Add metadata
for doc in docs:
    doc.metadata["source_manual"]  = "MAC_2000"
    doc.metadata["device_type"]    = "ECG Machine"
    doc.metadata["manufacturer"]   = "GE Healthcare"
    doc.metadata["model"]          = "MAC 2000"
    doc.metadata["source_file"]    = "MAC_2000.pdf"
    doc.metadata["page"]           = doc.metadata.get("page", 0) + 1

# ── Step 3: Chunk ─────────────────────────────────────────────────
from ingestion.chunk_documents import chunk_documents
chunks = chunk_documents(docs)
print(f"  ✓ Created {len(chunks)} chunks")

# ── Step 4: Re-embed and store ────────────────────────────────────
print("\nEmbedding and storing new MAC_2000 chunks...")
embeddings = HuggingFaceEmbeddings(
    model_name=MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name=COLL,
    connection=NEON,
    pre_delete_collection=False,
)

print(f"\n✅ Done — {len(chunks)} new MAC_2000 chunks stored in Neon")
print("Now run: python check_mac.py  to verify improvement")