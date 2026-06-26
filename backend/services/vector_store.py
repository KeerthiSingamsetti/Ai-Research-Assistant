import faiss
import numpy as np

DIMENSION = 384

index = faiss.IndexFlatL2(DIMENSION)

chunk_lookup = {}

def add_chunk_embedding(
    chunk_id,
    embedding
):
    vector = np.array(
        [embedding],
        dtype="float32"
    )

    index.add(vector)

    chunk_lookup[index.ntotal - 1] = chunk_id


def search_embeddings(
    embedding,
    top_k=5
):
    vector = np.array(
        [embedding],
        dtype="float32"
    )

    distances, indices = index.search(
        vector,
        top_k
    )

    return distances, indices