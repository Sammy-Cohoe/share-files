from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from src.config.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    
    document_type = Column(String(50))
    processing_status = Column(String(50), default="pending")
    processing_error = Column(Text)
    
    metadata = Column(JSON, default={})
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    #chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    #project = relationship("Project", back_populates="documents")