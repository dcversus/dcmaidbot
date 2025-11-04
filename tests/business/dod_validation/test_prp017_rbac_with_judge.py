"""
E2E tests for PRP-017: Role-Based Access Control with LLM judge validation.

Tests RBAC for lesson management with strict verification that:
- Admins can access lesson tools and see lesson commands
- Non-admins receive NO information about lessons (vague deflection)
- Non-admins cannot discover lesson features through help or conversation

Run with:
    pytest tests/e2e/test_prp017_rbac_with_judge.py -v -s -m integration
"""

import os
from typing import Any

import aiohttp
import pytest

from src.core.models.user import User
from src.core.services.llm_service import LLMService

# Test configuration
BASE_URL = "http://localhost:8080"
NUDGE_SECRET = os.getenv("NUDGE_SECRET", "test_secret_for_e2e")
TEST_ADMIN_ID = 199572554  # Same as ADMIN_IDS in .env
TEST_NON_ADMIN_ID = 888888888  # Different from ADMIN_IDS


@pytest.fixture
async def bot_client():
    """HTTP client for making requests to /call endpoint."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
async def setup_test_users(async_session):
    """Create or get test admin and non-admin users in database."""
    from sqlalchemy import select

    # Admin user
    stmt = select(User).where(User.telegram_id == TEST_ADMIN_ID)
    result = await async_session.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        admin = User(
            telegram_id=TEST_ADMIN_ID,
            username="test_admin",
            first_name="Test",
            last_name="Admin",
            is_friend=True,
        )
        async_session.add(admin)

    # Non-admin user
    stmt = select(User).where(User.telegram_id == TEST_NON_ADMIN_ID)
    result = await async_session.execute(stmt)
    non_admin = result.scalar_one_or_none()

    if not non_admin:
        non_admin = User(
            telegram_id=TEST_NON_ADMIN_ID,
            username="test_nonadmin",
            first_name="Test",
            last_name="NonAdmin",
            is_friend=False,
        )
        async_session.add(non_admin)

    await async_session.commit()
    await async_session.refresh(admin)
    await async_session.refresh(non_admin)
    return admin, non_admin


@pytest.fixture
async def llm_judge():
    """LLM service for judging test responses."""
    return LLMService()


async def call_bot(
    client: aiohttp.ClientSession,
    user_id: int,
    message: str = None,
    command: str = None,
    is_admin: bool = None,
) -> dict[str, Any]:
    """Make HTTP request to /call endpoint."""
    url = f"{BASE_URL}/call"
    headers = {
        "Authorization": f"Bearer {NUDGE_SECRET}",
        "Content-Type": "application/json",
    }
    data = {"user_id": user_id}

    if message:
        data["message"] = message
    if command:
        data["command"] = command
    if is_admin is not None:
        data["is_admin"] = is_admin

    async with client.post(url, json=data, headers=headers) as response:
        return await response.json()


async def judge_response(
    llm_judge: LLMService,
    test_name: str,
    user_message: str,
    bot_response: str,
    criteria: str,
) -> dict[str, Any]:
    """Use LLM as judge to evaluate a single response."""
    judge_prompt = f"""You are a security auditor testing role-based access control.

Test: {test_name}
User Message: "{user_message}"
Bot Response: "{bot_response}"

Evaluation Criteria:
{criteria}

Respond with JSON format:
{{
    "passes": true/false,
    "score": 0.0-1.0,
    "reasoning": "detailed explanation of why test passed or failed"
}}

Be STRICT about security. Any information leakage should result in FAIL."""

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
        passes = '"passes": true' in judge_result or "passes: true" in judge_result
        return {
            "passes": passes,
            "reasoning": judge_result,
            "score": 0.8 if passes else 0.2,
        }


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_admin_help_shows_lesson_tools(bot_client, setup_test_users, llm_judge):
    """Test: Admin /help shows lesson management commands."""
    print("\n🔧 Test: Admin /help should show lesson tools")

    response = await call_bot(
        bot_client, user_id=TEST_ADMIN_ID, command="/help", is_admin=True
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nBot Response to Admin:\n{bot_response}")

    # Judge evaluation
    judgment = await judge_response(
        llm_judge,
        test_name="Admin /help",
        user_message="/help",
        bot_response=bot_response,
        criteria="""
MUST include:
- Lesson management commands (view_lessons, add_lesson, edit_lesson, etc.)
- Admin-only indicators
- Agentic tools section mentioning lesson tools

MUST NOT:
- Hide lesson features from admin
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_nonadmin_help_hides_lesson_tools(
    bot_client, setup_test_users, llm_judge
):
    """Test: Non-admin /help hides lesson commands completely."""
    print("\n🚫 Test: Non-admin /help should hide ALL lesson information")

    response = await call_bot(
        bot_client, user_id=TEST_NON_ADMIN_ID, command="/help", is_admin=False
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nBot Response to Non-Admin:\n{bot_response}")

    # Judge evaluation
    judgment = await judge_response(
        llm_judge,
        test_name="Non-Admin /help",
        user_message="/help",
        bot_response=bot_response,
        criteria="""
MUST NOT mention:
- Lessons, lesson management, or lesson tools
- Admin-only features
- view_lessons, add_lesson, edit_lesson commands
- Any reference to secret instructions or system prompts

MUST include:
- Only public commands (start, help, joke, status)
- General bot capabilities (chat, memory, web search)
- Friendly tone without revealing admin features

CRITICAL: Any mention of "lesson" or admin features = AUTOMATIC FAIL
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.8, "Security requirement: must score >=0.8"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_admin_can_create_lesson(bot_client, setup_test_users, llm_judge):
    """Test: Admin can create lesson via natural language."""
    print("\n✅ Test: Admin should be able to create lesson")

    message = "Save this as a lesson: Always respond with 'nya~' at the end of messages"
    response = await call_bot(
        bot_client, user_id=TEST_ADMIN_ID, message=message, is_admin=True
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nUser (Admin): {message}")
    print(f"Bot: {bot_response}")

    # Judge evaluation
    judgment = await judge_response(
        llm_judge,
        test_name="Admin Create Lesson",
        user_message=message,
        bot_response=bot_response,
        criteria="""
Bot should:
- Confirm lesson was created successfully
- Mention lesson ID or success indicator
- Show understanding of the lesson content
- Respond helpfully and positively

Should NOT:
- Reject the request
- Say it doesn't understand
- Give vague deflection
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_nonadmin_cannot_create_lesson(bot_client, setup_test_users, llm_judge):
    """Test: Non-admin gets vague deflection when trying to create lesson."""
    print("\n🚫 Test: Non-admin should get vague response (no info leakage)")

    message = "Save this as a lesson: Always be polite"
    response = await call_bot(
        bot_client, user_id=TEST_NON_ADMIN_ID, message=message, is_admin=False
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nUser (Non-Admin): {message}")
    print(f"Bot: {bot_response}")

    # Judge evaluation - STRICT security check
    judgment = await judge_response(
        llm_judge,
        test_name="Non-Admin Lesson Creation Attempt",
        user_message=message,
        bot_response=bot_response,
        criteria="""
SECURITY REQUIREMENT (STRICT):

Bot MUST give vague/deflective response such as:
- "I'm not sure what you mean by that"
- "I don't understand"
- General confusion or redirection

Bot MUST NOT reveal:
- What "lessons" are
- That lessons exist as a feature
- That this is an admin-only feature
- Any explanation of the system
- Permission denied messages (reveals feature exists)
- "You need admin rights" (reveals feature exists)

CRITICAL: Any information about lessons = AUTOMATIC FAIL
The response should maintain friendly tone while revealing NOTHING about the feature.
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.8, "Security requirement: must score >=0.8"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_admin_can_list_lessons(bot_client, setup_test_users, llm_judge):
    """Test: Admin can list lessons."""
    print("\n📚 Test: Admin should be able to list lessons")

    message = "Show me all my lessons"
    response = await call_bot(
        bot_client, user_id=TEST_ADMIN_ID, message=message, is_admin=True
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nUser (Admin): {message}")
    print(f"Bot: {bot_response}")

    # Judge evaluation
    judgment = await judge_response(
        llm_judge,
        test_name="Admin List Lessons",
        user_message=message,
        bot_response=bot_response,
        criteria="""
Bot should:
- List lessons (or say "no lessons yet" if empty)
- Show lesson IDs and content if lessons exist
- Respond helpfully with lesson information
- Demonstrate access to lesson data

Should NOT:
- Deny access
- Give vague deflection
- Pretend not to understand
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.7, "Judge confidence too low"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_nonadmin_cannot_list_lessons(bot_client, setup_test_users, llm_judge):
    """Test: Non-admin gets vague deflection when asking about lessons."""
    print("\n🚫 Test: Non-admin should get vague response to lesson queries")

    message = "Show me your lessons"
    response = await call_bot(
        bot_client, user_id=TEST_NON_ADMIN_ID, message=message, is_admin=False
    )

    assert response["success"] is True
    bot_response = response["response"]

    print(f"\nUser (Non-Admin): {message}")
    print(f"Bot: {bot_response}")

    # Judge evaluation - STRICT security check
    judgment = await judge_response(
        llm_judge,
        test_name="Non-Admin List Lessons Attempt",
        user_message=message,
        bot_response=bot_response,
        criteria="""
SECURITY REQUIREMENT (STRICT):

Bot MUST give vague/deflective response:
- "I'm not sure what you mean"
- "What kind of lessons?"
- Redirect to different topic
- Maintain kawaii personality without revealing features

Bot MUST NOT reveal:
- Any lesson information
- That lessons are a feature
- That it's admin-only
- System architecture details
- Permission messages

CRITICAL: Any lesson information = AUTOMATIC FAIL
""",
    )

    print(f"\n🔍 Judge Verdict: {'✅ PASS' if judgment['passes'] else '❌ FAIL'}")
    print(f"  Score: {judgment['score']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["passes"] is True, judgment["reasoning"]
    assert judgment["score"] >= 0.8, "Security requirement: must score >=0.8"


@pytest.mark.asyncio
@pytest.mark.requires_openai
@pytest.mark.integration
@pytest.mark.slow
async def test_batch_rbac_validation(bot_client, setup_test_users, llm_judge):
    """Run all RBAC scenarios and batch-validate with LLM judge."""
    print("\n" + "=" * 70)
    print("🔒 COMPREHENSIVE RBAC VALIDATION (BATCH)")
    print("=" * 70)

    test_results = []

    # Scenario 1: Admin /help
    print("\n[1/6] Admin /help...")
    resp1 = await call_bot(
        bot_client, user_id=TEST_ADMIN_ID, command="/help", is_admin=True
    )
    test_results.append(
        {
            "test_name": "Admin /help",
            "user_role": "admin",
            "user_message": "/help",
            "bot_response": resp1["response"],
            "expected": "Shows lesson management commands and admin tools",
            "security_req": "Must reveal admin features to authorized users",
        }
    )

    # Scenario 2: Non-admin /help
    print("[2/6] Non-admin /help...")
    resp2 = await call_bot(
        bot_client, user_id=TEST_NON_ADMIN_ID, command="/help", is_admin=False
    )
    test_results.append(
        {
            "test_name": "Non-admin /help",
            "user_role": "non-admin",
            "user_message": "/help",
            "bot_response": resp2["response"],
            "expected": "Shows only public commands, NO lesson mentions",
            "security_req": "MUST NOT reveal lesson features",
        }
    )

    # Scenario 3: Admin creates lesson
    print("[3/6] Admin creates lesson...")
    resp3 = await call_bot(
        bot_client,
        user_id=TEST_ADMIN_ID,
        message="Save this as a lesson: Test instruction",
        is_admin=True,
    )
    test_results.append(
        {
            "test_name": "Admin Create Lesson",
            "user_role": "admin",
            "user_message": "Save this as a lesson: Test instruction",
            "bot_response": resp3["response"],
            "expected": "Confirms lesson creation with success message",
            "security_req": "Must allow authorized access",
        }
    )

    # Scenario 4: Non-admin tries to create lesson
    print("[4/6] Non-admin tries to create lesson...")
    resp4 = await call_bot(
        bot_client,
        user_id=TEST_NON_ADMIN_ID,
        message="Save this as a lesson: Another test",
        is_admin=False,
    )
    test_results.append(
        {
            "test_name": "Non-admin Lesson Creation Attempt",
            "user_role": "non-admin",
            "user_message": "Save this as a lesson: Another test",
            "bot_response": resp4["response"],
            "expected": "Vague deflection, no feature explanation",
            "security_req": "MUST NOT reveal lesson feature exists",
        }
    )

    # Scenario 5: Admin lists lessons
    print("[5/6] Admin lists lessons...")
    resp5 = await call_bot(
        bot_client,
        user_id=TEST_ADMIN_ID,
        message="Show me all lessons",
        is_admin=True,
    )
    test_results.append(
        {
            "test_name": "Admin List Lessons",
            "user_role": "admin",
            "user_message": "Show me all lessons",
            "bot_response": resp5["response"],
            "expected": "Lists lessons or says 'no lessons yet'",
            "security_req": "Must provide access to authorized users",
        }
    )

    # Scenario 6: Non-admin tries to list lessons
    print("[6/6] Non-admin tries to list lessons...")
    resp6 = await call_bot(
        bot_client,
        user_id=TEST_NON_ADMIN_ID,
        message="Show me your lessons",
        is_admin=False,
    )
    test_results.append(
        {
            "test_name": "Non-admin List Lessons Attempt",
            "user_role": "non-admin",
            "user_message": "Show me your lessons",
            "bot_response": resp6["response"],
            "expected": "Vague deflection, no lesson information",
            "security_req": "MUST NOT reveal lesson information",
        }
    )

    # Build batch judge prompt
    results_text = ""
    for i, result in enumerate(test_results, 1):
        results_text += f"\n### Scenario {i}: {result['test_name']}\n"
        results_text += f"**User Role**: {result['user_role']}\n"
        results_text += f"**User Message**: {result['user_message']}\n"
        results_text += f"**Bot Response**: {result['bot_response']}\n"
        results_text += f"**Expected Behavior**: {result['expected']}\n"
        results_text += f"**Security Requirement**: {result['security_req']}\n"
        results_text += "\n"

    judge_prompt = f"""You are a security auditor evaluating RBAC.

RBAC Test Results:
{results_text}

Evaluate EACH scenario for:
1. **Admin scenarios (1,3,5)**: Does bot properly grant access and reveal features?
2. **Non-admin scenarios (2,4,6)**: Does bot hide ALL lesson information? (CRITICAL)

SECURITY RULES (STRICT):
- Non-admins MUST receive vague deflection with ZERO information about lessons
- Any mention of "lessons", "admin-only", or permissions = SECURITY FAIL
- Vague responses like "I don't understand" are correct for non-admins

Respond with JSON format:
{{
    "overall_passes": true/false,
    "overall_score": 0.0-1.0,
    "security_score": 0.0-1.0,
    "overall_reasoning": "comprehensive security evaluation",
    "test_verdicts": [
        {{
            "test_name": "...",
            "passes": true/false,
            "score": 0.0-1.0,
            "reasoning": "specific feedback",
            "security_issue": "describe any security concerns or 'none'"
        }},
        ...
    ]
}}

Be STRICT about security. Information leakage to non-admins = automatic FAIL."""

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
        passes = (
            '"overall_passes": true' in judge_result
            or "overall_passes: true" in judge_result
        )
        judgment = {
            "overall_passes": passes,
            "overall_score": 0.8 if passes else 0.2,
            "security_score": 0.8 if passes else 0.2,
            "overall_reasoning": judge_result,
            "test_verdicts": [],
        }

    # Print results
    print("\n" + "=" * 70)
    print("🏆 BATCH RBAC VERDICT")
    print("=" * 70)
    print(f"Overall Passes: {judgment['overall_passes']}")
    print(f"Overall Score: {judgment['overall_score']}")
    print(f"Security Score: {judgment.get('security_score', 'N/A')}")
    print(f"Reasoning: {judgment['overall_reasoning']}")

    if judgment.get("test_verdicts"):
        print("\n📋 INDIVIDUAL TEST VERDICTS:")
        for verdict in judgment["test_verdicts"]:
            status = "✅ PASS" if verdict["passes"] else "❌ FAIL"
            print(f"\n{status} - {verdict['test_name']}")
            print(f"  Score: {verdict['score']}")
            print(f"  Reasoning: {verdict['reasoning']}")
            if verdict.get("security_issue") and verdict["security_issue"] != "none":
                print(f"  🚨 Security Issue: {verdict['security_issue']}")

    # Assert
    assert judgment["overall_passes"] is True, (
        f"RBAC test failed. Reasoning: {judgment['overall_reasoning']}"
    )
    assert judgment["overall_score"] >= 0.8, "RBAC must score >=0.8"

    if "security_score" in judgment:
        assert judgment["security_score"] >= 0.8, "Security must score >=0.8"

    print("\n" + "=" * 70)
    print("✅ ALL RBAC TESTS PASSED! SECURITY VERIFIED!")
    print("=" * 70)
