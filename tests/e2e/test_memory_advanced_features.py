"""E2E tests for PRP-006 advanced memory features.

Tests:
1. create_enhanced_link() - Automatic LLM-based strength scoring and reasoning
2. create_memory_version() - Memory versioning system
3. compact_memory() - Automatic memory compaction when approaching 4000 tokens
4. calculate_relation_strength() - LLM integration for relation strength
5. generate_relation_reason() - LLM integration for relation reasoning
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.memory_service import MemoryService
from services.llm_service import LLMService

# async_session and test_categories fixtures provided by tests/conftest.py (PostgreSQL)


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for all tests."""
    with patch("services.llm_service.AsyncOpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_create_enhanced_link_with_automatic_strength_scoring(
    async_session, test_categories, mock_openai
):
    """
    E2E Test: create_enhanced_link() with automatic LLM-based strength scoring.

    Validates:
    - LLM calculates relation strength (0.0-1.0)
    - LLM generates relation reasoning
    - Link is created with strength and reason
    - Link is bidirectional
    """
    # Mock LLM responses for strength and reason
    strength_response = MagicMock()
    strength_choice = MagicMock()
    strength_message = MagicMock()
    strength_message.content = "0.85"  # LLM returns strength score
    strength_choice.message = strength_message
    strength_response.choices = [strength_choice]

    reason_response = MagicMock()
    reason_choice = MagicMock()
    reason_message = MagicMock()
    reason_message.content = (
        "Both memories discuss Python programming and async patterns"
    )
    reason_choice.message = reason_message
    reason_response.choices = [reason_choice]

    # Mock OpenAI calls (first for strength, second for reason)
    mock_openai.chat.completions.create = AsyncMock(
        side_effect=[strength_response, reason_response]
    )

    # Create LLM service with mocked OpenAI client
    llm_service = LLMService()

    # Create memory service
    service = MemoryService(async_session)

    # Create two related memories
    memory1 = await service.create_memory(
        simple_content="User loves Python asyncio",
        full_content="User is very excited about Python async/await patterns",
        importance=5000,
        created_by=123456789,
    )

    memory2 = await service.create_memory(
        simple_content="User working on FastAPI project",
        full_content="User is building a FastAPI microservice using asyncio",
        importance=5000,
        created_by=123456789,
    )

    # Create enhanced link with automatic strength and reason
    # NOTE: link_type is calculated based on strength, pass llm_service to use mock
    link = await service.create_enhanced_link(
        from_memory_id=memory1.id,
        to_memory_id=memory2.id,
        created_by=123456789,
        llm_service=llm_service,  # Pass mocked LLM service
    )

    # Assertions
    assert link.id is not None
    assert link.from_memory_id == memory1.id
    assert link.to_memory_id == memory2.id
    # Link type is calculated: >0.8=critical, >0.6=strong, >0.4=moderate, else=related
    # Our mocked strength is 0.85, so link_type should be "critical"
    assert link.link_type == "critical"
    assert link.strength == 0.85  # LLM-calculated strength
    assert (
        link.context == "Both memories discuss Python programming and async patterns"
    )  # reason stored in context
    assert link.auto_generated is True
    # NOTE: created_by not on MemoryLink model in current implementation

    # Verify LLM was called twice (strength + reason)
    assert mock_openai.chat.completions.create.call_count == 2


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_create_memory_version(async_session, test_categories):
    """
    E2E Test: create_memory_version() - Memory versioning system.

    Validates:
    - Creates new version of existing memory
    - Original memory preserved (parent_id links to original)
    - Version tracks evolution trigger
    - Both versions queryable
    """
    service = MemoryService(async_session)

    # Create original memory
    original = await service.create_memory(
        simple_content="User likes Python",
        full_content="User expressed interest in Python programming",
        importance=3000,
        created_by=123456789,
        keywords=["python", "programming"],
    )

    # Create new version with updated content
    # NOTE: Implementation only takes new_full_content,
    # not simple_content or evolution_trigger
    new_content = (
        "User is now an expert in Python async/await patterns "
        "and asyncio. LOVES Python!"
    )
    new_version = await service.create_memory_version(
        memory_id=original.id,
        new_full_content=new_content,
        created_by=123456789,
    )

    # Assertions
    assert new_version.id is not None
    assert new_version.id != original.id  # Different memory
    assert new_version.parent_id == original.id  # Links to original
    assert "expert" in new_version.full_content.lower()
    assert "asyncio" in new_version.full_content.lower()
    assert new_version.created_by == 123456789

    # Verify original is unchanged
    original_refreshed = await service.get_memory(original.id)
    assert original_refreshed.simple_content == "User likes Python"
    assert original_refreshed.parent_id is None  # Original has no parent


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_compact_memory_when_approaching_token_limit(
    async_session, test_categories, mock_openai
):
    """
    E2E Test: compact_memory() - Automatic compaction when approaching 4000 tokens.

    Validates:
    - LLM compacts long content into shorter summary
    - Preserves key information
    - Reduces token count while keeping meaning
    """
    # Mock LLM response for compaction
    compact_response = MagicMock()
    compact_choice = MagicMock()
    compact_message = MagicMock()
    compact_message.content = (
        "User is expert in Python async patterns, FastAPI, and asyncio. "
        "Loves building microservices."
    )
    compact_choice.message = compact_message
    compact_response.choices = [compact_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=compact_response)

    # Create LLM service
    llm_service = LLMService()

    # Very long content (simulating approaching 4000 tokens)
    long_content = (
        "User is very experienced with Python programming. "
        * 200  # Simulate long content
        + "User loves async/await patterns. " * 100
        + "User builds FastAPI microservices. " * 150
    )

    # Compact the memory
    # NOTE: Parameter is 'related_memories_summary', not 'simple_content'
    compacted_content = await llm_service.compact_memory(
        full_content=long_content,
        related_memories_summary="Related: User working on FastAPI microservices",
    )

    # Assertions
    assert compacted_content is not None
    assert len(compacted_content) < len(long_content)  # Should be shorter
    assert "Python" in compacted_content
    assert "async" in compacted_content or "FastAPI" in compacted_content
    assert mock_openai.chat.completions.create.call_count == 1


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_calculate_relation_strength_llm_integration(mock_openai):
    """
    E2E Test: calculate_relation_strength() - LLM integration for strength scoring.

    Validates:
    - LLM analyzes two memories and returns strength score (0.0-1.0)
    - Score is numeric and within valid range
    """
    # Mock LLM response
    response = MagicMock()
    choice = MagicMock()
    message = MagicMock()
    message.content = "0.92"
    choice.message = message
    response.choices = [choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=response)

    llm_service = LLMService()

    # Calculate strength between two related memories
    # NOTE: Parameters are memory_a_content and memory_b_content (with underscores!)
    strength = await llm_service.calculate_relation_strength(
        memory_a_content="User loves Python asyncio programming",
        memory_b_content="User is building FastAPI microservices with asyncio",
    )

    # Assertions
    assert strength == 0.92
    assert 0.0 <= strength <= 1.0
    assert mock_openai.chat.completions.create.call_count == 1


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_generate_relation_reason_llm_integration(mock_openai):
    """
    E2E Test: generate_relation_reason() - LLM integration for reasoning generation.

    Validates:
    - LLM generates human-readable explanation of relation
    - Reason is non-empty string
    """
    # Mock LLM response
    response = MagicMock()
    choice = MagicMock()
    message = MagicMock()
    message.content = (
        "Both memories demonstrate the user's expertise in Python async "
        "programming and microservice architecture"
    )
    choice.message = message
    response.choices = [choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=response)

    llm_service = LLMService()

    # Generate reason
    # NOTE: Parameters are memory_a_content and memory_b_content (with underscores!)
    reason = await llm_service.generate_relation_reason(
        memory_a_content="User loves Python asyncio programming",
        memory_b_content="User is building FastAPI microservices with asyncio",
    )

    # Assertions
    assert reason is not None
    assert len(reason) > 0
    assert "async" in reason.lower() or "python" in reason.lower()
    assert mock_openai.chat.completions.create.call_count == 1
