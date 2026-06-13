from app.evaluation.test_queries import TEST_CASES
from app.retrieval.hybrid_retriever import hybrid_search

total_rr = 0

for case in TEST_CASES:

    query = case["query"]
    expected = case["expected"]

    results = hybrid_search(
        query,
        top_k=10
    )

    rank = None

    for i, result in enumerate(results, start=1):

        if expected.lower() in result["title"].lower():
            rank = i
            break

    if rank:
        rr = 1 / rank
        total_rr += rr

        print(
            f"{query} -> rank {rank} -> RR={rr:.2f}"
        )
    else:
        print(
            f"{query} -> not found"
        )

mrr = total_rr / len(TEST_CASES)

print(
    f"\nMRR: {mrr:.3f}"
)

