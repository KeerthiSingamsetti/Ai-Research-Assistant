from backend.services.performance_metrics import PerformanceTimer
from backend.services.embedding_service import generate_embedding
from backend.services.vector_store import search_embeddings
from backend.services.bm25_store import search_bm25
from backend.services.reranker import rerank

query = "What is machine learning?"

timer = PerformanceTimer()

timer.start("embedding_time_ms")
embedding = generate_embedding(query)
timer.stop("embedding_time_ms")

timer.start("faiss_time_ms")
faiss_results = search_embeddings(embedding)
timer.stop("faiss_time_ms")

timer.start("bm25_time_ms")
bm25_results = search_bm25(query)
timer.stop("bm25_time_ms")

combined = faiss_results + bm25_results

timer.start("cross_encoder_time_ms")
reranked = rerank(query, combined)
timer.stop("cross_encoder_time_ms")

metrics = timer.get_metrics()

print("\nPerformance Metrics")
print("-" * 40)

for key, value in metrics.items():
    print(f"{key:<30} {value:.2f} ms")