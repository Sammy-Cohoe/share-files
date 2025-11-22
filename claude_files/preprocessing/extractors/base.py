"""Base extractor interface for document content extraction."""

from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    """Structured container for extracted document content."""
    
    sections: Dict[str, List[str]]
    tables: List[Dict]
    metadata: Dict
    full_text: str
    has_tables: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'sections': self.sections,
            'tables': self.tables,
            'metadata': self.metadata,
            'full_text': self.full_text,
            'has_tables': self.has_tables
        }


class BaseExtractor(ABC):
    """Abstract base class for document content extractors."""
    
    @abstractmethod
    async def extract(self, file_path: str) -> ExtractedContent:
        """
        Extract content from a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractedContent object containing organized document data
        """
        pass
    
    @abstractmethod
    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if this extractor supports the given file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if file type is supported, False otherwise
        """
        pass
