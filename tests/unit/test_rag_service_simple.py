"""
Simple Working Tests for RAGService
===================================

Test suite for RAGService functionality that works with the actual implementation.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.services.rag_service import RAGService, get_rag_service


class TestRAGServiceSimple:
    """Simple test suite for RAGService functionality."""

    @pytest.fixture
    def rag_service(self):
        """Create a fresh RAGService instance."""
        return RAGService()

    def test_initialization(self, rag_service):
        """Test service initialization."""
        assert rag_service.client is None
        assert rag_service.collection is None
        assert rag_service.initialized is False

    @patch("services.rag_service.chromadb", None)
    @pytest.mark.asyncio
    async def test_initialization_without_chromadb(self, rag_service):
        """Test initialization when ChromaDB not available."""
        await rag_service.initialize()
        assert rag_service.initialized is True
        assert rag_service.client is None
        assert rag_service.collection is None

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_initialization_with_chromadb(self, rag_service, mock_chromadb):
        """Test initialization with ChromaDB available."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()

        assert rag_service.initialized is True
        assert rag_service.client is mock_client
        assert rag_service.collection is mock_collection

    @patch("services.rag_service.chromadb", None)
    @pytest.mark.asyncio
    async def test_add_document_no_chromadb(self, rag_service):
        """Test adding document when ChromaDB not available."""
        await rag_service.initialize()  # Initialize without ChromaDB

        result = await rag_service.add_document("test_doc", "test content")

        assert result is False

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_add_document_success(self, rag_service, mock_chromadb):
        """Test successfully adding document."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        result = await rag_service.add_document(
            "test_doc", "test content", {"type": "test"}
        )

        assert result is True
        mock_collection.add.assert_called_once_with(
            documents=["test content"], ids=["test_doc"], metadatas=[{"type": "test"}]
        )

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_add_document_failure(self, rag_service, mock_chromadb):
        """Test handling document addition failure."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.add.side_effect = Exception("Add failed")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        result = await rag_service.add_document("test_doc", "test content")

        assert result is False

    @patch("services.rag_service.chromadb", None)
    @pytest.mark.asyncio
    async def test_search_no_chromadb(self, rag_service):
        """Test searching when ChromaDB not available."""
        await rag_service.initialize()

        results = await rag_service.search("test query")

        assert results == []

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_search_success(self, rag_service, mock_chromadb):
        """Test successful search."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[{"type": "test"}, {"type": "test2"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        results = await rag_service.search("test query", n_results=5)

        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[0]["content"] == "Content 1"
        assert results[0]["metadata"] == {"type": "test"}
        assert results[0]["distance"] == 0.1

        mock_collection.query.assert_called_once_with(
            query_texts=["test query"], n_results=5
        )

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_search_no_distances(self, rag_service, mock_chromadb):
        """Test search when distances not returned."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Content 1"]],
            "metadatas": [[{"type": "test"}]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        results = await rag_service.search("test query")

        assert len(results) == 1
        assert results[0]["distance"] == 0.0

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_search_error(self, rag_service, mock_chromadb):
        """Test handling search errors."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query.side_effect = Exception("Search failed")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        results = await rag_service.search("test query")

        assert results == []

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_delete_document_success(self, rag_service, mock_chromadb):
        """Test successful document deletion."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        result = await rag_service.delete_document("test_doc")

        assert result is True
        mock_collection.delete.assert_called_once_with(ids=["test_doc"])

    def test_delete_document_no_collection(self, rag_service):
        """Test deleting document when collection not available."""
        result = rag_service.delete_document("test_doc")
        assert result is False

    @patch("services.rag_service.chromadb", None)
    @pytest.mark.asyncio
    async def test_health_check_no_chromadb(self, rag_service):
        """Test health check when ChromaDB not available."""
        await rag_service.initialize()

        health = await rag_service.health_check()

        assert health["status"] == "healthy"
        assert health["chromadb_available"] is False
        assert health["collection_exists"] is False
        assert health["document_count"] == 0

    @patch("services.rag_service.chromadb")
    @pytest.mark.asyncio
    async def test_health_check_with_chromadb(self, rag_service, mock_chromadb):
        """Test health check with ChromaDB available."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.get.return_value = {"ids": ["doc1", "doc2"]}
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client

        await rag_service.initialize()
        health = await rag_service.health_check()

        assert health["status"] == "healthy"
        assert health["chromadb_available"] is True
        assert health["collection_exists"] is True
        assert health["document_count"] == 2

    @pytest.mark.asyncio
    async def test_get_rag_service_singleton(self):
        """Test that get_rag_service returns singleton."""
        service1 = await get_rag_service()
        service2 = await get_rag_service()

        assert service1 is service2
        assert isinstance(service1, RAGService)
