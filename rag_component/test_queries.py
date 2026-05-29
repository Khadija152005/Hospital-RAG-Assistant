"""
test_queries.py
─────────────────────────────────────────────────────────────────────
Comprehensive test suite for the RAG component.

Tests 25+ queries across all categories:
    - Error codes and alarms
    - Maintenance and inspection
    - Calibration
    - Settings and configuration
    - Cleaning and disinfection
    - Battery
    - Installation
    - Troubleshooting
    - Specifications
    - Cross-manual queries

Usage:
    python test_queries.py              ← run all tests
    python test_queries.py --quick      ← run 1 test per category
    python test_queries.py --search     ← only test retrieval (no LLM)
─────────────────────────────────────────────────────────────────────
"""

import sys
import time
from retrieval.chain    import ask
from retrieval.retriever import search, detect_manual_from_query


# ─────────────────────────────────────────────────────────────────
# TEST QUERIES BY CATEGORY
# ─────────────────────────────────────────────────────────────────
TEST_CASES = [

    # ── Error Codes & Alarms ─────────────────────────────────────
    {
        "category": "Error Codes & Alarms",
        "question": "What does the [Occlusion] alarm mean on the infusion pump and how do I fix it?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "alarms",
    },
    {
        "category": "Error Codes & Alarms",
        "question": "The infusion pump shows [Air in line] alarm. What should I do step by step?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "alarms",
    },
    {
        "category": "Error Codes & Alarms",
        "question": "What is [System Error] on the BeneFusion pump? Can it be cancelled?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "alarms",
    },
    {
        "category": "Error Codes & Alarms",
        "question": "F01 Display error on the Fresenius 4008S. What does it mean?",
        "expected_manual": "Fresenius_4008S",
        "expected_section": "alarms",
    },
    {
        "category": "Error Codes & Alarms",
        "question": "The MAC 2000 is showing a battery icon with flashing LED. What is the issue?",
        "expected_manual": "MAC_2000",
        "expected_section": "alarms",
    },

    # ── Maintenance ───────────────────────────────────────────────
    {
        "category": "Maintenance",
        "question": "What is the preventive maintenance schedule for the BeneFusion VP3 infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "maintenance",
    },
    {
        "category": "Maintenance",
        "question": "What inspection checks must be done before using the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "maintenance",
    },
    {
        "category": "Maintenance",
        "question": "How often should the Fresenius 4008S undergo technical safety checks?",
        "expected_manual": "Fresenius_4008S",
        "expected_section": "maintenance",
    },
    {
        "category": "Maintenance",
        "question": "What does paper maintenance involve on the MAC 2000?",
        "expected_manual": "MAC_2000",
        "expected_section": "maintenance",
    },

    # ── Cleaning & Disinfection ───────────────────────────────────
    {
        "category": "Cleaning",
        "question": "What disinfectants are recommended for the BeneFusion VP3 infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "cleaning",
    },
    {
        "category": "Cleaning",
        "question": "Can I use EtO to disinfect the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "cleaning",
    },
    {
        "category": "Cleaning",
        "question": "What cleaning agents should I use for the infusion pump surface?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "cleaning",
    },

    # ── Battery ───────────────────────────────────────────────────
    {
        "category": "Battery",
        "question": "How long does the BeneFusion battery last when infusing at 25ml/h?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "battery",
    },
    {
        "category": "Battery",
        "question": "How do I optimize battery performance on the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "battery",
    },
    {
        "category": "Battery",
        "question": "When should I replace the lithium battery in the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "battery",
    },

    # ── Settings & Configuration ──────────────────────────────────
    {
        "category": "Settings",
        "question": "How do I change the occlusion pressure threshold on the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "configuration",
    },
    {
        "category": "Settings",
        "question": "How do I enable Body Weight Mode on the BeneFusion VP3?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "operation",
    },
    {
        "category": "Settings",
        "question": "What is the KVO rate range on the infusion pump and how do I set it?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "configuration",
    },

    # ── Installation & Setup ──────────────────────────────────────
    {
        "category": "Installation",
        "question": "How do I mount the BeneFusion VP3 on an IV pole?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "installation",
    },
    {
        "category": "Installation",
        "question": "How do I connect the drop sensor on the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "installation",
    },
    {
        "category": "Installation",
        "question": "What is the compatible power supply for the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "specifications",
    },

    # ── General Troubleshooting ───────────────────────────────────
    {
        "category": "Troubleshooting",
        "question": "The ECG data from the MAC 2000 shows a lot of noise. What should I check?",
        "expected_manual": "MAC_2000",
        "expected_section": "troubleshooting",
    },
    {
        "category": "Troubleshooting",
        "question": "The MAC 2000 won't power on. What are the troubleshooting steps?",
        "expected_manual": "MAC_2000",
        "expected_section": "troubleshooting",
    },

    # ── Specifications ────────────────────────────────────────────
    {
        "category": "Specifications",
        "question": "Which infusion set brands are compatible with the BeneFusion VP3?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "specifications",
    },
    {
        "category": "Specifications",
        "question": "What is the air detection sensitivity range on the infusion pump?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "specifications",
    },
    {
        "category": "Specifications",
        "question": "What are the operating temperature limits for the BeneFusion VP3?",
        "expected_manual": "BeneFusion_VP3",
        "expected_section": "specifications",
    },
]


# ─────────────────────────────────────────────────────────────────
# TEST RUNNER
# ─────────────────────────────────────────────────────────────────

def run_search_only_tests():
    """
    Test ONLY the retrieval (no LLM call).
    Verifies that the right chunks are being found before testing the full chain.
    Faster and free - doesn't use Groq API quota.
    """
    print("\n" + "="*60)
    print("RETRIEVAL TEST (Search Only — No LLM)")
    print("="*60)

    passed = 0
    failed = 0

    for i, case in enumerate(TEST_CASES, 1):
        question = case["question"]
        expected_manual = case["expected_manual"]

        results = search(question, k=5)

        if not results:
            print(f"  [{i:02d}] ✗ FAIL — No results returned")
            failed += 1
            continue

        # Check if expected manual appears in top results
        retrieved_manuals = [doc.metadata.get("source_manual") for doc, _ in results]
        found = expected_manual in retrieved_manuals

        top_score = results[0][1] if results else 0

        status = "✓ PASS" if found else "✗ FAIL"
        if found:
            passed += 1
        else:
            failed += 1

        print(f"  [{i:02d}] {status} | Score: {top_score:.3f} | "
              f"Expected: {expected_manual} | "
              f"Got: {retrieved_manuals[0]}")
        if not found:
            print(f"         Q: {question[:60]}...")

    print(f"\n  Results: {passed} passed / {failed} failed / {len(TEST_CASES)} total")
    return passed, failed


def run_full_tests(quick: bool = False):
    """
    Run full end-to-end tests including LLM generation.
    
    Args:
        quick: if True, only test 1 query per category (faster)
    """
    print("\n" + "="*60)
    print("FULL RAG TEST (Retrieval + LLM Generation)")
    print("="*60)

    if quick:
        # Pick one test per category
        seen_categories = set()
        test_subset = []
        for case in TEST_CASES:
            if case["category"] not in seen_categories:
                test_subset.append(case)
                seen_categories.add(case["category"])
        test_cases = test_subset
        print(f"  Quick mode: testing {len(test_cases)} queries (1 per category)\n")
    else:
        test_cases = TEST_CASES
        print(f"  Testing {len(test_cases)} queries across all categories\n")

    passed = 0
    failed = 0
    total_time = 0

    for i, case in enumerate(test_cases, 1):
        question = case["question"]
        category = case["category"]

        print(f"\n[{i:02d}/{len(test_cases)}] Category: {category}")
        print(f"  Q: {question[:70]}...")

        start = time.time()
        try:
            result = ask(question)
            elapsed = time.time() - start
            total_time += elapsed

            answer_preview = result["answer"][:120].replace("\n", " ")
            sources_found  = [s["manual"] for s in result["sources"]]

            print(f"  ✓ Answer ({elapsed:.1f}s): {answer_preview}...")
            print(f"  📖 Sources: {sources_found}")
            passed += 1

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ✗ ERROR ({elapsed:.1f}s): {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Results : {passed} passed / {failed} failed / {len(test_cases)} total")
    print(f"  Avg time: {total_time/len(test_cases):.1f}s per query")
    print(f"{'='*60}\n")


def run_single_test(question: str):
    """Run a single test query and print the full result."""
    from main import _print_result
    result = ask(question)
    _print_result(result)


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--search" in sys.argv:
        run_search_only_tests()
    elif "--quick" in sys.argv:
        run_full_tests(quick=True)
    else:
        run_full_tests(quick=False)
