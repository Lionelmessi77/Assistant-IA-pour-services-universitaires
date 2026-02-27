"""Text chunking module using Chonkie or simple fallback."""
from typing import List
from .simple_chunker import TokenChunker, Chunk


class TextChunker:
    """Chunk text into smaller pieces for RAG."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunker = TokenChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def chunk_text(self, text: str) -> List[Chunk]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Input text to chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        chunks = self.chunker.chunk(text)
        return chunks

    def chunk_documents(self, texts: dict[str, str]) -> List[dict]:
        """
        Chunk multiple documents with metadata.

        Args:
            texts: Dictionary mapping document names to text content

        Returns:
            List of dictionaries with chunked text and metadata
        """
        all_chunks = []

        for doc_name, text in texts.items():
            chunks = self.chunk_text(text)

            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk.text,
                    "metadata": {
                        "source": doc_name,
                        "chunk_index": i,
                    }
                })

        return all_chunks

    def format_for_qdrant(self, chunks: List[dict]) -> tuple[List[str], List[dict]]:
        """
        Format chunks for Qdrant insertion.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Tuple of (texts list, metadata list)
        """
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        return texts, metadatas
