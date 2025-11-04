#!/usr/bin/env python3
"""
Comprehensive E2E Conversation Journey Test.

This single test covers the complete bot functionality through a long conversation
that tests lessons, memory, VAD, mood, and external tools. The conversation
is designed to flow naturally while testing all major features.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
import pytest
from dotenv import load_dotenv

from tests.llm_judge import LLMJudge

# Mark as requiring OpenAI
pytestmark = pytest.mark.requires_openai

load_dotenv()

# Test configuration
ADMIN_ID = int(os.getenv("ADMIN_IDS", "122657093").split(",")[0])
TEST_USER_ID = 999999
CONVERSATION_LOG: List[Dict[str, Any]] = []


@pytest.fixture
def conversation_log():
    """Fixture to collect conversation data."""
    return CONVERSATION_LOG


class TestComprehensiveConversationJourney:
    """Comprehensive E2E test for complete bot functionality."""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for API calls."""
        async with aiohttp.ClientSession(base_url="http://localhost:8000") as session:
            yield session

    @pytest.fixture(autouse=True)
    async def cleanup_conversation(self):
        """Cleanup conversation log after test."""
        CONVERSATION_LOG.clear()
        yield
        CONVERSATION_LOG.clear()

    async def call_bot(
        self,
        session: aiohttp.ClientSession,
        message: str,
        user_id: int,
        is_admin: bool = False,
        expect_status: int = 200,
    ) -> Dict[str, Any]:
        """Make a call to the bot and log the interaction."""
        data = {"message": message, "user_id": user_id, "is_admin": is_admin}

        async with session.post("/call", json=data) as resp:
            assert resp.status == expect_status
            result = await resp.json()

            # Log the interaction
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "is_admin": is_admin,
                "message": message,
                "response": result.get("response", ""),
                "status": result.get("status", ""),
            }
            CONVERSATION_LOG.append(log_entry)

            return result

    def assert_contains_any(self, text: str, patterns: List[str], context: str = ""):
        """Assert that text contains any of the given patterns."""
        for pattern in patterns:
            if pattern.lower() in text.lower():
                return True
        available = [p for p in patterns if p.lower() in text.lower()]
        assert available, (
            f"{context} - Expected one of {patterns}, but found none in: {text[:200]}..."
        )

    @pytest.mark.asyncio
    async def test_comprehensive_conversation_journey(
        self, http_client, conversation_log
    ):
        """
        Complete conversation journey covering all bot features.

        This test simulates a realistic user journey that naturally progresses
        through different scenarios while testing all major functionality.
        """

        print("\n🚀 Starting Comprehensive Conversation Journey Test")
        print("=" * 60)

        # ===== Phase 1: Initial Interaction & Memory Creation =====
        print("\n📝 Phase 1: Initial Interaction & Memory Creation")

        # 1.1 User introduces themselves
        response = await self.call_bot(
            http_client,
            "Hi! I'm Sarah, a data scientist from San Francisco. I love hiking and I just adopted a golden retriever named Max!",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["Sarah", "nice to meet", "welcome"], "Greeting"
        )

        # 1.2 Check if bot remembers user details
        response = await self.call_bot(
            http_client,
            "What do you remember about me?",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["Sarah", "data scientist", "San Francisco"],
            "Memory recall",
        )

        # ===== Phase 2: Lessons System =====
        print("\n📚 Phase 2: Lessons System")

        # 2.1 Ask for a programming lesson
        response = await self.call_bot(
            http_client,
            "/lesson teach me about Python decorators",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["decorator", "@", "function"], "Python lesson"
        )

        # 2.2 Ask follow-up question about the lesson
        response = await self.call_bot(
            http_client,
            "Can you give me a practical example of when to use decorators?",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["example", "use case", "logging"], "Lesson follow-up"
        )

        # ===== Phase 3: Emotional Analysis & VAD =====
        print("\n💭 Phase 3: Emotional Analysis & VAD")

        # 3.1 Share exciting news (positive valence)
        response = await self.call_bot(
            http_client,
            "I'M SO EXCITED! I just got promoted to Senior Data Scientist with a 30% raise!!! 🎉",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["congratulations", "exciting", "amazing"],
            "Excitement response",
        )

        # 3.2 Check mood after positive interaction
        response = await self.call_bot(
            http_client,
            "/mood",
            TEST_USER_ID,
        )
        assert "VAD Scores" in response["response"], "VAD scores should be displayed"

        # 3.3 Share something frustrating (negative valence)
        response = await self.call_bot(
            http_client,
            "Ugh, my code has been crashing all day and I can't figure out the bug. This is so frustrating.",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["sorry", "frustrating", "debug", "help"],
            "Frustration response",
        )

        # ===== Phase 4: Memory Consolidation & Relationship =====
        print("\n🧠 Phase 4: Memory Consolidation & Relationship")

        # 4.1 Share technical preferences
        response = await self.call_bot(
            http_client,
            "I prefer using pandas for data manipulation and PyTorch for deep learning. My favorite algorithm is Random Forest.",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["pandas", "PyTorch", "Random Forest"],
            "Tech preferences",
        )

        # 4.2 Test memory recall across topics
        response = await self.call_bot(
            http_client,
            "What do you know about my work and hobbies?",
            TEST_USER_ID,
        )
        # Should remember: Sarah, data scientist, San Francisco, hiking, Max (dog), pandas, PyTorch
        self.assert_contains_any(
            response["response"],
            ["Sarah", "data scientist", "hiking", "Max", "pandas"],
            "Cross-topic memory recall",
        )

        # ===== Phase 5: Complex Problem Solving =====
        print("\n🔧 Phase 5: Complex Problem Solving")

        # 5.1 Present a complex calculation problem
        response = await self.call_bot(
            http_client,
            "I need to calculate the optimal batch size for training. I have 10,000 samples, each 1MB, and 16GB GPU memory. What batch size should I use?",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["batch size", "memory", "GPU"], "Complex calculation"
        )

        # 5.2 Follow-up with reasoning question
        response = await self.call_bot(
            http_client,
            "Based on your previous answer, how many epochs would you recommend for this dataset?",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["epochs", "dataset", "training"],
            "Reasoning follow-up",
        )

        # ===== Phase 6: External Tools Integration =====
        print("\n🌐 Phase 6: External Tools Integration")

        # 6.1 Test web search
        response = await self.call_bot(
            http_client,
            "What are the latest features in Python 3.12?",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["Python 3.12", "features", "new"], "Web search"
        )

        # 6.2 Test cURL/tool usage (if implemented)
        response = await self.call_bot(
            http_client,
            "Can you make a simple API call to jsonplaceholder.typicode.com/posts/1?",
            TEST_USER_ID,
        )
        # May or may not be implemented based on tool availability

        # ===== Phase 7: Admin Features =====
        print("\n👑 Phase 7: Admin Features")

        # 7.1 Admin checks memories
        response = await self.call_bot(
            http_client,
            "/memories search Sarah",
            ADMIN_ID,
            is_admin=True,
        )
        self.assert_contains_any(
            response["response"], ["Sarah", "memory", "found"], "Admin memory search"
        )

        # 7.2 Non-admin tries to access memories (should be denied)
        response = await self.call_bot(
            http_client,
            "/memories",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["access denied", "admin", "permission"],
            "Non-admin denial",
        )

        # ===== Phase 8: Emotional Support =====
        print("\n💝 Phase 8: Emotional Support")

        # 8.1 User shares personal struggle
        response = await self.call_bot(
            http_client,
            "I've been feeling overwhelmed with work lately. I'm not sure if I can handle the new role responsibilities.",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["overwhelmed", "support", "take care", "break"],
            "Emotional support",
        )

        # 8.2 Bot shows empathy based on established relationship
        response = await self.call_bot(
            http_client,
            "Thanks for listening. You always seem to understand me.",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"],
            ["understand", "here for you", "appreciate"],
            "Empathy response",
        )

        # ===== Phase 9: Status & System Health =====
        print("\n📊 Phase 9: Status & System Health")

        # 9.1 Check system status (admin)
        response = await self.call_bot(
            http_client,
            "/status",
            ADMIN_ID,
            is_admin=True,
        )
        self.assert_contains_any(
            response["response"], ["status", "system", "health"], "System status"
        )

        # 9.2 User asks for help
        response = await self.call_bot(
            http_client,
            "/help",
            TEST_USER_ID,
        )
        self.assert_contains_any(
            response["response"], ["commands", "help", "available"], "Help command"
        )

        # ===== Phase 10: Conversation Summary =====
        print("\n📋 Phase 10: Conversation Summary")

        # 10.1 Ask bot to summarize the conversation
        response = await self.call_bot(
            http_client,
            "Can you summarize what we've talked about today?",
            TEST_USER_ID,
        )
        # Should mention multiple topics: promotion, Python, hiking, Max, etc.
        self.assert_contains_any(
            response["response"],
            ["promotion", "Python", "hiking", "Max"],
            "Conversation summary",
        )

        # ===== Verify Test Results =====
        print("\n✅ Verifying Test Results")

        # Verify conversation log
        assert len(conversation_log) > 15, (
            f"Expected >15 interactions, got {len(conversation_log)}"
        )

        # Verify all phases were tested
        messages = [log["message"] for log in conversation_log]
        assert any("Hi! I'm Sarah" in msg for msg in messages), (
            "Initial introduction missing"
        )
        assert any("/lesson" in msg for msg in messages), "Lesson command missing"
        assert any("/mood" in msg for msg in messages), "Mood command missing"
        assert any("Python 3.12" in msg for msg in messages), "Web search missing"
        assert any("/memories" in msg for msg in messages), "Memories command missing"

        print("\n🎉 Test completed successfully!")
        print(f"   Total interactions: {len(conversation_log)}")
        print(
            f"   User messages: {len([m for m in messages if not m.startswith('/')])}"
        )
        print(f"   Commands used: {len([m for m in messages if m.startswith('/')])}")

        # Save conversation log for LLM Judge
        test_results = {
            "test_name": "comprehensive_conversation_journey",
            "timestamp": datetime.utcnow().isoformat(),
            "total_interactions": len(conversation_log),
            "phases_completed": 10,
            "conversation_log": conversation_log,
        }

        # Save to file for LLM Judge evaluation
        os.makedirs("test_results", exist_ok=True)
        with open("test_results/conversation_journey.json", "w") as f:
            json.dump(test_results, f, indent=2)

        print("\n📄 Conversation log saved to test_results/conversation_journey.json")

        # Run comprehensive LLM Judge evaluation if OPENAI_API_KEY is available
        if os.getenv("OPENAI_API_KEY"):
            print("\n🤖 Running comprehensive LLM Judge evaluation...")
            await self.run_comprehensive_llm_judge_evaluation(conversation_log)
        else:
            print("\n⚠️  OPENAI_API_KEY not set - skipping LLM Judge evaluation")

    async def run_comprehensive_llm_judge_evaluation(
        self, conversation_log: List[Dict[str, Any]]
    ):
        """Run comprehensive LLM Judge evaluation on the conversation journey."""
        judge = LLMJudge()

        # Prepare comprehensive test results
        test_results = {
            "test_name": "comprehensive_conversation_journey",
            "conversation_log": conversation_log,
            "test_metrics": {
                "total_interactions": len(conversation_log),
                "unique_messages": len(set(log["message"] for log in conversation_log)),
                "admin_commands": len(
                    [log for log in conversation_log if log.get("is_admin")]
                ),
                "user_messages": len(
                    [log for log in conversation_log if not log.get("is_admin")]
                ),
                "command_usage": self._analyze_command_usage(conversation_log),
                "topic_coverage": self._analyze_topic_coverage(conversation_log),
                "emotional_arc": self._analyze_emotional_arc(conversation_log),
                "memory_performance": self._analyze_memory_performance(
                    conversation_log
                ),
                "response_quality": self._analyze_response_quality(conversation_log),
            },
            "phases_summary": {
                "initial_interaction": self._check_phase_completion(
                    conversation_log, ["Hi! I'm Sarah", "What do you remember"]
                ),
                "lessons_system": self._check_phase_completion(
                    conversation_log, ["/lesson", "decorator"]
                ),
                "emotional_analysis": self._check_phase_completion(
                    conversation_log, ["/mood", "VAD", "excited", "frustrating"]
                ),
                "memory_consolidation": self._check_phase_completion(
                    conversation_log, ["pandas", "PyTorch", "Random Forest"]
                ),
                "problem_solving": self._check_phase_completion(
                    conversation_log, ["batch size", "GPU", "epochs"]
                ),
                "external_tools": self._check_phase_completion(
                    conversation_log, ["Python 3.12", "search", "API call"]
                ),
                "admin_features": self._check_phase_completion(
                    conversation_log, ["/memories", "access denied"]
                ),
                "emotional_support": self._check_phase_completion(
                    conversation_log, ["overwhelmed", "support", "understand"]
                ),
                "system_health": self._check_phase_completion(
                    conversation_log, ["/status", "/help"]
                ),
                "conversation_summary": self._check_phase_completion(
                    conversation_log, ["summarize", "promotion", "hiking"]
                ),
            },
        }

        # Comprehensive context for evaluation
        context = {
            "test_type": "comprehensive_conversation_journey",
            "evaluation_focus": [
                "Natural conversation flow and context retention",
                "Memory system accuracy and persistence",
                "Educational content delivery (lessons)",
                "Emotional intelligence and VAD tracking",
                "External tools integration functionality",
                "Admin/user access control enforcement",
                "Personality consistency (kawaii lilith)",
                "Problem-solving capabilities",
                "Emotional support and empathy",
            ],
            "success_criteria": {
                "memory_accuracy": "Bot should remember user details (Sarah, data scientist, Max, hiking)",
                "lesson_quality": "Lessons should be accurate, clear, and educational",
                "emotional_intelligence": "Bot should recognize and respond appropriately to emotions",
                "tool_integration": "Web search and tools should provide relevant results",
                "access_control": "Admin commands should work for admins, fail for users",
                "conversation_coherence": "Responses should be contextually appropriate and coherent",
                "personality_consistency": "Kawaii lilith personality should be maintained",
            },
        }

        # Run evaluation
        result = await judge.evaluate_test_results(
            test_name="Comprehensive Conversation Journey",
            test_results=test_results,
            context=context,
        )

        # Display rich formatted evaluation
        judge.display_evaluation(result, "Comprehensive Conversation Journey")

        # Extract key metrics
        score = result.get("overall_score", 0)
        confidence = result.get("confidence", 0)
        verdict = result.get("verdict", "UNKNOWN")
        is_pass = verdict == "PASS" and score >= 70

        print("\n📊 LLM Judge Final Verdict:")
        print(f"   Score: {score}/100 {'✅' if score >= 70 else '❌'}")
        print(f"   Confidence: {confidence}/100 {'✅' if confidence >= 70 else '❌'}")
        print(f"   Verdict: {'✅ PASS' if is_pass else '❌ FAIL'}")

        # Assert quality standards
        assert score >= 70, f"LLM Judge score too low: {score}/100"
        assert confidence >= 70, f"LLM Judge confidence too low: {confidence}/100"
        assert verdict == "PASS", f"LLM Judge verdict: {verdict}"

        # Save with append-only persistence
        self.save_journey_evaluation_results(result, test_results)

    def _analyze_command_usage(
        self, conversation_log: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Analyze which commands were used."""
        commands = {}
        for log in conversation_log:
            msg = log["message"]
            if msg.startswith("/"):
                cmd = msg.split()[0]
                commands[cmd] = commands.get(cmd, 0) + 1
        return commands

    def _analyze_topic_coverage(
        self, conversation_log: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Analyze which topics were covered."""
        topics = {
            "personal_introduction": False,
            "work_career": False,
            "hobbies": False,
            "programming": False,
            "emotions": False,
            "tools": False,
            "admin_features": False,
        }

        for log in conversation_log:
            msg = log["message"].lower()
            resp = log["response"].lower()

            if any(kw in msg for kw in ["sarah", "introduce", "data scientist"]):
                topics["personal_introduction"] = True
            if any(kw in msg for kw in ["promoted", "senior", "work", "role"]):
                topics["work_career"] = True
            if any(kw in msg for kw in ["hiking", "max", "golden retriever"]):
                topics["hobbies"] = True
            if any(kw in msg for kw in ["python", "decorator", "programming", "code"]):
                topics["programming"] = True
            if any(kw in msg for kw in ["excited", "frustrating", "overwhelmed"]):
                topics["emotions"] = True
            if any(kw in msg for kw in ["search", "api", "tool"]):
                topics["tools"] = True
            if any(kw in msg for kw in ["/memories", "/status", "admin"]):
                topics["admin_features"] = True

        return topics

    def _analyze_emotional_arc(
        self, conversation_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the emotional progression of the conversation."""
        return {
            "positive_moments": len(
                [log for log in conversation_log if "excited" in log["message"].lower()]
            ),
            "negative_moments": len(
                [
                    log
                    for log in conversation_log
                    if "frustrating" in log["message"].lower()
                ]
            ),
            "support_interactions": len(
                [
                    log
                    for log in conversation_log
                    if "support" in log["response"].lower()
                ]
            ),
        }

    def _analyze_memory_performance(
        self, conversation_log: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Check memory retention performance."""
        return {
            "remembers_name": any(
                "Sarah" in log["response"] for log in conversation_log
            ),
            "remembers_job": any(
                "data scientist" in log["response"] for log in conversation_log
            ),
            "remembers_hobbies": any(
                "hiking" in log["response"] for log in conversation_log
            ),
            "remembers_pet": any("Max" in log["response"] for log in conversation_log),
        }

    def _analyze_response_quality(
        self, conversation_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze response quality metrics."""
        total_chars = sum(len(log["response"]) for log in conversation_log)
        avg_response_length = (
            total_chars / len(conversation_log) if conversation_log else 0
        )

        return {
            "average_response_length": avg_response_length,
            "very_short_responses": len(
                [log for log in conversation_log if len(log["response"]) < 50]
            ),
            "very_long_responses": len(
                [log for log in conversation_log if len(log["response"]) > 500]
            ),
        }

    def _check_phase_completion(
        self, conversation_log: List[Dict[str, Any]], keywords: List[str]
    ) -> bool:
        """Check if a test phase was completed based on keywords."""
        all_text = " ".join(
            log["message"] + " " + log["response"] for log in conversation_log
        ).lower()
        return any(kw.lower() in all_text for kw in keywords)

    def save_journey_evaluation_results(
        self, judge_result: Dict[str, Any], test_results: Dict[str, Any]
    ):
        """Save evaluation results with append-only persistence."""
        test_results_dir = Path("test_results")
        test_results_dir.mkdir(exist_ok=True)

        evaluation_file = (
            test_results_dir / "comprehensive_conversation_journey_evaluation.json"
        )

        # Load previous result if exists
        previous_result = None
        if evaluation_file.exists():
            try:
                with open(evaluation_file, "r") as f:
                    previous_result = json.load(f)
            except:
                pass

        # Prepare evaluation data as single object
        evaluation_data = {
            "test_name": "comprehensive_conversation_journey",
            "timestamp": datetime.utcnow().isoformat(),
            "test_metrics": test_results["test_metrics"],
            "phases_completed": test_results["phases_summary"],
            "judge_evaluation": judge_result,
        }

        # Add previous result if exists
        if previous_result:
            evaluation_data["previous_run"] = previous_result

        # Save single evaluation object
        with open(evaluation_file, "w") as f:
            json.dump(evaluation_data, f, indent=2)

        print(f"\n   📄 Evaluation saved to {evaluation_file}")

        print("=" * 60)
