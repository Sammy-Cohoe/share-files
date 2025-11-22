"""Document service layer for handling uploads and processing."""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from pathlib import Path
from datetime import datetime
import shutil
import uuid

from src.preprocessing.pipeline import DocumentPreprocessingPipeline
from .websocket import manager


class DocumentService:
    """Service for document upload and processing operations."""
    
    def __init__(self, db: Session, storage_path: str = "/tmp/documents"):
        """
        Initialize service.
        
        Args:
            db: Database session
            storage_path: Base path for document storage
        """
        self.db = db
        self.storage_path = Path(storage_path)
        self.pipeline = DocumentPreprocessingPipeline(db)
    
    async def upload_and_process(
        self,
        file: UploadFile,
        project_id: str,
        document_type: str = "invention_disclosure",
        is_primary: bool = False
    ):
        """
        Upload file and start async processing.
        
        Args:
            file: Uploaded file
            project_id: Project UUID
            document_type: Type of document
            is_primary: Whether this is the primary disclosure
            
        Returns:
            Document record
        """
        from src.models.document import Document
        
        # Save file to storage
        storage_path = await self._save_file(file, project_id)
        
        # Create document record
        document = Document(
            project_id=project_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size_bytes=file.size if hasattr(file, 'size') else 0,
            storage_path=str(storage_path),
            document_type=document_type,
            processing_status="pending",
            metadata={
                'is_primary': is_primary,
                'original_filename': file.filename
            }
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    async def process_document(self, document_id: str, project_id: str, is_primary: bool = False):
        """
        Process document asynchronously with progress tracking.
        
        Args:
            document_id: Document UUID
            project_id: Project UUID
            is_primary: Whether this is primary disclosure
        """
        from src.models.document import Document
        
        # Get document
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Create progress callback
        async def progress_callback(progress_data: dict):
            await manager.send_progress(str(document_id), progress_data)
        
        # Process with progress tracking
        result = await self.pipeline.process_document(
            document_id=str(document_id),
            file_path=document.storage_path,
            project_id=project_id,
            is_primary=is_primary,
            progress_callback=progress_callback
        )
        
        return result
    
    async def _save_file(self, file: UploadFile, project_id: str) -> Path:
        """
        Save uploaded file to storage.
        
        Args:
            file: Uploaded file
            project_id: Project UUID
            
        Returns:
            Path to saved file
        """
        # Create project directory
        project_dir = self.storage_path / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = project_dir / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    def get_document(self, document_id: str):
        """Get document by ID."""
        from src.models.document import Document
        
        return self.db.query(Document).filter(
            Document.id == document_id
        ).first()
    
    def get_document_chunks(self, document_id: str, limit: Optional[int] = None):
        """Get chunks for a document."""
        from src.models.document import DocumentChunk
        
        query = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    async def soft_delete_document(self, document_id: str):
        """Soft delete a document."""
        from src.models.document import Document
        
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document not found")
        
        document.deleted_at = datetime.utcnow()
        self.db.commit()
        
        return {"status": "soft_deleted", "document_id": document_id}
