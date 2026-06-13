def judge_response(
    retrieval_count,
    verification_confidence
):

    retrieval_score = min(
        retrieval_count * 20,
        100
    )

    final_confidence = (
        retrieval_score * 0.4
        +
        verification_confidence * 0.6
    )

    return {
        "retrieval_score": retrieval_score,
        "verification_score": verification_confidence,
        "final_confidence": round(
            final_confidence,
            2
        )
    }