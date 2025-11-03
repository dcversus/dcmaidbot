"""
Status Judge Testing System with LLM Evaluation
Business Requirements: Comprehensive status validation with AI-powered analysis

This judge system validates the enhanced status service, analyzes tool documentation,
and provides structured scoring for confidence, acceptance, recommendations, and problems.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
from llm_judge import LLMJudge

# Import local modules
from core.services.llm_service import LLMService
from core.services.status_enhanced_service import EnhancedStatusService

load_dotenv()


class StatusJudge:
    """
    LLM-powered status judge for comprehensive system validation
    Business Value: AI-driven analysis of system health and documentation quality
    """

    def __init__(self, llm_service: LLMService):
        """Initialize status judge"""
        self.llm_service = llm_service
        self.llm_judge = LLMJudge(llm_service)
        self.status_service = EnhancedStatusService(llm_service)

    async def run_status_validation(self, environment: str = "local") -> Dict[str, Any]:
        """
        Run comprehensive status validation
        Business Story: AI judge evaluates system health and documentation quality
        """
        print(f"🏛️ Starting Status Judge Validation for {environment} environment")
        print("=" * 60)

        validation_results = {}

        try:
            # 1. Wait for or generate version thoughts
            print("🧠 Validating Version Thoughts...")
            version_validation = await self.validate_version_thoughts()
            validation_results["version_thoughts"] = version_validation

            # 2. Wait for or generate self-check thoughts
            print("🔍 Validating Self-Check Thoughts...")
            self_check_validation = await self.validate_self_check_thoughts()
            validation_results["self_check_thoughts"] = self_check_validation

            # 3. Load comprehensive status
            print("📊 Loading Comprehensive Status...")
            status_data = await self.status_service.get_comprehensive_status()
            validation_results["status_data"] = status_data

            # 4. Analyze tools documentation
            print("📚 Analyzing Tools Documentation...")
            tools_analysis = await self.analyze_tools_documentation()
            validation_results["tools_analysis"] = tools_analysis

            # 5. Generate comprehensive evaluation
            print("⚖️ Generating Comprehensive Evaluation...")
            comprehensive_evaluation = await self.generate_comprehensive_evaluation(
                status_data, tools_analysis, environment
            )
            validation_results["comprehensive_evaluation"] = comprehensive_evaluation

            # 6. Generate final verdict
            print("🎯 Generating Final Verdict...")
            final_verdict = self.generate_final_verdict(comprehensive_evaluation)
            validation_results["final_verdict"] = final_verdict

            print("\n✅ Status Judge Validation Complete")
            return validation_results

        except Exception as e:
            print(f"❌ Status Judge Validation failed: {e}")
            return {
                "validation_failed": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "environment": environment,
            }

    async def validate_version_thoughts(self) -> Dict[str, Any]:
        """
        Validate version thoughts generation and quality
        Business Requirement: Version thoughts should be meaningful and informative
        """
        print("  🔍 Checking version thoughts...")

        try:
            # Get or generate version thoughts
            if not self.status_service.version_thoughts:
                # Generate version thoughts with sample changelog
                sample_changelog = """
## [Unreleased]
### Added
- Enhanced status system with AI-powered diagnostics
- Crypto thoughts integration for market insights
- Comprehensive self-check system

### Changed
- Improved error handling and user experience
- Updated LLM integration for better performance

### Fixed
- Fixed database connection issues
- Resolved webhook endpoint problems
"""
                await self.status_service.generate_version_thoughts(sample_changelog)

            version_thoughts = self.status_service.version_thoughts

            if not version_thoughts or not version_thoughts.get("success"):
                return {
                    "status": "failed",
                    "error": "Version thoughts generation failed",
                    "confidence_score": 0,
                    "recommendations": ["Fix version thoughts generation system"],
                    "problems": ["Cannot generate version thoughts"],
                }

            # Evaluate quality of version thoughts
            thoughts_content = version_thoughts.get("version_thoughts", "")

            quality_score = 0
            validation_details = []

            # Check for meaningful content (3 points)
            if len(thoughts_content) > 100:
                quality_score += 3
                validation_details.append("✅ Substantial content (3/3)")
            else:
                validation_details.append("❌ Content too brief (0/3)")

            # Check for kawaii personality (2 points)
            if any(
                keyword in thoughts_content.lower()
                for keyword in ["lilith", "<3", "kawaii", "cute", "uwu"]
            ):
                quality_score += 2
                validation_details.append("✅ Kawaii personality present (2/2)")
            else:
                validation_details.append("❌ Missing kawaii personality (0/2)")

            # Check for markdown formatting (2 points)
            if (
                "**" in thoughts_content
                or "*" in thoughts_content
                or "#" in thoughts_content
            ):
                quality_score += 2
                validation_details.append("✅ Markdown formatting used (2/2)")
            else:
                validation_details.append("❌ No markdown formatting (0/2)")

            # Check for version information (3 points)
            if any(
                keyword in thoughts_content.lower()
                for keyword in ["version", "new", "update", "feature"]
            ):
                quality_score += 3
                validation_details.append("✅ Version information included (3/3)")
            else:
                validation_details.append("❌ Missing version information (0/3)")

            return {
                "status": "success",
                "quality_score": quality_score,
                "max_score": 10,
                "validation_details": validation_details,
                "confidence_score": quality_score / 10,
                "thoughts_length": len(thoughts_content),
                "generation_time": version_thoughts.get("generation_time", 0),
                "tokens_used": version_thoughts.get("tokens_used", 0),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "confidence_score": 0,
                "recommendations": ["Fix version thoughts validation"],
                "problems": [f"Validation error: {str(e)}"],
            }

    async def validate_self_check_thoughts(self) -> Dict[str, Any]:
        """
        Validate self-check thoughts generation and quality
        Business Requirement: Self-check should provide comprehensive system diagnostics
        """
        print("  🔍 Checking self-check thoughts...")

        try:
            # Get or generate self-check thoughts
            if not self.status_service.self_check_thoughts:
                await self.status_service.generate_self_check_thoughts()

            self_check_thoughts = self.status_service.self_check_thoughts

            if not self_check_thoughts or not self_check_thoughts.get("success"):
                return {
                    "status": "failed",
                    "error": "Self-check thoughts generation failed",
                    "confidence_score": 0,
                    "recommendations": ["Fix self-check thoughts generation system"],
                    "problems": ["Cannot generate self-check thoughts"],
                }

            # Evaluate quality of self-check thoughts
            thoughts_content = self_check_thoughts.get("self_check_thoughts", "")
            tool_results = self_check_thoughts.get("tool_results", [])

            quality_score = 0
            validation_details = []

            # Check for comprehensive analysis (3 points)
            if len(thoughts_content) > 200:
                quality_score += 3
                validation_details.append("✅ Comprehensive analysis (3/3)")
            else:
                validation_details.append("❌ Analysis too brief (0/3)")

            # Check for tool results coverage (3 points)
            if len(tool_results) >= 5:
                quality_score += 3
                validation_details.append("✅ All tools checked (3/3)")
            else:
                validation_details.append(
                    f"❌ Only {len(tool_results)} tools checked (0/3)"
                )

            # Check for structured reporting (2 points)
            if any(
                keyword in thoughts_content.lower()
                for keyword in ["confidence", "status", "working", "failing"]
            ):
                quality_score += 2
                validation_details.append("✅ Structured reporting (2/2)")
            else:
                validation_details.append("❌ Unstructured reporting (0/2)")

            # Check for actionable insights (2 points)
            if any(
                keyword in thoughts_content.lower()
                for keyword in ["recommend", "fix", "improve", "action"]
            ):
                quality_score += 2
                validation_details.append("✅ Actionable insights (2/2)")
            else:
                validation_details.append("❌ No actionable insights (0/2)")

            # Calculate tool health percentage
            working_tools = len(
                [t for t in tool_results if t.get("status") == "working"]
            )
            total_tools = len(tool_results)
            tool_health_percentage = (
                (working_tools / total_tools * 100) if total_tools > 0 else 0
            )

            return {
                "status": "success",
                "quality_score": quality_score,
                "max_score": 10,
                "validation_details": validation_details,
                "confidence_score": quality_score / 10,
                "tool_health_percentage": tool_health_percentage,
                "working_tools": working_tools,
                "total_tools": total_tools,
                "total_time": self_check_thoughts.get("total_time", 0),
                "tokens_used": self_check_thoughts.get("tokens_used", 0),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "confidence_score": 0,
                "recommendations": ["Fix self-check thoughts validation"],
                "problems": [f"Validation error: {str(e)}"],
            }

    async def analyze_tools_documentation(self) -> Dict[str, Any]:
        """
        Analyze tools documentation quality and completeness
        Business Requirement: All tools should have proper documentation
        """
        print("  📚 Analyzing tools documentation...")

        try:
            tools_path = Path("tools")
            if not tools_path.exists():
                return {
                    "status": "warning",
                    "message": "Tools directory not found",
                    "confidence_score": 0.5,
                    "recommendations": ["Create tools directory with documentation"],
                    "problems": ["Missing tools documentation"],
                }

            # Find all .md files in tools directory
            tool_files = list(tools_path.glob("*.md"))

            if not tool_files:
                return {
                    "status": "warning",
                    "message": "No tool documentation files found",
                    "confidence_score": 0.3,
                    "recommendations": ["Create documentation for all tools"],
                    "problems": ["No tool documentation found"],
                }

            # Analyze each tool documentation
            tool_analysis_results = []
            total_quality_score = 0

            for tool_file in tool_files:
                analysis = await self.analyze_single_tool_documentation(tool_file)
                tool_analysis_results.append(analysis)
                total_quality_score += analysis.get("quality_score", 0)

            # Calculate overall documentation quality
            avg_quality_score = (
                total_quality_score / len(tool_files) if tool_files else 0
            )

            return {
                "status": "success",
                "total_tools_documented": len(tool_files),
                "average_quality_score": avg_quality_score,
                "max_score": 10,
                "tool_results": tool_analysis_results,
                "confidence_score": avg_quality_score / 10,
                "recommendations": self.generate_documentation_recommendations(
                    tool_analysis_results
                ),
                "problems": self.identify_documentation_problems(tool_analysis_results),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "confidence_score": 0,
                "recommendations": ["Fix tools documentation analysis"],
                "problems": [f"Analysis error: {str(e)}"],
            }

    async def analyze_single_tool_documentation(
        self, tool_file: Path
    ) -> Dict[str, Any]:
        """
        Analyze a single tool documentation file
        """
        try:
            with open(tool_file, "r", encoding="utf-8") as f:
                content = f.read()

            tool_name = tool_file.stem
            quality_score = 0
            validation_details = []

            # Check for basic structure (2 points)
            if any(header in content for header in ["#", "##", "###"]):
                quality_score += 2
                validation_details.append("✅ Has proper headers (2/2)")
            else:
                validation_details.append("❌ Missing headers (0/2)")

            # Check for description (2 points)
            if len(content) > 200:
                quality_score += 2
                validation_details.append("✅ Substantial description (2/2)")
            else:
                validation_details.append("❌ Description too brief (0/2)")

            # Check for usage examples (2 points)
            if any(
                keyword in content.lower()
                for keyword in ["example", "usage", "how to", "```"]
            ):
                quality_score += 2
                validation_details.append("✅ Has usage examples (2/2)")
            else:
                validation_details.append("❌ Missing usage examples (0/2)")

            # Check for configuration (2 points)
            if any(
                keyword in content.lower()
                for keyword in ["config", "setting", "env", "environment"]
            ):
                quality_score += 2
                validation_details.append("✅ Has configuration info (2/2)")
            else:
                validation_details.append("❌ Missing configuration info (0/2)")

            # Check for troubleshooting (2 points)
            if any(
                keyword in content.lower()
                for keyword in ["troubleshoot", "error", "problem", "fix"]
            ):
                quality_score += 2
                validation_details.append("✅ Has troubleshooting (2/2)")
            else:
                validation_details.append("❌ Missing troubleshooting (0/2)")

            return {
                "tool_name": tool_name,
                "quality_score": quality_score,
                "max_score": 10,
                "validation_details": validation_details,
                "file_size": len(content),
                "last_modified": datetime.fromtimestamp(
                    tool_file.stat().st_mtime
                ).isoformat(),
            }

        except Exception as e:
            return {
                "tool_name": tool_file.stem,
                "quality_score": 0,
                "max_score": 10,
                "validation_details": [f"❌ File analysis failed: {str(e)}"],
                "error": str(e),
            }

    async def generate_comprehensive_evaluation(
        self,
        status_data: Dict[str, Any],
        tools_analysis: Dict[str, Any],
        environment: str,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation using LLM judge
        Business Value: AI-powered analysis of overall system health
        """
        print("  ⚖️ Running LLM judge comprehensive evaluation...")

        # Create evaluation prompt
        evaluation_prompt = f"""You are an expert system validation judge. Analyze the following system status data and provide a comprehensive evaluation.

ENVIRONMENT: {environment}

STATUS DATA:
{json.dumps(status_data, indent=2, default=str)}

TOOLS DOCUMENTATION ANALYSIS:
{json.dumps(tools_analysis, indent=2, default=str)}

Please provide a structured evaluation with:
1. Overall confidence score (0-10)
2. Acceptance score (0-10) - is this system ready for this environment?
3. List of specific recommendations (prioritized)
4. List of identified problems (categorized by severity)
5. Assessment of system readiness
6. Business impact analysis
7. Security considerations

Be thorough, professional, and provide actionable insights. Use markdown formatting."""

        try:
            # Get LLM evaluation
            evaluation_response = await self.llm_service.generate_response(
                evaluation_prompt
            )

            # Parse structured response (simplified - in real implementation would use structured parsing)
            evaluation_result = {
                "evaluation_response": evaluation_response,
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
                "status_data_summary": {
                    "version": status_data.get("version", "unknown"),
                    "uptime": status_data.get("uptime", 0),
                    "tokens_total": status_data.get("tokens_total", 0),
                    "components_working": self.count_working_components(status_data),
                },
                "tools_summary": {
                    "total_tools": tools_analysis.get("total_tools_documented", 0),
                    "avg_quality": tools_analysis.get("average_quality_score", 0),
                },
            }

            return evaluation_result

        except Exception as e:
            return {
                "evaluation_failed": True,
                "error": str(e),
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
            }

    def count_working_components(self, status_data: Dict[str, Any]) -> int:
        """
        Count working system components
        """
        working_components = 0

        # Check various components
        if status_data.get("redis", {}).get("status") == "operational":
            working_components += 1
        if status_data.get("postgresql", {}).get("status") == "operational":
            working_components += 1
        if status_data.get("telegram", {}).get("status") == "operational":
            working_components += 1
        if status_data.get("bot", {}).get("status") == "operational":
            working_components += 1

        return working_components

    def generate_final_verdict(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final verdict based on comprehensive evaluation
        Business Outcome: Clear pass/fail determination with reasoning
        """
        print("  🎯 Generating final verdict...")

        # Extract key metrics
        version_validation = evaluation.get("version_thoughts", {})
        self_check_validation = evaluation.get("self_check_thoughts", {})
        tools_analysis = evaluation.get("tools_analysis", {})

        # Calculate scores
        version_score = version_validation.get("quality_score", 0) / 10
        self_check_score = self_check_validation.get("quality_score", 0) / 10
        tools_score = tools_analysis.get("confidence_score", 0)

        # Overall score (weighted average)
        overall_score = version_score * 0.3 + self_check_score * 0.4 + tools_score * 0.3

        # Determine verdict
        if overall_score >= 0.8:
            verdict_status = "PASS"
            verdict_message = "System is ready for deployment"
            deployment_readiness = True
        elif overall_score >= 0.6:
            verdict_status = "CONDITIONAL"
            verdict_message = "System is ready with minor improvements recommended"
            deployment_readiness = True
        else:
            verdict_status = "FAIL"
            verdict_message = "System needs significant improvements before deployment"
            deployment_readiness = False

        # Generate recommendations
        all_recommendations = []
        all_recommendations.extend(version_validation.get("recommendations", []))
        all_recommendations.extend(self_check_validation.get("recommendations", []))
        all_recommendations.extend(tools_analysis.get("recommendations", []))

        # Generate problems list
        all_problems = []
        all_problems.extend(version_validation.get("problems", []))
        all_problems.extend(self_check_validation.get("problems", []))
        all_problems.extend(tools_analysis.get("problems", []))

        return {
            "verdict_status": verdict_status,
            "verdict_message": verdict_message,
            "deployment_readiness": deployment_readiness,
            "overall_score": overall_score,
            "max_score": 1.0,
            "component_scores": {
                "version_thoughts": version_score,
                "self_check_thoughts": self_check_score,
                "tools_documentation": tools_score,
            },
            "recommendations": all_recommendations,
            "problems": all_problems,
            "timestamp": datetime.now().isoformat(),
            "next_steps": self.generate_next_steps(verdict_status, all_recommendations),
        }

    def generate_documentation_recommendations(
        self, tool_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on tool documentation analysis
        """
        recommendations = []

        low_quality_tools = [t for t in tool_results if t.get("quality_score", 0) < 6]
        if low_quality_tools:
            recommendations.append(
                f"Improve documentation for: {', '.join([t['tool_name'] for t in low_quality_tools])}"
            )

        missing_examples = [
            t
            for t in tool_results
            if "Missing usage examples" in str(t.get("validation_details", []))
        ]
        if missing_examples:
            recommendations.append("Add usage examples to all tool documentation")

        missing_config = [
            t
            for t in tool_results
            if "Missing configuration info" in str(t.get("validation_details", []))
        ]
        if missing_config:
            recommendations.append(
                "Add configuration information to tool documentation"
            )

        return recommendations

    def identify_documentation_problems(
        self, tool_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identify problems in tool documentation
        """
        problems = []

        for tool in tool_results:
            tool_name = tool.get("tool_name", "unknown")
            issues = [
                detail
                for detail in tool.get("validation_details", [])
                if detail.startswith("❌")
            ]
            if issues:
                problems.append(f"{tool_name}: {', '.join(issues)}")

        return problems

    def generate_next_steps(
        self, verdict_status: str, recommendations: List[str]
    ) -> List[str]:
        """
        Generate next steps based on verdict
        """
        if verdict_status == "PASS":
            return [
                "✅ System is ready for deployment",
                "🚀 Proceed with deployment process",
                "📊 Continue monitoring in production",
            ]
        elif verdict_status == "CONDITIONAL":
            return [
                "⚠️ Address minor improvements before deployment",
                "🔧 Implement recommended improvements",
                "🔄 Re-run validation after improvements",
            ]
        else:
            return [
                "❌ Do not deploy - significant issues found",
                "🛠️ Address all major problems",
                "🔄 Re-run complete validation after fixes",
                "📋 Consider code review for critical issues",
            ]


async def run_status_judge(environment: str = "local"):
    """
    Main function to run status judge validation
    """
    print("🏛️ Status Judge Testing System")
    print(f"🎯 Environment: {environment}")
    print("=" * 60)

    # Initialize services
    llm_service = LLMService()
    status_judge = StatusJudge(llm_service)

    try:
        # Run comprehensive validation
        validation_results = await status_judge.run_status_validation(environment)

        # Display results
        print("\n" + "=" * 60)
        print("📊 STATUS JUDGE VALIDATION RESULTS")
        print("=" * 60)

        if "final_verdict" in validation_results:
            verdict = validation_results["final_verdict"]
            print(f"🎯 Verdict: {verdict['verdict_status']}")
            print(f"📈 Overall Score: {verdict['overall_score']:.1%}")
            print(f"💬 Message: {verdict['verdict_message']}")
            print(
                f"🚀 Deployment Ready: {'✅' if verdict['deployment_readiness'] else '❌'}"
            )

            if verdict.get("recommendations"):
                print("\n💡 Recommendations:")
                for rec in verdict["recommendations"]:
                    print(f"   • {rec}")

            if verdict.get("problems"):
                print("\n⚠️ Problems:")
                for prob in verdict["problems"]:
                    print(f"   • {prob}")

            if verdict.get("next_steps"):
                print("\n📋 Next Steps:")
                for step in verdict["next_steps"]:
                    print(f"   {step}")

        # Save results
        output_file = f"status_judge_results_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(validation_results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {output_file}")

        return validation_results

    except Exception as e:
        print(f"❌ Status judge validation failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Status Judge Validation")
    parser.add_argument(
        "--environment",
        default="local",
        choices=["local", "dev", "prod"],
        help="Environment to validate",
    )
    args = parser.parse_args()

    asyncio.run(run_status_judge(args.environment))
