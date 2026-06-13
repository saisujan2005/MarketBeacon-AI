from app.retrieval.reranker import rerank

documents = [
    "Oil Prices Cool: Brent Slips Below $90",
    "SpaceX IPO To Push Musk Past $1 Trillion",
    "Gold May See More Correction",
    "FPIs Remain Net Sellers"
]

results = rerank(
    "oil prices",
    documents
)

for doc, score in results:
    print(f"{score:.4f} | {doc}")