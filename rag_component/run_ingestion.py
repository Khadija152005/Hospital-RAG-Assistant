"""
run_ingestion.py
─────────────────────────────────────────────────────────────────────
ONE-TIME SCRIPT — Run this ONCE to build the vector database.

This script runs Steps 2, 3, and 4 in sequence:
    Step 2: Load the 3 PDF manuals
    Step 3: Split into smart chunks with metadata
    Step 4: Embed and store everything in Neon pgvector

After this runs successfully, the vectors are stored in Neon and
accessible to your entire team. You do NOT need to run this again
unless you add new manuals or want to rebuild from scratch.

Usage:
    python run_ingestion.py              ← normal run (safe, won't overwrite)
    python run_ingestion.py --rebuild    ← delete and rebuild from scratch
─────────────────────────────────────────────────────────────────────
"""

import sys
import time

from ingestion.load_pdfs       import load_all_manuals, print_document_stats
from ingestion.chunk_documents import chunk_documents, preview_chunks
from ingestion.store_vectors   import store_in_neon, verify_storage


def main(rebuild: bool = False):
    start_time = time.time()

    print("\n" + "🏥 " + "="*56)
    print("   Hospital RAG — Ingestion Pipeline")
    print("   Building vector knowledge base from device manuals")
    print("="*58 + "\n")

    if rebuild:
        print("  ⚠ REBUILD MODE: The existing vector collection will be")
        print("    deleted and rebuilt from scratch.")
        confirm = input("\n  Type 'yes' to confirm: ").strip().lower()
        if confirm != "yes":
            print("  Cancelled.")
            return

    # ── Step 2: Load PDFs ────────────────────────────────────────
    documents = load_all_manuals()
    print_document_stats(documents)

    # ── Step 3: Chunk ────────────────────────────────────────────
    chunks = chunk_documents(documents)

    # Show a preview of 2 chunks per manual (for verification)
    print("\n── Sample Chunks Preview ──")
    for manual_name in ["BeneFusion_VP3", "MAC_2000", "Fresenius_4008S"]:
        preview_chunks(chunks, manual_name=manual_name, n=1)

    # ── Step 4: Embed + Store ────────────────────────────────────
    store_in_neon(chunks, rebuild=rebuild)

    # ── Verify ───────────────────────────────────────────────────
    count = verify_storage()

    elapsed = time.time() - start_time
    minutes  = int(elapsed // 60)
    seconds  = int(elapsed % 60)

    print("\n" + "✅ " + "="*56)
    print("   INGESTION COMPLETE")
    print(f"   {count} vectors stored in Neon pgvector")
    print(f"   Time taken: {minutes}m {seconds}s")
    print("="*58 + "\n")
    print("  Next step: python main.py")
    print("  Or run tests: python test_queries.py\n")


if __name__ == "__main__":
    rebuild_flag = "--rebuild" in sys.argv
    main(rebuild=rebuild_flag)
