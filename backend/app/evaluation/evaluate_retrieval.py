from app.evaluation.test_queries import (
    TEST_CASES
)

from app.retrieval.hybrid_retriever import (
    hybrid_search
)

hits = 0

for case in TEST_CASES:

    query = case["query"]
    expected = case["expected"]

    results = hybrid_search(
        query,
        top_k=5
    )

    found = False

    for result in results:

        title = result["title"]

        if expected.lower() in title.lower():
            found = True
            break

    if found:
        hits += 1

    print(
        f"{query} -> {found}"
    )

recall = hits / len(TEST_CASES)

print(
    f"\nRecall@5: {recall:.2f}"
)