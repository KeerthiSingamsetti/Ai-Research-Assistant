from backend.services.retriever import retrieve_chunks
from backend.services.prompt_builder import build_prompt
from backend.services.llm_service import gemini_service
from backend.services.citation_service import extract_citations
from backend.services.hallucination_guard import should_answer, fallback_response
from backend.services.memory import build_memory_context, save_chat
from backend.services.query_expander import expand_query
from backend.services.output_validator import validate_answer
from backend.services.retry_service import retry_async
from backend.services.json_formatter import build_json_response
from backend.services.evaluation_service import evaluate_response
from backend.config import settings


async def generate_answer(query: str):

    # 1. Query expansion
    expanded_query = expand_query(query)

    # 2. Retrieval
    retrieval_result = await retrieve_chunks(
        query=expanded_query,
        top_k=settings.MAX_CONTEXT_CHUNKS
    )

    chunks = retrieval_result.get("chunks", [])
    confidence = retrieval_result.get("confidence", 0.0)

    # 3. Guardrail (low confidence fallback)
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

        evaluation = {
            "evaluation_score": 0,
            "faithfulness": confidence,
            "citation_count": 0
        }

        return build_json_response(
            answer=answer,
            confidence=confidence,
            citations=[],
            evaluation=evaluation
        )

    # 4. Memory
    memory = build_memory_context()

    # 5. Prompt
    prompt = build_prompt(
        query=query,
        chunks=chunks,
        memory=memory
    )

    # 6. LLM call with retry
    answer = await retry_async(
        lambda: gemini_service.generate(prompt)
    )

    # 7. Validate output
    answer = validate_answer(answer)

    # 8. Citations
    citations = extract_citations(chunks)

    # 9. Save chat
    save_chat(
        query=query,
        answer=answer,
        confidence=confidence
    )

    # 10. Evaluation
    evaluation = evaluate_response(
        answer=answer,
        confidence=confidence,
        citations_count=len(citations)
    )

    # 11. Final structured response (ONLY ONE FORMAT)
    return build_json_response(
        answer=answer,
        confidence=confidence,
        citations=citations,
        evaluation=evaluation
    )