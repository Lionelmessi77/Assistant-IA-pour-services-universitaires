"""Simple text chunking module - fallback when Chonkie is not available."""
from typing import List
import re


class Chunk:
    """Simple chunk class."""

    def __init__(self, text: str, token_count: int = None):
        self.text = text
        self.token_count = token_count or len(text.split())


class SimpleTokenChunker:
    """Simple token-based chunker without external dependencies."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> List[Chunk]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Input text to chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Split text into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = len(paragraph.split())

            # If single paragraph is too large, split by sentences
            if paragraph_tokens > self.chunk_size:
                sentences = re.split(r'[.!?]+\s+', paragraph)
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    sentence_tokens = len(sentence.split())

                    if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                        chunks.append(Chunk(current_chunk, current_tokens))
                        # Keep overlap
                        overlap_text = ' '.join(current_chunk.split()[-self.chunk_overlap:])
                        current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                        current_tokens = len(current_chunk.split())
                    else:
                        current_chunk = current_chunk + " " + sentence if current_chunk else sentence
                        current_tokens += sentence_tokens

            # Regular paragraph handling
            elif current_tokens + paragraph_tokens > self.chunk_size and current_chunk:
                chunks.append(Chunk(current_chunk, current_tokens))
                # Keep overlap
                overlap_words = current_chunk.split()[-self.chunk_overlap:]
                current_chunk = ' '.join(overlap_words) + " " + paragraph
                current_tokens = len(current_chunk.split())
            else:
                current_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
                current_tokens += paragraph_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(Chunk(current_chunk, current_tokens))

        return chunks


# Try to use Chonkie, fallback to simple chunker
try:
    from chonkie import TokenChunker as ChonkieChunker, Chunk as ChonkieChunk

    class TokenChunker:
        """Wrapper that uses Chonkie if available."""

        def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
            self.chunker = ChonkieChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        def chunk(self, text: str):
            return self.chunker.chunk(text)

except Exception as e:
    # Fallback to simple chunker
    TokenChunker = SimpleTokenChunker
    print(f"Using simple chunker (Chonkie not available): {e}")
