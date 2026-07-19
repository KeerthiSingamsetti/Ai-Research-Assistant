import asyncio

from backend.services.index_builder import build_index
from backend.services.retriever import retrieve_chunks


async def main():

    print("=" * 60)
    print("BUILDING INDEXES")
    print("=" * 60)

    await build_index()

    print("\nIndexes built successfully.\n")

    print("=" * 60)
    print("RUNNING RETRIEVAL")
    print("=" * 60)

    result = await retrieve_chunks(
        query="machine learning",
        top_k=3
    )

    print("\n" + "=" * 60)
    print("CONFIDENCE SCORE")
    print("=" * 60)

    print(result["confidence"])

    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)

    metrics = result["performance_metrics"]

    print(f"Embedding Time          : {metrics['embedding_time_ms']:.2f} ms")
    print(f"FAISS Search Time       : {metrics['faiss_time_ms']:.2f} ms")
    print(f"BM25 Search Time        : {metrics['bm25_time_ms']:.2f} ms")
    print(f"CrossEncoder Time       : {metrics['cross_encoder_time_ms']:.2f} ms")
    print(f"Total Retrieval Time    : {metrics['total_retrieval_time_ms']:.2f} ms")

    print("\n" + "=" * 60)
    print("RETRIEVED CHUNKS")
    print("=" * 60)

    for i, chunk in enumerate(result["chunks"], start=1):

        print(f"\nChunk {i}")
        print("-" * 50)

        print("Chunk ID       :", chunk["chunk_id"])
        print("Document ID    :", chunk["document_id"])
        print("Page Number    :", chunk["page_number"])
        print("Section        :", chunk["section_title"])
        print("Rerank Score   :", round(chunk["rerank_score"], 4))

        print("\nText Preview:")
        print(chunk["text"][:300])
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())