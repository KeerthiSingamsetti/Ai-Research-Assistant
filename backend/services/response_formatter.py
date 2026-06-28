from typing import Dict, List


def build_response(
    answer: str,
    confidence: float,
    citations: List[Dict]
) -> Dict:
    """
    Standardized API response.
    """

    return {
        "answer": answer,
        "confidence": round(
            confidence,
            3
        ),
        "citations": citations
    }