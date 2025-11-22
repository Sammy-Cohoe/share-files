"""Semantic chunking using LlamaIndex."""

from typing import List, Dict
from dataclasses import dataclass
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter


@dataclass
class Chunk:
    """Represents a document chunk."""
    
    text: str
    chunk_index: int
    section_type: str
    metadata: Dict
    token_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'chunk_index': self.chunk_index,
            'section_type': self.section_type,
            'metadata': self.metadata,
            'token_count': self.token_count
        }


class LlamaChunker:
    """Semantic chunker using LlamaIndex's SentenceSplitter."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    async def chunk_sections(
        self, 
        sections: Dict[str, List[str]], 
        base_metadata: Dict
    ) -> List[Chunk]:
        """
        Chunk document sections into semantic chunks.
        
        Args:
            sections: Dictionary mapping section names to text content
            base_metadata: Base metadata to attach to all chunks
            
        Returns:
            List of Chunk objects
        """
        all_chunks = []
        chunk_global_index = 0
        
        for section_name, section_texts in sections.items():
            if not section_texts:
                continue
            
            # Combine section texts
            section_text = '\n\n'.join(section_texts)
            
            # Create LlamaIndex document
            llama_doc = LlamaDocument(
                text=section_text,
                metadata={
                    **base_metadata,
                    'section_type': section_name
                }
            )
            
            # Split into nodes
            nodes = self.splitter.get_nodes_from_documents([llama_doc])
            
            # Convert nodes to Chunk objects
            for local_idx, node in enumerate(nodes):
                chunk = Chunk(
                    text=node.text,
                    chunk_index=chunk_global_index,
                    section_type=section_name,
                    metadata={
                        **base_metadata,
                        'section_type': section_name,
                        'node_id': node.node_id,
                        'local_chunk_index': local_idx,
                        'total_chunks_in_section': len(nodes)
                    },
                    token_count=self._estimate_tokens(node.text)
                )
                all_chunks.append(chunk)
                chunk_global_index += 1
        
        return all_chunks
    
    async def chunk_tables(
        self,
        tables: List[Dict],
        base_metadata: Dict
    ) -> List[Chunk]:
        """
        Create chunks for tables.
        
        Args:
            tables: List of table dictionaries
            base_metadata: Base metadata to attach to chunks
            
        Returns:
            List of Chunk objects for tables
        """
        table_chunks = []
        
        for idx, table in enumerate(tables):
            chunk = Chunk(
                text=table['text'],
                chunk_index=idx,
                section_type='table',
                metadata={
                    **base_metadata,
                    'section_type': 'table',
                    'table_index': idx,
                    'table_metadata': table.get('metadata', {})
                },
                token_count=self._estimate_tokens(table['text'])
            )
            table_chunks.append(chunk)
        
        return table_chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token count estimation."""
        # Approximation: 1 token ≈ 0.75 words
        words = len(text.split())
        return int(words * 1.33)
