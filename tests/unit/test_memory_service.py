"""Unit tests for MemoryService (PRP-005)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.memory import Category
from services.memory_service import MemoryService


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
            name="identity",
            domain="self",
            full_path="self.identity",
            description="Bot's identity",
            icon="🤖",
            importance_range_min=8000,
            importance_range_max=10000,
        ),
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


@pytest.mark.asyncio
async def test_create_memory(async_session, test_categories):
    """Test creating a memory with VAD emotions and Zettelkasten attributes."""
    service = MemoryService(async_session)

    memory = await service.create_memory(
        simple_content="User loves Python programming",
        full_content="The user expressed strong enthusiasm for Python. "
        "They mentioned working on asyncio projects and FastAPI.",
        importance=5000,
        created_by=123456789,
        category_ids=[test_categories[2].id],
        emotion_valence=0.8,
        emotion_arousal=0.6,
        emotion_dominance=0.5,
        emotion_label="joy",
        keywords=["python", "programming", "asyncio", "fastapi"],
        tags=["knowledge/python", "interest/tech_preference"],
        context_temporal="2025-10-29",
        context_situational="Discussion about favorite technologies",
    )

    assert memory.id is not None
    assert memory.simple_content == "User loves Python programming"
    assert memory.importance == 5000
    assert memory.emotion_valence == 0.8
    assert memory.emotion_label == "joy"
    assert memory.keywords == ["python", "programming", "asyncio", "fastapi"]
    assert memory.tags == ["knowledge/python", "interest/tech_preference"]
    assert len(memory.categories) == 1
    assert memory.categories[0].name == "tech_domain"


@pytest.mark.asyncio
async def test_get_memory(async_session, test_categories):
    """Test retrieving a memory by ID."""
    service = MemoryService(async_session)

    # Create memory
    created = await service.create_memory(
        simple_content="Test memory",
        full_content="Full test content",
        importance=1000,
        created_by=123456789,
        emotion_valence=0.5,
    )

    # Retrieve memory
    retrieved = await service.get_memory(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.simple_content == "Test memory"
    assert retrieved.access_count == 1
    assert retrieved.last_accessed is not None


@pytest.mark.asyncio
async def test_search_memories_by_query(async_session, test_categories):
    """Test searching memories by text query."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create test memories
    await service.create_memory(
        simple_content="Python is amazing",
        full_content="I love Python programming",
        importance=5000,
        created_by=user_id,
    )
    await service.create_memory(
        simple_content="JavaScript is flexible",
        full_content="JavaScript has many use cases",
        importance=3000,
        created_by=user_id,
    )
    await service.create_memory(
        simple_content="Python has great libraries",
        full_content="NumPy and Pandas are excellent",
        importance=4000,
        created_by=user_id,
    )

    # Search for Python
    results = await service.search_memories(user_id, query="Python")

    assert len(results) == 2
    assert all("Python" in m.simple_content for m in results)


@pytest.mark.asyncio
async def test_search_memories_by_importance(async_session, test_categories):
    """Test searching memories by importance range."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create memories with different importance
    await service.create_memory(
        simple_content="Low importance",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )
    await service.create_memory(
        simple_content="High importance",
        full_content="Content",
        importance=9000,
        created_by=user_id,
    )
    await service.create_memory(
        simple_content="Medium importance",
        full_content="Content",
        importance=5000,
        created_by=user_id,
    )

    # Search for high importance (>= 5000)
    results = await service.search_memories(
        user_id, min_importance=5000, max_importance=10000
    )

    assert len(results) == 2
    assert all(m.importance >= 5000 for m in results)


@pytest.mark.asyncio
async def test_search_memories_by_emotion(async_session, test_categories):
    """Test searching memories by emotion labels."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create memories with different emotions
    await service.create_memory(
        simple_content="Happy memory",
        full_content="Content",
        importance=1000,
        created_by=user_id,
        emotion_label="joy",
    )
    await service.create_memory(
        simple_content="Sad memory",
        full_content="Content",
        importance=1000,
        created_by=user_id,
        emotion_label="sadness",
    )
    await service.create_memory(
        simple_content="Another happy memory",
        full_content="Content",
        importance=1000,
        created_by=user_id,
        emotion_label="joy",
    )

    # Search for joy emotions
    results = await service.search_memories(user_id, emotion_labels=["joy"])

    assert len(results) == 2
    assert all(m.emotion_label == "joy" for m in results)


@pytest.mark.asyncio
async def test_update_memory(async_session, test_categories):
    """Test updating memory fields."""
    service = MemoryService(async_session)

    # Create memory
    memory = await service.create_memory(
        simple_content="Original content",
        full_content="Original full content",
        importance=1000,
        created_by=123456789,
    )

    # Update memory
    updated = await service.update_memory(
        memory.id,
        {"simple_content": "Updated content", "importance": 5000},
    )

    assert updated is not None
    assert updated.simple_content == "Updated content"
    assert updated.importance == 5000
    assert updated.updated_at is not None


@pytest.mark.asyncio
async def test_delete_memory(async_session, test_categories):
    """Test deleting a memory."""
    service = MemoryService(async_session)

    # Create memory
    memory = await service.create_memory(
        simple_content="To be deleted",
        full_content="Content",
        importance=1000,
        created_by=123456789,
    )

    memory_id = memory.id

    # Delete memory
    deleted = await service.delete_memory(memory_id)

    assert deleted is True

    # Verify it's gone
    retrieved = await service.get_memory(memory_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_create_memory_link(async_session, test_categories):
    """Test creating a Zettelkasten-style memory link."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create two memories
    memory1 = await service.create_memory(
        simple_content="Memory 1",
        full_content="Content 1",
        importance=1000,
        created_by=user_id,
    )
    memory2 = await service.create_memory(
        simple_content="Memory 2",
        full_content="Content 2",
        importance=1000,
        created_by=user_id,
    )

    # Create link
    link = await service.create_memory_link(
        from_memory_id=memory1.id,
        to_memory_id=memory2.id,
        link_type="related",
        strength=0.8,
        context="Both about similar topics",
        auto_generated=False,
    )

    assert link.id is not None
    assert link.from_memory_id == memory1.id
    assert link.to_memory_id == memory2.id
    assert link.link_type == "related"
    assert link.strength == 0.8


@pytest.mark.asyncio
async def test_get_linked_memories_outgoing(async_session, test_categories):
    """Test getting outgoing linked memories."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create three memories
    memory1 = await service.create_memory(
        simple_content="Memory 1",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )
    memory2 = await service.create_memory(
        simple_content="Memory 2",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )
    memory3 = await service.create_memory(
        simple_content="Memory 3",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )

    # Create links from memory1 to memory2 and memory3
    await service.create_memory_link(memory1.id, memory2.id, "related")
    await service.create_memory_link(memory1.id, memory3.id, "elaborates")

    # Get outgoing links
    linked = await service.get_linked_memories(memory1.id, direction="outgoing")

    assert len(linked) == 2
    linked_ids = {m.id for m in linked}
    assert memory2.id in linked_ids
    assert memory3.id in linked_ids


@pytest.mark.asyncio
async def test_get_linked_memories_incoming(async_session, test_categories):
    """Test getting incoming linked memories."""
    service = MemoryService(async_session)
    user_id = 123456789

    # Create two memories
    memory1 = await service.create_memory(
        simple_content="Memory 1",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )
    memory2 = await service.create_memory(
        simple_content="Memory 2",
        full_content="Content",
        importance=1000,
        created_by=user_id,
    )

    # Create link from memory1 to memory2
    await service.create_memory_link(memory1.id, memory2.id, "causes")

    # Get incoming links for memory2
    linked = await service.get_linked_memories(memory2.id, direction="incoming")

    assert len(linked) == 1
    assert linked[0].id == memory1.id


@pytest.mark.asyncio
async def test_get_category(async_session, test_categories):
    """Test getting category by full path."""
    service = MemoryService(async_session)

    category = await service.get_category("self.identity")

    assert category is not None
    assert category.name == "identity"
    assert category.domain == "self"
    assert category.icon == "🤖"


@pytest.mark.asyncio
async def test_get_categories_by_domain(async_session, test_categories):
    """Test getting all categories in a domain."""
    service = MemoryService(async_session)

    # Get social domain categories
    categories = await service.get_categories_by_domain("social")

    assert len(categories) == 1
    assert categories[0].name == "person"


@pytest.mark.asyncio
async def test_memory_access_tracking(async_session, test_categories):
    """Test that memory access is tracked correctly."""
    service = MemoryService(async_session)

    # Create memory
    memory = await service.create_memory(
        simple_content="Test memory",
        full_content="Content",
        importance=1000,
        created_by=123456789,
    )

    # Access it multiple times
    await service.get_memory(memory.id)
    await service.get_memory(memory.id)
    retrieved = await service.get_memory(memory.id)

    assert retrieved.access_count == 3
    assert retrieved.last_accessed is not None


@pytest.mark.asyncio
async def test_memory_with_multiple_categories(async_session, test_categories):
    """Test creating memory with multiple categories."""
    service = MemoryService(async_session)

    memory = await service.create_memory(
        simple_content="Multi-category memory",
        full_content="Content spans multiple domains",
        importance=5000,
        created_by=123456789,
        category_ids=[test_categories[0].id, test_categories[1].id],
    )

    assert len(memory.categories) == 2
    category_names = {c.name for c in memory.categories}
    assert "identity" in category_names
    assert "person" in category_names
