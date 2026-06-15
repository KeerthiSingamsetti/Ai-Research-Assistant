def compute_confidence(
    reranked_chunks
):

    if not reranked_chunks:
        return 0.0

    top_score = reranked_chunks[0][
        "rerank_score"
    ]

    return round(
        min(
            max(
                top_score / 10,
                0
            ),
            1
        ),
        2
    )