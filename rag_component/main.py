"""
main.py
─────────────────────────────────────────────────────────────────────
Main entry point for the RAG component.

This file has two purposes:
1. Standalone: Run as a simple CLI chatbot for testing
2. Integration: Exposes handle_technical_query() for the routing agent

The routing agent from the broader project calls handle_technical_query()
when it detects an incoming query is about device manuals, error codes,
maintenance, or any other technical question about the 3 devices.
─────────────────────────────────────────────────────────────────────
"""

from retrieval.chain import ask
from config import DEVICE_TO_MANUAL


# ─────────────────────────────────────────────────────────────────
# PUBLIC INTERFACE FOR THE ROUTING AGENT
# ─────────────────────────────────────────────────────────────────

def handle_technical_query(question: str, asset_id: str = None) -> str:
    """
    ─────────────────────────────────────────────────────────────
    MAIN INTERFACE — This is what the routing agent calls.
    ─────────────────────────────────────────────────────────────
    Handles any technical question about the 3 hospital devices
    by searching the manual vector store and generating an answer.

    Args:
        question : the engineer's natural language question
        asset_id : optional — if the routing agent knows the specific
                   device asset ID (from ASSET table in Neon), pass it
                   here. Used to automatically filter to the right manual.
                   Example: "MRI-001", "VEN-003", "DIA-002"

    Returns:
        A structured string answer grounded in the device manuals.
        If not found in manuals, returns a clear "not found" message.

    Example:
        >>> answer = handle_technical_query(
        ...     "What does the [Occlusion] alarm mean?",
        ...     asset_id="INF-001"
        ... )
        >>> print(answer)
    """
    manual_filter = None

    # If asset_id is known, try to map it to the right manual
    # Asset IDs follow the pattern: first letters = device type
    # e.g. INF-001 = Infusion Pump, DIA-001 = Dialysis Machine, ECG-001 = ECG
    if asset_id:
        manual_filter = _get_filter_from_asset_id(asset_id)

    result = ask(question, manual_filter)
    return result["answer"]


def handle_technical_query_verbose(question: str, asset_id: str = None) -> dict:
    """
    Same as handle_technical_query but returns full result including
    source chunks used. Useful for debugging or showing sources in the UI.

    Returns:
        dict with "answer", "sources", "filter_used"
    """
    manual_filter = None
    if asset_id:
        manual_filter = _get_filter_from_asset_id(asset_id)

    return ask(question, manual_filter)


# ─────────────────────────────────────────────────────────────────
# HELPER: MAP ASSET ID TO MANUAL FILTER
# ─────────────────────────────────────────────────────────────────
def _get_filter_from_asset_id(asset_id: str) -> dict | None:
    """
    Map an asset ID from the ASSET table to a manual filter.

    Asset IDs in the database start with letters that indicate device type:
        INF-xxx → Infusion Pump  → BeneFusion_VP3
        ECG-xxx → ECG Machine    → MAC_2000
        DIA-xxx → Dialysis       → Fresenius_4008S

    Extend this mapping as the hospital adds more device types.
    """
    asset_id_upper = asset_id.upper()

    if asset_id_upper.startswith("INF"):
        return {"source_manual": "BeneFusion_VP3"}
    if asset_id_upper.startswith("ECG"):
        return {"source_manual": "MAC_2000"}
    if asset_id_upper.startswith("DIA") or asset_id_upper.startswith("HEM"):
        return {"source_manual": "Fresenius_4008S"}

    return None   # Unknown asset type → search all manuals


# ─────────────────────────────────────────────────────────────────
# CLI CHATBOT (for testing only)
# ─────────────────────────────────────────────────────────────────
def _print_result(result: dict) -> None:
    """Pretty-print a query result in the terminal."""
    print("\n" + "─"*60)
    print(f"❓ Question: {result['question']}")

    if result.get("filter_used"):
        print(f"🔍 Searching: {result['filter_used'].get('source_manual', 'filtered')}")
    else:
        print("🔍 Searching: All manuals")

    print(f"\n💬 Answer:\n{result['answer']}")

    if result.get("sources"):
        print(f"\n📖 Sources used ({len(result['sources'])} chunks):")
        for i, src in enumerate(result["sources"], 1):
            print(f"   {i}. {src['manual']} | Page {src['page']} | [{src['section_type']}]")
    print("─"*60 + "\n")


def run_cli():
    """Run an interactive command-line chatbot for testing."""
    print("\n" + "🏥 " + "="*56)
    print("   Hospital Biomedical Engineering Assistant")
    print("   Powered by: LangChain + Groq + Neon pgvector")
    print("="*58)
    print("\n  Available manuals:")
    print("  - BeneFusion VP3 Vet Infusion Pump (Mindray)")
    print("  - MAC 2000 ECG Analysis System (GE Healthcare)")
    print("  - Fresenius 4008S Hemodialysis System")
    print("\n  Type your question below. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("Engineer: ").strip()

            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!\n")
                break

            result = ask(question)
            _print_result(result)

        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}\n")


if __name__ == "__main__":
    run_cli()
