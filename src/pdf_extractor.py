"""Document text extraction module supporting PDF and text files."""
from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader


class DocumentExtractor:
    """Extract text content from PDF and text files."""

    def __init__(self):
        """Initialize the document extractor."""
        pass

    def extract_text(self, file_path: str | Path) -> str:
        """
        Extract all text from a single file (PDF or text).

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Handle text files
        if file_path.suffix.lower() in ['.txt', '.md']:
            return file_path.read_text(encoding='utf-8')

        # Handle PDF files
        if file_path.suffix.lower() == '.pdf':
            try:
                reader = PdfReader(str(file_path))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except Exception as e:
                raise RuntimeError(f"Error extracting text from {file_path}: {e}")

        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def extract_from_directory(self, directory: str | Path) -> Dict[str, str]:
        """
        Extract text from all supported files in a directory.

        Args:
            directory: Path to directory containing files

        Returns:
            Dictionary mapping file names to extracted text
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        results = {}
        # Support both .pdf and .txt files
        supported_extensions = ['*.pdf', '*.txt', '*.md']
        files = []
        for ext in supported_extensions:
            files.extend(directory.glob(ext))
            files.extend(directory.glob(f"**/{ext}"))

        for file_path in files:
            try:
                text = self.extract_text(file_path)
                results[file_path.name] = text
                print(f"Extracted {len(text)} characters from {file_path.name}")
            except Exception as e:
                print(f"Warning: Failed to extract {file_path.name}: {e}")

        return results

    def extract_with_metadata(self, file_path: str | Path) -> Dict:
        """
        Extract text along with metadata from a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing text and metadata
        """
        file_path = Path(file_path)

        metadata = {
            "title": file_path.stem,
            "file_name": file_path.name,
        }

        # Handle text files
        if file_path.suffix.lower() in ['.txt', '.md']:
            text = file_path.read_text(encoding='utf-8')
            metadata["type"] = "text"
            return {
                "text": text.strip(),
                "metadata": metadata
            }

        # Handle PDF files
        if file_path.suffix.lower() == '.pdf':
            reader = PdfReader(str(file_path))
            metadata["num_pages"] = len(reader.pages)
            metadata["type"] = "pdf"

            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author

            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            return {
                "text": text.strip(),
                "metadata": metadata
            }

        raise ValueError(f"Unsupported file type: {file_path.suffix}")

# Backward compatibility alias
PDFExtractor = DocumentExtractor
