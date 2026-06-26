from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk

from backend.services.embedding_service import generate_embedding

from backend.services.vector_store import (
    add_chunk_embedding
)

from backend.services.bm25_store import (
    build_bm25
)


async def build_index():
    """
    Build all retrieval indexes at application startup.

    1. Load all chunks from database
    2. Generate embeddings
    3. Build FAISS vector index
    4. Build BM25 keyword index
    """

    async with SessionLocal() as db:

        result = await db.execute(
            select(Chunk)
        )

        chunks = result.scalars().all()

        if not chunks:
            print("No chunks found to index.")
            return

        # ==========================
        # Build FAISS Vector Index
        # ==========================

        for chunk in chunks:

            embedding = generate_embedding(
                chunk.text
            )

            add_chunk_embedding(
                chunk.id,
                embedding
            )

        print(
            f"FAISS indexed {len(chunks)} chunks"
        )

        # ==========================
        # Build BM25 Index
        # ==========================

        build_bm25(
            chunks
        )

        print(
            f"BM25 indexed {len(chunks)} chunks"
        )

        print(
            "All retrieval indexes built successfully."
        )