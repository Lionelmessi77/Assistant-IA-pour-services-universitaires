"""Data ingestion pipeline for processing PDFs and storing in vector database."""
from pathlib import Path
from .pdf_extractor import DocumentExtractor
from .chunker import TextChunker
from .qdrant_rest import QdrantRESTClient as VectorStore
from .config import Config


class IngestionPipeline:
    """Pipeline for ingesting documents (PDF and text files) into the vector store."""

    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.extractor = DocumentExtractor()
        self.chunker = TextChunker(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.vector_store = VectorStore()

    def ingest_directory(self, data_dir: str, force_reindex: bool = False) -> dict:
        """
        Ingest all documents (PDF and text files) from a directory.

        Args:
            data_dir: Path to directory containing documents
            force_reindex: Clear existing data before ingesting

        Returns:
            Summary of ingestion process
        """
        data_path = Path(data_dir)

        if not data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        # Clear collection if requested
        if force_reindex:
            print("Clearing existing data...")
            self.vector_store.clear_collection()

        # Extract text from PDFs
        print(f"Extracting text from {data_dir}...")
        documents = self.extractor.extract_from_directory(data_path)

        if not documents:
            return {
                "status": "warning",
                "message": "No PDF files found in directory",
                "files_processed": 0
            }

        # Chunk documents
        print("Chunking documents...")
        chunks = self.chunker.chunk_documents(documents)

        # Format for Qdrant
        texts, metadatas = self.chunker.format_for_qdrant(chunks)

        # Add to vector store
        print("Adding to vector store...")
        count = self.vector_store.add_documents(texts, metadatas)

        # Get collection info
        info = self.vector_store.get_collection_info()

        return {
            "status": "success",
            "files_processed": len(documents),
            "chunks_created": len(chunks),
            "chunks_added": count,
            "total_documents": info["points_count"]
        }

    def ingest_file(self, file_path: str) -> dict:
        """
        Ingest a single PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Summary of ingestion
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract text
        text = self.extractor.extract_text(file_path)

        # Chunk
        chunks = self.chunker.chunk_text(text)

        # Format
        formatted_chunks = [
            {
                "text": chunk.text,
                "metadata": {"source": file_path.name, "chunk_index": i}
            }
            for i, chunk in enumerate(chunks)
        ]
        texts, metadatas = self.chunker.format_for_qdrant([formatted_chunks])

        # Add to vector store
        count = self.vector_store.add_documents(texts, metadatas)

        return {
            "status": "success",
            "file": file_path.name,
            "chunks_created": len(chunks),
            "chunks_added": count
        }


def main():
    """Main ingestion script."""
    import sys

    data_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/Data"

    pipeline = IngestionPipeline()
    result = pipeline.ingest_directory(data_dir)

    print(f"\nIngestion complete:")
    print(f"  Files processed: {result['files_processed']}")
    print(f"  Chunks created: {result['chunks_created']}")
    print(f"  Total documents in store: {result['total_documents']}")


if __name__ == "__main__":
    main()
