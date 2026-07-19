"""
retrieval_evaluator.py

Evaluation metrics for Retrieval-Augmented Generation (RAG).

Metrics:
1. Precision@K
2. Recall@K
3. Mean Reciprocal Rank (MRR)
4. Normalized Discounted Cumulative Gain (NDCG)
5. Mean Average Precision (MAP)
"""

import math
from typing import List, Set


class RetrievalEvaluator:

    @staticmethod
    def precision_at_k(
        relevant_ids: Set[str],
        retrieved_ids: List[str],
        k: int = 5
    ) -> float:
        """
        Precision@K
        """

        retrieved = retrieved_ids[:k]

        if len(retrieved) == 0:
            return 0.0

        hits = sum(
            1 for doc in retrieved
            if doc in relevant_ids
        )

        return round(hits / len(retrieved), 4)

    @staticmethod
    def recall_at_k(
        relevant_ids: Set[str],
        retrieved_ids: List[str],
        k: int = 5
    ) -> float:
        """
        Recall@K
        """

        if len(relevant_ids) == 0:
            return 0.0

        retrieved = retrieved_ids[:k]

        hits = sum(
            1 for doc in retrieved
            if doc in relevant_ids
        )

        return round(hits / len(relevant_ids), 4)

    @staticmethod
    def reciprocal_rank(
        relevant_ids: Set[str],
        retrieved_ids: List[str]
    ) -> float:
        """
        Reciprocal Rank
        """

        for rank, doc in enumerate(retrieved_ids, start=1):

            if doc in relevant_ids:
                return round(1 / rank, 4)

        return 0.0

    @staticmethod
    def ndcg_at_k(
        relevant_ids: Set[str],
        retrieved_ids: List[str],
        k: int = 5
    ) -> float:
        """
        NDCG@K
        """

        retrieved = retrieved_ids[:k]

        dcg = 0.0

        for i, doc in enumerate(retrieved):

            if doc in relevant_ids:

                dcg += 1 / math.log2(i + 2)

        ideal_hits = min(len(relevant_ids), k)

        idcg = sum(
            1 / math.log2(i + 2)
            for i in range(ideal_hits)
        )

        if idcg == 0:
            return 0.0

        return round(dcg / idcg, 4)

    @staticmethod
    def average_precision(
        relevant_ids: Set[str],
        retrieved_ids: List[str]
    ) -> float:
        """
        Average Precision (AP)
        """

        hits = 0

        score = 0.0

        for rank, doc in enumerate(retrieved_ids, start=1):

            if doc in relevant_ids:

                hits += 1

                score += hits / rank

        if hits == 0:
            return 0.0

        return round(score / len(relevant_ids), 4)

    @staticmethod
    def evaluate(
        relevant_ids: Set[str],
        retrieved_ids: List[str],
        k: int = 5
    ) -> dict:
        """
        Compute all retrieval metrics.
        """

        return {

            "precision@k":
                RetrievalEvaluator.precision_at_k(
                    relevant_ids,
                    retrieved_ids,
                    k
                ),

            "recall@k":
                RetrievalEvaluator.recall_at_k(
                    relevant_ids,
                    retrieved_ids,
                    k
                ),

            "mrr":
                RetrievalEvaluator.reciprocal_rank(
                    relevant_ids,
                    retrieved_ids
                ),

            "ndcg@k":
                RetrievalEvaluator.ndcg_at_k(
                    relevant_ids,
                    retrieved_ids,
                    k
                ),

            "map":
                RetrievalEvaluator.average_precision(
                    relevant_ids,
                    retrieved_ids
                )
        }