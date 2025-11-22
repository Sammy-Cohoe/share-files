"""Pydantic schemas for document API validation and serialization."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    
    project_id: UUID
    document_type: str = "invention_disclosure"
    is_primary: bool = False


class DocumentResponse(BaseModel):
    """Response schema for document data."""
    
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    file_size_bytes: int
    storage_path: str
    document_type: Optional[str] = None
    processing_status: str
    processing_error: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # For SQLAlchemy models


class ChunkResponse(BaseModel):
    """Response schema for document chunk data."""
    
    id: UUID
    document_id: UUID
    chunk_text: str
    chunk_index: int
    section_type: Optional[str] = None
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    importance_score: float = 1.0
    metadata: Dict = Field(default_factory=dict)
    
    # Note: embedding is excluded from response (too large)
    
    class Config:
        from_attributes = True


class ProcessingProgressUpdate(BaseModel):
    """Schema for WebSocket progress updates."""
    
    stage: str  # "extracting", "chunking", "embedding", "storing", "complete", "failed"
    progress: int  # 0-100
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "stage": "embedding",
                "progress": 70,
                "error": None
            }
        }


class DocumentListResponse(BaseModel):
    """Response schema for list of documents."""
    
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
