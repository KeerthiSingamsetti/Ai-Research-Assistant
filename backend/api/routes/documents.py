import os
import uuid
from typing import List, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.config import settings
from backend.database.db import get_db
from backend.database.models import Document, Chunk
from backend.schemas.document import (
    DocumentUploadResponse,
    DocumentListItem,
    DocumentDetail,
    ChunkResponse,
    ChunkListResponse
)
from backend.services.deduplication import check_duplicate, get_file_hash
from backend.services.storage import save_file, delete_file
from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.chunker import chunk_document
from backend.utils.logger import setup_logger

logger = setup_logger("routes_documents")

# Initialize Router with /documents prefix
router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    responses={
        400: {"description": "Invalid file type or size exceeded"},
        409: {"description": "Duplicate document hash detected"},
        500: {"description": "Failed to parse or ingest PDF"}
    }
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Union[DocumentUploadResponse, JSONResponse]:
    """Uploads a PDF file, parses it, chunks it, and registers it in the system.

    Validates file extension and size, checks for duplicates, saves to disk,
    runs the PDF parser, runs the chunking pipeline, and saves all data to the DB.

    Args:
        file: Multipart uploaded file.
        db: Database AsyncSession dependency.

    Returns:
        DocumentUploadResponse or JSONResponse.
    """
    original_filename = file.filename or "unknown.pdf"
    
    # 1. Validation: Suffix must be .pdf
    if not original_filename.lower().endswith(".pdf"):
        logger.warning(f"Rejected upload: File '{original_filename}' is not a PDF.")
        return JSONResponse(
            status_code=400,
            content={"error": "InvalidFileTypeError", "detail": "Only PDF files are allowed"}
        )

    # 2. Validation: Read file bytes and verify size limits
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file upload bytes: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": "FileReadError", "detail": "Failed to read uploaded file"}
        )

    file_size_mb = len(file_bytes) / (1024 * 1024)
    logger.info(f"File upload received: {original_filename}, size: {file_size_mb:.2f} MB")
    
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        logger.warning(f"Rejected upload: File '{original_filename}' exceeds {settings.MAX_FILE_SIZE_MB}MB size limit.")
        return JSONResponse(
            status_code=400,
            content={
                "error": "FileSizeExceededError",
                "detail": f"File size ({file_size_mb:.2f}MB) exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB"
            }
        )

    # 3. Deduplication check
    try:
        is_dup, existing_doc_id = await check_duplicate(file_bytes, db)
        if is_dup:
            file_hash = get_file_hash(file_bytes)
            logger.warning(f"Duplicate detected. Hash: {file_hash}, existing doc_id: {existing_doc_id}")
            return JSONResponse(
                status_code=409,
                content={
                    "error": "DuplicateDocumentError",
                    "detail": f"Document already exists in the system.",
                    "existing_doc_id": existing_doc_id
                }
            )
    except Exception as e:
        logger.exception("Database error while checking for duplicates")
        return JSONResponse(
            status_code=500,
            content={"error": "DatabaseError", "detail": f"Internal database error: {str(e)}"}
        )

    # 4. Save file to disk
    try:
        file_path = await save_file(file_bytes, original_filename, settings.UPLOAD_DIR)
    except Exception as e:
        logger.error(f"Failed to save file to disk: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "StorageError", "detail": "Failed to save file to disk"}
        )

    # 5. Ingest into database (marked pending initially)
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        filename=os.path.basename(file_path),
        original_filename=original_filename,
        file_hash=get_file_hash(file_bytes),
        file_path=file_path,
        page_count=0,
        chunk_count=0,
        status="pending"
    )
    db.add(doc)
    await db.commit()

    # 6. Parse and Chunk
    try:
        # PDF text extraction
        pages = extract_text_from_pdf(file_path)
        page_count = len(pages)
        
        # Chunking
        chunks = chunk_document(
            pages,
            filename=original_filename,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        chunk_count = len(chunks)

        # 7. Update Document status and write Chunks
        doc.page_count = page_count
        doc.chunk_count = chunk_count
        doc.status = "processed"

        for c in chunks:
            db_chunk = Chunk(
                id=c["chunk_id"],
                document_id=doc_id,
                chunk_index=c["chunk_index"],
                text=c["text"],
                page_number=c["page_number"],
                section_title=c["section_title"] or None,
                char_count=c["char_count"]
            )
            db.add(db_chunk)

        await db.commit()
        logger.info(f"Successfully processed document: {doc_id}. Chunks written: {chunk_count}")

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=original_filename,
            page_count=page_count,
            chunk_count=chunk_count,
            status="processed",
            message="Document uploaded and processed successfully"
        )

    except Exception as e:
        logger.exception(f"Processing failed for document ID: {doc_id}")
        
        # Mark document as failed
        doc.status = "failed"
        await db.commit()
        
        # Clean up uploaded file
        await delete_file(file_path)

        return JSONResponse(
            status_code=500,
            content={"error": "ProcessingError", "detail": f"Failed to parse or chunk PDF: {str(e)}"}
        )


@router.get("/", response_model=List[DocumentListItem])
async def list_documents(db: AsyncSession = Depends(get_db)) -> List[DocumentListItem]:
    """Retrieves a list of all uploaded documents.

    Args:
        db: Database AsyncSession.

    Returns:
        List of DocumentListItem.
    """
    try:
        query = select(Document).order_by(Document.upload_time.desc())
        result = await db.execute(query)
        documents = result.scalars().all()
        return [
            DocumentListItem(
                document_id=doc.id,
                filename=doc.original_filename,
                upload_time=doc.upload_time,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                status=doc.status
            )
            for doc in documents
        ]
    except Exception as e:
        logger.exception("Failed to retrieve documents list")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_details(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
) -> DocumentDetail:
    """Gets detailed metadata for a single document.

    Args:
        doc_id: Unique UUID of the document.
        db: Database AsyncSession.

    Returns:
        DocumentDetail.
    """
    try:
        query = select(Document).where(Document.id == doc_id)
        result = await db.execute(query)
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentDetail(
            document_id=doc.id,
            filename=doc.original_filename,
            upload_time=doc.upload_time,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            status=doc.status,
            file_hash=doc.file_hash
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve document metadata for {doc_id}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Deletes a document, its database entries (chunks & document), and its physical file.

    Args:
        doc_id: Unique UUID of the document.
        db: Database AsyncSession.

    Returns:
        A success message dict.
    """
    try:
        query = select(Document).where(Document.id == doc_id)
        result = await db.execute(query)
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 1. Clean up file from disk
        file_deleted = await delete_file(doc.file_path)
        if not file_deleted:
            logger.warning(f"Target document file was not found on disk: {doc.file_path}")

        # 2. Delete database records (Chunks first, then Document)
        await db.execute(delete(Chunk).where(Chunk.document_id == doc_id))
        await db.delete(doc)
        await db.commit()

        logger.info(f"Deleted document {doc_id} and all related chunks successfully.")
        return {"message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete document {doc_id}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{doc_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
) -> ChunkListResponse:
    """Retrieves all chunks associated with a document.

    Args:
        doc_id: Unique UUID of the document.
        db: Database AsyncSession.

    Returns:
        ChunkListResponse.
    """
    try:
        # Check if document exists first
        doc_query = select(Document).where(Document.id == doc_id)
        doc_result = await db.execute(doc_query)
        doc = doc_result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Fetch chunks sorted sequentially by chunk_index
        chunks_query = select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
        chunks_result = await db.execute(chunks_query)
        chunks = chunks_result.scalars().all()

        return ChunkListResponse(
            document_id=doc_id,
            total_chunks=len(chunks),
            chunks=[
                ChunkResponse(
                    chunk_id=c.id,
                    document_id=c.document_id,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    page_number=c.page_number,
                    section_title=c.section_title,
                    char_count=c.char_count
                )
                for c in chunks
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve chunks for document {doc_id}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{doc_id}/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_document_chunk(
    doc_id: str,
    chunk_id: str,
    db: AsyncSession = Depends(get_db)
) -> ChunkResponse:
    """Retrieves a single chunk metadata and text.

    Args:
        doc_id: Unique UUID of the document.
        chunk_id: Unique UUID of the chunk.
        db: Database AsyncSession.

    Returns:
        ChunkResponse.
    """
    try:
        query = select(Chunk).where(Chunk.document_id == doc_id, Chunk.id == chunk_id)
        result = await db.execute(query)
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
            
        return ChunkResponse(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            char_count=chunk.char_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve chunk {chunk_id} for document {doc_id}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/health", tags=["health"])
async def router_health() -> Dict[str, str]:
    """Endpoint to check route status and API version.

    Returns:
        Dict detailing API status and version.
    """
    return {"status": "ok", "version": "1.0.0"}
