#!/usr/bin/env python3
"""
Simple Tile State Analysis (No External Dependencies)
======================================================

Manual analysis tool for examining tile state transitions:
- Compare visual differences between idle/hover/click states
- Analyze specific widget areas for expected changes
- Identify issues with state generation
- Create text-based reports

EXPECTED STATE CHANGES:
- Clock (time): idle → hover (soft glow) → click (enlarged, detailed)
- Cactus (status): idle → hover (slightly larger) → click (blooms with flower)
- Book (changelog): idle → hover (magical glow) → click (open with text)
- Poster (link): idle → hover (sparkles) → click (enhanced effects)
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image

# Paths
WORLD_TILES_DIR = Path("static/world")
WORLD_JSON = Path("static/world.json")
ANALYSIS_DIR = Path("analysis_results")
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


class SimpleTileStateAnalyzer:
    """Analyzes visual differences between tile states without external dependencies."""

    def __init__(self):
        self.widget_positions = self._load_widget_positions()

    def _load_widget_positions(self) -> Dict:
        """Load widget positions from world.json."""
        try:
            with open(WORLD_JSON) as f:
                world_data = json.load(f)

            widgets = {}
            for location in world_data.get("locations", []):
                location_widgets = {}
                for widget in location.get("widgets", []):
                    widget_id = widget["id"]
                    location_widgets[widget_id] = {
                        "type": widget["type"],
                        "name": widget["name"],
                        "position": widget["position"],
                        "size": widget["size"],
                        "description": widget["description"],
                        "interactions": widget.get("interactions", {}),
                    }
                widgets[location["id"]] = location_widgets

            return widgets

        except Exception as e:
            print(f"❌ Error loading widget positions: {e}")
            return {}

    def analyze_widget_area(self, tile_path: Path, widget_info: Dict) -> Dict:
        """Analyze specific widget area in a tile."""
        try:
            img = Image.open(tile_path)
            img_array = np.array(img)

            pos = widget_info["position"]
            size = widget_info["size"]
            margin = 10

            # Extract widget area with margin
            x1 = max(0, pos["x"] - margin)
            y1 = max(0, pos["y"] - margin)
            x2 = min(img_array.shape[1], pos["x"] + size["width"] + margin)
            y2 = min(img_array.shape[0], pos["y"] + size["height"] + margin)

            widget_area = img_array[y1:y2, x1:x2]

            # Calculate metrics
            brightness = np.mean(widget_area)
            color_variance = np.var(widget_area, axis=2).mean()

            # Calculate contrast (difference between brightest and darkest areas)
            if len(widget_area.shape) == 3:
                gray = np.mean(widget_area, axis=2)
                contrast = np.max(gray) - np.min(gray)
            else:
                contrast = 0

            return {
                "brightness": float(brightness),
                "color_variance": float(color_variance),
                "contrast": float(contrast),
                "area_size": (x2 - x1) * (y2 - y1),
                "position": (x1, y1, x2 - x1, y2 - y1),
            }

        except Exception as e:
            print(f"❌ Error analyzing widget area: {e}")
            return {}

    def compare_states(self, location_id: str) -> Dict:
        """Compare different states for a location."""
        print(f"\n🔍 Comparing states for: {location_id}")

        tile_files = {
            "idle": WORLD_TILES_DIR / f"{location_id}_idle.png",
            "hover": WORLD_TILES_DIR / f"{location_id}_hover.png",
            "click": WORLD_TILES_DIR / f"{location_id}_click.png",
        }

        # Check if all tiles exist
        missing = [state for state, path in tile_files.items() if not path.exists()]
        if missing:
            return {"error": f"Missing tiles: {', '.join(missing)}"}

        results = {
            "location_id": location_id,
            "state_comparisons": {},
            "widget_analysis": {},
            "full_tile_analysis": {},
            "expectation_analysis": {},
        }

        # Load widget positions for this location
        widgets = self.widget_positions.get(location_id, {})
        if not widgets:
            print("⚠️  No widget data found for location")
            return results

        # Analyze full tiles
        for state, tile_path in tile_files.items():
            try:
                img = Image.open(tile_path)
                img_array = np.array(img)

                results["full_tile_analysis"][state] = {
                    "brightness": float(np.mean(img_array)),
                    "color_variance": float(np.var(img_array, axis=2).mean()),
                    "size": img_array.shape[:2],
                }
                print(
                    f"   📊 {state}: brightness={np.mean(img_array):.1f}, variance={np.var(img_array, axis=2).mean():.1f}"
                )

            except Exception as e:
                print(f"   ❌ Error analyzing {state} tile: {e}")

        # Compare states
        states = list(tile_files.keys())
        for i in range(len(states)):
            for j in range(i + 1, len(states)):
                state1, state2 = states[i], states[j]

                try:
                    img1 = Image.open(tile_files[state1])
                    img2 = Image.open(tile_files[state2])

                    arr1 = np.array(img1)
                    arr2 = np.array(img2)

                    # Calculate pixel-wise difference
                    diff = np.abs(arr1.astype(float) - arr2.astype(float))
                    avg_diff = np.mean(diff)
                    max_diff = np.max(diff)

                    # Calculate similarity (inverse of difference)
                    max_possible_diff = 255 * 3  # RGB max difference
                    similarity = max(0, 100 - (avg_diff / max_possible_diff * 100))

                    results["state_comparisons"][f"{state1}_vs_{state2}"] = {
                        "average_difference": float(avg_diff),
                        "max_difference": float(max_diff),
                        "similarity_percentage": float(similarity),
                        "significant_difference": avg_diff
                        > 10,  # Threshold for visible difference
                    }

                    print(
                        f"   🔄 {state1} vs {state2}: {similarity:.1f}% similar, avg diff: {avg_diff:.1f}"
                    )

                except Exception as e:
                    print(f"   ❌ Error comparing {state1} and {state2}: {e}")

        # Analyze each widget across states
        for widget_id, widget_info in widgets.items():
            print(f"\n   🎯 Widget: {widget_id} ({widget_info['type']})")
            print(f"      Description: {widget_info['description']}")

            widget_results = {
                "widget_info": widget_info,
                "state_analysis": {},
                "state_changes": {},
                "expectation_analysis": {},
            }

            for state, tile_path in tile_files.items():
                analysis = self.analyze_widget_area(tile_path, widget_info)
                widget_results["state_analysis"][state] = analysis
                print(
                    f"      {state}: brightness={analysis.get('brightness', 0):.1f}, contrast={analysis.get('contrast', 0):.1f}"
                )

            # Check specific expectations for each widget type
            expectation_analysis = self._check_widget_expectations(
                widget_info,
                widget_results["state_analysis"],
                widget_results["state_changes"],
            )
            widget_results["expectation_analysis"] = expectation_analysis

            # Analyze state changes for this widget
            if (
                "idle" in widget_results["state_analysis"]
                and "hover" in widget_results["state_analysis"]
            ):
                idle_data = widget_results["state_analysis"]["idle"]
                hover_data = widget_results["state_analysis"]["hover"]

                hover_brightness_change = (
                    hover_data["brightness"] - idle_data["brightness"]
                )
                hover_contrast_change = hover_data["contrast"] - idle_data["contrast"]

                widget_results["state_changes"]["idle_to_hover"] = {
                    "brightness_change": float(hover_brightness_change),
                    "contrast_change": float(hover_contrast_change),
                    "significant_brightness_change": abs(hover_brightness_change) > 5,
                    "significant_contrast_change": abs(hover_contrast_change) > 10,
                }

                print(
                    f"      💡 Idle→Hover: brightness Δ{hover_brightness_change:+.1f}, contrast Δ{hover_contrast_change:+.1f}"
                )

            if (
                "hover" in widget_results["state_analysis"]
                and "click" in widget_results["state_analysis"]
            ):
                hover_data = widget_results["state_analysis"]["hover"]
                click_data = widget_results["state_analysis"]["click"]

                click_brightness_change = (
                    click_data["brightness"] - hover_data["brightness"]
                )
                click_contrast_change = click_data["contrast"] - hover_data["contrast"]

                widget_results["state_changes"]["hover_to_click"] = {
                    "brightness_change": float(click_brightness_change),
                    "contrast_change": float(click_contrast_change),
                    "significant_brightness_change": abs(click_brightness_change) > 5,
                    "significant_contrast_change": abs(click_contrast_change) > 10,
                }

                print(
                    f"      🎯 Hover→Click: brightness Δ{click_brightness_change:+.1f}, contrast Δ{click_contrast_change:+.1f}"
                )

            results["widget_analysis"][widget_id] = widget_results

        return results

    def _check_widget_expectations(
        self, widget_info: Dict, state_analysis: Dict, state_changes: Dict
    ) -> Dict:
        """Check if generated tiles meet specific widget expectations."""
        widget_type = widget_info.get("type", "")
        widget_info.get("interactions", {})

        expectation_results = {
            "widget_type": widget_type,
            "expectations_checked": [],
            "expectations_met": [],
            "expectations_failed": [],
            "issues_identified": [],
        }

        # Check clock (time widget) expectations
        if widget_type == "time":
            # Clock should be visible in all states
            for state, analysis in state_analysis.items():
                if analysis.get("brightness", 0) > 50:  # Visible threshold
                    expectation_results["expectations_met"].append(
                        f"Clock visible in {state} state"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        f"Clock not visible in {state} state"
                    )

            # Hover should make clock brighter (glow effect)
            if "idle_to_hover" in state_changes:
                change = state_changes["idle_to_hover"]
                if change["significant_brightness_change"]:
                    expectation_results["expectations_met"].append(
                        "Clock glows on hover"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Clock should glow on hover"
                    )
                    expectation_results["issues_identified"].append(
                        "clock_hover_no_effect"
                    )

            # Click should enhance clock
            if "hover_to_click" in state_changes:
                change = state_changes["hover_to_click"]
                if (
                    change["significant_brightness_change"]
                    or change["significant_contrast_change"]
                ):
                    expectation_results["expectations_met"].append(
                        "Clock enhanced on click"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Clock should be enhanced on click"
                    )
                    expectation_results["issues_identified"].append(
                        "clock_click_no_enhancement"
                    )

        # Check cactus (status widget) expectations
        elif widget_type == "status":
            # Check if cactus blooms on click
            if "idle_to_click" in state_changes:
                change = state_changes["idle_to_click"]
                if (
                    change["significant_brightness_change"]
                    or change["significant_contrast_change"]
                ):
                    expectation_results["expectations_met"].append(
                        "Cactus shows change on click"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Cactus should bloom on click"
                    )
                    expectation_results["issues_identified"].append("cactus_no_bloom")

        # Check book (changelog widget) expectations
        elif widget_type == "changelog":
            # Book should change significantly on click
            if "idle_to_click" in state_changes:
                change = state_changes["idle_to_click"]
                if (
                    change["significant_brightness_change"]
                    or change["significant_contrast_change"]
                ):
                    expectation_results["expectations_met"].append(
                        "Book changes on click"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Book should open on click"
                    )
                    expectation_results["issues_identified"].append("book_not_opening")

        # Check poster (link widget) expectations
        elif widget_type == "link":
            # Poster should show effects on hover/click
            if "idle_to_hover" in state_changes:
                change = state_changes["idle_to_hover"]
                if change["significant_brightness_change"]:
                    expectation_results["expectations_met"].append(
                        "Poster responds to hover"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Poster should respond to hover"
                    )
                    expectation_results["issues_identified"].append(
                        "poster_no_hover_effect"
                    )

            if "hover_to_click" in state_changes:
                change = state_changes["hover_to_click"]
                if (
                    change["significant_brightness_change"]
                    or change["significant_contrast_change"]
                ):
                    expectation_results["expectations_met"].append(
                        "Poster enhanced on click"
                    )
                else:
                    expectation_results["expectations_failed"].append(
                        "Poster should be enhanced on click"
                    )
                    expectation_results["issues_identified"].append(
                        "poster_no_click_enhancement"
                    )

        # Check all expectations checked
        expectation_results["expectations_checked"] = (
            expectation_results["expectations_met"]
            + expectation_results["expectations_failed"]
        )

        return expectation_results

    def save_analysis_report(self, location_id: str, analysis: Dict) -> Path:
        """Save comprehensive analysis report."""
        report = {
            "analysis_timestamp": "2025-10-31T21:45:00Z",
            "location_id": location_id,
            "state_comparison_analysis": analysis.get("state_comparisons", {}),
            "widget_analysis": analysis.get("widget_analysis", {}),
            "full_tile_analysis": analysis.get("full_tile_analysis", {}),
            "summary": self._generate_summary(analysis),
        }

        report_path = ANALYSIS_DIR / f"{location_id}_simple_analysis.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Analysis report saved: {report_path}")
        return report_path

    def _generate_summary(self, analysis: Dict) -> Dict:
        """Generate summary of analysis results."""
        summary = {
            "total_widgets": len(analysis.get("widget_analysis", {})),
            "widgets_with_issues": 0,
            "state_transition_issues": 0,
            "major_concerns": [],
        }

        # Count widgets with issues
        for widget_id, widget_data in analysis.get("widget_analysis", {}).items():
            expectation_analysis = widget_data.get("expectation_analysis", {})
            issues = expectation_analysis.get("issues_identified", [])
            if issues:
                summary["widgets_with_issues"] += 1
                summary["major_concerns"].extend(issues)

        # Check state transition issues
        state_comparisons = analysis.get("state_comparisons", {})
        for comparison, data in state_comparisons.items():
            if not data.get("significant_difference", False):
                summary["state_transition_issues"] += 1

        # Determine overall status
        if (
            summary["widgets_with_issues"] == 0
            and summary["state_transition_issues"] == 0
        ):
            summary["overall_status"] = "PASS"
        elif (
            summary["widgets_with_issues"] > 0
            and summary["state_transition_issues"] == 0
        ):
            summary["overall_status"] = "PARTIAL"
        else:
            summary["overall_status"] = "FAIL"

        return summary

    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []

        # Check state comparisons
        state_comparisons = analysis.get("state_comparisons", {})
        for comparison, data in state_comparisons.items():
            if not data.get("significant_difference", False):
                states = comparison.split("_vs_")
                recommendations.append(
                    f"States {states[0]} and {states[1]} are too similar (only {data['similarity_percentage']:.1f}% different)"
                )

        # Check widget analysis for specific issues
        widget_analysis = analysis.get("widget_analysis", {})
        for widget_id, widget_data in widget_analysis.items():
            expectation_analysis = widget_data.get("expectation_analysis", {})
            issues = expectation_analysis.get("issues_identified", [])

            for issue in issues:
                if "clock" in issue:
                    recommendations.append(f"Clock widget: {issue}")
                elif "cactus" in issue:
                    recommendations.append(f"Cactus widget: {issue}")
                elif "book" in issue:
                    recommendations.append(f"Book widget: {issue}")
                elif "poster" in issue:
                    recommendations.append(f"Poster widget: {issue}")
                else:
                    recommendations.append(f"Widget {widget_id}: {issue}")

        if not recommendations:
            recommendations.append(
                "Tile generation quality appears good - no major issues detected"
            )

        return recommendations


def main():
    """Run simple tile state analysis."""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "SIMPLE TILE ANALYSIS" + " " * 12 + "║")
    print("║" + " " * 8 + "No External Dependencies" + " " * 8 + "║")
    print("╚" + "=" * 68 + "╝\n")

    analyzer = SimpleTileStateAnalyzer()

    # Get locations to analyze
    location_ids = []
    for tile_file in WORLD_TILES_DIR.glob("*_idle.png"):
        location_id = tile_file.stem.replace("_idle", "")
        location_ids.append(location_id)

    if not location_ids:
        print("❌ No tiles found for analysis")
        return

    print(f"🎯 Analyzing {len(location_ids)} locations")
    print("📊 Will check visual expectations for state transitions\n")

    for location_id in location_ids:
        print(f"\n{'=' * 60}")
        print(f"LOCATION: {location_id}")
        print(f"{'=' * 60}")

        # Analyze states
        analysis = analyzer.compare_states(location_id)

        # Generate recommendations
        recommendations = analyzer.generate_recommendations(analysis)

        # Save analysis report
        report_path = analyzer.save_analysis_report(location_id, analysis)

        # Print summary
        summary = analysis.get("summary", {})
        state_comparisons = analysis.get("state_comparisons", {})
        avg_similarity = (
            np.mean(
                [
                    data.get("similarity_percentage", 0)
                    for data in state_comparisons.values()
                ]
            )
            if state_comparisons
            else 0
        )

        print(f"\n📊 SUMMARY for {location_id}:")
        print(f"   Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"   Total Widgets: {summary.get('total_widgets', 0)}")
        print(f"   Widgets with Issues: {summary.get('widgets_with_issues', 0)}")
        print(
            f"   State Transition Issues: {summary.get('state_transition_issues', 0)}"
        )
        print(f"   Average State Similarity: {avg_similarity:.1f}%")

        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")

        if len(recommendations) > 5:
            print(f"   ... and {len(recommendations) - 5} more")

        print(f"\n   📄 Analysis Report: {'✅ Saved' if report_path else '❌ Failed'}")

    print("\n🎉 Simple Tile Analysis Complete!")


if __name__ == "__main__":
    main()
