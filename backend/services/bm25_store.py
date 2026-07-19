from rank_bm25 import BM25Okapi
import numpy as np

bm25 = None
chunk_ids = []

'''
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

'''
def build_bm25(chunks):

    global bm25
    global chunk_ids

    chunk_ids.clear()

    texts = []

    for chunk in chunks:

        texts.append(chunk.text)

        chunk_ids.append(chunk.id)

    bm25 = BM25Okapi(
        [
            text.split()
            for text in texts
        ]
    )

def search_bm25(
    query,
    top_k=10
):

    if bm25 is None:
        raise RuntimeError(
            "BM25 index has not been built. Call build_bm25() first."
        )

    scores = bm25.get_scores(
        query.split()
    )

    ranked = np.argsort(scores)[::-1]

    return ranked[:top_k]

   