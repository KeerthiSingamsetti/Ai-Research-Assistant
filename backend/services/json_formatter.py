def build_json_response(
    answer: str,
    confidence: float,
    citations: list,
    evaluation: dict
):
    return {
        "answer": answer,
        "confidence": confidence,
        "citations": citations,
        "evaluation": evaluation
    }