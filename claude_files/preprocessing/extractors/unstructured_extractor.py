"""Document content extractor using Unstructured.io library."""

import asyncio
from pathlib import Path
from typing import Dict, List
from unstructured.partition.auto import partition

from .base import BaseExtractor, ExtractedContent


class UnstructuredExtractor(BaseExtractor):
    """Extractor using Unstructured.io for document parsing."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.txt', '.doc'}
    
    async def extract(self, file_path: str) -> ExtractedContent:
        """
        Extract content using Unstructured.io.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractedContent with organized sections and metadata
        """
        # Run CPU-intensive partition in thread pool
        loop = asyncio.get_event_loop()
        elements = await loop.run_in_executor(
            None, 
            partition,
            file_path
        )
        
        # Organize elements by type and section
        organized = self._organize_elements(elements)
        
        return ExtractedContent(
            sections=organized['sections'],
            tables=organized['tables'],
            metadata=organized['metadata'],
            full_text=organized['full_text'],
            has_tables=len(organized['tables']) > 0
        )
    
    def supports_file_type(self, file_path: str) -> bool:
        """Check if file type is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def _organize_elements(self, elements) -> Dict:
        """Organize extracted elements into structured format."""
        sections = {'introduction': []}
        tables = []
        all_text = []
        current_section = 'introduction'
        
        for element in elements:
            element_type = type(element).__name__
            
            if element_type == 'Title':
                # New section detected
                section_name = element.text.lower().replace(' ', '_')[:50]
                current_section = section_name
                sections[current_section] = []
                all_text.append(element.text)
                
            elif element_type == 'NarrativeText':
                # Add text to current section
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(element.text)
                all_text.append(element.text)
                
            elif element_type == 'Table':
                # Extract table data
                tables.append({
                    'text': element.text,
                    'metadata': self._extract_element_metadata(element)
                })
                all_text.append(element.text)
                
            elif element_type == 'ListItem':
                # Add lists to current section
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(element.text)
                all_text.append(element.text)
        
        return {
            'sections': sections,
            'tables': tables,
            'metadata': {
                'total_sections': len(sections),
                'total_tables': len(tables)
            },
            'full_text': '\n\n'.join(all_text)
        }
    
    def _extract_element_metadata(self, element) -> Dict:
        """Extract metadata from an element."""
        if hasattr(element, 'metadata') and element.metadata:
            if hasattr(element.metadata, 'to_dict'):
                return element.metadata.to_dict()
            return dict(element.metadata)
        return {}
