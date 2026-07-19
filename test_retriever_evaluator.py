import asyncio
from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk, Document

from backend.services.index_builder import build_index
from backend.services.retriever import retrieve_chunks
from backend.services.retrieval_evaluator import RetrievalEvaluator


async def load_evaluation_queries():
    """
    Dynamically generate evaluation queries from the database.
    """

    queries = []
    seen = set()

    async with SessionLocal() as db:

        result = await db.execute(
            select(Chunk, Document)
            .join(Document, Chunk.document_id == Document.id)
        )

        rows = result.all()

        for chunk, document in rows:

            # Skip invalid section titles
            if (
                chunk.section_title is None
                or chunk.section_title.strip() == ""
            ):
                continue

            # Skip very long metadata-like titles
            if len(chunk.section_title) > 80:
                continue

            expected = (
                document.original_filename,
                chunk.page_number,
                chunk.section_title
            )

            if expected in seen:
                continue

            seen.add(expected)

            queries.append(
                {
                    "query": f"Explain {chunk.section_title}",
                    "expected": expected
                }
            )

    return queries


async def main():

    print("=" * 80)
    print("BUILDING RETRIEVAL INDEXES")
    print("=" * 80)

    # Build FAISS + BM25
    await build_index()

    print("\nIndexes Built Successfully.\n")

    evaluation_queries = await load_evaluation_queries()

    print(f"Generated {len(evaluation_queries)} evaluation queries.\n")

    precision_scores = []
    recall_scores = []
    mrr_scores = []
    ndcg_scores = []
    map_scores = []

    print("=" * 80)
    print("DYNAMIC RETRIEVAL EVALUATION")
    print("=" * 80)

    for sample in evaluation_queries:

        query = sample["query"]

        expected = {sample["expected"]}

        print("\n" + "-" * 80)
        print("Query :", query)

        retrieval = await retrieve_chunks(query)

        retrieved = []

        for chunk in retrieval["chunks"]:

            retrieved.append(
                (
                    chunk["original_filename"],
                    chunk["page_number"],
                    chunk["section_title"]
                )
            )

        metrics = RetrievalEvaluator.evaluate(
            relevant_ids=expected,
            retrieved_ids=retrieved,
            k=5
        )

        precision_scores.append(metrics["precision@k"])
        recall_scores.append(metrics["recall@k"])
        mrr_scores.append(metrics["mrr"])
        ndcg_scores.append(metrics["ndcg@k"])
        map_scores.append(metrics["map"])

        print("\nExpected:")
        print(expected)

        print("\nRetrieved:")

        for item in retrieved:
            print(item)

        print("\nMetrics:")
        print(metrics)

    if len(precision_scores) == 0:
        print("\nNo evaluation queries generated.")
        return

    n = len(precision_scores)

    print("\n" + "=" * 80)
    print("FINAL RETRIEVAL METRICS")
    print("=" * 80)

    print(f"Queries Evaluated : {n}")
    print(f"Precision@5 : {sum(precision_scores)/n:.4f}")
    print(f"Recall@5    : {sum(recall_scores)/n:.4f}")
    print(f"MRR         : {sum(mrr_scores)/n:.4f}")
    print(f"NDCG@5      : {sum(ndcg_scores)/n:.4f}")
    print(f"MAP         : {sum(map_scores)/n:.4f}")


if __name__ == "__main__":
    asyncio.run(main())