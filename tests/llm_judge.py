"""
LLM Judge Implementation

Based on research from "LLM-as-a-Judge: Evaluating Complex Systems with AI"
- Strong LLM judges like GPT-4 approximate human preferences with >80% agreement
- Multi-turn questions and structured evaluation provide better results
- Position, verbosity, and self-enhancement biases must be addressed
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import openai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

logger = logging.getLogger(__name__)
console = Console()


class LLMJudge:
    """LLM Judge implementation using OpenAI API."""

    def __init__(self):
        """Initialize with OpenAI client."""
        self.client = openai.OpenAI()
        self.model = "gpt-4"  # Use GPT-4 for best judgment quality

    async def evaluate_test_results(
        self,
        test_name: str,
        test_results: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate test results using structured LLM judgment.

        Returns structured evaluation with scores and analysis.
        """
        # Load previous result for comparison if exists
        previous_result = self._load_previous_result(test_name)

        # Build comprehensive evaluation prompt
        prompt = self._build_evaluation_prompt(
            test_name, test_results, context, previous_result
        )

        try:
            # Get LLM evaluation
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Low temperature for consistent evaluation
                max_tokens=2000,
            )

            # Parse structured response
            evaluation = self._parse_evaluation_response(
                response.choices[0].message.content
            )

            # Add metadata
            evaluation["test_name"] = test_name
            evaluation["timestamp"] = datetime.utcnow().isoformat()
            evaluation["model"] = self.model
            evaluation["context"] = context or {}

            # Add historical comparison if previous result exists
            if previous_result:
                evaluation["historical_comparison"] = {
                    "previous_timestamp": previous_result.get("timestamp"),
                    "previous_score": previous_result.get("overall_score", 0),
                    "previous_verdict": previous_result.get("verdict", "UNKNOWN"),
                    "score_change": evaluation.get("overall_score", 0)
                    - previous_result.get("overall_score", 0),
                    "trend": self._calculate_trend(
                        previous_result.get("overall_score", 0),
                        evaluation.get("overall_score", 0),
                    ),
                }

            return evaluation

        except Exception as e:
            logger.error(f"LLM Judge evaluation failed: {e}")
            return {
                "test_name": test_name,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "score": 0.0,
                "confidence": 0.0,
                "verdict": "ERROR",
            }

    def _load_previous_result(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Load previous test result for comparison."""
        test_results_dir = Path("test_results")
        filename_map = {
            "Status Check with Thoughts": "status_check_with_thoughts_evaluation.json",
            "Comprehensive Conversation Journey": "comprehensive_conversation_journey_evaluation.json",
        }

        filename = filename_map.get(
            test_name, f"{test_name.lower().replace(' ', '_')}_evaluation.json"
        )
        filepath = test_results_dir / filename

        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    # If it's an array, get the most recent result
                    if isinstance(data, list):
                        return data[-1] if data else None
                    else:
                        return data
            except Exception as e:
                logger.warning(f"Could not load previous result: {e}")

        return None

    def _calculate_trend(self, previous_score: float, current_score: float) -> str:
        """Calculate trend based on score change."""
        change = current_score - previous_score
        if change > 5:
            return "IMPROVING"
        elif change < -5:
            return "DECLINING"
        else:
            return "STABLE"

    def _get_system_prompt(self) -> str:
        """Get system prompt for consistent evaluation."""
        return """You are an expert QA evaluator for DCMAIDBot, an AI assistant with emotional intelligence, memory, and tool integration capabilities.

Your role is to evaluate test results based on:
1. Business value and user experience
2. Technical correctness and robustness
3. Alignment with stated requirements
4. Quality of AI responses and interactions

Provide structured evaluation with:
- Overall score (0-100)
- Confidence in evaluation (0-100)
- Detailed strengths and weaknesses
- Specific recommendations
- PASS/FAIL verdict

Be objective, thorough, and evidence-based. Avoid position bias (don't be lenient or harsh)."""

    def _build_evaluation_prompt(
        self,
        test_name: str,
        test_results: Dict[str, Any],
        context: Dict[str, Any],
        previous_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build comprehensive evaluation prompt."""

        prompt = f"""
# Test: {test_name}
# Timestamp: {datetime.utcnow().isoformat()}

## TEST RESULTS TO EVALUATE:

```json
{json.dumps(test_results, indent=2)}
```

## HISTORICAL COMPARISON:
"""

        if previous_result:
            prompt += f"""

Previous test result from {previous_result.get("timestamp", "unknown time")}:
- Previous score: {previous_result.get("overall_score", "N/A")}/100
- Previous verdict: {previous_result.get("verdict", "UNKNOWN")}

Compare the current test results with the previous run and provide analysis on:
1. Score changes and trends
2. Improvements or regressions
3. Consistency of performance
4. Areas of progress or concern
"""
        else:
            prompt += """

No previous test results found. This is the baseline evaluation.
"""

        prompt += """

## EVALUATION CRITERIA:

### 1. Business Value Assessment (30%)
- Does the test validate real user journeys and business requirements?
- Are the interactions meaningful and valuable to users?
- Does the test cover critical user scenarios?

### 2. Technical Quality (25%)
- Are responses technically correct?
- Is the system robust and handling errors appropriately?
- Are all integrations working properly?

### 3. AI Response Quality (25%)
- Are responses natural and contextually appropriate?
- Does the AI demonstrate intelligence and understanding?
- Is personality (kawaii lilith) consistent and appropriate?

### 4. System Integration (20%)
- Are all components (memory, tools, emotions) working together?
- Is data persistence and retrieval working?
- Are admin/user access controls properly enforced?

## EVALUATION FORMAT:

Please provide your evaluation in this EXACT JSON format:

```json
{{
    "overall_score": <0-100>,
    "confidence": <0-100>,
    "business_value_score": <0-100>,
    "technical_quality_score": <0-100>,
    "ai_response_score": <0-100>,
    "integration_score": <0-100>,
    "verdict": "PASS" or "FAIL",
    "strengths": [
        "Specific strength 1",
        "Specific strength 2",
        "Specific strength 3"
    ],
    "weaknesses": [
        "Specific weakness 1",
        "Specific weakness 2",
        "Specific weakness 3"
    ],
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2",
        "Specific recommendation 3"
    ],
    "detailed_analysis": "Comprehensive analysis of test performance, including specific examples from the test results that support your scores."
}}
```

## EVALUATION GUIDELINES:

- Score 90-100: Excellent - Exceeds expectations, ready for production
- Score 80-89: Good - Meets expectations with minor improvements needed
- Score 70-79: Acceptable - Meets basic requirements but needs improvements
- Score 60-69: Marginal - Has significant issues that need addressing
- Score <60: Failing - Does not meet requirements

Consider the complexity of the test and the criticality of the features being tested.
"""

        return prompt

    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured evaluation."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # Try to parse entire response as JSON
                json_str = response.strip()

            evaluation = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "overall_score",
                "confidence",
                "business_value_score",
                "technical_quality_score",
                "ai_response_score",
                "integration_score",
                "verdict",
                "strengths",
                "weaknesses",
                "recommendations",
            ]

            for field in required_fields:
                if field not in evaluation:
                    logger.warning(f"Missing field in evaluation: {field}")
                    evaluation[field] = 0 if "score" in field else []

            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON evaluation: {e}")
            logger.error(f"Response was: {response[:500]}...")
            return {
                "error": "Failed to parse evaluation",
                "raw_response": response,
                "score": 0,
                "confidence": 0,
                "verdict": "ERROR",
            }

    def display_evaluation(self, evaluation: Dict[str, Any], test_name: str):
        """Display evaluation with rich formatting."""
        # Main verdict panel
        score = evaluation.get("overall_score", 0)
        confidence = evaluation.get("confidence", 0)
        verdict = evaluation.get("verdict", "UNKNOWN")

        is_pass = verdict == "PASS" and score >= 70
        color = "green" if is_pass else "red"

        panel_content = f"""
[bold]Score:[/bold] {score}/100
[bold]Confidence:[/bold] {confidence}/100
[bold]Business Value:[/bold] {evaluation.get("business_value_score", 0)}/100
[bold]Technical Quality:[/bold] {evaluation.get("technical_quality_score", 0)}/100
[bold]AI Response:[/bold] {evaluation.get("ai_response_score", 0)}/100
[bold]Integration:[/bold] {evaluation.get("integration_score", 0)}/100
[bold]Verdict:[/bold] [{color}]{verdict}[/{color}]
        """

        console.print(
            Panel(
                panel_content,
                title=f"[bold]🤖 LLM Judge Results - {test_name}[/bold]",
                border_style=color,
            )
        )

        # Scores breakdown
        scores_table = Table(title="Score Breakdown")
        scores_table.add_column("Category", style="cyan")
        scores_table.add_column("Score", justify="center", style="bold")
        scores_table.add_column("Weight", justify="center")
        scores_table.add_column("Weighted", justify="center", style="bold")

        scores_table.add_row(
            "Business Value",
            f"{evaluation.get('business_value_score', 0)}",
            "30%",
            f"{evaluation.get('business_value_score', 0) * 0.3:.1f}",
        )
        scores_table.add_row(
            "Technical Quality",
            f"{evaluation.get('technical_quality_score', 0)}",
            "25%",
            f"{evaluation.get('technical_quality_score', 0) * 0.25:.1f}",
        )
        scores_table.add_row(
            "AI Response",
            f"{evaluation.get('ai_response_score', 0)}",
            "25%",
            f"{evaluation.get('ai_response_score', 0) * 0.25:.1f}",
        )
        scores_table.add_row(
            "Integration",
            f"{evaluation.get('integration_score', 0)}",
            "20%",
            f"{evaluation.get('integration_score', 0) * 0.20:.1f}",
        )

        console.print(scores_table)

        # Strengths
        if evaluation.get("strengths"):
            strengths_tree = Tree("[green]✅ Strengths[/green]")
            for strength in evaluation["strengths"][:5]:
                strengths_tree.add(f"• {strength}")
            console.print(strengths)

        # Weaknesses
        if evaluation.get("weaknesses"):
            weaknesses_tree = Tree("[red]⚠️  Weaknesses[/red]")
            for weakness in evaluation["weaknesses"][:5]:
                weaknesses_tree.add(f"• {weakness}")
            console.print(weaknesses)

        # Recommendations
        if evaluation.get("recommendations"):
            rec_tree = Tree("[blue]💡 Recommendations[/blue]")
            for rec in evaluation["recommendations"][:5]:
                rec_tree.add(f"• {rec}")
            console.print(rec_tree)

        # Detailed analysis
        if evaluation.get("detailed_analysis"):
            console.print("\n[bold]Detailed Analysis:[/bold]")
            console.print(evaluation["detailed_analysis"])

    async def save_evaluation(self, evaluation: Dict[str, Any], test_name: str) -> str:
        """
        Save evaluation to JSON file.

        Returns file path.
        """
        # Create test_results directory
        test_results_dir = Path("test_results")
        test_results_dir.mkdir(exist_ok=True)

        # Generate filename from test name
        filename = test_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        filepath = test_results_dir / f"{filename}_evaluation.json"

        # Save single evaluation object (not array)
        with open(filepath, "w") as f:
            json.dump(evaluation, f, indent=2)

        logger.info(f"Evaluation saved to {filepath}")
        return str(filepath)


# Status-specific evaluation prompts
STATUS_EVALUATION_PROMPT = """
# Status Check Test Evaluation

## Special Considerations for Status Tests:

### System Health Metrics
- Component health scores should be >80% for healthy systems
- Response times should be <1 second for API endpoints
- Database and Redis connections should be stable

### Thoughts Generation
- Version thoughts should show kawaii lilith personality
- Self-check thoughts should provide meaningful diagnostics
- Crypto thoughts should demonstrate market analysis capability

### Evaluation Focus:
1. System reliability and uptime
2. Thoughts generation quality and relevance
3. Monitoring and diagnostic capabilities
4. API responsiveness and accuracy
"""

# Journey test specific evaluation prompts
JOURNEY_EVALUATION_PROMPT = """
# Comprehensive Conversation Journey Evaluation

## Special Considerations for Journey Tests:

### Conversation Flow
- Natural progression through different features
- Context retention across multiple turns
- Appropriate transitions between topics

### Feature Integration
- Memory system should remember user details
- Lessons should be delivered effectively
- VAD/mood tracking should work consistently
- Tools (search, curl) should integrate seamlessly

### AI Personality
- Kawaii lilith personality should be consistent
- Emotional intelligence should be demonstrated
- Responses should be helpful and engaging

### Evaluation Focus:
1. User experience and journey completion
2. Memory persistence and recall accuracy
3. Emotional intelligence and VAD scoring
4. Tool integration and functionality
5. Educational value through lessons
"""
