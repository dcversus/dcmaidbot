"""
Comprehensive Tests for RAGService
==================================

Test suite for RAG (Retrieval-Augmented Generation) service functionality.
Covers document management, search operations, error handling, and edge cases.
"""

import asyncio
import os

# Import the service we're testing
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.services.rag_service import RAGService, get_rag_service


class TestRAGService:
    """Test suite for RAGService functionality."""

    @pytest.fixture
    def rag_service(self):
        """Create a fresh RAGService instance for each test."""
        return RAGService()

    @pytest.fixture
    def mock_chromadb(self):
        """Mock ChromaDB for testing without actual DB."""
        with patch("services.rag_service.chromadb") as mock_chroma:
            # Mock client
            mock_client = Mock()
            mock_chroma.Client.return_value = mock_client

            # Mock collection
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            # Setup mock responses
            mock_collection.get.return_value = {"ids": []}

            yield mock_chroma, mock_client, mock_collection

    @pytest.mark.asyncio
    async def test_initialization_with_chromadb(self, rag_service, mock_chromadb):
        """Test successful initialization with ChromaDB available."""
        mock_chroma, mock_client, mock_collection = mock_chromadb

        await rag_service.initialize()

        assert rag_service.initialized is True
        assert rag_service.client is mock_client
        assert rag_service.collection is mock_collection
        mock_client.get_or_create_collection.assert_called_once_with(
            name="documents", metadata={"hnsw:space": "cosine"}
        )

    @pytest.mark.asyncio
    async def test_initialization_without_chromadb(self, rag_service):
        """Test initialization fallback when ChromaDB not available."""
        with patch("services.rag_service.chromadb", None):
            await rag_service.initialize()

            assert rag_service.initialized is True
            assert rag_service.client is None
            assert rag_service.collection is None

    @pytest.mark.asyncio
    async def test_initialization_error_handling(self, rag_service):
        """Test graceful handling of initialization errors."""
        with patch("services.rag_service.chromadb") as mock_chroma:
            mock_client = Mock()
            mock_chroma.Client.return_value = mock_client
            mock_client.get_or_create_collection.side_effect = Exception("DB Error")

            await rag_service.initialize()

            assert rag_service.initialized is False

    @pytest.mark.asyncio
    async def test_add_document_success(self, rag_service, mock_chromadb):
        """Test successful document addition."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        result = await rag_service.add_document(
            doc_id="test_doc_1",
            content="This is a test document",
            metadata={"source": "test", "version": 1},
        )

        assert result is True
        mock_collection.add.assert_called_once_with(
            documents=["This is a test document"],
            ids=["test_doc_1"],
            metadatas=[{"source": "test", "version": 1}],
        )

    @pytest.mark.asyncio
    async def test_add_document_without_metadata(self, rag_service, mock_chromadb):
        """Test adding document without metadata."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        result = await rag_service.add_document(
            doc_id="test_doc_2", content="Document without metadata"
        )

        assert result is True
        mock_collection.add.assert_called_once_with(
            documents=["Document without metadata"], ids=["test_doc_2"], metadatas=[{}]
        )

    @pytest.mark.asyncio
    async def test_add_document_uninitialized(self, rag_service, mock_chromadb):
        """Test adding document when service not initialized."""
        mock_chroma, mock_client, mock_collection = mock_chromadb

        result = await rag_service.add_document("test_doc", "content")

        assert result is True
        assert rag_service.initialized is True

    @pytest.mark.asyncio
    async def test_add_document_failure(self, rag_service, mock_chromadb):
        """Test handling of document addition failures."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()
        mock_collection.add.side_effect = Exception("Add failed")

        result = await rag_service.add_document("test_doc", "content")

        assert result is False

    @pytest.mark.asyncio
    async def test_add_document_no_collection(self, rag_service):
        """Test adding document when collection not available."""
        with patch("services.rag_service.chromadb", None):
            await rag_service.initialize()

            result = await rag_service.add_document("test_doc", "content")

            assert result is False

    @pytest.mark.asyncio
    async def test_search_success(self, rag_service, mock_chromadb):
        """Test successful document search."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Mock search results
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
            "distances": [[0.1, 0.3]],
        }

        results = await rag_service.search("test query", n_results=2)

        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[0]["content"] == "Content 1"
        assert results[0]["metadata"] == {"source": "test1"}
        assert results[0]["distance"] == 0.1

        mock_collection.query.assert_called_once_with(
            query_texts=["test query"], n_results=2
        )

    @pytest.mark.asyncio
    async def test_search_no_distances(self, rag_service, mock_chromadb):
        """Test search when distances not returned."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Content 1"]],
            "metadatas": [[{"source": "test"}]],
        }

        results = await rag_service.search("test query")

        assert len(results) == 1
        assert results[0]["distance"] == 0.0

    @pytest.mark.asyncio
    async def test_search_no_metadatas(self, rag_service, mock_chromadb):
        """Test search when metadatas not returned."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Content 1"]],
            "metadatas": None,
        }

        results = await rag_service.search("test query")

        assert len(results) == 1
        assert results[0]["metadata"] == {}

    @pytest.mark.asyncio
    async def test_search_uninitialized(self, rag_service, mock_chromadb):
        """Test search when service not initialized."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Content 1"]],
            "metadatas": [[{}]],
            "distances": [[0.1]],
        }

        results = await rag_service.search("test query")

        assert len(results) == 1
        assert rag_service.initialized is True

    @pytest.mark.asyncio
    async def test_search_no_collection(self, rag_service):
        """Test search when collection not available."""
        with patch("services.rag_service.chromadb", None):
            await rag_service.initialize()

            results = await rag_service.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_error_handling(self, rag_service, mock_chromadb):
        """Test handling of search errors."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()
        mock_collection.query.side_effect = Exception("Search failed")

        results = await rag_service.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_delete_document_success(self, rag_service, mock_chromadb):
        """Test successful document deletion."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        result = await rag_service.delete_document("test_doc")

        assert result is True
        mock_collection.delete.assert_called_once_with(ids=["test_doc"])

    @pytest.mark.asyncio
    async def test_delete_document_no_collection(self, rag_service):
        """Test deletion when collection not available."""
        result = await rag_service.delete_document("test_doc")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_document_error(self, rag_service, mock_chromadb):
        """Test handling of deletion errors."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()
        mock_collection.delete.side_effect = Exception("Delete failed")

        result = await rag_service.delete_document("test_doc")

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, rag_service, mock_chromadb):
        """Test health check when service is healthy."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()
        mock_collection.get.return_value = {"ids": ["doc1", "doc2"]}

        health = await rag_service.health_check()

        assert health["status"] == "healthy"
        assert health["chromadb_available"] is True
        assert health["collection_exists"] is True
        assert health["document_count"] == 2

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, rag_service):
        """Test health check when service is unhealthy."""
        health = await rag_service.health_check()

        assert health["status"] == "unhealthy"
        assert health["chromadb_available"] is False
        assert health["collection_exists"] is False
        assert health["document_count"] == 0

    @pytest.mark.asyncio
    async def test_health_check_no_chromadb(self, rag_service):
        """Test health check when ChromaDB not available."""
        with patch("services.rag_service.chromadb", None):
            await rag_service.initialize()

            health = await rag_service.health_check()

            assert health["status"] == "healthy"
            assert health["chromadb_available"] is False
            assert health["collection_exists"] is False
            assert health["document_count"] == 0

    def test_singleton_pattern(self):
        """Test that get_rag_service returns singleton instance."""

        async def test_singleton():
            service1 = await get_rag_service()
            service2 = await get_rag_service()

            assert service1 is service2
            assert isinstance(service1, RAGService)

        asyncio.run(test_singleton())

    @pytest.mark.asyncio
    async def test_large_document_handling(self, rag_service, mock_chromadb):
        """Test handling of large documents."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Create a large document (1MB+)
        large_content = "test " * 50000  # ~500KB

        result = await rag_service.add_document("large_doc", large_content)

        assert result is True
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self, rag_service, mock_chromadb):
        """Test handling of special characters in document content."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        special_content = "Special chars: ñáéíóú 🎀 💕 \n\t\"'\\"

        result = await rag_service.add_document("special_doc", special_content)

        assert result is True

    @pytest.mark.asyncio
    async def test_unicode_document_ids(self, rag_service, mock_chromadb):
        """Test handling of Unicode characters in document IDs."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        result = await rag_service.add_document("文档_1", "Unicode content")

        assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, rag_service, mock_chromadb):
        """Test concurrent document operations."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Create multiple concurrent operations
        tasks = []
        for i in range(10):
            task = rag_service.add_document(f"doc_{i}", f"Content {i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(results)
        assert mock_collection.add.call_count == 10

    @pytest.mark.asyncio
    async def test_search_with_different_result_counts(
        self, rag_service, mock_chromadb
    ):
        """Test search with different n_results values."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [["Content 1", "Content 2", "Content 3"]],
            "metadatas": [[{}, {}, {}]],
            "distances": [[0.1, 0.2, 0.3]],
        }

        # Test with n_results=1
        results = await rag_service.search("query", n_results=1)
        assert len(results) == 1

        # Test with n_results=10 (more than available)
        results = await rag_service.search("query", n_results=10)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_empty_search_query(self, rag_service, mock_chromadb):
        """Test search with empty query."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        results = await rag_service.search("", n_results=5)

        assert results == []

    @pytest.mark.asyncio
    async def test_metadata_preservation(self, rag_service, mock_chromadb):
        """Test that metadata is properly preserved and returned."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Add document with complex metadata
        metadata = {
            "source": "test",
            "version": 1,
            "tags": ["tag1", "tag2"],
            "nested": {"key": "value"},
        }

        await rag_service.add_document("meta_doc", "content", metadata)

        # Mock search to return the metadata
        mock_collection.query.return_value = {
            "ids": [["meta_doc"]],
            "documents": [["content"]],
            "metadatas": [[metadata]],
            "distances": [[0.1]],
        }

        results = await rag_service.search("query")

        assert results[0]["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_performance_search_speed(self, rag_service, mock_chromadb):
        """Test that search operations complete within reasonable time."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["content"]],
            "metadatas": [[{}]],
            "distances": [[0.1]],
        }

        import time

        start_time = time.time()

        await rag_service.search("test query")

        elapsed_time = time.time() - start_time

        # Search should complete in under 100ms (even with mock overhead)
        assert elapsed_time < 0.1

    @pytest.mark.asyncio
    async def test_service_idempotency(self, rag_service, mock_chromadb):
        """Test that initializing multiple times doesn't cause issues."""
        mock_chroma, mock_client, mock_collection = mock_chromadb

        # Initialize multiple times
        await rag_service.initialize()
        await rag_service.initialize()
        await rag_service.initialize()

        # Should still work properly
        assert rag_service.initialized is True
        assert rag_service.client is mock_client
        assert rag_service.collection is mock_collection

    @pytest.mark.asyncio
    async def test_null_values_handling(self, rag_service, mock_chromadb):
        """Test handling of None values in parameters."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Test with None metadata
        result = await rag_service.add_document("doc", "content", None)
        assert result is True

        # Test search with None query (should handle gracefully)
        try:
            results = await rag_service.search(None)
            # Should either return empty list or handle gracefully
            assert isinstance(results, list)
        except AttributeError:
            # Raised when trying to call .lower() on None - acceptable
            pass


class TestRAGServiceIntegration:
    """Integration tests for RAGService with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_document_lifecycle(self, rag_service, mock_chromadb):
        """Test complete document lifecycle: add, search, delete."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Add document
        add_result = await rag_service.add_document(
            "lifecycle_doc",
            "This is a document about the lifecycle test",
            {"category": "test", "priority": "high"},
        )
        assert add_result is True

        # Search for document
        mock_collection.query.return_value = {
            "ids": [["lifecycle_doc"]],
            "documents": [["This is a document about the lifecycle test"]],
            "metadatas": [[{"category": "test", "priority": "high"}]],
            "distances": [[0.05]],
        }

        search_results = await rag_service.search("lifecycle test")
        assert len(search_results) == 1
        assert search_results[0]["id"] == "lifecycle_doc"

        # Delete document
        delete_result = await rag_service.delete_document("lifecycle_doc")
        assert delete_result is True

    @pytest.mark.asyncio
    async def test_batch_operations_simulation(self, rag_service, mock_chromadb):
        """Test simulating batch document operations."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Add multiple documents
        documents = [
            ("doc1", "First document content", {"type": "article"}),
            ("doc2", "Second document content", {"type": "blog"}),
            ("doc3", "Third document content", {"type": "news"}),
        ]

        for doc_id, content, metadata in documents:
            result = await rag_service.add_document(doc_id, content, metadata)
            assert result is True

        # Verify all documents were added
        assert mock_collection.add.call_count == 3

        # Search and get multiple results
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc3"]],
            "documents": [["First document content", "Third document content"]],
            "metadatas": [[{"type": "article"}, {"type": "news"}]],
            "distances": [[0.1, 0.2]],
        }

        results = await rag_service.search("document", n_results=5)
        assert len(results) == 2
        assert results[0]["metadata"]["type"] == "article"
        assert results[1]["metadata"]["type"] == "news"

    @pytest.mark.asyncio
    async def test_error_recovery(self, rag_service, mock_chromadb):
        """Test service recovery from errors."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Simulate error on add
        mock_collection.add.side_effect = Exception("Temporary error")

        add_result = await rag_service.add_document("error_doc", "content")
        assert add_result is False

        # Reset error
        mock_collection.add.side_effect = None

        # Should work again
        add_result = await rag_service.add_document("recovery_doc", "content")
        assert add_result is True

    @pytest.mark.asyncio
    async def test_memory_usage_simulation(self, rag_service, mock_chromadb):
        """Test service behavior with memory constraints (simulated)."""
        mock_chroma, mock_client, mock_collection = mock_chromadb
        await rag_service.initialize()

        # Simulate large number of documents
        for i in range(100):
            await rag_service.add_document(f"doc_{i}", f"Content for document {i}")

        # Verify service still responds correctly
        health = await rag_service.health_check()
        assert health["status"] == "healthy"

        # Search should still work
        mock_collection.query.return_value = {
            "ids": [["doc_50"]],
            "documents": [["Content for document 50"]],
            "metadatas": [[{}]],
            "distances": [[0.1]],
        }

        results = await rag_service.search("document 50")
        assert len(results) == 1
