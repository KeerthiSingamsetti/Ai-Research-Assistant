from typing import List, Dict


def build_prompt(
    query: str,
    chunks: List[Dict],
    memory: str = ""
) -> str:

    context_parts = []

    for chunk in chunks:

        page = chunk.get(
            "page_number",
            "Unknown"
        )

        section = chunk.get(
            "section_title",
            "Unknown Section"
        )

        text = chunk.get(
            "text",
            ""
        )

        context_parts.append(
            f"[Page {page} | {section}]\n{text}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are an AI Research Assistant.

Previous Conversation:

{memory}

--------------------

Use ONLY the context below.

If the answer is not present,
reply exactly:

I could not find this information in the uploaded documents.

--------------------

CONTEXT

{context}

--------------------

QUESTION

{query}

--------------------

ANSWER
"""

    return prompt.strip()