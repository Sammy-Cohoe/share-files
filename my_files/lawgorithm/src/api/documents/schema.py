from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class DocumentStatus(BaseModel):
    id: UUID
    processing_status: str
    processing_error: Optional[str] = None
    chunk_count: Optional[int] = None
    processed_at: Optional[datetime] = None

class ChunkResponse(BaseModel):
    id: UUID
    chunk_text: str
    chunk_index: int
    section_type: Optional[str]
    similarity_score: Optional[float] = None