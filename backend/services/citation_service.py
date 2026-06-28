from typing import List, Dict


def extract_citations(
    chunks: List[Dict]
) -> List[Dict]:
    """
    Extract citation information from retrieved chunks.
    """

    citations = []

    seen = set()

    for chunk in chunks:

        page = chunk.get("page_number")
        section = chunk.get("section_title")

        key = (page, section)

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            {
                "page": page,
                "section": section
            }
        )

    return citations