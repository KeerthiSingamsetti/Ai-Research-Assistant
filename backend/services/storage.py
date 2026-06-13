import os
import uuid
import aiofiles
import aiofiles.os
from backend.utils.logger import setup_logger

logger = setup_logger("storage")

async def save_file(file_bytes: bytes, original_filename: str, upload_dir: str) -> str:
    """Asynchronously saves uploaded file bytes to the specified upload directory.

    Generates a unique name for the file keeping the original extension to avoid collision.

    Args:
        file_bytes: The binary content of the file.
        original_filename: The original name of the uploaded file.
        upload_dir: Directory where the file should be saved.

    Returns:
        The absolute file path of the saved file.
    """
    # Create upload directory if it does not exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Created upload directory: {upload_dir}")

    # Generate a unique name
    _, ext = os.path.splitext(original_filename)
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Write bytes to disk using aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_bytes)

    absolute_path = os.path.abspath(file_path)
    logger.info(f"Saved file {original_filename} as {unique_filename} to {absolute_path}")
    return absolute_path

async def delete_file(file_path: str) -> bool:
    """Asynchronously deletes a file from the disk if it exists.

    Args:
        file_path: Path of the file to delete.

    Returns:
        True if the file was deleted successfully, False if it was not found or failed.
    """
    try:
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
            logger.info(f"Deleted file from disk: {file_path}")
            return True
        logger.warning(f"File not found for deletion: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        # Fallback to synchronous delete in case of issues
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file from disk (sync fallback): {file_path}")
                return True
        except Exception as se:
            logger.error(f"Sync fallback deletion failed for {file_path}: {str(se)}")
        return False
