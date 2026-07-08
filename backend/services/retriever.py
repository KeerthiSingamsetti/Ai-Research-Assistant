from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk, Document

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
    2. FAISS retrieval
    3. BM25 retrieval
    4. Merge candidate chunk IDs
    5. Fetch chunk data
    6. Cross-encoder reranking
    7. Compute confidence
    """

    print("\n========== RETRIEVAL START ==========")
    print("Query:", query)

    # ----------------------------------
    # Generate Query Embedding
    # ----------------------------------

    query_embedding = generate_embedding(query)

    # ----------------------------------
    # FAISS Retrieval
    # ----------------------------------

    distances, indices = search_embeddings(
        query_embedding,
        top_k 
    )

    print("\nFAISS Indices:")
    print(indices)

    print("\nFAISS Distances:")
    print(distances)

    # ----------------------------------
    # BM25 Retrieval
    # ----------------------------------

    bm25_results = search_bm25(
        query,
        top_k 
    )

    print("\nBM25 Indices:")
    print(bm25_results)

    # ----------------------------------
    # Merge Candidate Chunk IDs
    # ----------------------------------

    candidate_chunk_ids = set()

    # FAISS Candidates
    for idx in indices[0]:

        if idx == -1:
            continue

        if idx in chunk_lookup:
            candidate_chunk_ids.add(
                chunk_lookup[idx]
            )

    # BM25 Candidates
    for idx in bm25_results:

        if idx < len(chunk_ids):
            candidate_chunk_ids.add(
                chunk_ids[idx]
            )

    print("\nCandidate Chunk IDs:")
    print(candidate_chunk_ids)

    # ----------------------------------
    # Fetch Chunks From Database
    # ----------------------------------

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

            # -----------------------------
            # Fetch Document
            # -----------------------------

            doc_result = await db.execute(
                select(Document).where(
                    Document.id == chunk.document_id
                )
            )

            document = doc_result.scalar_one_or_none()

            print("--------------------------------")
            print("Chunk ID           :", chunk.id)
            print("Document ID        :", chunk.document_id)

            if document:
                print("Stored Filename    :", document.filename)
                print("Original Filename  :", document.original_filename)

            print("Page Number        :", chunk.page_number)
            print("Section Title      :", chunk.section_title)

            print("Chunk Preview:")
            print(chunk.text[:200])
            print()

            results.append(
                {
                    "document_id": chunk.document_id,
                    "stored_filename": document.filename if document else None,
                    "original_filename": document.original_filename if document else None,
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                    "text": chunk.text
                }
            )

    print(f"\nRetrieved Before Reranking: {len(results)}")

    # ----------------------------------
    # Cross Encoder Reranking
    # ----------------------------------

    results = rerank(
        query,
        results
    )

    results = results[:top_k]

    print(f"Retrieved After Reranking: {len(results)}")

    # ----------------------------------
    # Confidence Score
    # ----------------------------------

    confidence = compute_confidence(
        results
    )

    print("\nConfidence:", confidence)
    print("========== RETRIEVAL END ==========\n")

    return {
        "confidence": confidence,
        "chunks": results
    }