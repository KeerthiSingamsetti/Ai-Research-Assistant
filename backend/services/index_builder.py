'''

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

print("\n========== BUILD INDEX STARTED ==========\n")
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
        print("Chunks loaded from DB:", len(chunks))

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



from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk

from backend.services.embedding_service import generate_embedding
from backend.services.vector_store import add_chunk_embedding
from backend.services.bm25_store import build_bm25


async def build_index():

    print("\n========== BUILD INDEX STARTED ==========\n")

    async with SessionLocal() as db:

        print("✅ Database session opened")

        result = await db.execute(
            select(Chunk)
        )

        print("✅ Database query executed")

        chunks = result.scalars().all()

        print(f"✅ Chunks loaded from DB: {len(chunks)}")

        if not chunks:
            print("❌ No chunks found.")
            return

        print("✅ Building FAISS index...")

        for chunk in chunks:

            embedding = generate_embedding(chunk.text)

            add_chunk_embedding(
                chunk.id,
                embedding
            )

        print(f"✅ FAISS indexed {len(chunks)} chunks")

        print("✅ Building BM25 index...")

        build_bm25(chunks)

        print(f"✅ BM25 indexed {len(chunks)} chunks")

        print("✅ All retrieval indexes built successfully.")  '''


from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk

from backend.services.embedding_service import generate_embedding

from backend.services.vector_store import (
    add_chunk_embedding,
    clear_index
)

from backend.services.bm25_store import (
    build_bm25
)


from backend.services.vector_store import chunk_lookup
from backend.services.bm25_store import chunk_ids



print("\n========== BUILD INDEX STARTED ==========\n")


async def build_index():
    """
    Build retrieval indexes.

    Steps:
    1. Clear old FAISS index
    2. Load all chunks from DB
    3. Generate embeddings
    4. Build FAISS index
    5. Build BM25 index
    """

    

    print("\n==============================")
    print("FAISS lookup:", len(chunk_lookup))
    print(chunk_lookup)

    print("BM25 ids:", len(chunk_ids))
    print(chunk_ids)
    print("==============================")

    # ---------------------------------------
    # Clear old FAISS index
    # ---------------------------------------

    clear_index()

    async with SessionLocal() as db:

        print("✅ Database session opened")

        result = await db.execute(
            select(Chunk)
        )

        print("✅ Database query executed")

        chunks = result.scalars().all()

        print(f"✅ Chunks loaded from DB: {len(chunks)}")

        if not chunks:
            print("⚠️ No chunks found.")
            return

        # ---------------------------------------
        # Build FAISS
        # ---------------------------------------

        print("✅ Building FAISS index...")

        for chunk in chunks:

            embedding = generate_embedding(
                chunk.text
            )

            add_chunk_embedding(
                chunk.id,
                embedding
            )

        print(f"✅ FAISS indexed {len(chunks)} chunks")

        # ---------------------------------------
        # Build BM25
        # ---------------------------------------

        print("✅ Building BM25 index...")

        build_bm25(chunks)

        print(f"✅ BM25 indexed {len(chunks)} chunks")

        print("✅ All retrieval indexes built successfully.")

        

        print("\n========== INDEX STATUS ==========")
        print("Chunks in DB        :", len(chunks))
        print("FAISS lookup size   :", len(chunk_lookup))
        print("BM25 chunk_ids size :", len(chunk_ids))
        print("==================================")