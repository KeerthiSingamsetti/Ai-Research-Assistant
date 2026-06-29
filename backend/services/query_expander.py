def expand_query(query: str) -> str:
    """
    Simple query expansion for retrieval.
    """

    query_lower = query.lower()

    expansions = {
        "ai": "Artificial Intelligence Machine Learning Deep Learning",
        "ml": "Machine Learning Artificial Intelligence",
        "nlp": "Natural Language Processing Transformers Language Models",
        "rag": "Retrieval Augmented Generation Vector Search"
    }

    expanded = query

    for key, value in expansions.items():

        if key in query_lower:
            expanded += " " + value

    return expanded