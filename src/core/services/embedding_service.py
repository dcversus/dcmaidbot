"""Simple embedding service using native PostgreSQL JSON columns.

This service provides embedding functionality without requiring pgvector extension.
It stores embeddings as JSON arrays in PostgreSQL JSON/JSONB columns.
"""

import json
import logging
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Simple embedding service using JSON storage."""

    def __init__(self):
        """Initialize the embedding service."""
        # We can add different embedding models here
        # For now, we'll use simple placeholder logic
        self.embedding_dim = 384  # Default for sentence-transformers models

    def create_embedding(self, text: str) -> List[float]:
        """Create an embedding for the given text.

        Args:
            text: The text to embed

        Returns:
            A list of float values representing the embedding
        """
        # For now, return a simple hash-based embedding
        # In production, this would call an embedding API like OpenAI or a local model
        logger.debug(f"Creating embedding for text: {text[:50]}...")

        # Simple deterministic embedding based on text hash
        # This is just for demonstration - replace with real embeddings
        import hashlib

        # Create a deterministic "fake" embedding based on text
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        hash_bytes = hash_obj.digest()

        # Convert to float values between -1 and 1
        embedding = []
        for i in range(0, min(len(hash_bytes), self.embedding_dim)):
            val = hash_bytes[i] / 127.5 - 1.0  # Normalize to [-1, 1]
            embedding.append(float(val))

        # Pad or truncate to the right dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)

        return embedding[: self.embedding_dim]

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score between 0 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0

        # Convert to numpy arrays
        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def format_embedding_for_db(self, embedding: List[float]) -> str:
        """Format embedding for database storage.

        Args:
            embedding: The embedding to format

        Returns:
            JSON string representation of the embedding
        """
        return json.dumps(embedding)

    def parse_embedding_from_db(self, embedding_json: str) -> List[float]:
        """Parse embedding from database storage.

        Args:
            embedding_json: JSON string from database

        Returns:
            List of float values
        """
        if not embedding_json:
            return []

        try:
            return json.loads(embedding_json)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse embedding from JSON: {embedding_json}")
            return []

    def find_similar_memories(
        self,
        query_embedding: List[float],
        memory_embeddings: Dict[str, str],
        threshold: float = 0.5,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar memories based on embedding similarity.

        Args:
            query_embedding: The query embedding
            memory_embeddings: Dict of memory_id -> embedding_json
            threshold: Minimum similarity threshold
            limit: Maximum number of results

        Returns:
            List of similar memories with scores
        """
        results = []

        for memory_id, embedding_json in memory_embeddings.items():
            if not embedding_json:
                continue

            memory_embedding = self.parse_embedding_from_db(embedding_json)
            if not memory_embedding:
                continue

            similarity = self.calculate_similarity(query_embedding, memory_embedding)

            if similarity >= threshold:
                results.append(
                    {
                        "memory_id": memory_id,
                        "similarity": similarity,
                        "embedding": memory_embedding,
                    }
                )

        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    async def batch_create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            embedding = self.create_embedding(text)
            embeddings.append(embedding)

        return embeddings

    def update_embedding_dimension(self, new_dim: int):
        """Update the embedding dimension.

        Args:
            new_dim: New embedding dimension
        """
        self.embedding_dim = new_dim
        logger.info(f"Updated embedding dimension to {new_dim}")


# Global instance
embedding_service = EmbeddingService()
