from backend.services.embedding_service import generate_embedding

text = "Machine learning is a branch of AI."

embedding = generate_embedding(text)

print(type(embedding))
print(len(embedding))