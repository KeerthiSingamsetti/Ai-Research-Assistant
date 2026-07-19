from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk, Document

from backend.services.embedding_service import (
    generate_embedding
)

import backend.services.vector_store as vector_store
import backend.services.bm25_store as bm25_store

from backend.services.reranker import (
    rerank
)

from backend.services.confidence import (
    compute_confidence
)

from backend.services.performance_metrics import (
    PerformanceTimer
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

    timer = PerformanceTimer()

    # ----------------------------------
    # Generate Query Embedding
    # ----------------------------------

    timer.start("embedding_time_ms")

    query_embedding = generate_embedding(query)

    timer.stop("embedding_time_ms")

    # ----------------------------------
    # FAISS Retrieval
    # ----------------------------------

    # Retrieve more candidates than the final output
    RETRIEVAL_TOP_K = 20
    #FASSI_TOP_K = 3
    #BM25_TOP_K = 20
    #FINAL_TOP_K = 20


    timer.start("faiss_time_ms")

    distances, indices = vector_store.search_embeddings(
        query_embedding,
         RETRIEVAL_TOP_K
    )

    timer.stop("faiss_time_ms")



    print("\nFAISS Indices:")
    print(indices)

    print("\nFAISS Distances:")
    print(distances)

    # ----------------------------------
    # BM25 Retrieval
    # ----------------------------------

    timer.start("bm25_time_ms")

    bm25_results = bm25_store.search_bm25(
        query,
         RETRIEVAL_TOP_K
    )

    timer.stop("bm25_time_ms")

    print("\nBM25 Indices:")
    print(bm25_results)

    # ----------------------------------
    # Merge Candidate Chunk IDs
    # ----------------------------------

    print("\n========== INDEX STATUS ==========")
    print("FAISS total vectors:", len(vector_store.chunk_lookup))
    print("BM25 total chunks :", len(bm25_store.chunk_ids))
    print("chunk_lookup =", vector_store.chunk_lookup)
    print("chunk_ids =", bm25_store.chunk_ids)
    print("==================================")


    print("\n========== RETRIEVER STATUS ==========")
    print("FAISS lookup size   :", len(vector_store.chunk_lookup))
    print("BM25 chunk_ids size :", len(bm25_store.chunk_ids))
    print("======================================")

    candidate_chunk_ids = []
    seen = set()

    # -------------------------
    # FAISS Candidates
    # -------------------------

    for idx in indices[0]:

        if idx == -1:
            continue

        if idx in vector_store.chunk_lookup:

            chunk_id = vector_store.chunk_lookup[idx]

            if chunk_id not in seen:
                seen.add(chunk_id)
                candidate_chunk_ids.append(chunk_id)

    # -------------------------
    # BM25 Candidates
    # -------------------------

    for idx in bm25_results:

        if idx >= len(bm25_store.chunk_ids):
            continue

        chunk_id = bm25_store.chunk_ids[idx]

        if chunk_id not in seen:
            seen.add(chunk_id)
            candidate_chunk_ids.append(chunk_id)

    print("\nMerged Candidate Chunk IDs:")
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
            print(chunk.text[:300])
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
   

    ##newly added part

    print(f"\nRetrieved Before Reranking: {len(results)}")

    # Limit the number of candidates before reranking
    #results = results[:10]      # You can choose 3, 5, or 10

    # ----------------------------------
    # Cross Encoder Reranking
    # ----------------------------------

    timer.start("cross_encoder_time_ms")

    results = rerank(
        query,
        results
    )

    timer.stop("cross_encoder_time_ms")

    results = results[:8]

    print(f"Retrieved After Reranking: {len(results)}")

    # ----------------------------------
    # Confidence Score
    # ----------------------------------

    confidence = compute_confidence(
        results
    )

    # ----------------------------------
    # Performance Metrics
    # ----------------------------------

    metrics = timer.get_metrics()

    metrics["total_retrieval_time_ms"] = round(
        metrics["embedding_time_ms"]
        + metrics["faiss_time_ms"]
        + metrics["bm25_time_ms"]
        + metrics["cross_encoder_time_ms"],
        2
    )

    print("\n========== PERFORMANCE METRICS ==========")

    for key, value in metrics.items():
        print(f"{key:<30}: {value:.2f} ms")

    print("\nConfidence:", confidence)
    print("========== RETRIEVAL END ==========\n")

    return {
        "confidence": confidence,
        "chunks": results,
        "performance_metrics": metrics
    }