from typing import List
import asyncio
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class PatentEmbedder:
    def __init__(
        self, model_name: str = "AI-Growth-Lab/PatentSBERTa", device: str = "cpu"
    ):

        self.embedder = HuggingFaceEmbedding(model_name=model_name, device=device)

    async def generate_embeddings(
        self, text: List[str], batch_size: int = 32
    ) -> List[float]:

        if len(text) == 0:
            return []

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self._generate_batch, text, batch_size
        )

        return embeddings

    def _generate_batch(self, text: List[str], batch_size: int) -> List[List[float]]:

        all_embeddings = []

        for i in range(0, len(text), batch_size):
            batch = text[i : i + batch_size]
            batch_embeddings = self.embedder.get_text_embedding_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def generate_single_embeddings(self, text: str) -> List[float]:
        if len(text) == 0:
            return []

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.embedder.get_text_embedding, text
        )

        return embeddings

    def _get_embedding_dimension(self) -> int:
        test_embedding = self.embedder.get_text_embedding("test")
        return len(test_embedding)

    @property
    def dimension(self) -> int:
        return self.embedding_dim
