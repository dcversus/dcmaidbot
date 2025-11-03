"""E2E tests for bot integration with memories, history, and LLM-as-judge validation.

These tests verify the ACTUAL bot behavior by:
1. Making HTTP requests to /call endpoint
2. Testing with DISABLE_TG=true (no Telegram needed)
3. Using REAL LLM integration (not mocked)
4. Validating responses with LLM-as-judge

This is the RIGHT way to test - we test what the user experiences!
"""

import os
import time

import aiohttp
import psutil
import pytest

from core.models.user import User
from core.services.llm_service import LLMService
from core.services.memory_service import MemoryService

# Test configuration
BASE_URL = "http://localhost:8080"  # Bot running locally
NUDGE_SECRET = os.getenv("NUDGE_SECRET", "test_secret_for_e2e")

# Admin user ID for testing
TEST_ADMIN_ID = 199572554


# Performance tracking
class PerformanceTracker:
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.end_memory = None
        self.response_time = None
        self.memory_increase = None

    def start_tracking(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def end_tracking(self):
        self.end_time = time.time()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.response_time = (self.end_time - self.start_time) * 1000  # ms
        self.memory_increase = self.end_memory - self.start_memory  # MB
        return self

    def get_metrics(self):
        return {
            "response_time_ms": self.response_time,
            "memory_usage_mb": self.end_memory,
            "memory_increase_mb": self.memory_increase,
            "start_memory_mb": self.start_memory,
            "end_memory_mb": self.end_memory,
        }


@pytest.fixture
async def bot_client():
    """HTTP client for making requests to /call endpoint."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
async def setup_test_admin(async_session):
    """Create test admin user in database."""
    user = User(
        telegram_id=TEST_ADMIN_ID,
        username="test_admin",
        first_name="Test",
        last_name="Admin",
        is_friend=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def llm_judge():
    """LLM service for judging test responses."""
    return LLMService()


async def call_bot(
    client: aiohttp.ClientSession,
    user_id: int,
    message: str,
    performance_tracker: PerformanceTracker = None,
) -> dict:
    """Make HTTP request to /call endpoint.

    Args:
        client: aiohttp session
        user_id: Telegram user ID
        message: Message text to send
        performance_tracker: Optional PerformanceTracker for metrics

    Returns:
        dict: Response from /call endpoint
    """
    url = f"{BASE_URL}/call"
    headers = {
        "Authorization": f"Bearer {NUDGE_SECRET}",
        "Content-Type": "application/json",
    }
    data = {
        "user_id": user_id,
        "message": message,
    }

    if performance_tracker:
        performance_tracker.start_tracking()

    async with client.post(url, json=data, headers=headers) as response:
        result = await response.json()

    if performance_tracker:
        performance_tracker.end_tracking()

    return result


async def judge_response(
    llm_judge: LLMService,
    user_message: str,
    bot_response: str,
    criteria: str,
) -> dict:
    """Use LLM as judge to evaluate bot response quality.

    Args:
        llm_judge: LLM service for judging
        user_message: Original user message
        bot_response: Bot's response
        criteria: What to evaluate (e.g., "mentions previous conversation")

    Returns:
        dict: {"passes": bool, "reasoning": str, "score": float}
    """
    judge_prompt = f"""You are evaluating a chatbot's response quality.

User message: "{user_message}"
Bot response: "{bot_response}"

Evaluation criteria: {criteria}

Respond with JSON format:
{{
    "passes": true/false,
    "reasoning": "explanation of why it passes or fails",
    "score": 0.0-1.0 (confidence score)
}}

Be strict but fair. The bot should clearly meet the criteria."""

    user_info = {"id": 999999, "username": "judge"}
    chat_info = {"id": 999999, "type": "private"}

    judge_result = await llm_judge.get_response(
        user_message=judge_prompt,
        user_info=user_info,
        chat_info=chat_info,
        use_complex_model=True,  # Use GPT-4 for judging
    )

    # Parse JSON response
    import json

    try:
        result = json.loads(judge_result)
        return result
    except json.JSONDecodeError:
        # Fallback: check if response contains "passes": true
        passes = '"passes": true' in judge_result or "passes: true" in judge_result
        return {
            "passes": passes,
            "reasoning": judge_result,
            "score": 0.8 if passes else 0.2,
        }


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
async def test_bot_remembers_message_history(
    bot_client, setup_test_admin, async_session, llm_judge
):
    """E2E test: Bot should remember and reference previous messages.

    This tests the FULL INTEGRATION:
    1. User sends first message
    2. User sends second message referencing first
    3. Bot should remember first message and respond contextually
    4. LLM judge validates that bot actually used history
    5. Performance metrics are collected and validated
    """
    # Performance tracking setup
    first_message_tracker = PerformanceTracker()
    second_message_tracker = PerformanceTracker()

    # Step 1: Send first message with performance tracking
    first_message = "My name is Alice and I love Python programming!"
    response1 = await call_bot(
        bot_client, TEST_ADMIN_ID, first_message, first_message_tracker
    )

    assert response1["success"] is True
    response1["response"]

    # Validate first message performance
    first_metrics = first_message_tracker.get_metrics()
    print("\n📊 First Message Performance:")
    print(f"  Response time: {first_metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {first_metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {first_metrics['memory_increase_mb']:.2f}MB")

    # Performance assertions
    assert first_metrics["response_time_ms"] < 5000, (
        f"First message response too slow: {first_metrics['response_time_ms']}ms"
    )
    assert first_metrics["memory_increase_mb"] < 50, (
        f"Memory increase too high: {first_metrics['memory_increase_mb']}MB"
    )

    # Step 2: Send second message asking about previous conversation with performance tracking
    second_message = "What did I just tell you about myself?"
    response2 = await call_bot(
        bot_client, TEST_ADMIN_ID, second_message, second_message_tracker
    )

    assert response2["success"] is True
    bot_response2 = response2["response"]

    # Validate second message performance
    second_metrics = second_message_tracker.get_metrics()
    print("\n📊 Second Message Performance:")
    print(f"  Response time: {second_metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {second_metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {second_metrics['memory_increase_mb']:.2f}MB")

    # Performance assertions for second message (should be faster with context)
    assert second_metrics["response_time_ms"] < 8000, (
        f"Second message response too slow: {second_metrics['response_time_ms']}ms"
    )
    assert second_metrics["memory_increase_mb"] < 75, (
        f"Memory increase too high: {second_metrics['memory_increase_mb']}MB"
    )

    # Step 3: Use LLM as judge to validate bot remembered
    judgment = await judge_response(
        llm_judge,
        user_message=second_message,
        bot_response=bot_response2,
        criteria=(
            "The bot should reference that the user's name is Alice "
            "and/or that they love Python programming. The bot should "
            "demonstrate memory of the previous conversation."
        ),
    )

    print("\n🔍 LLM Judge Result:")
    print(f"  Passes: {judgment['passes']}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    # Assert that bot passed the test
    assert judgment["passes"] is True, (
        f"Bot failed to remember previous message. "
        f"Judge reasoning: {judgment['reasoning']}"
    )
    assert judgment["score"] >= 0.7, "Judge confidence too low"

    # Overall performance summary
    avg_response_time = (
        first_metrics["response_time_ms"] + second_metrics["response_time_ms"]
    ) / 2
    total_memory_increase = (
        first_metrics["memory_increase_mb"] + second_metrics["memory_increase_mb"]
    )

    print("\n📈 Overall Performance Summary:")
    print(f"  Average response time: {avg_response_time:.2f}ms")
    print(f"  Total memory increase: {total_memory_increase:.2f}MB")


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
async def test_bot_uses_memories_in_response(
    bot_client, setup_test_admin, async_session, llm_judge, test_categories
):
    """E2E test: Bot should use stored memories when responding.

    This tests:
    1. Create a memory about the user
    2. User asks something related to that memory
    3. Bot should reference the memory in response
    4. LLM judge validates memory was used
    5. Performance metrics are collected and validated
    """
    # Performance tracking setup
    performance_tracker = PerformanceTracker()

    # Step 1: Create a memory about the user
    memory_service = MemoryService(async_session)
    await memory_service.create_memory(
        simple_content="Alice is an expert Python developer who loves async/await",
        full_content=(
            "Alice is a senior Python developer with 10 years of experience. "
            "She specializes in async/await patterns, FastAPI, and asyncio. "
            "She's currently building a microservices architecture."
        ),
        importance=7000,
        created_by=TEST_ADMIN_ID,
        category_ids=[test_categories[1].id],  # tech_domain category
        keywords=["Python", "async", "expert", "FastAPI"],
    )

    # Step 2: User asks about Python with performance tracking
    user_message = "I'm working on a FastAPI project. Any tips?"
    response = await call_bot(
        bot_client, TEST_ADMIN_ID, user_message, performance_tracker
    )

    assert response["success"] is True
    bot_response = response["response"]

    # Validate performance metrics
    metrics = performance_tracker.get_metrics()
    print("\n📊 Memory Query Performance:")
    print(f"  Response time: {metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {metrics['memory_increase_mb']:.2f}MB")

    # Performance assertions (memory queries should be efficient)
    assert metrics["response_time_ms"] < 10000, (
        f"Memory query response too slow: {metrics['response_time_ms']}ms"
    )
    assert metrics["memory_increase_mb"] < 100, (
        f"Memory increase too high: {metrics['memory_increase_mb']}MB"
    )

    # Step 3: Use LLM as judge to validate bot used memory
    judgment = await judge_response(
        llm_judge,
        user_message=user_message,
        bot_response=bot_response,
        criteria=(
            "The bot should demonstrate knowledge that the user (Alice) "
            "is already an expert in Python/FastAPI/async patterns. "
            "The bot should NOT give beginner advice, but should engage "
            "at an expert level or reference the user's expertise."
        ),
    )

    print("\n🔍 LLM Judge Result:")
    print(f"  Passes: {judgment['passes']}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, (
        f"Bot failed to use stored memory. Judge reasoning: {judgment['reasoning']}"
    )
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
async def test_bot_creates_memories_from_conversation(
    bot_client, setup_test_admin, async_session, llm_judge
):
    """E2E test: Bot should create memories from important information.

    This tests:
    1. User shares important information
    2. Bot responds
    3. Check that a memory was created in database
    4. Verify memory contains key information
    5. Performance metrics are collected and validated
    """
    # Performance tracking setup
    performance_tracker = PerformanceTracker()

    # Step 1: User shares important personal information with performance tracking
    user_message = (
        "I just got promoted to Senior Engineer at Google! "
        "I'll be leading the infrastructure team!"
    )
    response = await call_bot(
        bot_client, TEST_ADMIN_ID, user_message, performance_tracker
    )

    assert response["success"] is True

    # Validate performance metrics
    metrics = performance_tracker.get_metrics()
    print("\n📊 Memory Creation Performance:")
    print(f"  Response time: {metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {metrics['memory_increase_mb']:.2f}MB")

    # Performance assertions (memory creation should be reasonable)
    assert metrics["response_time_ms"] < 12000, (
        f"Memory creation response too slow: {metrics['response_time_ms']}ms"
    )
    assert metrics["memory_increase_mb"] < 150, (
        f"Memory increase too high: {metrics['memory_increase_mb']}MB"
    )

    # Step 2: Check that a memory was created
    MemoryService(async_session)

    # Search for memories created by this user
    # NOTE: This requires implementing get_user_memories() in MemoryService
    # For now, we'll query directly
    from sqlalchemy import select

    from core.models.memory import Memory

    stmt = (
        select(Memory)
        .where(Memory.created_by == TEST_ADMIN_ID)
        .order_by(Memory.created_at.desc())
        .limit(5)
    )
    result = await async_session.execute(stmt)
    recent_memories = result.scalars().all()

    # Step 3: Verify at least one memory mentions the promotion
    memory_found = False
    for mem in recent_memories:
        if (
            "google" in mem.full_content.lower()
            or "senior engineer" in mem.full_content.lower()
        ):
            memory_found = True
            print(f"\n✅ Found memory: {mem.simple_content}")
            break

    # NOTE: This will FAIL until we implement memory creation in handle_message!
    # That's the point - tests should fail first, then we fix the code!
    assert memory_found, (
        "Bot did not create a memory from important user information! "
        "Recent memories: " + str([m.simple_content for m in recent_memories])
    )


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
async def test_bot_uses_vad_emotions_in_context(
    bot_client, setup_test_admin, async_session, llm_judge, test_categories
):
    """E2E test: Bot should consider emotional context (VAD) when responding.

    This tests:
    1. Create a memory with negative emotion (sadness about project)
    2. User asks about that project
    3. Bot should show empathy/awareness of emotional context
    4. LLM judge validates emotional awareness
    5. Performance metrics are collected and validated
    """
    # Performance tracking setup
    performance_tracker = PerformanceTracker()

    # Step 1: Create memory with negative emotional context
    memory_service = MemoryService(async_session)
    await memory_service.create_memory(
        simple_content="Alice is frustrated with legacy codebase refactoring",
        full_content=(
            "Alice has been struggling with a massive legacy codebase refactor. "
            "The code is poorly documented, has no tests, and keeps breaking. "
            "She's been working overtime and feeling burned out."
        ),
        importance=6000,
        created_by=TEST_ADMIN_ID,
        category_ids=[test_categories[2].id],  # project category
        keywords=["refactoring", "legacy", "frustrated", "burnout"],
        emotion_valence=-0.7,  # Negative emotion
        emotion_arousal=0.4,  # Moderate arousal
        emotion_dominance=-0.3,  # Feeling out of control
    )

    # Step 2: User mentions the project with performance tracking
    user_message = "Still working on that refactoring project..."
    response = await call_bot(
        bot_client, TEST_ADMIN_ID, user_message, performance_tracker
    )

    assert response["success"] is True
    bot_response = response["response"]

    # Validate performance metrics
    metrics = performance_tracker.get_metrics()
    print("\n📊 Emotional Context Performance:")
    print(f"  Response time: {metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {metrics['memory_increase_mb']:.2f}MB")

    # Performance assertions (emotional context processing should be efficient)
    assert metrics["response_time_ms"] < 10000, (
        f"Emotional context response too slow: {metrics['response_time_ms']}ms"
    )
    assert metrics["memory_increase_mb"] < 100, (
        f"Memory increase too high: {metrics['memory_increase_mb']}MB"
    )

    # Step 3: Use LLM as judge to validate emotional awareness
    judgment = await judge_response(
        llm_judge,
        user_message=user_message,
        bot_response=bot_response,
        criteria=(
            "The bot should show empathy and awareness that the user has been "
            "struggling/frustrated with this refactoring project. The bot should "
            "be supportive and NOT be overly cheerful or ignore the emotional context. "
            "The response should demonstrate emotional intelligence."
        ),
    )

    print("\n🔍 LLM Judge Result:")
    print(f"  Passes: {judgment['passes']}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, (
        f"Bot failed to consider emotional context (VAD). "
        f"Judge reasoning: {judgment['reasoning']}"
    )
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_openai
async def test_bot_responds_without_telegram(bot_client, setup_test_admin):
    """Basic test: Verify /call endpoint works without Telegram.

    This is a smoke test to ensure the integration tests can run with DISABLE_TG=true.
    """
    # Performance tracking setup
    performance_tracker = PerformanceTracker()

    response = await call_bot(bot_client, TEST_ADMIN_ID, "Hello!", performance_tracker)

    assert response["success"] is True
    assert "response" in response
    assert len(response["response"]) > 0

    # Validate performance metrics for basic smoke test
    metrics = performance_tracker.get_metrics()
    print("\n📊 Basic Smoke Test Performance:")
    print(f"  Response time: {metrics['response_time_ms']:.2f}ms")
    print(f"  Memory usage: {metrics['memory_usage_mb']:.2f}MB")
    print(f"  Memory increase: {metrics['memory_increase_mb']:.2f}MB")

    # Basic performance assertions for smoke test
    assert metrics["response_time_ms"] < 3000, (
        f"Basic response too slow: {metrics['response_time_ms']}ms"
    )
    assert metrics["memory_increase_mb"] < 25, (
        f"Memory increase too high for basic test: {metrics['memory_increase_mb']}MB"
    )

    print(f"\n✅ Bot responded: {response['response'][:100]}...")
