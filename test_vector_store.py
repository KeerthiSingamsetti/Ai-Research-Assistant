from backend.services.embedding_service import generate_embedding
from backend.services.vector_store import (
    add_chunk_embedding,
    search_embeddings,
    chunk_lookup,
    index,
)

# Sample data
chunks = {
    "1": "Machine learning is a subset of artificial intelligence.",
    "2": "FastAPI is a modern Python web framework.",
    "3": "FAISS is used for vector similarity search."
}

print("Adding embeddings...\n")

# Add embeddings to FAISS
for chunk_id, text in chunks.items():
    embedding = generate_embedding(text)
    add_chunk_embedding(chunk_id, embedding)
    print(f"Added Chunk {chunk_id}")

print("\n----------------------------")
print("Total vectors in FAISS:", index.ntotal)
print("----------------------------\n")

# Search
query = "What is machine learning?"
query_embedding = generate_embedding(query)

distances, indices = search_embeddings(query_embedding, top_k=3)

print("Search Results\n")

for distance, idx in zip(distances[0], indices[0]):

    if idx == -1:
        continue

    chunk_id = chunk_lookup[idx]

    print(f"Chunk ID : {chunk_id}")
    print(f"Distance : {distance}")
    print(f"Text     : {chunks[chunk_id]}")
    print()