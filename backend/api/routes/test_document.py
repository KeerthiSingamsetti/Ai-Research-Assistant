from sqlalchemy import select
from backend.database.db import SessionLocal
from backend.database.models import Chunk

@router.get("/chunks/{document_id}")
async def get_chunks(document_id: str):

    async with SessionLocal() as db:

        result = await db.execute(
            select(Chunk).where(
                Chunk.document_id == document_id
            )
        )

        chunks = result.scalars().all()

        return [
            {
                "chunk_id": chunk.id,
                "page": chunk.page_number,
                "section": chunk.section_title,
                "text": chunk.text[:300]
            }
            for chunk in chunks
        ]