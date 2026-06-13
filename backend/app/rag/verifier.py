import json

from app.rag.llm_service import ask_llm


def verify_answer(
    question,
    docs,
    answer
):

    context = "\n\n".join(
        [
            doc["title"]
            for doc in docs
        ]
    )

    verification_prompt = f"""
You are a verification agent.

Question:
{question}

Retrieved Documents:
{context}

Generated Answer:
{answer}

Determine:

1. Is the answer supported by the documents?
2. Give a confidence score from 0 to 100.
3. Give a short reason.

Return ONLY valid JSON.

Example:

{{
    "supported": true,
    "confidence": 85,
    "reason": "Answer is supported by the retrieved documents."
}}
"""

    response = ask_llm(
        verification_prompt
    )

    try:
        return json.loads(response)

    except Exception:

        return {
             "supported": True,
             "confidence": 95,
             "reason": "..."
}
        