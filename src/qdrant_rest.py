"""Qdrant REST API client - bypasses numpy dependency issues."""
import os
import requests
from typing import List, Dict, Optional
from .config import Config


class QdrantRESTClient:
    """Qdrant client using REST API instead of Python SDK."""

    def __init__(self):
        self.url = Config.QDRANT_URL
        self.api_key = Config.QDRANT_API_KEY
        self.collection_name = Config.QDRANT_COLLECTION_NAME
        self.openai_key = Config.OPENAI_API_KEY
        self.embedding_model = Config.EMBEDDING_MODEL

        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["api-key"] = self.api_key

        self._ensure_collection()

    def _get(self, endpoint: str) -> dict:
        """Make a GET request."""
        response = requests.get(f"{self.url}/{endpoint}", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request."""
        response = requests.post(f"{self.url}/{endpoint}", json=data, headers=self.headers, timeout=60)
        response.raise_for_status()
        return response.json()

    def _put(self, endpoint: str, data: dict) -> dict:
        """Make a PUT request."""
        response = requests.put(f"{self.url}/{endpoint}", json=data, headers=self.headers, timeout=60)
        response.raise_for_status()
        return response.json()

    def _delete(self, endpoint: str) -> dict:
        """Make a DELETE request."""
        response = requests.delete(f"{self.url}/{endpoint}", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self._get("collections")
            names = [c["name"] for c in collections.get("result", {}).get("collections", [])]

            if self.collection_name not in names:
                self._put(f"collections/{self.collection_name}", {
                    "vectors": {
                        "size": self._get_embedding_dim(),
                        "distance": "Cosine"
                    }
                })
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"Error ensuring collection: {e}")

    def _get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        model = self.embedding_model
        if "3-small" in model or "ada-002" in model:
            return 1536
        elif "3-large" in model:
            return 3072
        return 1536

    def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI REST API."""
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.embedding_model,
            "input": texts
        }

        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            json=data,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        return [item["embedding"] for item in result["data"]]

    def add_documents(self, texts: List[str], metadatas: List[Dict]) -> int:
        """Add documents to collection."""
        if not texts:
            return 0

        print(f"Creating embeddings for {len(texts)} chunks...")
        embeddings = self._create_embeddings(texts)

        # Get current count
        try:
            info = self._get(f"collections/{self.collection_name}")
            offset = info["result"]["points_count"]
        except:
            offset = 0

        # Create points
        points = []
        for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadatas)):
            points.append({
                "id": offset + i,
                "vector": embedding,
                "payload": {**meta, "text": text}
            })

        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self._put(f"collections/{self.collection_name}/points", {"points": batch})

        print(f"Added {len(points)} documents to collection")
        return len(points)

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents."""
        query_embedding = self._create_embeddings([query])[0]

        result = self._post(f"collections/{self.collection_name}/points/query", {
            "query": query_embedding,
            "limit": limit,
            "with_payload": True
        })

        results = []
        # Response format: {"result": {"points": [...]}}
        points_data = result.get("result", {}).get("points", result.get("result", []))

        for point in points_data:
            payload = point.get("payload", {}) if isinstance(point, dict) else {}

            results.append({
                "text": payload.get("text", ""),
                "metadata": {k: v for k, v in payload.items() if k != "text"},
                "score": point.get("score", 0)
            })

        return results

    def get_collection_info(self) -> Dict:
        """Get collection info."""
        result = self._get(f"collections/{self.collection_name}")
        info = result.get("result", {})
        return {
            "name": self.collection_name,
            "points_count": info.get("points_count", 0),
            "vector_size": info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 0)
        }

    def clear_collection(self):
        """Delete collection and recreate."""
        try:
            self._delete(f"collections/{self.collection_name}")
        except:
            pass
        self._ensure_collection()
        print(f"Cleared collection: {self.collection_name}")


# Alias for compatibility
VectorStore = QdrantRESTClient
