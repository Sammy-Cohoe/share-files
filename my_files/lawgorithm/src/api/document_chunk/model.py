from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import uuid
from src.config.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    embedding = Column(Vector(768))  # Adjust dimension as needed
    
    section_type = Column(String(50))
    page_number = Column(Integer)
    token_count = Column(Integer)
    importance_score = Column(Float, default=1.0)
    
    metadata = Column(JSON, default={})
    
    # Relationships
    #document = relationship("Document", back_populates="chunks")