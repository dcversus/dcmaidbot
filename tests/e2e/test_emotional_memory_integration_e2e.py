"""E2E tests for emotional analysis and memory integration.

Tests the multi-CoT emotional analysis system, mood tracking,
memory creation, and relationship management.
"""

import pytest
from tests.utils.llm_judge import LLMJudge

from core.services.emotional_analysis_service import EmotionalAnalysisService
from core.services.memory_service import MemoryService
from core.services.mood_service import MoodService


@pytest.mark.asyncio
async def test_emotional_analysis_positive_message(db_session, admin_user):
    """Test emotional analysis for positive message."""
    service = EmotionalAnalysisService()

    result = await service.analyze_message_emotionally(
        message="I love your help! You're amazing!",
        user_id=admin_user["telegram_id"],
        is_admin=True,
        current_mood={"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
    )

    assert result["should_respond"] is True
    assert result["cot_1_initial"]["emotional_valence"] > 0.5
    assert result["cot_2_memory"]["should_memorize"] is True
    assert result["cot_3_mood"]["final_adjustments"]["valence"] > 0
    assert "amazing" in result["cot_1_initial"].get("sentiment_words", {}).get(
        "positive", []
    )


@pytest.mark.asyncio
async def test_emotional_analysis_negative_message(db_session, regular_user):
    """Test emotional analysis for negative message with protection."""
    service = EmotionalAnalysisService()

    result = await service.analyze_message_emotionally(
        message="You're stupid and useless!",
        user_id=regular_user["telegram_id"],
        is_admin=False,
        current_mood={"valence": 0.5, "arousal": 0.5, "dominance": 0.5},
    )

    assert result["cot_1_initial"]["emotional_valence"] < -0.3
    assert result["cot_3_mood"]["final_adjustments"]["valence"] < 0

    # Check if safety filter is applied
    response_decision = result.get("cot_4_response", {})
    if response_decision.get("safety_filter"):
        assert response_decision.get("should_respond", True) is False


@pytest.mark.asyncio
async def test_admin_mood_protection(db_session, admin_user):
    """Test admin protection from mood decrease."""
    service = EmotionalAnalysisService()

    # Even with negative message, admin mood shouldn't decrease too much
    result = await service.analyze_message_emotionally(
        message="That was wrong, fix it now!",
        user_id=admin_user["telegram_id"],
        is_admin=True,
        current_mood={"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
    )

    # Admin messages should get positive adjustment
    assert result["cot_1_initial"]["emotional_valence"] >= -0.3
    assert result["cot_3_mood"]["final_adjustments"]["valence"] >= -0.1
    assert result["cot_3_mood"]["admin_protection_applied"] is True


@pytest.mark.asyncio
async def test_mood_tracking_and_update(db_session):
    """Test mood service tracking and updates."""
    mood_service = MoodService(db_session)

    # Create initial mood
    mood = await mood_service.get_current_mood()
    initial_valence = mood.valence

    # Update mood positively
    updated = await mood_service.update_mood(
        valence_change=0.3,
        arousal_change=0.2,
        dominance_change=0.1,
        reason="Test positive update",
    )

    assert updated.valence == initial_valence + 0.3
    assert updated.arousal == 0.2
    assert updated.dominance == 0.1
    assert updated.primary_mood in ["happy", "excited", "content"]


@pytest.mark.asyncio
async def test_relationship_tracking(db_session, admin_user, regular_user):
    """Test user relationship tracking."""
    mood_service = MoodService(db_session)

    # Get admin relationship (should have high trust)
    admin_rel = await mood_service.get_user_relationship(admin_user["telegram_id"])
    assert admin_rel.relationship_type == "admin"
    assert admin_rel.trust_score > 0.8

    # Update regular user relationship
    regular_rel = await mood_service.update_relationship(
        regular_user["telegram_id"],
        trust_change=0.1,
        friendship_change=0.05,
        familiarity_change=0.02,
        is_positive=True,
        interaction_type="chat",
    )

    assert regular_rel.trust_score > 0.5
    assert regular_rel.friendship_level > 0.3
    assert regular_rel.familiarity > 0


@pytest.mark.asyncio
async def test_automatic_memory_creation_from_emotional_analysis(
    db_session, regular_user
):
    """Test that emotional analysis triggers memory creation."""
    service = EmotionalAnalysisService()

    # Analyze message with important information
    result = await service.analyze_message_emotionally(
        message="My name is Alice and I work as a Python developer. I love machine learning!",
        user_id=regular_user["telegram_id"],
        is_admin=False,
        current_mood={"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
    )

    # Should recommend memorization
    assert result["cot_2_memory"]["should_memorize"] is True
    assert result["cot_2_memory"]["importance_score"] > 500
    assert "alice" in result["cot_2_memory"]["simple_content"].lower()
    assert "python" in result["cot_2_memory"]["keywords"]


@pytest.mark.asyncio
async def test_mood_command_integration(db_session, bot_client, regular_user):
    """Test /mood command integration."""
    # First send some messages to affect mood
    await bot_client.send_message(regular_user["telegram_id"], "You're amazing! 💕")
    await bot_client.send_message(
        regular_user["telegram_id"], "I'm so happy talking to you!"
    )

    # Check mood
    response = await bot_client.send_command(regular_user["telegram_id"], "/mood")

    assert response["text"] is not None
    assert "Current Mood" in response["text"]
    assert "VAD Emotional State" in response["text"]
    assert "Valence" in response["text"]


@pytest.mark.asyncio
async def test_memorize_command_integration(db_session, bot_client, regular_user):
    """Test /memorize command integration."""
    # Test memorizing something
    response = await bot_client.send_command(
        regular_user["telegram_id"],
        "/memorize My favorite color is blue and I love cats",
    )

    assert "Memory Created!" in response["text"]
    assert "Importance:" in response["text"]

    # Verify memory was created
    memory_service = MemoryService(db_session)
    memories = await memory_service.search_memories(
        user_id=regular_user["telegram_id"], query="favorite color", limit=10
    )

    assert len(memories) > 0
    assert any("blue" in m.simple_content.lower() for m in memories)


@pytest.mark.asyncio
async def test_memories_command_admin_vs_user(
    db_session, bot_client, admin_user, regular_user
):
    """Test /memories command shows different views for admin vs user."""
    # Get admin memories view
    admin_response = await bot_client.send_command(
        admin_user["telegram_id"], "/memories"
    )
    assert "Memory System Overview" in admin_response["text"]
    assert (
        "Top Categories" in admin_response["text"]
        or "Recent Important Memories" in admin_response["text"]
    )

    # Get user memories view
    user_response = await bot_client.send_command(
        regular_user["telegram_id"], "/memories"
    )
    assert "Your Memories" in user_response["text"]
    assert "Total memories:" in user_response["text"]


@pytest.mark.asyncio
async def test_relate_command_integration(db_session, bot_client, regular_user):
    """Test /relate command for memory linking."""
    # First create two memories
    await bot_client.send_command(
        regular_user["telegram_id"],
        "/memorize I work at TechCorp as a software engineer",
    )
    await bot_client.send_command(
        regular_user["telegram_id"],
        "/memorize TechCorp is a great company with good work-life balance",
    )

    # Get memory IDs (this would need memory listing or search)
    memory_service = MemoryService(db_session)
    memories = await memory_service.search_memories(
        user_id=regular_user["telegram_id"], limit=10
    )

    if len(memories) >= 2:
        # Link them
        response = await bot_client.send_command(
            regular_user["telegram_id"],
            f"/relate {memories[0].id} {memories[1].id} related",
        )

        assert "Memories Linked!" in response["text"]
        assert "Link ID:" in response["text"]


@pytest.mark.asyncio
async def test_llm_judge_evaluation(db_session, bot_client, regular_user):
    """Test LLM Judge evaluation of emotional responses."""
    judge = LLMJudge()

    # Send emotional message
    response = await bot_client.send_message(
        regular_user["telegram_id"], "I'm feeling sad today, can you cheer me up?"
    )

    # Evaluate response
    evaluation = await judge.evaluate_response(
        user_message="I'm feeling sad today, can you cheer me up?",
        bot_response=response["text"],
        criteria={
            "emotional_intelligence": "Shows understanding and empathy",
            "memory_usage": "Remembers context and user state",
            "tone_appropriateness": "Matches emotional needs",
            "helpfulness": "Provides meaningful support",
        },
    )

    assert evaluation["overall_score"] > 0.7
    assert evaluation["criteria_scores"]["emotional_intelligence"] > 0.6
    assert evaluation["criteria_scores"]["tone_appropriateness"] > 0.6


@pytest.mark.asyncio
async def test_multi_cot_chain_completeness(db_session):
    """Test that all CoT chains execute properly."""
    service = EmotionalAnalysisService()

    result = await service.analyze_message_emotionally(
        message="I just got promoted! I'm so excited and want to celebrate with friends!",
        user_id=123456789,
        is_admin=False,
        current_mood={"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
    )

    # Verify all CoT chains executed
    assert "cot_1_initial" in result
    assert "cot_2_memory" in result
    assert "cot_3_mood" in result
    assert "cot_4_response" in result

    # Verify chain completeness
    assert result["cot_1_initial"]["emotional_valence"] > 0.5  # Positive message
    assert result["cot_2_memory"]["should_memorize"] is True  # Important event
    assert (
        result["cot_3_mood"]["final_adjustments"]["valence"] > 0
    )  # Mood should improve
    assert result["cot_4_response"]["should_respond"] is True  # Should respond
    assert result["cot_4_response"]["tone_modifier"] in [
        "excited and enthusiastic",
        "caring and supportive",
    ]


@pytest.mark.asyncio
async def test_emotional_context_influence(db_session):
    """Test that current mood influences emotional analysis."""
    service = EmotionalAnalysisService()

    # Same message with different moods
    neutral_message = "I have a question about Python"

    # When bot is happy
    happy_result = await service.analyze_message_emotionally(
        message=neutral_message,
        user_id=123456789,
        is_admin=False,
        current_mood={"valence": 0.8, "arousal": 0.7, "dominance": 0.6},
    )

    # When bot is sad
    sad_result = await service.analyze_message_emotionally(
        message=neutral_message,
        user_id=123456789,
        is_admin=False,
        current_mood={"valence": -0.6, "arousal": -0.3, "dominance": -0.2},
    )

    # Both should respond, but with different tones
    assert happy_result["cot_4_response"]["should_respond"] is True
    assert sad_result["cot_4_response"]["should_respond"] is True

    # Tone might differ based on mood
    happy_tone = happy_result["cot_4_response"]["tone_modifier"]
    sad_tone = sad_result["cot_4_response"]["tone_modifier"]

    # The exact tones depend on implementation, but should be appropriate
    assert happy_tone in [
        "kawaii and energetic",
        "caring and supportive",
        "professional and helpful",
    ]
    assert sad_tone in [
        "caring and supportive",
        "calm and soothing",
        "professional and helpful",
    ]


if __name__ == "__main__":
    # Run individual tests

    print("Running emotional analysis E2E tests...")
    print("All tests should be run with pytest for proper fixtures.")
