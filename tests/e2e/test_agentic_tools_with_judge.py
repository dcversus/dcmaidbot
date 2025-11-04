"""Comprehensive E2E tests for agentic tools with LLM-as-judge validation.

This test suite validates that the bot can autonomously use tools:
- create_memory: Bot creates memories when user shares important info
- search_memories: Bot searches memories to recall information
- web_search: Bot searches web for current information

All tests use REAL LLM calls and LLM-as-judge for validation.

Run with:
    pytest tests/e2e/test_agentic_tools_with_judge.py -v -s -m integration
"""

import os
from typing import Any

import aiohttp
import pytest

from models.user import User
from services.llm_service import LLMService

# Test configuration
BASE_URL = "http://localhost:8080"
NUDGE_SECRET = os.getenv("NUDGE_SECRET", "test_secret_for_e2e")
TEST_ADMIN_ID = 199572554


@pytest.fixture
async def bot_client():
    """HTTP client for making requests to /call endpoint."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
async def setup_test_admin(async_session):
    """Create or get test admin user in database."""
    from sqlalchemy import select

    # Check if user already exists
    stmt = select(User).where(User.telegram_id == TEST_ADMIN_ID)
    result = await async_session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create new user
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
    client: aiohttp.ClientSession, user_id: int, message: str
) -> dict[str, Any]:
    """Make HTTP request to /call endpoint."""
    url = f"{BASE_URL}/call"
    headers = {
        "Authorization": f"Bearer {NUDGE_SECRET}",
        "Content-Type": "application/json",
    }
    data = {"user_id": user_id, "message": message}

    async with client.post(url, json=data, headers=headers) as response:
        return await response.json()


async def batch_judge(
    llm_judge: LLMService, test_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Use LLM as judge to evaluate multiple test results in batch.

    Args:
        llm_judge: LLM service for judging
        test_results: List of test result dicts

    Returns:
        dict: Overall judgment with per-test verdicts
    """
    # Build comprehensive prompt with all test results
    results_text = ""
    for i, result in enumerate(test_results, 1):
        results_text += f"\n### Test {i}: {result['test_name']}\n"
        results_text += f"**User Input**: {result['user_message']}\n"
        results_text += f"**Bot Response**: {result['bot_response']}\n"
        results_text += f"**Expected Behavior**: {result['expected_behavior']}\n"
        results_text += f"**Tool Expected**: {result.get('tool_expected', 'any')}\n"
        results_text += "\n"

    judge_prompt = f"""You are evaluating an agentic AI bot's performance
across multiple tests. The bot should autonomously use tools
(create_memory, search_memories, web_search) when appropriate.

Test Results:
{results_text}

For EACH test, evaluate:
1. Did the bot demonstrate tool usage (created memory, searched, etc.)?
2. Does the response show awareness of tool execution results?
3. Is the response appropriate given the expected behavior?

Respond with JSON format:
{{
    "overall_passes": true/false,
    "overall_score": 0.0-1.0,
    "overall_reasoning": "explanation of overall performance",
    "test_verdicts": [
        {{
            "test_name": "...",
            "passes": true/false,
            "score": 0.0-1.0,
            "reasoning": "specific feedback for this test"
        }},
        ...
    ]
}}

Be strict but fair. The bot should clearly demonstrate agentic tool usage."""

    user_info = {"id": 999999, "username": "judge"}
    chat_info = {"id": 999999, "type": "private"}

    judge_result = await llm_judge.get_response(
        user_message=judge_prompt,
        user_info=user_info,
        chat_info=chat_info,
        use_complex_model=True,
    )

    import json

    try:
        return json.loads(judge_result)
    except json.JSONDecodeError:
        # Fallback parsing
        passes = (
            '"overall_passes": true' in judge_result
            or "overall_passes: true" in judge_result
        )
        return {
            "overall_passes": passes,
            "overall_score": 0.8 if passes else 0.2,
            "overall_reasoning": judge_result,
            "test_verdicts": [],
        }


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_all_agentic_tools_with_batch_judge(
    bot_client, setup_test_admin, async_session, llm_judge
):
    """
    Comprehensive E2E test: All agentic tools with batch LLM judge.

    This test runs multiple scenarios, collects all results,
    and sends them to LLM judge in one batch for comprehensive evaluation.
    """
    test_results = []

    # Test 1: Memory Creation
    print("\n🧪 Test 1: Bot should create memory when user shares important info")
    msg1 = (
        "Remember this: My favorite programming language is Python and "
        "I specialize in async/await patterns!"
    )
    response1 = await call_bot(bot_client, TEST_ADMIN_ID, msg1)
    assert response1["success"] is True

    test_results.append(
        {
            "test_name": "Memory Creation",
            "user_message": msg1,
            "bot_response": response1["response"],
            "expected_behavior": (
                "Bot should create a memory about user's Python expertise "
                "and async/await specialization. Response should confirm "
                "memory creation."
            ),
            "tool_expected": "create_memory",
        }
    )

    # Test 2: Memory Search
    print("\n🧪 Test 2: Bot should search memories and recall information")
    msg2 = "What programming language did I say I specialize in?"
    response2 = await call_bot(bot_client, TEST_ADMIN_ID, msg2)
    assert response2["success"] is True

    test_results.append(
        {
            "test_name": "Memory Search & Recall",
            "user_message": msg2,
            "bot_response": response2["response"],
            "expected_behavior": (
                "Bot should search memories, find Python/async info, "
                "and answer correctly. Should demonstrate memory recall."
            ),
            "tool_expected": "search_memories",
        }
    )

    # Test 3: Web Search
    print("\n🧪 Test 3: Bot should search web for current information")
    msg3 = "What is the latest stable version of Python?"
    response3 = await call_bot(bot_client, TEST_ADMIN_ID, msg3)
    assert response3["success"] is True

    test_results.append(
        {
            "test_name": "Web Search",
            "user_message": msg3,
            "bot_response": response3["response"],
            "expected_behavior": (
                "Bot should search web for Python version info, "
                "find current stable version, and provide specific "
                "version number (e.g., Python 3.12.x)"
            ),
            "tool_expected": "web_search",
        }
    )

    # Test 4: Automatic Memory Creation (Implicit)
    print("\n🧪 Test 4: Bot should automatically create memory without being asked")
    msg4 = (
        "I just got promoted to Senior Engineer at Microsoft! "
        "I'm so excited to work on Azure infrastructure!"
    )
    response4 = await call_bot(bot_client, TEST_ADMIN_ID, msg4)
    assert response4["success"] is True

    test_results.append(
        {
            "test_name": "Automatic Memory Creation",
            "user_message": msg4,
            "bot_response": response4["response"],
            "expected_behavior": (
                "Bot should autonomously create memory about promotion "
                "without user explicitly asking to remember. Response "
                "should show congratulations and may mention saving info."
            ),
            "tool_expected": "create_memory",
        }
    )

    # Test 5: Combined Tools (Memory + Context)
    print("\n🧪 Test 5: Bot should combine memory search with context awareness")
    msg5 = "Based on my skills, what Azure services should I focus on?"
    response5 = await call_bot(bot_client, TEST_ADMIN_ID, msg5)
    assert response5["success"] is True

    test_results.append(
        {
            "test_name": "Combined Tools Usage",
            "user_message": msg5,
            "bot_response": response5["response"],
            "expected_behavior": (
                "Bot should search memories to recall: Python expertise, "
                "async/await patterns, Microsoft job, Azure infrastructure. "
                "Then provide relevant recommendations. Should demonstrate "
                "memory integration with reasoning."
            ),
            "tool_expected": "search_memories",
        }
    )

    # Batch Judge: Send all results to judge at once
    print("\n" + "=" * 70)
    print("📊 BATCH JUDGING ALL TESTS")
    print("=" * 70)

    judgment = await batch_judge(llm_judge, test_results)

    # Print overall results
    print("\n🏆 OVERALL VERDICT:")
    print(f"  Passes: {judgment['overall_passes']}")
    print(f"  Score: {judgment['overall_score']}")
    print(f"  Reasoning: {judgment['overall_reasoning']}")

    # Print individual test verdicts
    if judgment.get("test_verdicts"):
        print("\n📋 INDIVIDUAL TEST VERDICTS:")
        for verdict in judgment["test_verdicts"]:
            status = "✅ PASS" if verdict["passes"] else "❌ FAIL"
            print(f"\n{status} - {verdict['test_name']}")
            print(f"  Score: {verdict['score']}")
            print(f"  Reasoning: {verdict['reasoning']}")

    # Assert overall success
    assert judgment["overall_passes"] is True, (
        f"Agentic tools test failed. Overall reasoning: {judgment['overall_reasoning']}"
    )
    assert judgment["overall_score"] >= 0.7, "Judge confidence too low"

    print("\n" + "=" * 70)
    print("✅ ALL AGENTIC TOOLS TESTS PASSED!")
    print("=" * 70)


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
async def test_web_search_tool_explicitly(bot_client, setup_test_admin, llm_judge):
    """Test that web search tool works for current information."""
    print("\n🔍 Testing Web Search Tool")

    msg = "Search the web: What is the latest version of FastAPI?"
    response = await call_bot(bot_client, TEST_ADMIN_ID, msg)

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nUser: {msg}")
    print(f"Bot: {bot_response}")

    # Judge should verify web search was used
    judge_prompt = f"""Did the bot use web search to answer this question?

User asked: "{msg}"
Bot responded: "{bot_response}"

The bot should have:
1. Searched the web for FastAPI version information
2. Provided a specific version number (e.g., 0.109.x or similar)
3. Demonstrated that it found current/recent information

Respond with JSON:
{{
    "passes": true/false,
    "reasoning": "explanation",
    "score": 0.0-1.0
}}"""

    user_info = {"id": 999999, "username": "judge"}
    chat_info = {"id": 999999, "type": "private"}

    judge_result = await llm_judge.get_response(
        user_message=judge_prompt,
        user_info=user_info,
        chat_info=chat_info,
        use_complex_model=True,
    )

    import json

    try:
        judgment = json.loads(judge_result)
    except json.JSONDecodeError:
        passes = '"passes": true' in judge_result or "passes: true" in judge_result
        judgment = {
            "passes": passes,
            "reasoning": judge_result,
            "score": 0.8 if passes else 0.2,
        }

    print("\n🔍 LLM Judge Result (Web Search):")
    print(f"  Passes: {judgment['passes']}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, (
        f"Web search tool not properly used. Judge reasoning: {judgment['reasoning']}"
    )
    assert judgment["score"] >= 0.7, "Judge confidence too low"
