import faiss
import numpy as np

DIMENSION = 384

# Global FAISS index
index = faiss.IndexFlatL2(DIMENSION)

# Maps FAISS position -> Chunk ID
chunk_lookup = {}


def clear_index():
    """
    Clears the FAISS index and lookup table.
    Call this before rebuilding the index.
    """
    global index
    global chunk_lookup

    index = faiss.IndexFlatL2(DIMENSION)
    chunk_lookup = {}

    print("✅ FAISS index cleared")


def add_chunk_embedding(chunk_id, embedding):
    """
    Add a chunk embedding to the FAISS index.
    """

    vector = np.array(
        [embedding],
        dtype=np.float32
    )

    index.add(vector)

    chunk_lookup[index.ntotal - 1] = chunk_id


def search_embeddings(
    embedding,
    top_k=5
):
    """
    Search FAISS index for nearest neighbors.
    """

    if index.ntotal == 0:
        print("⚠️ FAISS index is empty.")
        return (
            np.empty((1, 0), dtype=np.float32),
            np.empty((1, 0), dtype=np.int64)
        )

    vector = np.array(
        [embedding],
        dtype=np.float32
    )

    top_k = min(top_k, index.ntotal)

    distances, indices = index.search(
        vector,
        top_k
    )

    return distances, indices