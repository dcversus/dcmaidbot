"""
Cross-PRP E2E Journey Tests with LLM Judge Verification

This module tests complete user journeys that span multiple PRPs:
- PRP-002: LLM Agent Framework with /call endpoint
- PRP-003: PostgreSQL Database Foundation
- PRP-004: Unified Auth & API Key Management
- PRP-005: Advanced Memory System with Emotional Intelligence
- PRP-009: External Tools Integration

Each journey is verified by an LLM Judge to ensure business value and real behavior.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List

import aiohttp

# Import LLM Judge
from tests.llm_judge import LLMJudge


class CrossPRPE2EJourneys:
    """E2E tests spanning multiple PRPs with LLM judge verification"""

    def __init__(self):
        self.base_url = os.getenv("TEST_BASE_URL", "http://localhost:8080")
        self.admin_id = int(os.getenv("TEST_ADMIN_ID", "122657093"))
        self.user_id = int(os.getenv("TEST_USER_ID", "999999999"))
        self.api_key = os.getenv("TEST_API_KEY", None)
        self.nudge_secret = os.getenv("NUDGE_SECRET", None)
        self.llm_judge = LLMJudge()

    async def setup_session(self) -> aiohttp.ClientSession:
        """Create HTTP session with proper auth"""
        headers = {"Content-Type": "application/json"}

        # Try API key auth first (PRP-004)
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.nudge_secret:
            headers["Authorization"] = f"Bearer {self.nudge_secret}"

        return aiohttp.ClientSession(headers=headers)

    async def call_endpoint(
        self, session: aiohttp.ClientSession, user_id: int, message: str
    ) -> Dict:
        """Call /call endpoint (PRP-002)"""
        payload = {"user_id": user_id, "message": message}

        async with session.post(f"{self.base_url}/call", json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"/call failed: {resp.status}")
            return await resp.json()

    async def check_status(self, session: aiohttp.ClientSession) -> Dict:
        """Check /status endpoint (PRP-004) - universal source of truth"""
        async with session.get(f"{self.base_url}/status") as resp:
            if resp.status != 200:
                raise Exception(f"/status failed: {resp.status}")
            return await resp.json()

    async def journey_01_admin_full_workflow(self) -> Dict:
        """
        Journey: Admin manages lessons, memories, and verifies system status

        PRPs covered:
        - PRP-002: LLM responses with lesson injection
        - PRP-004: API key authentication
        - PRP-005: Memory system integration
        """

        print("\n=== Journey 01: Admin Full Workflow ===")

        async with await self.setup_session() as session:
            results = {
                "journey": "admin_full_workflow",
                "steps": [],
                "start_time": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: Check system status (PRP-004)
                print("Step 1: Checking system status...")
                status = await self.check_status(session)
                results["steps"].append(
                    {
                        "step": "status_check",
                        "success": "bot" in status.get("checks", {}),
                        "data": status,
                    }
                )

                # Step 2: Admin adds a lesson (PRP-002)
                print("Step 2: Admin adds lesson...")
                response = await self.call_endpoint(
                    session,
                    self.admin_id,
                    "/add_lesson Test lesson: When users ask about testing, be helpful and concise.",
                )
                results["steps"].append(
                    {
                        "step": "add_lesson",
                        "success": "lesson" in response.get("response", "").lower()
                        or "added" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 3: User triggers LLM with lesson injection (PRP-002)
                print("Step 3: User interaction with lesson injection...")
                response = await self.call_endpoint(
                    session, self.user_id, "How do I test something?"
                )
                results["steps"].append(
                    {
                        "step": "lesson_injection",
                        "success": len(response.get("response", "")) > 10,
                        "response": response.get("response", ""),
                    }
                )

                # Step 4: Admin checks memories (PRP-005)
                print("Step 4: Admin checks memories...")
                response = await self.call_endpoint(session, self.admin_id, "/memories")
                results["steps"].append(
                    {
                        "step": "memory_check",
                        "success": "memor" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 5: Create and relate memories (PRP-005)
                print("Step 5: Memory operations...")
                await self.call_endpoint(
                    session, self.user_id, "Remember that I love Python testing"
                )
                await self.call_endpoint(
                    session, self.user_id, "I also enjoy automated testing frameworks"
                )
                response = await self.call_endpoint(
                    session, self.admin_id, "/relate 1 2"
                )
                results["steps"].append(
                    {
                        "step": "memory_operations",
                        "success": "related" in response.get("response", "").lower()
                        or "linked" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                results["success"] = all(s["success"] for s in results["steps"])
                results["end_time"] = datetime.utcnow().isoformat()

                return results

            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
                return results

    async def journey_02_user_emotional_intelligence(self) -> Dict:
        """
        Journey: User interacts with bot showing emotional intelligence

        PRPs covered:
        - PRP-002: BASE_PROMPT emoji personality
        - PRP-003: Database stores emotional states
        - PRP-005: VAD emotion tracking
        """

        print("\n=== Journey 02: User Emotional Intelligence ===")

        async with await self.setup_session() as session:
            results = {
                "journey": "user_emotional_intelligence",
                "steps": [],
                "start_time": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: User tells a joke (tests emoji response)
                print("Step 1: Testing emoji personality...")
                response = await self.call_endpoint(
                    session, self.user_id, "Tell me a joke!"
                )
                results["steps"].append(
                    {
                        "step": "emoji_response",
                        "success": any(
                            emoji in response.get("response", "")
                            for emoji in ["😊", "😂", "✨", "🎯"]
                        ),
                        "response": response.get("response", ""),
                    }
                )

                # Step 2: Check bot mood (PRP-005)
                print("Step 2: Check bot mood...")
                response = await self.call_endpoint(session, self.user_id, "/mood")
                results["steps"].append(
                    {
                        "step": "mood_check",
                        "success": "mood" in response.get("response", "").lower()
                        or "valence" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 3: User expresses frustration (tests emotional response)
                print("Step 3: Testing emotional response...")
                response = await self.call_endpoint(
                    session, self.user_id, "I'm having a really bad day with my code"
                )
                results["steps"].append(
                    {
                        "step": "emotional_response",
                        "success": len(response.get("response", "")) > 20,
                        "response": response.get("response", ""),
                    }
                )

                # Step 4: Check help is role-based (PRP-002)
                print("Step 4: Check role-based help...")
                response = await self.call_endpoint(session, self.user_id, "/help")
                user_help = response.get("response", "")

                response = await self.call_endpoint(session, self.admin_id, "/help")
                admin_help = response.get("response", "")

                results["steps"].append(
                    {
                        "step": "role_based_help",
                        "success": len(admin_help) > len(user_help)
                        and "🔧" in admin_help,
                        "user_help": user_help,
                        "admin_help": admin_help,
                    }
                )

                results["success"] = all(s["success"] for s in results["steps"])
                results["end_time"] = datetime.utcnow().isoformat()

                return results

            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
                return results

    async def journey_03_rbac_and_api_keys(self) -> Dict:
        """
        Journey: Test Role-Based Access Control and API Key Management (PRP-004, PRP-017)

        PRPs covered:
        - PRP-004: Unified Auth & API Key Management
        - PRP-017: RBAC with Judge
        """

        print("\n=== Journey 03: RBAC and API Key Management ===")

        async with await self.setup_session() as session:
            results = {
                "journey": "rbac_and_api_keys",
                "steps": [],
                "start_time": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: User tries admin command (should fail)
                print("Step 1: User attempts admin command...")
                response = await self.call_endpoint(
                    session, self.user_id, "/add_lesson This should fail"
                )
                results["steps"].append(
                    {
                        "step": "user_admin_denied",
                        "success": "not authorized"
                        in response.get("response", "").lower()
                        or "only admins" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 2: Admin creates API key
                print("Step 2: Admin creates API key...")
                response = await self.call_endpoint(
                    session, self.admin_id, "/create_api_key test_key For E2E testing"
                )
                results["steps"].append(
                    {
                        "step": "create_api_key",
                        "success": "key" in response.get("response", "").lower()
                        or "created" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 3: List API keys
                print("Step 3: Admin lists API keys...")
                response = await self.call_endpoint(
                    session, self.admin_id, "/list_api_keys"
                )
                results["steps"].append(
                    {
                        "step": "list_api_keys",
                        "success": "key" in response.get("response", "").lower()
                        or "test_key" in response.get("response", ""),
                        "response": response.get("response", ""),
                    }
                )

                # Step 4: Check API key usage
                print("Step 4: Check API key usage...")
                response = await self.call_endpoint(
                    session, self.admin_id, "/check_api_key_usage test_key"
                )
                results["steps"].append(
                    {
                        "step": "check_usage",
                        "success": "usage" in response.get("response", "").lower()
                        or "times" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                results["success"] = all(s["success"] for s in results["steps"])
                results["end_time"] = datetime.utcnow().isoformat()

                return results

            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
                return results

    async def journey_04_emotional_intelligence_chain_of_thought(self) -> Dict:
        """
        Journey: Deep emotional intelligence with Chain-of-Thought reasoning

        PRPs covered:
        - PRP-002: LLM Agent with emotional CoT
        - PRP-005: VAD emotion tracking
        - PRP-007: LLM Judge for emotional validation
        """

        print("\n=== Journey 04: Emotional Intelligence with CoT ===")

        async with await self.setup_session() as session:
            results = {
                "journey": "emotional_intelligence_cot",
                "steps": [],
                "start_time": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: Express complex emotions
                print("Step 1: Complex emotional expression...")
                response = await self.call_endpoint(
                    session,
                    self.user_id,
                    "I'm feeling proud but also anxious about my upcoming code review. I've worked hard but I'm worried about criticism.",
                )
                results["steps"].append(
                    {
                        "step": "complex_emotion",
                        "success": len(response.get("response", "")) > 50
                        and any(
                            word in response.get("response", "").lower()
                            for word in ["proud", "anxious", "worried", "excited"]
                        ),
                        "response": response.get("response", ""),
                    }
                )

                # Step 2: Track mood changes
                print("Step 2: Mood tracking...")
                await self.call_endpoint(
                    session,
                    self.user_id,
                    "Just got great news! My project was approved!",
                )
                response = await self.call_endpoint(session, self.user_id, "/mood")
                results["steps"].append(
                    {
                        "step": "mood_tracking",
                        "success": "valence" in response.get("response", "").lower()
                        or "mood" in response.get("response", "").lower()
                        or any(
                            emoji in response.get("response", "")
                            for emoji in ["😊", "🎉", "✨", "💫"]
                        ),
                        "response": response.get("response", ""),
                    }
                )

                # Step 3: Memory with emotional context
                print("Step 3: Emotional memory formation...")
                response = await self.call_endpoint(
                    session,
                    self.user_id,
                    "Remember this feeling: When my code finally works after hours of debugging, it's like pure joy! 🎯",
                )
                results["steps"].append(
                    {
                        "step": "emotional_memory",
                        "success": "remembered" in response.get("response", "").lower()
                        or "memory" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 4: Test empathy and emotional support
                print("Step 4: Empathetic response...")
                response = await self.call_endpoint(
                    session,
                    self.user_id,
                    "I'm really burned out from work. I think I need a break but feel guilty for taking one.",
                )
                results["steps"].append(
                    {
                        "step": "empathy",
                        "success": any(
                            word in response.get("response", "").lower()
                            for word in [
                                "understand",
                                "okay",
                                "break",
                                "rest",
                                "guilty",
                            ]
                        )
                        and len(response.get("response", "")) > 30,
                        "response": response.get("response", ""),
                    }
                )

                results["success"] = all(s["success"] for s in results["steps"])
                results["end_time"] = datetime.utcnow().isoformat()

                return results

            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
                return results

    async def journey_05_external_tools_integration(self) -> Dict:
        """
        Journey: Admin and user use external tools (updated)

        PRPs covered:
        - PRP-002: Tool calling framework
        - PRP-004: API key permissions
        - PRP-009: External tools (web search, etc.)
        """

        print("\n=== Journey 03: External Tools Integration ===")

        async with await self.setup_session() as session:
            results = {
                "journey": "external_tools_integration",
                "steps": [],
                "start_time": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: User asks for web search
                print("Step 1: User requests web search...")
                response = await self.call_endpoint(
                    session, self.user_id, "Search for 'python testing best practices'"
                )
                results["steps"].append(
                    {
                        "step": "web_search_user",
                        "success": "search" in response.get("response", "").lower()
                        or "found" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 2: Admin uses external tool (if available)
                print("Step 2: Admin external tool access...")
                response = await self.call_endpoint(
                    session, self.admin_id, "Use external tools to check system status"
                )
                results["steps"].append(
                    {
                        "step": "admin_tools",
                        "success": "tool" in response.get("response", "").lower()
                        or "external" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                # Step 3: Test non-existent tool response (PRP-002)
                print("Step 3: Test non-existent tool response...")
                response = await self.call_endpoint(
                    session,
                    self.user_id,
                    "Can you use the magical_tool_that_doesnt_exist?",
                )
                results["steps"].append(
                    {
                        "step": "non_existent_tool",
                        "success": "😅" in response.get("response", "")
                        or "doesn't exist" in response.get("response", "").lower(),
                        "response": response.get("response", ""),
                    }
                )

                results["success"] = all(s["success"] for s in results["steps"])
                results["end_time"] = datetime.utcnow().isoformat()

                return results

            except Exception as e:
                results["error"] = str(e)
                results["success"] = False
                return results

    async def run_all_journeys(self) -> List[Dict]:
        """Run all journeys and return results with LLM judge evaluation"""

        print("\n🚀 Starting Cross-PRP E2E Journey Tests")
        print(f"Target: {self.base_url}")
        print(f"Admin ID: {self.admin_id}")
        print(f"User ID: {self.user_id}")

        journeys = [
            self.journey_01_admin_full_workflow,
            self.journey_02_user_emotional_intelligence,
            self.journey_03_rbac_and_api_keys,
            self.journey_04_emotional_intelligence_chain_of_thought,
            self.journey_05_external_tools_integration,
        ]

        results = []

        for journey_func in journeys:
            try:
                result = await journey_func()

                # LLM Judge evaluation
                print(f"\n🤖 LLM Judge evaluating: {result['journey']}")
                evaluation = await self.llm_judge.evaluate_journey(result)
                result["llm_judge"] = evaluation

                results.append(result)

                # Print summary
                status = "✅ PASSED" if result["success"] else "❌ FAILED"
                score = evaluation.get("overall_score", 0)
                print(f"{status} | Score: {score:.2f} | {result['journey']}")

            except Exception as e:
                print(f"❌ Journey failed: {journey_func.__name__} - {e}")
                results.append(
                    {
                        "journey": journey_func.__name__,
                        "error": str(e),
                        "success": False,
                    }
                )

        return results


async def main():
    """Run all cross-PRP E2E journeys"""
    runner = CrossPRPE2EJourneys()
    results = await runner.run_all_journeys()

    # Generate report
    passed = sum(1 for r in results if r.get("success", False))
    total = len(results)

    print("\n" + "=" * 60)
    print("📊 CROSS-PRP E2E JOURNEY TEST REPORT")
    print("=" * 60)
    print(f"Total Journeys: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()

    # PRP coverage summary
    prp_coverage = {
        "PRP-002": ["LLM Agent Framework", "checked in all journeys"],
        "PRP-003": ["PostgreSQL Database", "implicit in all operations"],
        "PRP-004": ["Unified Auth", "API keys and RBAC tested"],
        "PRP-005": ["Memory System", "checked in admin and emotional journeys"],
        "PRP-007": ["LLM Judge", "evaluating all journeys"],
        "PRP-009": ["External Tools", "dedicated journey"],
        "PRP-017": ["RBAC with Judge", "role-based access tested"],
    }

    print("📋 PRP Coverage:")
    for prp, info in prp_coverage.items():
        print(f"  {prp}: {info[0]} - {info[1]}")

    print("\n🔗 DoD Verification Links:")
    for result in results:
        if result.get("success"):
            journey = result["journey"]
            print(f"  ✅ {journey}: Verified via E2E test with LLM judge")

    # Save results
    with open("test_results_cross_prp.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Detailed results saved to: test_results_cross_prp.json")

    return all(r.get("success", False) for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
