from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    
    sections: Dict[str, List[str]]
    tables: List[Dict]
    metadata: Dict
    full_text: str
    has_tables: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'sections': self.sections,
            'tables': self.tables,
            'metadata': self.metadata,
            'full_text': self.full_text,
            'has_tables': self.has_tables
        }


class BaseExtractor(ABC):
    
    @abstractmethod
    async def extract(self, file_path: str) -> ExtractedContent:
        pass
    
    @abstractmethod
    def supports_file_type(self, file_path: str) -> bool:
        pass