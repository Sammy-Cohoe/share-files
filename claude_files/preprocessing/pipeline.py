"""Main document preprocessing pipeline with async processing and progress tracking."""

from typing import Callable, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from enum import Enum

from .extractors.unstructured_extractor import UnstructuredExtractor
from .chunkers.llama_chunker import LlamaChunker
from .embedders.patent_embedder import PatentEmbedder
from .classifiers.domain_classifier import DomainClassifier


class ProcessingStage(Enum):
    """Enumeration of processing stages."""
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETE = "complete"
    FAILED = "failed"


class DocumentPreprocessingPipeline:
    """Orchestrates document preprocessing with progress tracking."""
    
    def __init__(
        self, 
        db: Session,
        embedding_model: str = "AI-Growth-Lab/PatentSBERTa",
        device: str = "cpu"
    ):
        """
        Initialize pipeline with required components.
        
        Args:
            db: SQLAlchemy database session
            embedding_model: Model name for embeddings
            device: 'cpu' or 'cuda'
        """
        self.db = db
        self.extractor = UnstructuredExtractor()
        self.chunker = LlamaChunker(chunk_size=512, chunk_overlap=50)
        self.embedder = PatentEmbedder(model_name=embedding_model, device=device)
        self.classifier = DomainClassifier()
    
    async def process_document(
        self,
        document_id: str,
        file_path: str,
        project_id: str,
        is_primary: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Process document through full pipeline.
        
        Args:
            document_id: UUID of document in database
            file_path: Path to document file
            project_id: UUID of parent project
            is_primary: Whether this is the primary invention disclosure
            progress_callback: Optional async function to call with progress updates
            
        Returns:
            Processing result dictionary
        """
        try:
            # Import here to avoid circular imports
            from src.models.document import Document, DocumentChunk
            
            # Get document from database
            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Update status to processing
            document.processing_status = "processing"
            self.db.commit()
            
            # Stage 1: Extract content
            await self._update_progress(progress_callback, ProcessingStage.EXTRACTING, 20)
            extracted = await self.extractor.extract(file_path)
            
            # Stage 2: Classify domain
            await self._update_progress(progress_callback, ProcessingStage.CLASSIFYING, 35)
            domains = self.classifier.classify(extracted.full_text)
            technical_terms = self.classifier.extract_technical_terms(extracted.full_text)
            cpc_hints = self.classifier.get_cpc_hints(domains)
            
            # Stage 3: Create chunks
            await self._update_progress(progress_callback, ProcessingStage.CHUNKING, 50)
            base_metadata = {
                'document_id': str(document_id),
                'project_id': str(project_id),
                'is_primary': is_primary,
                'technical_domains': domains,
                'cpc_hints': cpc_hints
            }
            
            # Chunk sections
            section_chunks = await self.chunker.chunk_sections(
                extracted.sections, 
                base_metadata
            )
            
            # Chunk tables
            table_chunks = await self.chunker.chunk_tables(
                extracted.tables,
                base_metadata
            )
            
            all_chunks = section_chunks + table_chunks
            
            # Stage 4: Generate embeddings
            await self._update_progress(progress_callback, ProcessingStage.EMBEDDING, 70)
            chunk_texts = [chunk.text for chunk in all_chunks]
            embeddings = await self.embedder.generate_embeddings(chunk_texts)
            
            # Stage 5: Store in database
            await self._update_progress(progress_callback, ProcessingStage.STORING, 85)
            for chunk, embedding in zip(all_chunks, embeddings):
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    embedding=embedding,
                    section_type=chunk.section_type,
                    token_count=chunk.token_count,
                    importance_score=1.0,
                    metadata=chunk.metadata
                )
                self.db.add(db_chunk)
            
            # Update document metadata
            document.processing_status = "completed"
            document.processed_at = datetime.utcnow()
            document.metadata = {
                **document.metadata,
                'total_chunks': len(all_chunks),
                'technical_domains': domains,
                'technical_terms': technical_terms,
                'cpc_hints': cpc_hints,
                'has_tables': extracted.has_tables,
                'embedding_model': self.embedder.embed_model.model_name,
                'embedding_dimension': self.embedder.dimension
            }
            
            self.db.commit()
            
            # Stage 6: Complete
            await self._update_progress(progress_callback, ProcessingStage.COMPLETE, 100)
            
            return {
                'status': 'success',
                'document_id': str(document_id),
                'chunks_created': len(all_chunks),
                'domains': domains,
                'has_tables': extracted.has_tables
            }
            
        except Exception as e:
            # Update document status to failed
            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if document:
                document.processing_status = "failed"
                document.processing_error = str(e)
                self.db.commit()
            
            await self._update_progress(progress_callback, ProcessingStage.FAILED, 0, str(e))
            raise e
    
    async def _update_progress(
        self,
        callback: Optional[Callable],
        stage: ProcessingStage,
        progress: int,
        error: Optional[str] = None
    ):
        """
        Send progress update through callback.
        
        Args:
            callback: Progress callback function
            stage: Current processing stage
            progress: Progress percentage (0-100)
            error: Optional error message
        """
        if callback:
            await callback({
                'stage': stage.value,
                'progress': progress,
                'error': error
            })
