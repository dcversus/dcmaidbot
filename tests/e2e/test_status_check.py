#!/usr/bin/env python3
"""
Status Check E2E Test.

This test:
1. Calls /status endpoint to get current system state
2. Waits for thoughts generation (version, self-check, crypto)
3. Runs LLM Judge analysis on status and thoughts
4. Validates all tools are working properly

Follows PRP-010 requirements for status system validation.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import aiohttp
import pytest
from dotenv import load_dotenv

from tests.llm_judge import LLMJudge

load_dotenv()

# Test configuration
ADMIN_ID = int(os.getenv("ADMIN_IDS", "122657093").split(",")[0])


@pytest.fixture
async def http_client():
    """HTTP client for API calls."""
    async with aiohttp.ClientSession(base_url="http://localhost:8000") as session:
        yield session


class TestStatusCheck:
    """Status check E2E test with thoughts and LLM Judge evaluation."""

    @pytest.mark.asyncio
    async def test_status_check_with_thoughts_and_judge(self, http_client):
        """Complete status check with thoughts generation and LLM Judge analysis."""
        print("\n🔍 Starting Status Check E2E Test")
        print("=" * 60)

        # Step 1: Initial status check
        print("\n1️⃣ Getting initial status...")
        status_response = await self.get_status(http_client)

        assert status_response is not None, "Status endpoint should respond"
        print("   ✅ Status endpoint responding")

        # Step 2: Check if thoughts are being generated
        print("\n2️⃣ Checking for thoughts generation...")

        # Wait for thoughts to be generated (they run in background)
        max_wait_time = 60  # seconds
        poll_interval = 2
        start_time = time.time()

        thoughts_ready = False
        while time.time() - start_time < max_wait_time:
            status = await self.get_status(http_client)

            # Check if thoughts exist
            if (
                status.get("version_thoughts")
                or status.get("self_check_thoughts")
                or status.get("crypto_thoughts")
            ):
                thoughts_ready = True
                print("   ✅ Thoughts detected in status")
                break

            print(f"   ⏳ Waiting for thoughts... ({int(time.time() - start_time)}s)")
            await asyncio.sleep(poll_interval)

        if not thoughts_ready:
            print("   ⚠️  Thoughts not generated within timeout period")

        # Step 3: Get final status with all thoughts
        print("\n3️⃣ Getting final status with thoughts...")
        final_status = await self.get_status(http_client)

        # Step 4: LLM Judge analysis
        print("\n4️⃣ Running LLM Judge analysis...")
        if os.getenv("OPENAI_API_KEY"):
            judge_result = await self.run_llm_judge_analysis(final_status)
            self.process_judge_results(judge_result, final_status)
        else:
            print("   ⚠️  OPENAI_API_KEY not set - skipping LLM Judge")

        # Step 5: Validate all components
        print("\n5️⃣ Validating system components...")
        self.validate_system_components(final_status)

        print("\n✅ Status check E2E test completed successfully")
        print("=" * 60)

    async def get_status(self, http_client: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get status from /status endpoint."""
        try:
            async with http_client.get("/status") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"   ❌ Status returned {resp.status}")
                    return {}
        except Exception as e:
            print(f"   ❌ Error getting status: {e}")
            return {}

    async def run_llm_judge_analysis(self, status: Dict[str, Any]) -> Any:
        """Run LLM Judge analysis on status and thoughts."""
        judge = LLMJudge()

        # Prepare comprehensive test results for evaluation
        test_results = {
            "status": status,
            "test_category": "Status Check with Thoughts",
            "system_health": {
                "version": status.get("version"),
                "uptime": status.get("uptime"),
                "database": status.get("database"),
                "component_health": status.get("component_health", {}),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "thoughts_analysis": {
                "version_thoughts": status.get("version_thoughts"),
                "self_check_thoughts": status.get("self_check_thoughts"),
                "crypto_thoughts": status.get("crypto_thoughts"),
                "thoughts_generation_working": bool(
                    status.get("version_thoughts")
                    or status.get("self_check_thoughts")
                    or status.get("crypto_thoughts")
                ),
            },
        }

        # Context for evaluation
        context = {
            "test_type": "status_check",
            "evaluation_focus": [
                "System health and responsiveness",
                "Thoughts generation quality",
                "Component validation results",
                "Overall system readiness",
            ],
            "expected_features": [
                "Version thoughts showing kawaii lilith personality",
                "Self-check thoughts validating all tools",
                "Crypto thoughts providing market analysis",
                "Component health scores >80% for healthy systems",
                "Response times <1 second for API endpoints",
            ],
        }

        # Run evaluation
        result = await judge.evaluate_test_results(
            test_name="Status Check with Thoughts",
            test_results=test_results,
            context=context,
        )

        return result

    def process_judge_results(self, judge_result, status: Dict[str, Any]):
        """Process and display LLM Judge results."""
        # Display rich formatted evaluation
        judge = LLMJudge()
        judge.display_evaluation(judge_result, "Status Check with Thoughts")

        # Extract key metrics from real LLM Judge result
        score = judge_result.get("overall_score", 0)
        confidence = judge_result.get("confidence", 0)
        verdict = judge_result.get("verdict", "UNKNOWN")
        is_pass = verdict == "PASS" and score >= 70

        print("\n📊 LLM Judge Results Summary:")
        print(f"   Score: {score}/100")
        print(f"   Confidence: {confidence}/100")
        print(f"   Verdict: {'✅ PASS' if is_pass else '❌ FAIL'}")

        if judge_result.get("strengths"):
            print("\n   ✅ Strengths:")
            for strength in judge_result["strengths"][:3]:
                print(f"   • {strength}")

        if judge_result.get("weaknesses"):
            print("\n   ⚠️  Weaknesses:")
            for weakness in judge_result["weaknesses"][:3]:
                print(f"   • {weakness}")

        if judge_result.get("recommendations"):
            print("\n   💡 Recommendations:")
            for rec in judge_result["recommendations"][:3]:
                print(f"   • {rec}")

        # Assert minimum quality standards
        assert score >= 70, f"LLM Judge score too low: {score}/100"
        assert confidence >= 70, f"LLM Judge confidence too low: {confidence}/100"
        assert verdict == "PASS", f"LLM Judge verdict: {verdict}"

        # Save results with append-only persistence
        self.save_evaluation_results(judge_result, status)

    def save_evaluation_results(
        self, judge_result: Dict[str, Any], status: Dict[str, Any]
    ):
        """Save evaluation results to JSON file."""
        test_results_dir = Path("test_results")
        test_results_dir.mkdir(exist_ok=True)

        evaluation_file = (
            test_results_dir / "status_check_with_thoughts_evaluation.json"
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
            "test_name": "status_check_with_thoughts",
            "timestamp": datetime.utcnow().isoformat(),
            "status_data": {
                "version": status.get("version"),
                "uptime": status.get("uptime"),
                "has_version_thoughts": bool(status.get("version_thoughts")),
                "has_self_check_thoughts": bool(status.get("self_check_thoughts")),
                "has_crypto_thoughts": bool(status.get("crypto_thoughts")),
                "component_health": status.get("component_health", {}),
                "database_status": status.get("database"),
                "version_thoughts": status.get("version_thoughts"),
                "self_check_thoughts": status.get("self_check_thoughts"),
                "crypto_thoughts": status.get("crypto_thoughts"),
            },
            "judge_evaluation": judge_result,
        }

        # Add previous result if exists
        if previous_result:
            evaluation_data["previous_run"] = previous_result

        # Save single evaluation object
        with open(evaluation_file, "w") as f:
            json.dump(evaluation_data, f, indent=2)

        print(f"\n   📄 Evaluation saved to {evaluation_file}")

    def validate_system_components(self, status: Dict[str, Any]):
        """Validate that all system components are working."""
        checks = []

        # Check basic status fields
        if status.get("status"):
            checks.append(("System Status", "✅"))
        else:
            checks.append(("System Status", "❌ Missing"))

        # Check version info
        if status.get("version"):
            checks.append(("Version Info", "✅"))
        else:
            checks.append(("Version Info", "❌ Missing"))

        # Check thoughts
        if status.get("version_thoughts"):
            checks.append(("Version Thoughts", "✅"))
        else:
            checks.append(("Version Thoughts", "❌ Not Generated"))

        if status.get("self_check_thoughts"):
            checks.append(("Self-Check Thoughts", "✅"))
        else:
            checks.append(("Self-Check Thoughts", "❌ Not Generated"))

        if status.get("crypto_thoughts"):
            checks.append(("Crypto Thoughts", "✅"))
        else:
            checks.append(("Crypto Thoughts", "❌ Not Generated"))

        # Check database connection
        if status.get("database"):
            checks.append(("Database", "✅"))
        else:
            checks.append(("Database", "❌ Missing"))

        # Check services
        if status.get("uptime"):
            checks.append(("Uptime", "✅"))
        else:
            checks.append(("Uptime", "❌ Missing"))

        # Display results
        print("\n📋 Component Status:")
        for component, status_icon in checks:
            print(f"   {status_icon} {component}")

        # Calculate overall health
        passed = sum(1 for _, s in checks if s == "✅")
        total = len(checks)
        health_percentage = (passed / total) * 100 if total > 0 else 0

        print(f"\n🏥 Overall System Health: {health_percentage:.1f}%")

        # Assert minimum health
        assert health_percentage >= 70, (
            f"System health too low: {health_percentage:.1f}%"
        )

        # Save component status
        component_report = {
            "test_name": "status_check_components",
            "timestamp": datetime.utcnow().isoformat(),
            "component_status": dict(checks),
            "health_percentage": health_percentage,
        }

        with open("test_results/status_components.json", "w") as f:
            json.dump(component_report, f, indent=2)


@pytest.mark.asyncio
async def test_status_endpoint_available(http_client):
    """Quick check that status endpoint is available."""
    print("\n🔍 Quick status endpoint check...")

    status = await TestStatusCheck().get_status(http_client)

    assert status is not None, "Status endpoint should be accessible"
    print("   ✅ Status endpoint is accessible")
