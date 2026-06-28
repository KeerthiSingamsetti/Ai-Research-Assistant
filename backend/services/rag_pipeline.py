from backend.services.retriever import (
    retrieve_chunks
)

from backend.services.prompt_builder import (
    build_prompt
)

from backend.services.llm_service import (
    gemini_service
)

from backend.services.citation_service import (
    extract_citations
)

from backend.services.hallucination_guard import (
    should_answer,
    fallback_response
)

from backend.services.response_formatter import (
    build_response
)

from backend.services.memory import (
    build_memory_context,
    save_chat
)

from backend.services.query_expander import (
    expand_query
)

from backend.config import settings


async def generate_answer(
    query: str
):
    """
    Complete RAG Pipeline

    User Query
        ↓
    Query Expansion
        ↓
    Hybrid Retrieval
        ↓
    Hallucination Guard
        ↓
    Conversation Memory
        ↓
    Prompt Builder
        ↓
    Gemini
        ↓
    Citation Extraction
        ↓
    Response Builder
    """

    # Expand query for better retrieval
    expanded_query = expand_query(
        query
    )

    # Retrieve chunks
    retrieval_result = await retrieve_chunks(
        query=expanded_query,
        top_k=settings.MAX_CONTEXT_CHUNKS
    )

    chunks = retrieval_result.get(
        "chunks",
        []
    )

    confidence = retrieval_result.get(
        "confidence",
        0.0
    )

    # Hallucination protection
    if not should_answer(
        chunks,
        confidence,
        settings.CONFIDENCE_THRESHOLD
    ):

        answer = fallback_response()

        save_chat(
            query=query,
            answer=answer,
            confidence=confidence
        )

        return build_response(
            answer=answer,
            confidence=confidence,
            citations=[]
        )

    # Load conversation memory
    memory = build_memory_context()

    # Build prompt
    prompt = build_prompt(
        query=query,
        chunks=chunks,
        memory=memory
    )

    # Generate answer
    answer = await gemini_service.generate(
        prompt
    )

    # Extract citations
    citations = extract_citations(
        chunks
    )

    # Save conversation
    save_chat(
        query=query,
        answer=answer,
        confidence=confidence
    )

    # Final response
    return build_response(
        answer=answer,
        confidence=confidence,
        citations=citations
    )