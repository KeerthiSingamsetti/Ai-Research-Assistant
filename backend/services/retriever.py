from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk

from backend.services.embedding_service import (
    generate_embedding
)

from backend.services.vector_store import (
    search_embeddings,
    chunk_lookup
)

from backend.services.bm25_store import (
    search_bm25,
    chunk_ids
)

from backend.services.reranker import (
    rerank
)

from backend.services.confidence import (
    compute_confidence
)


async def retrieve_chunks(
    query: str,
    top_k: int = 5
):
    """
    Hybrid Retrieval Pipeline

    1. Generate query embedding
    2. FAISS search
    3. BM25 search
    4. Merge candidates
    5. Fetch chunks from DB
    6. Cross-encoder rerank
    7. Compute confidence
    8. Return top-k results
    """

    # Generate query embedding
    query_embedding = generate_embedding(
        query
    )

    # FAISS retrieval
    distances, indices = search_embeddings(
        query_embedding,
        top_k * 2
    )

    # BM25 retrieval
    bm25_results = search_bm25(
        query,
        top_k * 2
    )

    # Merge candidate chunk IDs
    candidate_chunk_ids = set()

    # FAISS candidates
    for idx in indices[0]:

        if idx == -1:
            continue

        if idx in chunk_lookup:

            candidate_chunk_ids.add(
                chunk_lookup[idx]
            )

    # BM25 candidates
    for idx in bm25_results:

        if idx < len(chunk_ids):

            candidate_chunk_ids.add(
                chunk_ids[idx]
            )

    # Fetch chunk data
    results = []

    async with SessionLocal() as db:

        for chunk_id in candidate_chunk_ids:

            result = await db.execute(
                select(Chunk).where(
                    Chunk.id == chunk_id
                )
            )

            chunk = result.scalar_one_or_none()

            if chunk is None:
                continue

            results.append(
                {
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                    "text": chunk.text
                }
            )

    # Rerank results
    results = rerank(
        query,
        results
    )

    # Keep only top_k
    results = results[:top_k]

    # Confidence score
    confidence = compute_confidence(
        results
    )

    return {
        "confidence": confidence,
        "chunks": results
    }