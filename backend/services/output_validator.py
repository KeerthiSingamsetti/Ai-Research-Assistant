def validate_answer(
    answer: str
) -> str:
    """
    Validate LLM output.
    """

    if not answer:
        return (
            "I could not generate an answer."
        )

    answer = answer.strip()

    if len(answer) > 5000:
        answer = answer[:5000]

    forbidden = [
        "As an AI language model",
        "I cannot access documents",
        "I don't have access"
    ]

    for text in forbidden:

        answer = answer.replace(
            text,
            ""
        )

    return answer.strip()