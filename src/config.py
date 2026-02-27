"""Configuration management for UniHelp."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Qdrant
    QDRANT_URL = os.getenv("QDRANT_URL", "localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "university_docs")

    # Remove port from URL for cloud Qdrant if present in URL format
    if "://qdrant.io:" in QDRANT_URL or "://gcp.cloud.qdrant.io:" in QDRANT_URL:
        # Cloud URL already has port embedded
        pass

    # Chunking
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50

    # App
    APP_TITLE = os.getenv("APP_TITLE", "UniHelp - Assistant Universitaire")

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in .env file")
        return True
