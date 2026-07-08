import asyncio

from backend.services.index_builder import build_index
from backend.services.retriever import retrieve_chunks

async def main():
    print("Building indexes...")

    await build_index()

    print("Indexes built successfully.\n")

    result = await retrieve_chunks(
        query="machine learning",
        top_k=3
    )

    print("\nConfidence:", result["confidence"])

    print("\nRetrieved Chunks:\n")

    for chunk in result["chunks"]:
        print(chunk)

asyncio.run(main())