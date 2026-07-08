import backend.services.bm25_store as bm25_store

# Dummy Chunk class
class Chunk:
    def __init__(self, id, text):
        self.id = id
        self.text = text

chunks = [
    Chunk("1", "Machine learning is a subset of artificial intelligence."),
    Chunk("2", "FastAPI is a modern Python web framework."),
    Chunk("3", "FAISS is used for vector similarity search.")
]

print("Building BM25 index...\n")

bm25_store.build_bm25(chunks)

print("BM25 index built successfully.\n")

query = "machine learning"

results = bm25_store.search_bm25(query, top_k=3)

print("Search Results:\n")

for idx in results:
    print(f"Chunk ID : {bm25_store.chunk_ids[idx]}")
    print(f"Text     : {chunks[idx].text}")
    print()