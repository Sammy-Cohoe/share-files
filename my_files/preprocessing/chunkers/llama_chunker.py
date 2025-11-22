from typing import List, Dict
from dataclasses import dataclass
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter


@dataclass
class Chunk:
    """Class to store and return chunk information"""

    text: str
    chunk_index: int
    section: str
    metadata: Dict
    token_count: int

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "section": self.section,
            "metadata": self.metadata,
            "token_count": self.token_count,
        }


class LlamaChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):

        self.splitter = SentenceSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    async def chunk_sections(
        self, sections: Dict[str, List[str]], base_metadata: dict
    ) -> List[Chunk]:

        all_chunks = []
        chunk_global_index = 0

        for section_name, section_texts in sections.items():
            if not section_texts:
                continue

            section_text = "\n\n".join(section_texts)

            llama_doc = LlamaDocument(
                text=section_text,
                metadata={**base_metadata, "section_type": section_name},
            )

            nodes = self.splitter.get_nodes_from_documents([llama_doc])

            for i, node in enumerate(nodes):
                chunk = Chunk(
                    text=node.text,
                    chunk_index=chunk_global_index,
                    section=section_name,
                    metadata={
                        **base_metadata,
                        "section_type": section_name,
                        "node_id": node.node_id,
                        "local_chunk_index": i,
                        "total_chunks_in_section": len(nodes),
                    },
                    token_count=self._estimate_tokens(node.text),
                )
                all_chunks.append(chunk)
                chunk_global_index += 1

        return all_chunks

    async def chunk_tables(
        self, tables: List[Dict], base_metadata: Dict
    ) -> List[Chunk]:

        table_chunks = []

        for i, table in enumerate(tables):
            chunk = Chunk(
                text=table["text"],
                chunk_index=i,
                section="table",
                metadata={
                    **base_metadata,
                    "table_index": i,
                    "table_metadata": table.get("metadata", {}),
                },
                token_count=self._estimate_tokens(table["text"]),
            )
            table_chunks.append(chunk)

        return table_chunks

    def _estimate_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * 1.33)
