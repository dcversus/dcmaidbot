"""E2E tests for bot integration with memories, history, and LLM-as-judge validation.

These tests verify the ACTUAL bot behavior by:
1. Making HTTP requests to /call endpoint
2. Testing with DISABLE_TG=true (no Telegram needed)
3. Using REAL LLM integration (not mocked)
4. Validating responses with LLM-as-judge

This is the RIGHT way to test - we test what the user experiences!
"""

import os
import pytest
import aiohttp

from services.memory_service import MemoryService
from services.llm_service import LLMService
from models.user import User

# Test configuration
BASE_URL = "http://localhost:8080"  # Bot running locally
NUDGE_SECRET = os.getenv("NUDGE_SECRET", "test_secret_for_e2e")

# Admin user ID for testing
TEST_ADMIN_ID = 199572554


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


async def call_bot(client: aiohttp.ClientSession, user_id: int, message: str) -> dict:
    """Make HTTP request to /call endpoint.

    Args:
        client: aiohttp session
        user_id: Telegram user ID
        message: Message text to send

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

    async with client.post(url, json=data, headers=headers) as response:
        return await response.json()


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
    """
    # Step 1: Send first message
    first_message = "My name is Alice and I love Python programming!"
    response1 = await call_bot(bot_client, TEST_ADMIN_ID, first_message)

    assert response1["success"] is True
    response1["response"]

    # Step 2: Send second message asking about previous conversation
    second_message = "What did I just tell you about myself?"
    response2 = await call_bot(bot_client, TEST_ADMIN_ID, second_message)

    assert response2["success"] is True
    bot_response2 = response2["response"]

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


@pytest.mark.asyncio
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
    """
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

    # Step 2: User asks about Python
    user_message = "I'm working on a FastAPI project. Any tips?"
    response = await call_bot(bot_client, TEST_ADMIN_ID, user_message)

    assert response["success"] is True
    bot_response = response["response"]

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

    assert (
        judgment["passes"] is True
    ), f"Bot failed to use stored memory. Judge reasoning: {judgment['reasoning']}"
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
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
    """
    # Step 1: User shares important personal information
    user_message = (
        "I just got promoted to Senior Engineer at Google! "
        "I'll be leading the infrastructure team!"
    )
    response = await call_bot(bot_client, TEST_ADMIN_ID, user_message)

    assert response["success"] is True

    # Step 2: Check that a memory was created
    MemoryService(async_session)

    # Search for memories created by this user
    # NOTE: This requires implementing get_user_memories() in MemoryService
    # For now, we'll query directly
    from sqlalchemy import select
    from models.memory import Memory

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
    """
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
        valence=-0.7,  # Negative emotion
        arousal=0.4,  # Moderate arousal
        dominance=-0.3,  # Feeling out of control
    )

    # Step 2: User mentions the project
    user_message = "Still working on that refactoring project..."
    response = await call_bot(bot_client, TEST_ADMIN_ID, user_message)

    assert response["success"] is True
    bot_response = response["response"]

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
    response = await call_bot(bot_client, TEST_ADMIN_ID, "Hello!")

    assert response["success"] is True
    assert "response" in response
    assert len(response["response"]) > 0

    print(f"\n✅ Bot responded: {response['response'][:100]}...")
