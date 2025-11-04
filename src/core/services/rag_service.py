"""
RAG Service Implementation
=========================

Retrieval-Augmented Generation service for document-based responses.
Implements PRP-006 RAG System functionality.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for document search and responses."""

    def __init__(self):
        """Initialize RAG service with ChromaDB."""
        self.client = None
        self.collection = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        if not chromadb:
            logger.warning("ChromaDB not available, RAG service running in mock mode")
            self.initialized = True
            return

        try:
            # Initialize ChromaDB client
            self.client = chromadb.Client(
                Settings(persist_directory="./data/chroma", anonymized_telemetry=False)
            )

            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name="documents", metadata={"hnsw:space": "cosine"}
            )

            self.initialized = True
            logger.info("RAG service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            self.initialized = False

    async def add_document(
        self, doc_id: str, content: str, metadata: Optional[Dict] = None
    ) -> bool:
        """Add a document to the RAG collection.

        Args:
            doc_id: Document identifier
            content: Document content
            metadata: Optional document metadata

        Returns:
            True if document added successfully
        """
        if not self.initialized:
            await self.initialize()

        if not self.collection:
            logger.warning("RAG collection not available")
            return False

        try:
            # Add document to collection
            self.collection.add(
                documents=[content], ids=[doc_id], metadatas=[metadata or {}]
            )

            logger.info(f"Added document {doc_id} to RAG collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            return False

    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of search results with documents and metadata
        """
        if not self.initialized:
            await self.initialize()

        if not self.collection:
            logger.warning("RAG collection not available")
            return []

        try:
            # Query collection
            results = self.collection.query(query_texts=[query], n_results=n_results)

            # Format results
            formatted_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if "distances" in results
                        else 0.0,
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search RAG collection: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the collection.

        Args:
            doc_id: Document identifier

        Returns:
            True if document deleted successfully
        """
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id} from RAG collection")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check RAG service health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.initialized else "unhealthy",
            "chromadb_available": chromadb is not None,
            "collection_exists": self.collection is not None,
            "document_count": len(self.collection.get()["ids"])
            if self.collection
            else 0,
        }


# Singleton instance
_rag_service = None


async def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
        await _rag_service.initialize()
    return _rag_service
