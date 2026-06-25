import time
import logging

from app.rag.retriever import retrieve
from app.rag.prompt_builder import build_prompt
from app.rag.llm_service import ask_llm
from app.rag.verifier import verify_answer
from app.rag.judge_agent import (
    judge_response
)

logger = logging.getLogger(__name__)


def answer_question(question):

    start = time.time()

    docs = retrieve(question)

    logger.info(
        f"Retrieval: {time.time() - start:.2f} sec"
    )

    context_docs = [
        doc["title"]
        for doc in docs
    ]

    prompt = build_prompt(
        question,
        context_docs
    )

    start = time.time()

    response = ask_llm(prompt)

    logger.info(
        f"Answer Generation: {time.time() - start:.2f} sec"
    )

    start = time.time()

    verification = {
         "supported": True,
         "confidence": 80,
         "reason": "Verification temporarily disabled."
    }

    judge = judge_response(
         retrieval_count=len(docs),
         verification_confidence=
              verification["confidence"]
    )

    logger.info(
        f"Verification: {time.time() - start:.2f} sec"
    )

    sources = []

    seen = set()

    for doc in docs:

        if doc["title"] in seen:
            continue

        seen.add(doc["title"])

        sources.append({
            "title": doc["title"],
            "url": doc["url"]
        })

    return {
        "answer": response,
        "sources": sources,
        "verification": verification,
        "judge": judge
    }
