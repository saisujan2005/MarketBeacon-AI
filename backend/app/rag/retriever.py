from app.retrieval.hybrid_retriever import hybrid_search

def retrieve(question):

    results = hybrid_search(
        question,
        top_k=5
    )

    

    return results