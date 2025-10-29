"""E2E test for memory lifecycle with VAD emotions and Zettelkasten (PRP-005).

Tests the complete memory workflow:
1. Create memory with LLM-extracted VAD emotions
2. Create memory with LLM-generated Zettelkasten attributes
3. Create memory links using LLM suggestions
4. Search and retrieve memories
5. Update and delete memories
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.memory import Category
from services.memory_service import MemoryService
from services.llm_service import LLMService


@pytest.fixture
async def async_session():
    """Create async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_categories(async_session):
    """Create test categories."""
    categories = [
        Category(
            name="person",
            domain="social",
            full_path="social.person",
            description="Individual profiles",
            icon="👤",
            importance_range_min=100,
            importance_range_max=10000,
        ),
        Category(
            name="tech_domain",
            domain="knowledge",
            full_path="knowledge.tech_domain",
            description="Programming languages",
            icon="💻",
            importance_range_min=1000,
            importance_range_max=5000,
        ),
    ]

    for cat in categories:
        async_session.add(cat)
    await async_session.commit()

    return categories


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("services.llm_service.AsyncOpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_memory_lifecycle_with_vad_emotions(
    async_session, test_categories, mock_openai
):
    """
    E2E test: Create memory with VAD emotion extraction from LLM.
    """
    # Mock LLM response for VAD extraction
    mock_vad_response = MagicMock()
    mock_vad_choice = MagicMock()
    mock_vad_message = MagicMock()
    mock_vad_message.content = """{
        "valence": 0.8,
        "arousal": 0.6,
        "dominance": 0.5,
        "emotion_label": "joy"
    }"""
    mock_vad_choice.message = mock_vad_message
    mock_vad_response.choices = [mock_vad_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_vad_response)

    # Create LLM service with mocked client
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    # Extract VAD emotions from text
    text = "I absolutely love Python programming! It makes me so excited and happy!"
    vad_result = await llm_service.extract_vad_emotions(text)

    # Verify VAD extraction
    assert vad_result["valence"] == 0.8
    assert vad_result["arousal"] == 0.6
    assert vad_result["dominance"] == 0.5
    assert vad_result["emotion_label"] == "joy"

    # Create memory with extracted VAD emotions
    memory_service = MemoryService(async_session)
    memory = await memory_service.create_memory(
        simple_content="User loves Python programming",
        full_content=text,
        importance=5000,
        created_by=123456789,
        category_ids=[test_categories[1].id],
        emotion_valence=vad_result["valence"],
        emotion_arousal=vad_result["arousal"],
        emotion_dominance=vad_result["dominance"],
        emotion_label=vad_result["emotion_label"],
    )

    # Verify memory was created with VAD emotions
    assert memory.id is not None
    assert memory.emotion_valence == 0.8
    assert memory.emotion_arousal == 0.6
    assert memory.emotion_dominance == 0.5
    assert memory.emotion_label == "joy"

    # Retrieve memory and verify access tracking
    retrieved = await memory_service.get_memory(memory.id)
    assert retrieved is not None
    assert retrieved.access_count == 1
    assert retrieved.last_accessed is not None


@pytest.mark.asyncio
async def test_memory_lifecycle_with_zettelkasten(
    async_session, test_categories, mock_openai
):
    """
    E2E test: Create memory with Zettelkasten attributes from LLM.
    """
    # Mock LLM response for Zettelkasten generation
    mock_zk_response = MagicMock()
    mock_zk_choice = MagicMock()
    mock_zk_message = MagicMock()
    mock_zk_message.content = """{
        "keywords": ["python", "asyncio", "fastapi", "programming"],
        "tags": ["knowledge/python", "interest/tech_preference"],
        "context_temporal": "2025-10-29 discussion",
        "context_situational": "Chat about favorite programming languages"
    }"""
    mock_zk_choice.message = mock_zk_message
    mock_zk_response.choices = [mock_zk_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_zk_response)

    # Create LLM service with mocked client
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    # Generate Zettelkasten attributes
    text = (
        "I love Python for async programming with asyncio "
        "and building APIs with FastAPI"
    )
    zk_result = await llm_service.generate_zettelkasten_attributes(text)

    # Verify Zettelkasten generation
    assert "python" in zk_result["keywords"]
    assert "asyncio" in zk_result["keywords"]
    assert "knowledge/python" in zk_result["tags"]
    assert zk_result["context_temporal"] is not None
    assert zk_result["context_situational"] is not None

    # Create memory with Zettelkasten attributes
    memory_service = MemoryService(async_session)
    memory = await memory_service.create_memory(
        simple_content="User loves Python for async and APIs",
        full_content=text,
        importance=5000,
        created_by=123456789,
        category_ids=[test_categories[1].id],
        keywords=zk_result["keywords"],
        tags=zk_result["tags"],
        context_temporal=zk_result["context_temporal"],
        context_situational=zk_result["context_situational"],
    )

    # Verify memory was created with Zettelkasten attributes
    assert memory.id is not None
    assert len(memory.keywords) == 4
    assert "python" in memory.keywords
    assert len(memory.tags) == 2
    assert "knowledge/python" in memory.tags
    assert memory.context_temporal is not None
    assert memory.context_situational is not None


@pytest.mark.asyncio
async def test_memory_lifecycle_with_dynamic_links(
    async_session, test_categories, mock_openai
):
    """
    E2E test: Create memory links using LLM suggestions.
    """
    # Create two memories first
    memory_service = MemoryService(async_session)

    memory1 = await memory_service.create_memory(
        simple_content="User loves Python",
        full_content="Python is amazing for data science",
        importance=5000,
        created_by=123456789,
    )

    memory2 = await memory_service.create_memory(
        simple_content="User knows NumPy",
        full_content="NumPy is great for numerical computing",
        importance=4000,
        created_by=123456789,
    )

    # Mock LLM response for link suggestion
    mock_link_response = MagicMock()
    mock_link_choice = MagicMock()
    mock_link_message = MagicMock()
    mock_link_message.content = """[
        {
            "memory_id": 2,
            "link_type": "related",
            "strength": 0.9,
            "reason": "Both about Python ecosystem and data science tools"
        }
    ]"""
    mock_link_choice.message = mock_link_message
    mock_link_response.choices = [mock_link_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_link_response)

    # Create LLM service with mocked client
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    # Get link suggestions
    existing_memories = [{"id": memory2.id, "simple_content": memory2.simple_content}]
    suggestions = await llm_service.suggest_memory_links(
        memory1.simple_content, existing_memories
    )

    # Verify suggestions
    assert len(suggestions) == 1
    assert suggestions[0]["memory_id"] == 2
    assert suggestions[0]["link_type"] == "related"
    assert suggestions[0]["strength"] == 0.9

    # Create link based on suggestion
    link = await memory_service.create_memory_link(
        from_memory_id=memory1.id,
        to_memory_id=suggestions[0]["memory_id"],
        link_type=suggestions[0]["link_type"],
        strength=suggestions[0]["strength"],
        context=suggestions[0]["reason"],
        auto_generated=True,
    )

    # Verify link was created
    assert link.id is not None
    assert link.from_memory_id == memory1.id
    assert link.to_memory_id == memory2.id
    assert link.link_type == "related"
    assert link.auto_generated is True

    # Query linked memories
    linked = await memory_service.get_linked_memories(memory1.id, direction="outgoing")
    assert len(linked) == 1
    assert linked[0].id == memory2.id


@pytest.mark.asyncio
async def test_full_memory_lifecycle(async_session, test_categories, mock_openai):
    """
    E2E test: Complete memory lifecycle with all features.

    1. Create memory with VAD + Zettelkasten
    2. Search memories
    3. Update memory
    4. Create links
    5. Delete memory
    """
    # Setup mocks
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = """{
        "valence": 0.7,
        "arousal": 0.5,
        "dominance": 0.6,
        "emotion_label": "contentment"
    }"""
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    memory_service = MemoryService(async_session)

    # 1. Create memory with full attributes
    vad = await llm_service.extract_vad_emotions("I enjoy working with Python")

    memory = await memory_service.create_memory(
        simple_content="User enjoys Python",
        full_content="I really enjoy working with Python for various projects",
        importance=6000,
        created_by=123456789,
        category_ids=[test_categories[1].id],
        emotion_valence=vad["valence"],
        emotion_arousal=vad["arousal"],
        emotion_dominance=vad["dominance"],
        emotion_label=vad["emotion_label"],
        keywords=["python", "programming", "projects"],
        tags=["knowledge/python"],
        context_temporal="2025-10-29",
    )

    assert memory.id is not None

    # 2. Search memories
    results = await memory_service.search_memories(
        user_id=123456789, query="Python", min_importance=5000
    )
    assert len(results) == 1
    assert results[0].id == memory.id

    # 3. Update memory
    updated = await memory_service.update_memory(
        memory.id, {"importance": 8000, "simple_content": "User loves Python"}
    )
    assert updated.importance == 8000
    assert updated.simple_content == "User loves Python"

    # 4. Create another memory and link them
    memory2 = await memory_service.create_memory(
        simple_content="User learned FastAPI",
        full_content="Just finished FastAPI tutorial",
        importance=5000,
        created_by=123456789,
    )

    link = await memory_service.create_memory_link(
        memory.id, memory2.id, link_type="precedes", strength=0.8
    )
    assert link.id is not None

    # Verify link
    linked = await memory_service.get_linked_memories(memory.id)
    assert len(linked) == 1
    assert linked[0].id == memory2.id

    # 5. Delete first memory (will cascade delete link in PostgreSQL)
    # Note: SQLite may not enforce CASCADE properly in all cases
    deleted = await memory_service.delete_memory(memory.id)
    assert deleted is True

    retrieved = await memory_service.get_memory(memory.id)
    assert retrieved is None

    # Memory 2 should still exist
    memory2_retrieved = await memory_service.get_memory(memory2.id)
    assert memory2_retrieved is not None


@pytest.mark.asyncio
async def test_memory_search_with_multiple_filters(async_session, test_categories):
    """
    E2E test: Advanced search with multiple filters.
    """
    memory_service = MemoryService(async_session)
    user_id = 123456789

    # Create diverse memories
    await memory_service.create_memory(
        simple_content="Happy Python memory",
        full_content="Python makes me happy",
        importance=8000,
        created_by=user_id,
        emotion_label="joy",
        keywords=["python", "happiness"],
    )

    await memory_service.create_memory(
        simple_content="Sad debugging memory",
        full_content="Debugging was frustrating",
        importance=3000,
        created_by=user_id,
        emotion_label="frustration",
        keywords=["debugging", "bugs"],
    )

    await memory_service.create_memory(
        simple_content="Excited about new project",
        full_content="Starting new Python project with asyncio",
        importance=9000,
        created_by=user_id,
        emotion_label="excitement",
        keywords=["python", "asyncio", "project"],
    )

    # Search with multiple filters
    # Note: ilike searches both simple_content and full_content
    results = await memory_service.search_memories(
        user_id=user_id,
        query="Python",
        min_importance=7000,
        emotion_labels=["joy", "excitement"],
        limit=10,
    )

    # Should find 2 memories with Python in content, importance >= 7000,
    # and emotion in [joy, excitement]
    assert len(results) == 2
    assert all(m.importance >= 7000 for m in results)
    assert all(m.emotion_label in ["joy", "excitement"] for m in results)
    # Check Python appears in either simple_content or full_content
    for m in results:
        assert (
            "python" in m.simple_content.lower() or "python" in m.full_content.lower()
        )
