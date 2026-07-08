import asyncio

from sqlalchemy import select

from backend.database.db import SessionLocal
from backend.database.models import Chunk


DOCUMENT_ID = "402b5085-81ac-4fcb-b328-548e061accfc"


async def main():

    async with SessionLocal() as db:

        result = await db.execute(
            select(Chunk).where(
                Chunk.document_id == DOCUMENT_ID
            )
        )

        chunks = result.scalars().all()

        print("Chunks:", len(chunks))

        for c in chunks:
            print("=" * 60)
            print("Page:", c.page_number)
            print(c.text[:300])


asyncio.run(main())