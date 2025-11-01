#!/usr/bin/env python3
"""
LLM Tile Judge System
====================

Uses LLM to analyze tile generation failures and provide detailed feedback:
- Analyzes failed E2E tests with visual context
- Provides detailed analysis of tile quality issues
- Writes findings to related PRP files
- Offers recommendations for improvement

JUDGE CRITERIA:
1. Visual Consistency: Do tiles maintain visual identity across states?
2. State Transitions: Are hover/click states appropriately different?
3. Widget Visibility: Are interactive elements properly visible?
4. Overall Quality: Does the tile meet kawaii anime style expectations?
"""

import base64
import json
import os
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Paths
TEST_RESULTS_DIR = Path("test_results/tile_quality")
PRP_DIR = Path("PRPs")
JUDGEMENTS_DIR = Path("test_results/llm_judgements")
JUDGEMENTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TileJudgement:
    """LLM judgement result for tile quality."""

    location_id: str
    widget_id: Optional[str]
    test_type: str
    overall_score: float  # 0-100
    visual_consistency_score: float
    state_transition_score: float
    widget_visibility_score: float
    style_compliance_score: float
    detailed_analysis: str
    recommendations: List[str]
    passed: bool


class LLMTileJudge:
    """LLM-powered judge for tile quality analysis."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o"  # Current vision model for image analysis

    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64 for LLM analysis."""
        try:
            with Image.open(image_path) as img:
                # Resize if too large (max 512x512 for vision models)
                if img.size[0] > 512 or img.size[1] > 512:
                    img.thumbnail((512, 512), Image.Resampling.LANCZOS)

                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")

        except Exception as e:
            print(f"❌ Error encoding image {image_path}: {e}")
            return ""

    def create_judgement_prompt(self, tile_info: Dict, test_results: Dict) -> str:
        """Create detailed prompt for LLM judgement."""
        prompt = f"""
You are an expert judge for anime-style tile generation quality. Please analyze the provided tile images and test results.

CONTEXT:
- Location: {tile_info.get("name", "Unknown")}
- Description: {tile_info.get("description", "No description")}
- Style: kawaii anime, peaceful atmosphere, pastel colors

TILE STATES TO ANALYZE:
- Idle: Normal peaceful state
- Hover: Interactive highlight state (should have soft glow/aura)
- Click: Active interaction state (should be more dynamic/magical)

EVALUATION CRITERIA:
1. Visual Consistency (25%): Do tiles maintain visual identity across states while showing appropriate changes?
2. State Transitions (25%): Are hover/click states appropriately different from idle?
3. Widget Visibility (25%): Are interactive elements (clock, book, poster, etc.) properly visible and clear?
4. Style Compliance (25%): Does the tile meet kawaii anime style expectations?

TEST RESULTS:
{json.dumps(test_results, indent=2)}

Please provide:
1. Overall quality score (0-100)
2. Individual scores for each criterion
3. Detailed analysis of what works and what doesn't
4. Specific recommendations for improvement
5. Pass/Fail determination (minimum 70% overall score to pass)

Respond in JSON format:
{{
    "overall_score": 85,
    "visual_consistency_score": 80,
    "state_transition_score": 85,
    "widget_visibility_score": 90,
    "style_compliance_score": 85,
    "detailed_analysis": "Detailed analysis of tile quality...",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "passed": true,
    "specific_issues": ["Issue 1", "Issue 2"]
}}
"""
        return prompt

    def analyze_tile_with_llm(
        self, location_id: str, widget_id: Optional[str] = None
    ) -> Optional[TileJudgement]:
        """Analyze tile quality using LLM vision capabilities."""
        if not self.api_key:
            print("⚠️  OpenAI API key not found, skipping LLM analysis")
            return None

        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            # Prepare tile images
            tile_paths = {
                "idle": Path(f"static/world/{location_id}_idle.png"),
                "hover": Path(f"static/world/{location_id}_hover.png"),
                "click": Path(f"static/world/{location_id}_click.png"),
            }

            # Check if tiles exist
            available_tiles = {}
            for state, path in tile_paths.items():
                if path.exists():
                    available_tiles[state] = path

            if not available_tiles:
                print(f"❌ No tiles found for location: {location_id}")
                return None

            # Create content with images
            content = [{"type": "text", "text": "Please analyze these tile images:"}]

            for state, path in available_tiles.items():
                base64_image = self.encode_image(path)
                if base64_image:
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low",
                            },
                        }
                    )

            # Load location info
            location_info = {}
            try:
                with open("static/world.json") as f:
                    world_data = json.load(f)
                    for location in world_data.get("locations", []):
                        if location["id"] == location_id:
                            location_info = location
                            break
            except Exception as e:
                print(f"⚠️  Could not load location info: {e}")

            # Create prompt
            test_results = {
                "tile_states": list(available_tiles.keys()),
                "location_info": location_info,
                "widget_focus": widget_id,
            }

            prompt = self.create_judgement_prompt(location_info, test_results)
            content.append({"type": "text", "text": prompt})

            print(f"🤖 Requesting LLM judgement for: {location_id}")

            # Make API request
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=1000,
                temperature=0.1,
            )

            # Parse response
            judgement_text = response.choices[0].message.content

            try:
                # Extract JSON from response (handle markdown formatting)
                if "```json" in judgement_text:
                    # Extract JSON from markdown code block
                    start = judgement_text.find("```json") + 7
                    end = judgement_text.find("```", start)
                    json_text = judgement_text[start:end].strip()
                elif "{" in judgement_text and "}" in judgement_text:
                    # Extract JSON from plain text
                    start = judgement_text.find("{")
                    end = judgement_text.rfind("}") + 1
                    json_text = judgement_text[start:end]
                else:
                    raise ValueError("No JSON found in response")

                judgement_data = json.loads(json_text)

                return TileJudgement(
                    location_id=location_id,
                    widget_id=widget_id,
                    test_type="comprehensive_tile_quality",
                    overall_score=judgement_data.get("overall_score", 0),
                    visual_consistency_score=judgement_data.get(
                        "visual_consistency_score", 0
                    ),
                    state_transition_score=judgement_data.get(
                        "state_transition_score", 0
                    ),
                    widget_visibility_score=judgement_data.get(
                        "widget_visibility_score", 0
                    ),
                    style_compliance_score=judgement_data.get(
                        "style_compliance_score", 0
                    ),
                    detailed_analysis=judgement_data.get("detailed_analysis", ""),
                    recommendations=judgement_data.get("recommendations", []),
                    passed=judgement_data.get("passed", False),
                )

            except json.JSONDecodeError:
                print(f"❌ Could not parse LLM response as JSON: {judgement_text}")
                return None

        except Exception as e:
            print(f"❌ Error in LLM analysis: {e}")
            return None

    def write_judgement_to_prp(self, judgement: TileJudgement, prp_number: str = "016"):
        """Write LLM judgement to PRP file."""
        prp_file = PRP_DIR / f"PRP-{prp_number}.md"

        if not prp_file.exists():
            print(f"⚠️  PRP-{prp_number}.md not found, creating new entry")
            return

        try:
            with open(prp_file, "r") as f:
                content = f.read()

            # Find the right place to add judgement (after progress section)
            judgement_section = f"""

---

### **🤖 LLM Tile Quality Judgement - {time.strftime("%Y-%m-%d %H:%M")}**

**Location:** {judgement.location_id}
**Widget:** {judgement.widget_id or "Overall Location"}
**Overall Score:** {judgement.overall_score}/100
**Status:** {"✅ PASS" if judgement.passed else "❌ FAIL"}

#### **Individual Scores:**
- **Visual Consistency:** {judgement.visual_consistency_score}/100
- **State Transitions:** {judgement.state_transition_score}/100
- **Widget Visibility:** {judgement.widget_visibility_score}/100
- **Style Compliance:** {judgement.style_compliance_score}/100

#### **📋 Detailed Analysis:**
{judgement.detailed_analysis}

#### **💡 Recommendations:**
{chr(10).join(f"- {rec}" for rec in judgement.recommendations)}

#### **🎯 Action Items:**
- [ ] {"✅ No action needed" if judgement.passed else "❌ Address identified issues"}
- [ ] Review and implement recommendations
- [ ] Re-run quality tests after improvements

---

"""

            # Add judgement to PRP
            updated_content = content + judgement_section

            with open(prp_file, "w") as f:
                f.write(updated_content)

            print(f"📝 Judgement written to PRP-{prp_number}.md")

        except Exception as e:
            print(f"❌ Error writing judgement to PRP: {e}")

    def save_judgement_report(self, judgements: List[TileJudgement]) -> Path:
        """Save comprehensive judgement report."""
        report = {
            "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model_used": self.model,
            "total_analyses": len(judgements),
            "passed_analyses": sum(1 for j in judgements if j.passed),
            "average_scores": {
                "overall": sum(j.overall_score for j in judgements) / len(judgements)
                if judgements
                else 0,
                "visual_consistency": sum(
                    j.visual_consistency_score for j in judgements
                )
                / len(judgements)
                if judgements
                else 0,
                "state_transition": sum(j.state_transition_score for j in judgements)
                / len(judgements)
                if judgements
                else 0,
                "widget_visibility": sum(j.widget_visibility_score for j in judgements)
                / len(judgements)
                if judgements
                else 0,
                "style_compliance": sum(j.style_compliance_score for j in judgements)
                / len(judgements)
                if judgements
                else 0,
            },
            "judgements": [],
        }

        for judgement in judgements:
            judgement_data = {
                "location_id": judgement.location_id,
                "widget_id": judgement.widget_id,
                "test_type": judgement.test_type,
                "overall_score": judgement.overall_score,
                "visual_consistency_score": judgement.visual_consistency_score,
                "state_transition_score": judgement.state_transition_score,
                "widget_visibility_score": judgement.widget_visibility_score,
                "style_compliance_score": judgement.style_compliance_score,
                "passed": judgement.passed,
                "detailed_analysis": judgement.detailed_analysis[:500] + "..."
                if len(judgement.detailed_analysis) > 500
                else judgement.detailed_analysis,
                "recommendations": judgement.recommendations,
            }
            report["judgements"].append(judgement_data)

        # Save report
        report_path = JUDGEMENTS_DIR / f"llm_judgement_report_{int(time.time())}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📊 Judgement report saved: {report_path}")
        return report_path


def main():
    """Run LLM tile judgement system."""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "LLM TILE JUDGE" + " " * 15 + "║")
    print("║" + " " * 10 + "AI-Powered Quality Analysis" + " " * 10 + "║")
    print("╚" + "=" * 68 + "╝\n")

    judge = LLMTileJudge()

    # Get locations to analyze
    world_tiles_dir = Path("static/world")
    location_ids = []

    for tile_file in world_tiles_dir.glob("*_idle.png"):
        location_id = tile_file.stem.replace("_idle", "")
        location_ids.append(location_id)

    if not location_ids:
        print("❌ No tiles found for analysis")
        return

    print(f"🎯 Analyzing {len(location_ids)} locations with LLM judge")
    print(f"🤖 Using model: {judge.model}\n")

    judgements = []
    for location_id in location_ids:
        print(f"\n{'=' * 50}")
        print(f"Analyzing: {location_id}")
        print(f"{'=' * 50}")

        judgement = judge.analyze_tile_with_llm(location_id)
        if judgement:
            judgements.append(judgement)
            print(f"✅ Overall Score: {judgement.overall_score}/100")
            print(f"📊 Status: {'PASS' if judgement.passed else 'FAIL'}")
            print(f"💡 Key Findings: {len(judgement.recommendations)} recommendations")

            # Write to PRP
            judge.write_judgement_to_prp(judgement)

            # Brief summary of analysis
            if len(judgement.detailed_analysis) > 200:
                print(f"📝 Analysis: {judgement.detailed_analysis[:200]}...")
            else:
                print(f"📝 Analysis: {judgement.detailed_analysis}")
        else:
            print(f"❌ Failed to get LLM judgement for {location_id}")

    # Save comprehensive report
    if judgements:
        judge.save_judgement_report(judgements)

        passed = sum(1 for j in judgements if j.passed)
        print("\n🎉 LLM Analysis Complete!")
        print(f"   Total Analyses: {len(judgements)}")
        print(f"   Passed: {passed}/{len(judgements)}")
        print(f"   Pass Rate: {passed / len(judgements) * 100:.1f}%")

        avg_score = sum(j.overall_score for j in judgements) / len(judgements)
        print(f"   Average Score: {avg_score:.1f}/100")
    else:
        print("\n❌ No judgements completed")


if __name__ == "__main__":
    main()
