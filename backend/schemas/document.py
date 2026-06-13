from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class DocumentUploadResponse(BaseModel):
    """Schema for document upload and ingestion response."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="The unique UUID of the ingested document.")
    filename: str = Field(..., description="The original filename of the document.")
    page_count: int = Field(..., description="Total pages processed.")
    chunk_count: int = Field(..., description="Total semantic chunks generated.")
    status: str = Field(..., description="Processing status of the document.")
    message: str = Field(..., description="Detailed status message.")

class DocumentListItem(BaseModel):
    """Schema for document item in list views."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Unique UUID of the document.")
    filename: str = Field(..., description="Original filename.")
    upload_time: datetime = Field(..., description="UTC timestamp of the upload.")
    page_count: int = Field(..., description="Total pages in the document.")
    chunk_count: int = Field(..., description="Total chunks in the document.")
    status: str = Field(..., description="Processing status.")

class DocumentDetail(DocumentListItem):
    """Detailed schema for a document including structural integrity hash."""
    file_hash: str = Field(..., description="SHA-256 integrity hash of the document.")

class ChunkResponse(BaseModel):
    """Schema representing an individual text chunk response."""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(..., description="Unique UUID of the chunk.")
    document_id: str = Field(..., description="UUID of the parent document.")
    chunk_index: int = Field(..., description="Sequential index of the chunk (0-based).")
    text: str = Field(..., description="The raw textual content of the chunk.")
    page_number: int = Field(..., description="The page number where the chunk originated (1-based).")
    section_title: Optional[str] = Field(None, description="The structural heading or section title this chunk falls under.")
    char_count: int = Field(..., description="Total characters in the chunk.")

class ChunkListResponse(BaseModel):
    """Schema representing a list of all chunks for a document."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="UUID of the parent document.")
    total_chunks: int = Field(..., description="Total count of retrieved chunks.")
    chunks: List[ChunkResponse] = Field(..., description="List of chunk details.")

class ErrorResponse(BaseModel):
    """Standardized error payload schema."""
    error: str = Field(..., description="Short error code or identifier.")
    detail: str = Field(..., description="Descriptive error explanation.")
