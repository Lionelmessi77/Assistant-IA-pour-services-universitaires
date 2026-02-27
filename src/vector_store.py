"""Vector store module using Qdrant and OpenAI embeddings."""
from typing import List, Dict, Optional
from openai import OpenAI
from .config import Config

# Try to use Qdrant SDK, fallback to REST API
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, QueryVector
    USE_SDK = True
except Exception:
    USE_SDK = False
    print("Qdrant SDK not available, using REST API")


class VectorStore:
    """Manage document embeddings in Qdrant."""

    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the Qdrant collection
        """
        self.collection_name = collection_name or Config.QDRANT_COLLECTION_NAME
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Try SDK first, fallback to REST
        if USE_SDK:
            try:
                if Config.QDRANT_API_KEY:
                    self.client = QdrantClient(
                        url=Config.QDRANT_URL,
                        api_key=Config.QDRANT_API_KEY,
                        prefer_grpc=False
                    )
                else:
                    self.client = QdrantClient(url=Config.QDRANT_URL)
                self.use_rest = False
            except Exception as e:
                print(f"SDK init failed, using REST: {e}")
                self.use_rest = True
        else:
            self.use_rest = True

        if self.use_rest:
            # Import REST client
            from .qdrant_rest import QdrantRESTClient
            self.rest_client = QdrantRESTClient()
            # Copy methods
            self.add_documents = self.rest_client.add_documents
            self.search = self.rest_client.search
            self.get_collection_info = self.rest_client.get_collection_info
            self.clear_collection = self.rest_client.clear_collection
            return

        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self._get_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"Error ensuring collection: {e}")
            raise

    def _get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model."""
        model = Config.EMBEDDING_MODEL
        if "3-small" in model or "ada-002" in model:
            return 1536
        elif "3-large" in model:
            return 3072
        return 1536

    def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        response = self.openai_client.embeddings.create(
            model=Config.EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]

    def add_documents(self, texts: List[str], metadatas: List[Dict]) -> int:
        """
        Add documents to the vector store.

        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries

        Returns:
            Number of documents added
        """
        if not texts:
            return 0

        # Create embeddings
        print(f"Creating embeddings for {len(texts)} chunks...")
        embeddings = self._create_embeddings(texts)

        # Get current offset
        try:
            collection_info = self.client.get_collection(self.collection_name)
            offset = collection_info.points_count if collection_info.points_count else 0
        except:
            offset = 0

        # Create points
        points = [
            PointStruct(
                id=offset + i,
                vector=embedding,
                payload={**metadatas[i], "text": texts[i]}
            )
            for i, embedding in enumerate(embeddings)
        ]

        # Upload points
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"Added {len(points)} documents to collection")
        return len(points)

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for similar documents.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching documents with scores
        """
        # Create query embedding
        query_embedding = self._create_embeddings([query])[0]

        # Use query_points for newer Qdrant client
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=0.5
            )

            return [
                {
                    "text": hit.payload.get("text", "") if hit.payload else "",
                    "metadata": {k: v for k, v in (hit.payload or {}).items() if k != "text"},
                    "score": hit.score
                }
                for hit in results.points
            ]
        except AttributeError:
            # Fallback to older API
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.5
            )

            return [
                {
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                    "score": hit.score
                }
                for hit in results
            ]

    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "vector_size": info.config.params.vectors.size
        }

    def clear_collection(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()
        print(f"Cleared collection: {self.collection_name}")
