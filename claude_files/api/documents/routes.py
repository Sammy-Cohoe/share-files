"""API routes for document upload and management."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from .services import DocumentService
from .websocket import manager
from .schemas import DocumentResponse, DocumentUploadRequest, ChunkResponse
# from src.database import get_db  # Import your database dependency


router = APIRouter(prefix="/api/documents", tags=["documents"])


# Placeholder for database dependency - replace with your actual implementation
async def get_db():
    """Placeholder for database session dependency."""
    pass


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    document_type: str = "invention_disclosure",
    is_primary: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a document and start async processing.
    
    Returns immediately with document ID. Processing happens in background.
    Connect to WebSocket endpoint for real-time progress updates.
    """
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.pptx', '.txt', '.doc'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Initialize service
    service = DocumentService(db)
    
    # Upload file and create database record
    document = await service.upload_and_process(
        file=file,
        project_id=project_id,
        document_type=document_type,
        is_primary=is_primary
    )
    
    # Start processing in background
    background_tasks.add_task(
        service.process_document,
        str(document.id),
        project_id,
        is_primary
    )
    
    return document


@router.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time document processing updates.
    
    Connect to this endpoint after uploading a document to receive
    progress updates in real-time.
    
    Message format:
    {
        "stage": "extracting" | "classifying" | "chunking" | "embedding" | "storing" | "complete" | "failed",
        "progress": 0-100,
        "error": "error message" (only if failed)
    }
    """
    await manager.connect(websocket, document_id)
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Echo back (optional - can be used for ping/pong)
            await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, document_id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get document details by ID."""
    service = DocumentService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get chunks for a specific document."""
    service = DocumentService(db)
    chunks = service.get_document_chunks(document_id, limit)
    return chunks


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    permanent: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete a document.
    
    Args:
        document_id: Document UUID
        permanent: If True, permanently delete. If False, soft delete (default)
    """
    service = DocumentService(db)
    
    if permanent:
        # Permanent delete - you'd implement this in the service
        raise HTTPException(status_code=501, detail="Permanent delete not yet implemented")
    else:
        result = await service.soft_delete_document(document_id)
        return result
