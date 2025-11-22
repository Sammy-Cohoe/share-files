"""Embedding generation for patent and technical documents."""

from typing import List
import asyncio
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class PatentEmbedder:
    """Generates embeddings optimized for patent text."""
    
    def __init__(self, model_name: str = "AI-Growth-Lab/PatentSBERTa", device: str = "cpu"):
        """
        Initialize embedder.
        
        Args:
            model_name: HuggingFace model name for embeddings
            device: 'cpu' or 'cuda' for GPU acceleration
        """
        self.embed_model = HuggingFaceEmbedding(
            model_name=model_name,
            device=device
        )
        self.embedding_dim = self._get_embedding_dimension()
    
    async def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Run CPU-intensive embedding generation in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self._generate_batch,
            texts,
            batch_size
        )
        
        return embeddings
    
    def _generate_batch(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Generate embeddings in batches (runs in thread pool)."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embed_model.get_text_embedding_batch(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self.embed_model.get_text_embedding,
            text
        )
        return embedding
    
    def _get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        # Generate a test embedding to determine dimension
        test_embedding = self.embed_model.get_text_embedding("test")
        return len(test_embedding)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dim
