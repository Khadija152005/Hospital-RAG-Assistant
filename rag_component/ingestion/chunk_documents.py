"""
ingestion/chunk_documents.py
─────────────────────────────────────────────────────────────────────
Step 3: Split loaded documents into smaller chunks for embedding.

Strategy:
- RecursiveCharacterTextSplitter respects paragraph and sentence
  boundaries before splitting mid-sentence.
- chunk_size=1000 : specific enough for precise retrieval
- chunk_overlap=150: prevents context being cut at chunk boundaries
- Every chunk gets a section_type label auto-detected from its content
  to allow filtered searches later (e.g. only search "maintenance" chunks)
─────────────────────────────────────────────────────────────────────
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP, SECTION_TYPE_KEYWORDS


def detect_section_type(text: str) -> str:
    """
    Auto-detect the content category of a chunk based on keywords.

    Checks the text against keyword lists in config.SECTION_TYPE_KEYWORDS.
    Returns the best matching section type, or 'operation' as default.

    Args:
        text: the chunk's page_content

    Returns:
        section_type string, one of:
        'alarms', 'maintenance', 'calibration', 'installation',
        'cleaning', 'battery', 'troubleshooting', 'specifications',
        'configuration', 'operation'
    """
    text_lower = text.lower()

    # Count keyword matches for each section type
    scores = {}
    for section_type, keywords in SECTION_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[section_type] = score

    # Return the type with the highest keyword match count
    best_match = max(scores, key=scores.get)

    # Only assign a specific type if at least 1 keyword matched
    if scores[best_match] > 0:
        return best_match

    return "operation"  # default for general operational content


def chunk_documents(documents: list) -> list:
    """
    Split all loaded documents into smaller, overlapping chunks.

    Args:
        documents: list of LangChain Document objects from load_pdfs.py

    Returns:
        List of smaller Document chunks with enriched metadata.
    """
    print("\n" + "="*60)
    print("STEP 3 — Chunking Documents")
    print("="*60)
    print(f"  Settings: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # Try splitting at these boundaries in order:
        # paragraph → newline → sentence → space → character
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    # Add section_type metadata to every chunk
    print("\n  Detecting section types...")
    section_counts = {}

    for chunk in chunks:
        section_type = detect_section_type(chunk.page_content)
        chunk.metadata["section_type"] = section_type
        # Track counts for reporting
        section_counts[section_type] = section_counts.get(section_type, 0) + 1

    # Print summary
    print(f"\n  ✓ Created {len(chunks)} total chunks")
    print("\n── Chunks by Section Type ──")
    for section_type, count in sorted(section_counts.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 10)
        print(f"  {section_type:<20} {count:>4}  {bar}")

    print("\n── Chunks by Manual ──")
    manual_counts = {}
    for chunk in chunks:
        manual = chunk.metadata.get("source_manual", "Unknown")
        manual_counts[manual] = manual_counts.get(manual, 0) + 1
    for manual, count in manual_counts.items():
        print(f"  {manual:<25} {count:>4} chunks")

    print(f"\n{'='*60}\n")

    return chunks


def preview_chunks(chunks: list, manual_name: str = None, n: int = 3) -> None:
    """
    Print a preview of n chunks for inspection.
    Useful for verifying the chunking quality during development.

    Args:
        chunks     : list of chunks from chunk_documents()
        manual_name: if provided, only preview chunks from this manual
        n          : number of chunks to preview
    """
    filtered = chunks
    if manual_name:
        filtered = [c for c in chunks if c.metadata.get("source_manual") == manual_name]

    print(f"\n── Preview: {n} chunks from {manual_name or 'all manuals'} ──")
    for i, chunk in enumerate(filtered[:n]):
        print(f"\n[Chunk {i+1}]")
        print(f"  Manual   : {chunk.metadata.get('source_manual')}")
        print(f"  Page     : {chunk.metadata.get('page')}")
        print(f"  Type     : {chunk.metadata.get('section_type')}")
        print(f"  Length   : {len(chunk.page_content)} chars")
        print(f"  Content  : {chunk.page_content[:300]}...")
        print(f"  {'─'*50}")
