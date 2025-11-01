"""Test PRP-007: Memory search with semantic vector embeddings and specialized retrieval tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.memory import Category, Memory
from services.memory_service import MemoryService
from tools.tool_executor import ToolExecutor


class TestMemoryServicePRP007:
    """Test memory service semantic search and specialized retrieval tools."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def memory_service(self, mock_session):
        """Create memory service instance."""
        return MemoryService(mock_session)

    @pytest.fixture
    def sample_memory(self):
        """Create sample memory for testing."""
        memory = Memory()
        memory.id = 1
        memory.simple_content = "Vasilisa is a kind person who loves programming"
        memory.full_content = "Vasilisa is a very kind person who enjoys programming and helping others learn Python"
        memory.importance = 850
        memory.created_by = 123456789
        memory.emotion_label = "joy"
        memory.embedding = json.dumps(
            [0.1, 0.2, 0.3] * 128
        )  # 384-dimensional mock embedding as JSON string
        memory.categories = []
        return memory

    @pytest.fixture
    def sample_category(self):
        """Create sample category for testing."""
        category = Category()
        category.id = 1
        category.name = "person"
        category.domain = "social"
        category.full_path = "social.person"
        return category

    @pytest.mark.asyncio
    async def test_create_embedding_with_model(self, memory_service):
        """Test embedding generation when model is available."""

        with patch("services.memory_service.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            # Mock numpy array with tolist method
            mock_array = MagicMock()
            mock_array.tolist.return_value = [0.1, 0.2, 0.3] * 128
            mock_model.encode.return_value = mock_array
            mock_get_model.return_value = mock_model

            result = await memory_service.create_embedding("test text")

            assert result == [0.1, 0.2, 0.3] * 128
            mock_model.encode.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_create_embedding_no_model(self, memory_service):
        """Test embedding generation when model is not available."""
        with patch("services.memory_service.get_embedding_model") as mock_get_model:
            mock_get_model.return_value = None

            result = await memory_service.create_embedding("test text")

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_and_store_embedding_success(
        self, memory_service, sample_memory
    ):
        """Test successful embedding generation and storage."""
        with patch.object(memory_service, "create_embedding") as mock_create_embedding:
            mock_create_embedding.return_value = [0.1, 0.2, 0.3] * 128

            # Mock database query
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_memory
            memory_service.session.execute.return_value = mock_result

            with patch.object(memory_service, "_invalidate_cache") as mock_invalidate:
                await memory_service._generate_and_store_embedding(1, "test content")

                # Verify embedding was stored as JSON string
                assert json.loads(sample_memory.embedding) == [0.1, 0.2, 0.3] * 128

                mock_invalidate.assert_called_once_with(123456789)

    @pytest.mark.asyncio
    async def test_semantic_search_fallback_behavior(self, memory_service):
        """Test semantic search fallback behavior."""
        with patch("services.memory_service.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            with patch.object(
                memory_service, "_fallback_semantic_search"
            ) as mock_fallback:
                mock_fallback.return_value = []

                result = await memory_service.semantic_search(
                    query="test query",
                    user_id=123456789,
                    categories=["social.person"],
                    min_importance=500,
                    limit=10,
                )

                # Should call fallback search
                mock_fallback.assert_called_once_with(
                    "test query", 123456789, ["social.person"], 500, 10
                )
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_semantic_search_fallback(self, memory_service):
        """Test semantic search fallback when pgvector unavailable."""
        with (
            patch("services.memory_service.get_embedding_model") as mock_get_model,
            patch("models.memory.PGVECTOR_AVAILABLE", False),
        ):
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            with patch.object(
                memory_service, "_fallback_semantic_search"
            ) as mock_fallback:
                mock_fallback.return_value = []

                await memory_service.semantic_search(
                    query="test query", user_id=123456789
                )

                mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_friends(
        self, memory_service, sample_memory, sample_category
    ):
        """Test getting all friend memories."""
        sample_memory.categories = [sample_category]

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_memory]
        memory_service.session.execute.return_value = mock_result

        result = await memory_service.get_all_friends(user_id=123456789)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Vasilisa"  # Extracted from simple_content
        assert (
            "summary" in result[0]
        )  # get_all_friends returns "summary" not "simple_content"

    @pytest.mark.asyncio
    async def test_get_panic_attacks(
        self, memory_service, sample_memory, sample_category
    ):
        """Test getting panic attack memories."""
        sample_memory.simple_content = "Panic attack during meeting"
        sample_memory.categories = [sample_category]
        sample_category.full_path = "self.emotion"

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_memory]
        memory_service.session.execute.return_value = mock_result

        result = await memory_service.get_panic_attacks(user_id=123456789)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert "summary" in result[0]
        assert "date" in result[0]

    @pytest.mark.asyncio
    async def test_get_interests(self, memory_service, sample_memory, sample_category):
        """Test getting interest memories."""
        sample_memory.simple_content = "interest: programming in Python"
        sample_memory.categories = [sample_category]
        sample_category.full_path = "interest"

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_memory]
        memory_service.session.execute.return_value = mock_result

        result = await memory_service.get_interests(user_id=123456789)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert "programming in Python" in result[0]["interest"]

    @pytest.mark.asyncio
    async def test_search_by_person(self, memory_service):
        """Test searching memories by person name."""
        with patch.object(memory_service, "semantic_search") as mock_semantic:
            mock_semantic.return_value = [
                {
                    "id": 1,
                    "simple_content": "Memory about Vasilisa",
                    "importance": 850,
                    "categories": ["social.person"],
                    "emotion_label": "joy",
                }
            ]

            result = await memory_service.search_by_person(
                user_id=123456789, person_name="Vasilisa"
            )

            assert len(result) == 1
            mock_semantic.assert_called_once_with(
                query="memories about Vasilisa", user_id=123456789, limit=50
            )

    @pytest.mark.asyncio
    async def test_search_by_emotion(self, memory_service):
        """Test searching memories by emotion."""
        with patch.object(memory_service, "semantic_search") as mock_semantic:
            mock_semantic.return_value = []

            await memory_service.search_by_emotion(user_id=123456789, emotion="happy")

            mock_semantic.assert_called_once_with(
                query="happy feeling emotion",
                user_id=123456789,
                categories=["self.emotion"],
                limit=20,
            )

    @pytest.mark.asyncio
    async def test_search_across_versions(self, memory_service):
        """Test searching across all memory versions."""
        with patch("services.memory_service.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            with (
                patch.object(
                    memory_service, "create_embedding"
                ) as mock_create_embedding,
                patch("models.memory.PGVECTOR_AVAILABLE", True),
                patch("models.memory.IS_SQLITE", False),
            ):
                mock_create_embedding.return_value = [0.1, 0.2, 0.3] * 128

                # Mock database query result
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                memory_service.session.execute.return_value = mock_result

                result = await memory_service.search_across_versions(
                    user_id=123456789, query="test query", limit=10
                )

                assert isinstance(result, list)

    def test_extract_person_name(self, memory_service):
        """Test person name extraction from content."""
        content = "name: Vasilisa\nShe is a programmer"
        result = memory_service._extract_person_name(content)
        assert result == "Vasilisa"

        # Test fallback
        content_no_name = "Vasilisa is a programmer"
        result = memory_service._extract_person_name(content_no_name)
        assert result == "Vasilisa"

        # Test unknown
        content_empty = "No name here"
        result = memory_service._extract_person_name(content_empty)
        assert result == "Unknown"

    def test_extract_interest_name(self, memory_service):
        """Test interest name extraction from content."""
        content = "interest: Programming in Python"
        result = memory_service._extract_interest_name(content)
        assert result == "Programming in Python"

        content_hobby = "hobby: Painting landscapes"
        result = memory_service._extract_interest_name(content_hobby)
        assert result == "Painting landscapes"

        # Test fallback
        content_fallback = "I enjoy programming very much"
        result = memory_service._extract_interest_name(content_fallback)
        assert result == "I enjoy programming very much"


class TestToolExecutorPRP007:
    """Test tool executor semantic search and specialized retrieval tools."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def tool_executor(self, mock_session):
        """Create tool executor instance."""
        return ToolExecutor(mock_session)

    @pytest.mark.asyncio
    async def test_execute_semantic_search(self, tool_executor):
        """Execute semantic_search tool."""
        with patch.object(
            tool_executor.memory_service, "semantic_search"
        ) as mock_search:
            mock_search.return_value = [
                {
                    "id": 1,
                    "simple_content": "Test memory",
                    "importance": 850,
                    "categories": ["social.person"],
                    "emotion_label": "joy",
                }
            ]

            result = await tool_executor.execute(
                tool_name="semantic_search",
                arguments={"query": "test query", "limit": 5},
                user_id=123456789,
            )

            assert result["success"] is True
            assert result["count"] == 1
            assert len(result["memories"]) == 1
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_semantic_search_no_query(self, tool_executor):
        """Execute semantic_search tool without query."""
        result = await tool_executor.execute(
            tool_name="semantic_search", arguments={}, user_id=123456789
        )

        assert result["success"] is False
        assert "Query is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_get_all_friends(self, tool_executor):
        """Execute get_all_friends tool."""
        with patch.object(
            tool_executor.memory_service, "get_all_friends"
        ) as mock_friends:
            mock_friends.return_value = [
                {
                    "id": 1,
                    "name": "Vasilisa",
                    "summary": "Kind person who loves programming",
                    "importance": 850,
                }
            ]

            result = await tool_executor.execute(
                tool_name="get_all_friends", arguments={}, user_id=123456789
            )

            assert result["success"] is True
            assert result["count"] == 1
            assert len(result["friends"]) == 1
            mock_friends.assert_called_once_with(user_id=123456789)

    @pytest.mark.asyncio
    async def test_execute_get_panic_attacks(self, tool_executor):
        """Execute get_panic_attacks tool."""
        with patch.object(
            tool_executor.memory_service, "get_panic_attacks"
        ) as mock_panic:
            mock_panic.return_value = []

            result = await tool_executor.execute(
                tool_name="get_panic_attacks", arguments={}, user_id=123456789
            )

            assert result["success"] is True
            assert result["count"] == 0
            assert len(result["panic_attacks"]) == 0
            mock_panic.assert_called_once_with(user_id=123456789)

    @pytest.mark.asyncio
    async def test_execute_get_interests(self, tool_executor):
        """Execute get_interests tool."""
        with patch.object(
            tool_executor.memory_service, "get_interests"
        ) as mock_interests:
            mock_interests.return_value = [
                {
                    "id": 1,
                    "interest": "Programming",
                    "summary": "Love coding in Python",
                    "importance": 900,
                }
            ]

            result = await tool_executor.execute(
                tool_name="get_interests", arguments={}, user_id=123456789
            )

            assert result["success"] is True
            assert result["count"] == 1
            assert len(result["interests"]) == 1
            mock_interests.assert_called_once_with(user_id=123456789)

    @pytest.mark.asyncio
    async def test_execute_search_by_person(self, tool_executor):
        """Execute search_by_person tool."""
        with patch.object(
            tool_executor.memory_service, "search_by_person"
        ) as mock_search:
            mock_search.return_value = [
                {"id": 1, "simple_content": "Memory about Vasilisa", "importance": 850}
            ]

            result = await tool_executor.execute(
                tool_name="search_by_person",
                arguments={"person_name": "Vasilisa"},
                user_id=123456789,
            )

            assert result["success"] is True
            assert result["person_name"] == "Vasilisa"
            assert result["count"] == 1
            mock_search.assert_called_once_with(
                user_id=123456789, person_name="Vasilisa"
            )

    @pytest.mark.asyncio
    async def test_execute_search_by_person_no_name(self, tool_executor):
        """Execute search_by_person tool without person_name."""
        result = await tool_executor.execute(
            tool_name="search_by_person", arguments={}, user_id=123456789
        )

        assert result["success"] is False
        assert "person_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_search_by_emotion(self, tool_executor):
        """Execute search_by_emotion tool."""
        with patch.object(
            tool_executor.memory_service, "search_by_emotion"
        ) as mock_search:
            mock_search.return_value = []

            result = await tool_executor.execute(
                tool_name="search_by_emotion",
                arguments={"emotion": "happy"},
                user_id=123456789,
            )

            assert result["success"] is True
            assert result["emotion"] == "happy"
            assert result["count"] == 0
            mock_search.assert_called_once_with(user_id=123456789, emotion="happy")

    @pytest.mark.asyncio
    async def test_execute_search_across_versions(self, tool_executor):
        """Execute search_across_versions tool."""
        with patch.object(
            tool_executor.memory_service, "search_across_versions"
        ) as mock_search:
            mock_search.return_value = [
                {
                    "id": 1,
                    "version": 2,
                    "simple_content": "Updated memory",
                    "importance": 900,
                }
            ]

            result = await tool_executor.execute(
                tool_name="search_across_versions",
                arguments={"query": "test query", "limit": 15},
                user_id=123456789,
            )

            assert result["success"] is True
            assert result["query"] == "test query"
            assert result["count"] == 1
            mock_search.assert_called_once_with(
                user_id=123456789, query="test query", limit=15
            )

    @pytest.mark.asyncio
    async def test_execute_search_across_versions_no_query(self, tool_executor):
        """Execute search_across_versions tool without query."""
        result = await tool_executor.execute(
            tool_name="search_across_versions", arguments={}, user_id=123456789
        )

        assert result["success"] is False
        assert "query is required" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
