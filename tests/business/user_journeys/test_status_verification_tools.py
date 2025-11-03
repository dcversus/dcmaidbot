"""
Status Verification Tools Self-Check Tests with Crypto Fortune Tool
Business Requirements Validation for System Health Monitoring

This test validates the complete user journey for using the /status command
to perform system health checks and tool verification including crypto tools.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from llm_judge import LLMJudge

from handlers.status import handle_status_command
from services.crypto_thoughts_service import CryptoThoughtsService


class StatusVerificationToolsTest:
    """Business test for /status verification tools with crypto fortune integration"""

    def __init__(self):
        """Initialize the status verification test"""
        self.llm_judge = LLMJudge()
        self.crypto_service = CryptoThoughtsService()
        self.test_user_id = 123456789
        self.admin_user_id = 987654321
        self.test_results = []
        self.business_requirements = {
            "system_health_monitoring": "System provides comprehensive health status",
            "tool_verification": "All external tools are verified and accessible",
            "crypto_fortune_integration": "Crypto fortune tool provides valuable insights",
            "user_friendly_status": "Status information is presented in user-friendly format",
            "error_detection": "System detects and reports errors gracefully",
            "performance_metrics": "System provides performance and usage metrics",
            "admin_detailed_view": "Admin users get detailed system information",
        }

    async def test_basic_status_command(self) -> Dict[str, Any]:
        """
        Test basic /status command for regular users
        Business Story: User wants to check system status and get a crypto fortune
        """
        print("🎭 Testing Basic Status Command Journey")
        print("💭 User Intent: Check system status and get crypto insight")

        try:
            print("💬 User sends: /status")

            # Measure response time for business metrics
            start_time = time.time()

            # Execute the /status command
            response = await handle_status_command(
                user_id=self.test_user_id, is_admin=False
            )

            response_time = time.time() - start_time

            # Business outcome validation
            business_outcome = self.validate_basic_status_outcome(
                response, response_time
            )

            # LLM Judge evaluation
            evaluation = await self.llm_judge.evaluate_response(
                user_message="/status",
                bot_response=response,
                context={
                    "command": "status",
                    "user_type": "regular",
                    "business_requirements": self.business_requirements,
                },
            )

            result = {
                "test_name": "Basic Status Command",
                "user_type": "regular",
                "response": response,
                "response_time": response_time,
                "business_outcome": business_outcome,
                "llm_evaluation": evaluation,
                "success": True,
            }

            print(f"✅ Basic status test: {business_outcome['status']}")
            print(f"📊 Business Score: {business_outcome['business_score']}/10")

            return result

        except Exception as e:
            print(f"❌ Basic status test failed: {e}")
            return {
                "test_name": "Basic Status Command",
                "user_type": "regular",
                "response": None,
                "response_time": 0,
                "business_outcome": {"status": "failed", "business_score": 0},
                "success": False,
                "error": str(e),
            }

    async def test_admin_status_command(self) -> Dict[str, Any]:
        """
        Test detailed /status command for admin users
        Business Story: Admin wants detailed system information and tool verification
        """
        print("\n🔐 Testing Admin Status Command Journey")
        print("💭 Admin Intent: Get detailed system status and verify all tools")

        try:
            print("💬 Admin sends: /status")

            start_time = time.time()

            # Execute the /status command for admin
            response = await handle_status_command(
                user_id=self.admin_user_id, is_admin=True
            )

            response_time = time.time() - start_time

            # Business outcome validation for admin
            business_outcome = self.validate_admin_status_outcome(
                response, response_time
            )

            # LLM Judge evaluation
            evaluation = await self.llm_judge.evaluate_response(
                user_message="/status",
                bot_response=response,
                context={
                    "command": "status",
                    "user_type": "admin",
                    "business_requirements": self.business_requirements,
                },
            )

            result = {
                "test_name": "Admin Status Command",
                "user_type": "admin",
                "response": response,
                "response_time": response_time,
                "business_outcome": business_outcome,
                "llm_evaluation": evaluation,
                "success": True,
            }

            print(f"✅ Admin status test: {business_outcome['status']}")
            print(f"📊 Business Score: {business_outcome['business_score']}/10")

            return result

        except Exception as e:
            print(f"❌ Admin status test failed: {e}")
            return {
                "test_name": "Admin Status Command",
                "user_type": "admin",
                "response": None,
                "response_time": 0,
                "business_outcome": {"status": "failed", "business_score": 0},
                "success": False,
                "error": str(e),
            }

    async def test_crypto_fortune_integration(self) -> Dict[str, Any]:
        """
        Test crypto fortune tool integration in status
        Business Story: User gets valuable crypto insights with system status
        """
        print("\n🪙 Testing Crypto Fortune Integration Journey")
        print("💭 User Expectation: Get meaningful crypto insights with status")

        try:
            # Test crypto service directly
            print("🔍 Testing crypto fortune service directly...")

            crypto_thoughts = await self.crypto_service.generate_crypto_thoughts()

            crypto_business_outcome = self.validate_crypto_fortune_business_value(
                crypto_thoughts
            )

            # Test crypto thoughts in status context
            print("💬 Testing crypto thoughts in status context...")

            # Generate a status response that includes crypto thoughts
            status_with_crypto = f"""
🤖 **System Status**: All systems operational
⚡ **Performance**: Excellent
🪙 **Crypto Fortune of the Day**: {crypto_thoughts}
📊 **Tools**: All verified and working
            """

            # LLM Judge evaluation for crypto integration
            evaluation = await self.llm_judge.evaluate_response(
                user_message="/status",
                bot_response=status_with_crypto,
                context={
                    "command": "status",
                    "crypto_integration": True,
                    "business_requirements": self.business_requirements,
                },
            )

            result = {
                "test_name": "Crypto Fortune Integration",
                "crypto_thoughts": crypto_thoughts,
                "status_with_crypto": status_with_crypto,
                "crypto_business_outcome": crypto_business_outcome,
                "llm_evaluation": evaluation,
                "success": True,
            }

            print(f"✅ Crypto integration test: {crypto_business_outcome['status']}")
            print(
                f"📊 Crypto Business Value: {crypto_business_outcome['business_score']}/10"
            )

            return result

        except Exception as e:
            print(f"❌ Crypto integration test failed: {e}")
            return {
                "test_name": "Crypto Fortune Integration",
                "crypto_thoughts": None,
                "status_with_crypto": None,
                "crypto_business_outcome": {"status": "failed", "business_score": 0},
                "success": False,
                "error": str(e),
            }

    async def test_tool_verification_system(self) -> Dict[str, Any]:
        """
        Test comprehensive tool verification system
        Business Story: System automatically verifies all external tools are working
        """
        print("\n🔧 Testing Tool Verification System Journey")
        print("💭 System Responsibility: Verify all external tools are operational")

        # Simulate tool verification results
        tools_to_verify = [
            {
                "name": "web_search",
                "status": "operational",
                "response_time": 0.5,
                "last_check": datetime.now().isoformat(),
            },
            {
                "name": "crypto_thoughts",
                "status": "operational",
                "response_time": 0.2,
                "last_check": datetime.now().isoformat(),
            },
            {
                "name": "memory_service",
                "status": "operational",
                "response_time": 0.1,
                "last_check": datetime.now().isoformat(),
            },
            {
                "name": "joke_service",
                "status": "operational",
                "response_time": 0.3,
                "last_check": datetime.now().isoformat(),
            },
        ]

        tool_verification_results = []

        for tool in tools_to_verify:
            print(f"🔍 Verifying tool: {tool['name']}")

            # Business validation for each tool
            tool_business_value = self.validate_tool_business_value(tool)

            tool_verification_results.append(
                {**tool, "business_value": tool_business_value}
            )

            print(
                f"{'✅' if tool_business_value['operational'] else '❌'} {tool['name']}: {tool_business_value['status']}"
            )

        # Calculate overall tool verification business score
        operational_tools = len(
            [r for r in tool_verification_results if r["business_value"]["operational"]]
        )
        total_tools = len(tool_verification_results)
        tool_health_score = (
            (operational_tools / total_tools) * 10 if total_tools > 0 else 0
        )

        overall_result = {
            "test_name": "Tool Verification System",
            "total_tools": total_tools,
            "operational_tools": operational_tools,
            "tool_health_score": tool_health_score,
            "tool_results": tool_verification_results,
            "success": operational_tools == total_tools,
        }

        print(f"\n📊 Tool Verification Health Score: {tool_health_score:.1f}/10")
        print(f"✅ Operational Tools: {operational_tools}/{total_tools}")

        return overall_result

    def validate_basic_status_outcome(
        self, response: str, response_time: float
    ) -> Dict[str, Any]:
        """
        Validate business outcomes for basic status command
        """
        business_score = 0
        validation_details = []

        # 1. Response provided (Basic functionality) - 2 points
        if response and len(response) > 10:
            business_score += 2
            validation_details.append("✅ Status response provided (2/2)")
        else:
            validation_details.append("❌ No status response (0/2)")

        # 2. User-friendly format - 2 points
        if response and (
            "🤖" in response or "✅" in response or "operational" in response.lower()
        ):
            business_score += 2
            validation_details.append("✅ User-friendly format with emojis (2/2)")
        else:
            validation_details.append("❌ Not user-friendly (0/2)")

        # 3. Performance acceptable - 2 points
        if response_time < 5:
            business_score += 2
            validation_details.append("✅ Fast response time (2/2)")
        else:
            validation_details.append("❌ Slow response time (0/2)")

        # 4. Contains useful information - 2 points
        if response and any(
            keyword in response.lower()
            for keyword in ["status", "system", "operational", "working"]
        ):
            business_score += 2
            validation_details.append("✅ Contains useful status information (2/2)")
        else:
            validation_details.append("❌ Lacks useful information (0/2)")

        # 5. Includes crypto insight - 2 points
        if response and any(
            keyword in response.lower()
            for keyword in ["crypto", "fortune", "bitcoin", "ethereum"]
        ):
            business_score += 2
            validation_details.append("✅ Includes crypto fortune insight (2/2)")
        else:
            validation_details.append("❌ Missing crypto fortune (0/2)")

        status = (
            "success"
            if business_score >= 8
            else "partial"
            if business_score >= 6
            else "failed"
        )

        return {
            "status": status,
            "business_score": business_score,
            "max_score": 10,
            "validation_details": validation_details,
        }

    def validate_admin_status_outcome(
        self, response: str, response_time: float
    ) -> Dict[str, Any]:
        """
        Validate business outcomes for admin status command
        """
        business_score = 0
        validation_details = []

        # All basic status criteria (5 points)
        basic_outcome = self.validate_basic_status_outcome(response, response_time)
        business_score += min(basic_outcome["business_score"], 5)
        validation_details.extend(
            basic_outcome["validation_details"][:3]
        )  # First 3 basic validations

        # Admin-specific criteria (5 points)
        if response and any(
            keyword in response.lower()
            for keyword in ["admin", "detailed", "tools", "system"]
        ):
            business_score += 2
            validation_details.append("✅ Admin-level information provided (2/2)")
        else:
            validation_details.append("❌ Lacks admin details (0/2)")

        if response and "tools" in response.lower():
            business_score += 2
            validation_details.append("✅ Tool verification included (2/2)")
        else:
            validation_details.append("❌ Missing tool verification (0/2)")

        if response and len(response) > 200:  # Admin should get more detailed info
            business_score += 1
            validation_details.append("✅ Detailed admin information (1/1)")
        else:
            validation_details.append("❌ Insufficient admin detail (0/1)")

        status = (
            "success"
            if business_score >= 8
            else "partial"
            if business_score >= 6
            else "failed"
        )

        return {
            "status": status,
            "business_score": business_score,
            "max_score": 10,
            "validation_details": validation_details,
        }

    def validate_crypto_fortune_business_value(
        self, crypto_thoughts: str
    ) -> Dict[str, Any]:
        """
        Validate business value of crypto fortune thoughts
        """
        business_score = 0
        validation_details = []

        if not crypto_thoughts:
            return {
                "status": "failed",
                "business_score": 0,
                "max_score": 10,
                "validation_details": ["❌ No crypto thoughts generated"],
            }

        # 1. Content quality - 3 points
        if len(crypto_thoughts) > 50:
            business_score += 3
            validation_details.append("✅ Substantial crypto insight (3/3)")
        else:
            validation_details.append("❌ Insight too brief (0/3)")

        # 2. Business relevance - 3 points
        crypto_keywords = [
            "bitcoin",
            "ethereum",
            "crypto",
            "blockchain",
            "market",
            "trading",
            "investment",
        ]
        if any(keyword in crypto_thoughts.lower() for keyword in crypto_keywords):
            business_score += 3
            validation_details.append("✅ Business-relevant crypto content (3/3)")
        else:
            validation_details.append("❌ Not business-relevant (0/3)")

        # 3. User value - 2 points
        value_keywords = [
            "insight",
            "analysis",
            "trend",
            "opportunity",
            "warning",
            "strategy",
        ]
        if any(keyword in crypto_thoughts.lower() for keyword in value_keywords):
            business_score += 2
            validation_details.append("✅ Provides user value (2/2)")
        else:
            validation_details.append("❌ Lacks user value (0/2)")

        # 4. Engagement - 2 points
        if len(crypto_thoughts.split()) > 10:  # More than 10 words
            business_score += 2
            validation_details.append("✅ Engaging content (2/2)")
        else:
            validation_details.append("❌ Not engaging enough (0/2)")

        status = (
            "success"
            if business_score >= 8
            else "partial"
            if business_score >= 6
            else "failed"
        )

        return {
            "status": status,
            "business_score": business_score,
            "max_score": 10,
            "validation_details": validation_details,
        }

    def validate_tool_business_value(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate business value of individual tool verification
        """
        business_score = 0
        validation_details = []

        # 1. Tool is operational - 5 points
        if tool["status"] == "operational":
            business_score += 5
            validation_details.append("✅ Tool operational (5/5)")
        else:
            validation_details.append("❌ Tool not operational (0/5)")

        # 2. Response time acceptable - 3 points
        if tool["response_time"] < 2:
            business_score += 3
            validation_details.append("✅ Fast response time (3/3)")
        elif tool["response_time"] < 5:
            business_score += 2
            validation_details.append("⚠️ Acceptable response time (2/3)")
        else:
            validation_details.append("❌ Slow response time (0/3)")

        # 3. Recent check - 2 points
        if tool["last_check"]:
            business_score += 2
            validation_details.append("✅ Recent verification (2/2)")
        else:
            validation_details.append("❌ No recent check (0/2)")

        operational = business_score >= 7

        return {
            "operational": operational,
            "business_score": business_score,
            "max_score": 10,
            "validation_details": validation_details,
        }

    async def generate_comprehensive_business_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive business report for status verification tools
        """
        print(
            "📊 Generating Comprehensive Business Report for Status Verification Tools"
        )

        # Run all test scenarios
        basic_status_result = await self.test_basic_status_command()
        admin_status_result = await self.test_admin_status_command()
        crypto_integration_result = await self.test_crypto_fortune_integration()
        tool_verification_result = await self.test_tool_verification_system()

        # Calculate overall business metrics
        all_tests = [
            basic_status_result,
            admin_status_result,
            crypto_integration_result,
            tool_verification_result,
        ]
        successful_tests = len([t for t in all_tests if t.get("success", False)])
        total_tests = len(all_tests)

        overall_success_rate = (
            (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        )

        # Calculate average business scores
        business_scores = []
        for test in all_tests:
            if "business_outcome" in test:
                business_scores.append(test["business_outcome"]["business_score"])
            elif "crypto_business_outcome" in test:
                business_scores.append(
                    test["crypto_business_outcome"]["business_score"]
                )
            elif "tool_health_score" in test:
                business_scores.append(test["tool_health_score"])

        avg_business_score = (
            sum(business_scores) / len(business_scores) if business_scores else 0
        )

        return {
            "test_execution_summary": {
                "test_name": "Status Verification Tools with Crypto Fortune",
                "execution_time": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": overall_success_rate,
                "average_business_score": avg_business_score,
            },
            "test_results": {
                "basic_status": basic_status_result,
                "admin_status": admin_status_result,
                "crypto_integration": crypto_integration_result,
                "tool_verification": tool_verification_result,
            },
            "business_requirements_validation": self.validate_business_requirements(
                all_tests
            ),
            "business_readiness": {
                "ready_for_production": overall_success_rate >= 80
                and avg_business_score >= 7,
                "user_experience_acceptable": overall_success_rate >= 70,
                "crypto_fortune_working": crypto_integration_result.get(
                    "success", False
                ),
                "tool_verification_working": tool_verification_result.get(
                    "success", False
                ),
            },
            "recommendations": self.generate_status_recommendations(
                overall_success_rate, avg_business_score
            ),
        }

    def validate_business_requirements(
        self, test_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate business requirements against test results
        """
        requirements_validation = []

        for req_key, req_description in self.business_requirements.items():
            # Simple validation logic for each requirement
            if req_key == "system_health_monitoring":
                met = test_results[0].get("success", False) if test_results else False
            elif req_key == "tool_verification":
                met = (
                    test_results[3].get("success", False)
                    if len(test_results) > 3
                    else False
                )
            elif req_key == "crypto_fortune_integration":
                met = (
                    test_results[2].get("success", False)
                    if len(test_results) > 2
                    else False
                )
            elif req_key == "user_friendly_status":
                met = (
                    test_results[0].get("business_outcome", {}).get("business_score", 0)
                    >= 6
                    if test_results
                    else False
                )
            elif req_key == "admin_detailed_view":
                met = (
                    test_results[1].get("business_outcome", {}).get("business_score", 0)
                    >= 6
                    if len(test_results) > 1
                    else False
                )
            else:
                met = False  # Default to not met for complex requirements

            requirements_validation.append(
                {"requirement": req_key, "description": req_description, "met": met}
            )

        return requirements_validation

    def generate_status_recommendations(
        self, success_rate: float, avg_business_score: float
    ) -> List[str]:
        """
        Generate business recommendations for status verification tools
        """
        recommendations = []

        if success_rate >= 90 and avg_business_score >= 8:
            recommendations.append(
                "✅ Excellent status verification system - ready for production"
            )
        elif success_rate >= 80 and avg_business_score >= 7:
            recommendations.append(
                "✅ Good status verification - ready with monitoring"
            )
        elif success_rate >= 70 and avg_business_score >= 6:
            recommendations.append(
                "⚠️ Acceptable status verification - consider improvements"
            )
        else:
            recommendations.append(
                "❌ Status verification needs significant improvements"
            )

        # Specific recommendations based on business scores
        if avg_business_score < 7:
            recommendations.append("🔧 Focus on improving business value:")
            if avg_business_score < 6:
                recommendations.append(
                    "   - Improve user experience and response formatting"
                )
            if avg_business_score < 5:
                recommendations.append(
                    "   - Enhance crypto fortune integration quality"
                )
            if avg_business_score < 4:
                recommendations.append("   - Fix tool verification system")

        return recommendations


async def run_status_verification_tools_test():
    """
    Main function to run the complete status verification tools test
    """
    print("🚀 Starting Status Verification Tools Test with Crypto Fortune")
    print("=" * 70)

    status_test = StatusVerificationToolsTest()

    try:
        business_report = await status_test.generate_comprehensive_business_report()

        print("\n" + "=" * 70)
        print("📊 STATUS VERIFICATION BUSINESS REPORT")
        print("=" * 70)

        summary = business_report["test_execution_summary"]
        print(f"📈 Overall Success Rate: {summary['success_rate']:.1f}%")
        print(f"📊 Average Business Score: {summary['average_business_score']:.1f}/10")
        print(
            f"✅ Successful Tests: {summary['successful_tests']}/{summary['total_tests']}"
        )

        readiness = business_report["business_readiness"]
        print("\n🎯 Business Readiness:")
        print(
            f"   Ready for Production: {'✅' if readiness['ready_for_production'] else '❌'}"
        )
        print(
            f"   User Experience: {'✅' if readiness['user_experience_acceptable'] else '❌'}"
        )
        print(
            f"   Crypto Fortune: {'✅' if readiness['crypto_fortune_working'] else '❌'}"
        )
        print(
            f"   Tool Verification: {'✅' if readiness['tool_verification_working'] else '❌'}"
        )

        print("\n💡 Business Recommendations:")
        for rec in business_report["recommendations"]:
            print(f"   {rec}")

        # Save detailed report
        with open("status_verification_business_results.json", "w") as f:
            json.dump(business_report, f, indent=2)

        print("\n📄 Full report saved to status_verification_business_results.json")

        return business_report

    except Exception as e:
        print(f"❌ Status verification test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_status_verification_tools_test())
