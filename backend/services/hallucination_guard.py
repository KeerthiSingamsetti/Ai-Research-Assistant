from typing import List, Dict


MIN_CONTEXT_LENGTH = 50


def should_answer(
    chunks: List[Dict],
    confidence: float,
    threshold: float = 0.40
) -> bool:
    """
    Determine whether enough evidence exists
    to generate an answer.
    """

    if confidence < threshold:
        return False

    if len(chunks) == 0:
        return False

    total_context = sum(
        len(chunk.get("text", ""))
        for chunk in chunks
    )

    if total_context < MIN_CONTEXT_LENGTH:
        return False

    return True


def fallback_response() -> str:
    """
    Safe fallback message.
    """

    return (
        "I could not find this information "
        "in the uploaded documents."
    )