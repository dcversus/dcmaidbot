"""
LLM-as-Judge Verification System

This module implements an LLM-powered judge system for evaluating test results
with structured responses, confidence scores, and acceptance criteria.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class JudgeResult:
    """Structured result from LLM judge evaluation."""

    # Overall assessment
    overall_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    is_acceptable: bool  # Pass/Fail decision

    # Detailed breakdown
    functionality_score: float
    performance_score: float
    security_score: float
    usability_score: float

    # Feedback and recommendations
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

    # Metadata
    judge_name: str
    evaluation_timestamp: str
    context_info: Dict[str, Any]


class LLMJudge:
    """LLM-powered judge for test evaluation and quality assessment."""

    def __init__(self, llm_service: LLMService):
        """Initialize the LLM judge.

        Args:
            llm_service: LLM service instance for generating judgments
        """
        self.llm_service = llm_service
        self.judge_name = "Claude-Judge-v4.5"

    async def evaluate_test_results(
        self,
        test_category: str,
        test_results: Dict[str, Any],
        expected_outcomes: List[str],
        actual_outcomes: List[str],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> JudgeResult:
        """
        Evaluate test results using LLM as judge.

        Args:
            test_category: Category of tests being evaluated (e.g., "PRP-009 External Tools")
            test_results: Detailed test results and metrics
            expected_outcomes: List of expected outcomes from DoD/requirements
            actual_outcomes: List of actual observed outcomes
            additional_context: Additional context for evaluation

        Returns:
            JudgeResult: Structured evaluation with scores and feedback
        """

        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            test_category=test_category,
            test_results=test_results,
            expected_outcomes=expected_outcomes,
            actual_outcomes=actual_outcomes,
            additional_context=additional_context,
        )

        try:
            # Get LLM judgment
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_judge_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
            )

            # Parse LLM response
            judgment_text = response.choices[0].message.content
            result = self._parse_judgment_response(judgment_text)

            # Add metadata
            result.judge_name = self.judge_name
            result.evaluation_timestamp = datetime.utcnow().isoformat()
            result.context_info = {
                "test_category": test_category,
                "expected_count": len(expected_outcomes),
                "actual_count": len(actual_outcomes),
                "llm_model": "gpt-4o-mini",
                **(additional_context or {}),
            }

            logger.info(
                f"LLM Judge evaluation completed for {test_category}: "
                f"Score={result.overall_score:.2f}, "
                f"Acceptable={result.is_acceptable}"
            )

            return result

        except Exception as e:
            logger.error(f"LLM Judge evaluation failed: {e}")
            # Return fallback result
            return JudgeResult(
                overall_score=0.0,
                confidence=0.0,
                is_acceptable=False,
                functionality_score=0.0,
                performance_score=0.0,
                security_score=0.0,
                usability_score=0.0,
                summary=f"Evaluation failed due to error: {str(e)}",
                strengths=[],
                weaknesses=["LLM evaluation failed"],
                recommendations=["Fix evaluation system and retry"],
                judge_name=self.judge_name,
                evaluation_timestamp=datetime.utcnow().isoformat(),
                context_info={"error": str(e)},
            )

    def _get_judge_system_prompt(self) -> str:
        """Get system prompt for the LLM judge."""
        return """You are an expert QA Engineer and Software Evaluator with 15+ years of experience in testing complex systems. Your role is to evaluate test results against requirements and provide structured, objective assessments.

Your evaluation must be:
1. **Objective**: Base judgments on evidence, not assumptions
2. **Structured**: Follow the exact output format specified
3. **Detailed**: Provide specific feedback and recommendations
4. **Fair**: Consider both strengths and weaknesses
5. **Professional**: Use clear, constructive language

Scoring Guidelines:
- 0.0-0.3: Critical issues, major functionality broken
- 0.3-0.6: Significant issues, core functionality affected
- 0.6-0.8: Minor issues, functionality mostly working
- 0.8-0.9: Good quality, minor improvements needed
- 0.9-1.0: Excellent quality, meets all requirements

Focus on actual functionality, security, and user experience rather than test infrastructure issues."""

    def _build_evaluation_prompt(
        self,
        test_category: str,
        test_results: Dict[str, Any],
        expected_outcomes: List[str],
        actual_outcomes: List[str],
        additional_context: Optional[Dict[str, Any]],
    ) -> str:
        """Build comprehensive evaluation prompt for the LLM judge."""

        prompt = f"""# Test Evaluation Request

## Test Category
{test_category}

## Expected Outcomes (Requirements)
{self._format_list(expected_outcomes)}

## Actual Outcomes (Test Results)
{self._format_list(actual_outcomes)}

## Detailed Test Results
```json
{json.dumps(test_results, indent=2)}
```

## Additional Context
{self._format_context(additional_context)}

## Evaluation Instructions

Please evaluate these test results against the expected outcomes and provide a comprehensive assessment. Consider:

1. **Functionality**: Are the core features working as specified?
2. **Performance**: Are response times and resource usage acceptable?
3. **Security**: Are access controls and safety measures working?
4. **User Experience**: Is the system intuitive and reliable?

## Required Output Format

Please respond with a JSON object containing:

```json
{{
    "overall_score": 0.85,
    "confidence": 0.90,
    "is_acceptable": true,
    "functionality_score": 0.90,
    "performance_score": 0.80,
    "security_score": 0.85,
    "usability_score": 0.85,
    "summary": "Clear summary of overall assessment",
    "strengths": [
        "Specific strength 1",
        "Specific strength 2"
    ],
    "weaknesses": [
        "Specific weakness 1",
        "Specific weakness 2"
    ],
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ]
}}
```

Score each category from 0.0 to 1.0. Be honest and constructive in your assessment."""

        return prompt

    def _format_list(self, items: List[str]) -> str:
        """Format list items for prompt."""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    def _format_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format additional context for prompt."""
        if not context:
            return "No additional context provided."

        formatted = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                formatted.append(
                    f"**{key}**:\n```json\n{json.dumps(value, indent=2)}\n```"
                )
            else:
                formatted.append(f"**{key}**: {value}")

        return "\n\n".join(formatted)

    def _parse_judgment_response(self, response_text: str) -> JudgeResult:
        """Parse LLM judgment response into JudgeResult object."""
        try:
            # Extract JSON from response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "overall_score",
                "confidence",
                "is_acceptable",
                "functionality_score",
                "performance_score",
                "security_score",
                "usability_score",
                "summary",
                "strengths",
                "weaknesses",
                "recommendations",
            ]

            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field '{field}' in LLM response")
                    data[field] = self._get_default_value(field)

            return JudgeResult(**data)

        except Exception as e:
            logger.error(f"Failed to parse LLM judgment response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Return minimal fallback result
            return JudgeResult(
                overall_score=0.5,
                confidence=0.3,
                is_acceptable=False,
                functionality_score=0.5,
                performance_score=0.5,
                security_score=0.5,
                usability_score=0.5,
                summary=f"Failed to parse LLM response: {str(e)}",
                strengths=["Response received"],
                weaknesses=["Response parsing failed"],
                recommendations=["Fix response format"],
                judge_name=self.judge_name,
                evaluation_timestamp=datetime.utcnow().isoformat(),
                context_info={"parse_error": str(e)},
            )

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field."""
        defaults = {
            "overall_score": 0.5,
            "confidence": 0.3,
            "is_acceptable": False,
            "functionality_score": 0.5,
            "performance_score": 0.5,
            "security_score": 0.5,
            "usability_score": 0.5,
            "summary": "No summary provided",
            "strengths": [],
            "weaknesses": ["Missing data"],
            "recommendations": ["Provide complete evaluation"],
        }
        return defaults.get(field, None)


class TestSuiteEvaluator:
    """Evaluates entire test suites using LLM judge."""

    def __init__(self, llm_service: LLMService):
        """Initialize test suite evaluator."""
        self.llm_judge = LLMJudge(llm_service)

    async def evaluate_prp_compliance(
        self,
        prp_name: str,
        test_results: Dict[str, Any],
        dod_criteria: List[str],
        test_categories: Dict[str, Dict[str, Any]],
    ) -> Dict[str, JudgeResult]:
        """
        Evaluate PRP compliance across multiple test categories.

        Args:
            prp_name: Name of the PRP being evaluated
            test_results: Overall test results summary
            dod_criteria: List of Definition of Done criteria
            test_categories: Detailed results by test category

        Returns:
            Dict mapping category names to JudgeResult objects
        """

        results = {}

        # Evaluate each test category
        for category_name, category_data in test_categories.items():
            expected = category_data.get("expected_outcomes", [])
            actual = category_data.get("actual_outcomes", [])
            context = {
                "prp_name": prp_name,
                "category_type": category_data.get("type", "unknown"),
                "test_count": category_data.get("test_count", 0),
                "pass_rate": category_data.get("pass_rate", 0.0),
            }

            result = await self.llm_judge.evaluate_test_results(
                test_category=f"{prp_name} - {category_name}",
                test_results=category_data,
                expected_outcomes=expected,
                actual_outcomes=actual,
                additional_context=context,
            )

            results[category_name] = result

        # Evaluate overall PRP compliance
        overall_context = {
            "prp_name": prp_name,
            "dod_criteria_count": len(dod_criteria),
            "test_categories_count": len(test_categories),
            "categories_evaluated": list(test_categories.keys()),
        }

        overall_result = await self.llm_judge.evaluate_test_results(
            test_category=f"{prp_name} - Overall Compliance",
            test_results=test_results,
            expected_outcomes=dod_criteria,
            actual_outcomes=[
                cat.get("summary", "") for cat in test_categories.values()
            ],
            additional_context=overall_context,
        )

        results["overall"] = overall_result

        return results

    def generate_evaluation_report(
        self, prp_name: str, evaluation_results: Dict[str, JudgeResult]
    ) -> str:
        """
        Generate comprehensive evaluation report.

        Args:
            prp_name: Name of the PRP evaluated
            evaluation_results: Results from LLM judge evaluation

        Returns:
            Formatted evaluation report
        """

        report = f"""# LLM Judge Evaluation Report

## PRP: {prp_name}
**Evaluation Date**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Judge**: {evaluation_results.get("overall", {}).judge_name or "Unknown"}

## Executive Summary

"""

        if "overall" in evaluation_results:
            overall = evaluation_results["overall"]
            report += f"""**Overall Score**: {overall.overall_score:.2f}/1.0
**Confidence**: {overall.confidence:.2f}
**Status**: {"✅ ACCEPTABLE" if overall.is_acceptable else "❌ NOT ACCEPTABLE"}

### Summary
{overall.summary}

"""

        # Category breakdown
        report += "## Category Breakdown\n\n"

        for category, result in evaluation_results.items():
            if category == "overall":
                continue

            report += f"""### {category}
- **Score**: {result.overall_score:.2f}/1.0
- **Confidence**: {result.confidence:.2f}
- **Status**: {"✅ PASS" if result.is_acceptable else "❌ FAIL"}

**Strengths**:
{chr(10).join(f"- {s}" for s in result.strengths[:3])}

**Weaknesses**:
{chr(10).join(f"- {w}" for w in result.weaknesses[:3])}

**Recommendations**:
{chr(10).join(f"- {r}" for r in result.recommendations[:3])}

"""

        # Overall recommendations
        if "overall" in evaluation_results:
            report += """## Overall Recommendations

"""
            report += "\n".join(f"- {r}" for r in overall.recommendations)
            report += "\n\n"

        report += "---\n"
        report += "*Report generated by LLM Judge System*"

        return report
