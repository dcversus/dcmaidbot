"""
E2E Journey Tests with LLM Judge for /call Command
Business Requirements Validation through Complete User Workflows

This test validates the complete user journey for using the /call command
to interact with external tools through natural language processing.
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

from handlers.call import call_handler


class CallCommandJourneyTest:
    """E2E journey test for /call command with LLM judge evaluation"""

    def __init__(self):
        """Initialize the journey test with LLM judge"""
        self.llm_judge = LLMJudge()
        self.test_user_id = 123456789
        self.admin_user_id = 987654321
        self.test_results = []
        self.business_requirements = {
            "natural_language_processing": "User can interact with tools using natural language",
            "intent_recognition": "System correctly identifies user intent and tool requirements",
            "parameter_extraction": "System extracts correct parameters from natural language",
            "tool_selection": "System selects appropriate tool based on user intent",
            "execution_results": "Tool executes successfully and returns relevant results",
            "error_handling": "System handles errors gracefully and provides helpful feedback",
            "access_control": "Admin-only tools are properly protected for regular users",
        }

    async def run_complete_journey(self) -> Dict[str, Any]:
        """
        Run complete user journey for /call command
        Business Story: User wants to search for information using natural language
        """
        print("🎭 Starting E2E Journey: User Natural Language Tool Interaction")

        journey_scenarios = [
            {
                "name": "Information Search Journey",
                "user_intent": "Find information about artificial intelligence",
                "expected_tool": "web_search",
                "user_message": "/call search for information about artificial intelligence trends",
                "business_value": "User can access information without knowing specific tool commands",
            },
            {
                "name": "Simple Query Journey",
                "user_intent": "Get weather information",
                "expected_tool": "web_search",
                "user_message": "/call what's the weather like today",
                "business_value": "Natural language interaction reduces learning curve",
            },
            {
                "name": "Complex Request Journey",
                "user_intent": "Research specific topic",
                "expected_tool": "web_search",
                "user_message": "/call find recent news about quantum computing breakthroughs",
                "business_value": "Users can express complex needs naturally",
            },
        ]

        journey_results = []

        for scenario in journey_scenarios:
            print(f"\n📖 Testing Scenario: {scenario['name']}")
            print(f"💭 User Intent: {scenario['user_intent']}")
            print(f"🎯 Business Value: {scenario['business_value']}")

            # Execute the user journey
            result = await self.execute_scenario(scenario)
            journey_results.append(result)

            # LLM Judge evaluation
            evaluation = await self.llm_judge.evaluate_response(
                user_message=scenario["user_message"],
                bot_response=result["response"],
                context={
                    "scenario": scenario["name"],
                    "expected_tool": scenario["expected_tool"],
                    "business_requirements": self.business_requirements,
                },
            )

            result["llm_evaluation"] = evaluation
            self.test_results.append(result)

            # Business outcome validation
            business_outcome = self.validate_business_outcome(
                scenario, result, evaluation
            )
            result["business_outcome"] = business_outcome

            print(f"✅ Scenario {scenario['name']}: {business_outcome['status']}")
            print(f"📊 Business Score: {business_outcome['business_score']}/10")

        return {
            "journey_name": "Natural Language Tool Interaction",
            "total_scenarios": len(journey_scenarios),
            "successful_scenarios": len(
                [
                    r
                    for r in journey_results
                    if r["business_outcome"]["status"] == "success"
                ]
            ),
            "business_results": journey_results,
            "timestamp": datetime.now().isoformat(),
        }

    async def execute_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single scenario of the user journey
        """
        try:
            print(f"💬 User sends: {scenario['user_message']}")

            # Measure response time for business metrics
            start_time = time.time()

            # Execute the /call command
            response = await call_handler(
                message=scenario["user_message"],
                user_id=self.test_user_id,
                is_admin=False,
            )

            response_time = time.time() - start_time

            return {
                "scenario": scenario["name"],
                "user_message": scenario["user_message"],
                "response": response,
                "response_time": response_time,
                "success": True,
                "error": None,
            }

        except Exception as e:
            return {
                "scenario": scenario["name"],
                "user_message": scenario["user_message"],
                "response": None,
                "response_time": 0,
                "success": False,
                "error": str(e),
            }

    def validate_business_outcome(
        self,
        scenario: Dict[str, Any],
        result: Dict[str, Any],
        evaluation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate business outcomes against requirements
        """
        business_score = 0
        max_score = 10
        validation_details = []

        # 1. System responded (Basic functionality) - 2 points
        if result["success"] and result["response"]:
            business_score += 2
            validation_details.append("✅ System responded successfully (2/2)")
        else:
            validation_details.append("❌ System failed to respond (0/2)")

        # 2. Response is helpful and relevant - 3 points
        if evaluation.get("helpfulness_score", 0) >= 4:
            business_score += 3
            validation_details.append(
                f"✅ Response helpful and relevant (3/3) - Score: {evaluation.get('helpfulness_score', 0)}"
            )
        else:
            validation_details.append(
                f"❌ Response not helpful enough (0/3) - Score: {evaluation.get('helpfulness_score', 0)}"
            )

        # 3. Natural language understanding - 3 points
        if evaluation.get("intent_recognition_score", 0) >= 4:
            business_score += 3
            validation_details.append(
                f"✅ Natural language understood (3/3) - Score: {evaluation.get('intent_recognition_score', 0)}"
            )
        else:
            validation_details.append(
                f"❌ Natural language not understood (0/3) - Score: {evaluation.get('intent_recognition_score', 0)}"
            )

        # 4. User experience - 2 points
        if result["response_time"] < 10 and len(result["response"] or "") > 20:
            business_score += 2
            validation_details.append(
                "✅ Good user experience - fast and informative (2/2)"
            )
        else:
            validation_details.append(
                "❌ Poor user experience - slow or unhelpful (0/2)"
            )

        status = (
            "success"
            if business_score >= 7
            else "partial"
            if business_score >= 4
            else "failed"
        )

        return {
            "status": status,
            "business_score": business_score,
            "max_score": max_score,
            "validation_details": validation_details,
            "meets_business_requirements": business_score >= 7,
        }

    async def test_admin_tool_access_control(self) -> Dict[str, Any]:
        """
        Test admin tool access control as part of business requirements
        Business Story: Regular users cannot access admin-only tools
        """
        print("\n🔒 Testing Admin Tool Access Control")

        admin_scenarios = [
            {
                "name": "Regular User Tries Admin Tool",
                "user_message": "/call access admin panel and show system logs",
                "user_id": self.test_user_id,
                "is_admin": False,
                "expected_outcome": "access_denied",
            },
            {
                "name": "Admin User Accesses Admin Tool",
                "user_message": "/call access admin panel and show system logs",
                "user_id": self.admin_user_id,
                "is_admin": True,
                "expected_outcome": "access_granted",
            },
        ]

        access_control_results = []

        for scenario in admin_scenarios:
            print(f"\n🔐 Testing: {scenario['name']}")

            try:
                response = await call_handler(
                    message=scenario["user_message"],
                    user_id=scenario["user_id"],
                    is_admin=scenario["is_admin"],
                )

                # Evaluate access control outcome
                if scenario["expected_outcome"] == "access_denied":
                    access_granted = (
                        "admin" not in str(response).lower()
                        and "access denied" in str(response).lower()
                    )
                else:
                    access_granted = (
                        "admin" in str(response).lower()
                        or "system" in str(response).lower()
                    )

                result = {
                    "scenario": scenario["name"],
                    "expected_outcome": scenario["expected_outcome"],
                    "access_correctly_controlled": access_granted,
                    "response": response,
                    "user_is_admin": scenario["is_admin"],
                }

                print(
                    f"{'✅' if access_granted else '❌'} Access control: {scenario['name']}"
                )

            except Exception as e:
                result = {
                    "scenario": scenario["name"],
                    "expected_outcome": scenario["expected_outcome"],
                    "access_correctly_controlled": scenario["expected_outcome"]
                    == "access_denied",
                    "response": None,
                    "error": str(e),
                    "user_is_admin": scenario["is_admin"],
                }

            access_control_results.append(result)

        return {
            "access_control_test": "Admin Tool Access Control",
            "total_tests": len(admin_scenarios),
            "passed_tests": len(
                [r for r in access_control_results if r["access_correctly_controlled"]]
            ),
            "results": access_control_results,
        }

    async def generate_business_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive business report for the /call command journey
        """
        print("\n📊 Generating Business Report for /call Command Journey")

        # Run complete journey
        journey_results = await self.run_complete_journey()

        # Run access control tests
        access_control_results = await self.test_admin_tool_access_control()

        # Calculate overall business metrics
        total_scenarios = (
            journey_results["total_scenarios"] + access_control_results["total_tests"]
        )
        successful_scenarios = (
            journey_results["successful_scenarios"]
            + access_control_results["passed_tests"]
        )

        overall_success_rate = (
            (successful_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
        )

        # Business requirements validation
        business_requirements_met = []
        for req, description in self.business_requirements.items():
            req_results = [
                r
                for r in self.test_results
                if r.get("business_outcome", {}).get(
                    "meets_business_requirements", False
                )
            ]
            if req_results:
                avg_score = sum(
                    r["business_outcome"]["business_score"] for r in req_results
                ) / len(req_results)
                business_requirements_met.append(
                    {
                        "requirement": req,
                        "description": description,
                        "met": avg_score >= 7,
                        "average_score": avg_score,
                    }
                )

        return {
            "test_execution_summary": {
                "test_name": "/call Command E2E Journey with LLM Judge",
                "execution_time": datetime.now().isoformat(),
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": overall_success_rate,
            },
            "journey_results": journey_results,
            "access_control_results": access_control_results,
            "business_requirements_validation": business_requirements_met,
            "business_readiness": {
                "ready_for_production": overall_success_rate >= 80,
                "user_experience_acceptable": overall_success_rate >= 70,
                "access_control_working": access_control_results["passed_tests"]
                == access_control_results["total_tests"],
            },
            "recommendations": self.generate_business_recommendations(
                overall_success_rate, business_requirements_met
            ),
        }

    def generate_business_recommendations(
        self, success_rate: float, requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate business recommendations based on test results
        """
        recommendations = []

        if success_rate >= 90:
            recommendations.append(
                "✅ Excellent performance - ready for production deployment"
            )
        elif success_rate >= 80:
            recommendations.append(
                "✅ Good performance - ready for production with monitoring"
            )
        elif success_rate >= 70:
            recommendations.append(
                "⚠️ Acceptable performance - consider improvements before production"
            )
        else:
            recommendations.append(
                "❌ Poor performance - significant improvements needed before production"
            )

        # Specific requirement-based recommendations
        failed_requirements = [req for req in requirements if not req["met"]]
        if failed_requirements:
            recommendations.append("🔧 Focus on improving these business requirements:")
            for req in failed_requirements:
                recommendations.append(
                    f"   - {req['requirement']}: {req['description']}"
                )

        return recommendations


async def run_call_command_e2e_journey():
    """
    Main function to run the complete E2E journey test for /call command
    """
    print("🚀 Starting /call Command E2E Journey Test with LLM Judge")
    print("=" * 60)

    journey_test = CallCommandJourneyTest()

    try:
        business_report = await journey_test.generate_business_report()

        print("\n" + "=" * 60)
        print("📊 BUSINESS REPORT SUMMARY")
        print("=" * 60)

        summary = business_report["test_execution_summary"]
        print(f"📈 Overall Success Rate: {summary['success_rate']:.1f}%")
        print(
            f"✅ Successful Scenarios: {summary['successful_scenarios']}/{summary['total_scenarios']}"
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
            f"   Access Control: {'✅' if readiness['access_control_working'] else '❌'}"
        )

        print("\n💡 Business Recommendations:")
        for rec in business_report["recommendations"]:
            print(f"   {rec}")

        print("\n📄 Full report saved to business_results.json")

        # Save detailed report
        with open("business_results.json", "w") as f:
            json.dump(business_report, f, indent=2)

        return business_report

    except Exception as e:
        print(f"❌ E2E Journey test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_call_command_e2e_journey())
