from retrieval.retriever import search

queries = [
    "ECG noise troubleshooting MAC 2000",
    "MAC 2000 won't power on",
    "battery icon flashing LED MAC 2000",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Query: {q}")
    results = search(q, filter={"source_manual": "MAC_2000"}, k=3)
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n  Result {i} | Score: {score:.3f} | Page: {doc.metadata.get('page')}")
        print(f"  Text: {doc.page_content[:300]}")