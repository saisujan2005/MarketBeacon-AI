from app.retrieval.hybrid_retriever import hybrid_search
import uuid

def retrieve(question, user_id: uuid.UUID = None, include_research_library=False):
    results = hybrid_search(
        question,
        user_id=user_id,
        top_k=5,
        include_research_library=include_research_library
    )
    return results