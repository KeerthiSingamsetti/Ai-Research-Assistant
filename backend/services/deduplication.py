import hashlib
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.models import Document
from backend.utils.logger import setup_logger

logger = setup_logger("deduplication")

def get_file_hash(file_bytes: bytes) -> str:
    """Computes the hex SHA-256 digest of the given file bytes.

    Args:
        file_bytes: Binary data of the file.

    Returns:
        The hex SHA-256 hash string.
    """
    return hashlib.sha256(file_bytes).hexdigest()

async def check_duplicate(file_bytes: bytes, db: AsyncSession) -> Tuple[bool, Optional[str]]:
    """Checks if a document with the same SHA-256 hash already exists in the database.

    Args:
        file_bytes: Binary data of the file to check.
        db: Database AsyncSession.

    Returns:
        A tuple of (is_duplicate, existing_document_id).
    """
    file_hash = get_file_hash(file_bytes)
    logger.debug(f"Checking deduplication for file hash: {file_hash}")
    
    # Query document by file_hash
    query = select(Document).where(Document.file_hash == file_hash)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if doc:
        logger.info(f"Duplicate document detected. Existing ID: {doc.id}")
        return True, doc.id
        
    return False, None
