from rank_bm25 import BM25Okapi
import numpy as np

bm25 = None
chunk_ids = []


def build_bm25(chunks):

    global bm25
    global chunk_ids

    tokenized_docs = []
    chunk_ids = []

    for chunk in chunks:

        tokenized_docs.append(
            chunk.text.split()
        )

        chunk_ids.append(
            chunk.id
        )

    bm25 = BM25Okapi(
        tokenized_docs
    )


def search_bm25(
    query,
    top_k=10
):

    scores = bm25.get_scores(
        query.split()
    )

    ranked = np.argsort(
        scores
    )[::-1]

    return ranked[:top_k]