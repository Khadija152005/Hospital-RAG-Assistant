"""
ingestion/load_pdfs.py
─────────────────────────────────────────────────────────────────────
Step 2: Load all 3 PDF manuals and extract their text.

Uses PDFPlumberLoader because it handles tables and structured text
better than basic PyPDF - critical for the Fresenius error code tables
and the BeneFusion alarm tables.

Each loaded page becomes a LangChain Document object with:
    - page_content : extracted text from that page
    - metadata     : source_manual, device_type, manufacturer, page number
─────────────────────────────────────────────────────────────────────
"""

import os
from langchain_community.document_loaders import PDFPlumberLoader
from config import MANUALS


def load_single_manual(manual_name: str) -> list:
    """
    Load a single PDF manual and add base metadata to every page.

    Args:
        manual_name: key from the MANUALS dict in config.py
                     e.g. "BeneFusion_VP3"

    Returns:
        List of LangChain Document objects (one per page)
    """
    info = MANUALS[manual_name]
    path = info["path"]

    # Check that file exists before trying to load
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n[ERROR] Manual file not found: {path}"
            f"\nMake sure you placed the PDF inside data/manuals/ folder."
            f"\nExpected file: {os.path.abspath(path)}"
        )

    print(f"  Loading {manual_name} from {path} ...")

    loader = PDFPlumberLoader(path)
    docs   = loader.load()

    # Enrich every page document with metadata
    for doc in docs:
        doc.metadata["source_manual"]  = manual_name
        doc.metadata["device_type"]    = info["device_type"]
        doc.metadata["manufacturer"]   = info["manufacturer"]
        doc.metadata["model"]          = info["model"]
        doc.metadata["source_file"]    = info["source_file"]
        # PDFPlumberLoader sets 'page' as 0-indexed, convert to 1-indexed
        doc.metadata["page"]           = doc.metadata.get("page", 0) + 1

    print(f"  ✓ Loaded {len(docs)} pages from {manual_name}")
    return docs


def load_all_manuals() -> list:
    """
    Load all 3 manuals defined in config.MANUALS.

    Returns:
        Combined list of all Document objects across all manuals.
    """
    print("\n" + "="*60)
    print("STEP 2 — Loading PDF Manuals")
    print("="*60)

    all_documents = []

    for manual_name in MANUALS:
        try:
            docs = load_single_manual(manual_name)
            all_documents.extend(docs)
        except FileNotFoundError as e:
            # Print warning but continue with other manuals
            print(f"\n  ⚠ WARNING: {e}")
            print(f"  Skipping {manual_name} and continuing...\n")

    print(f"\n{'='*60}")
    print(f"Total pages loaded across all manuals: {len(all_documents)}")
    print(f"{'='*60}\n")

    if not all_documents:
        raise RuntimeError(
            "No documents were loaded. "
            "Please place your PDF files in data/manuals/ and try again."
        )

    return all_documents


def print_document_stats(documents: list) -> None:
    """Print a summary of loaded documents per manual."""
    from collections import Counter
    counts = Counter(doc.metadata.get("source_manual", "Unknown") for doc in documents)

    print("\n── Document Statistics ──")
    for manual, count in counts.items():
        print(f"  {manual}: {count} pages")
    print(f"  {'─'*30}")
    print(f"  Total: {sum(counts.values())} pages\n")
