#!/usr/bin/env python3
"""
Tile State Visual Analysis
==========================

Manual analysis tool for examining tile state transitions:
- Compare visual differences between idle/hover/click states
- Analyze specific widget areas for expected changes
- Identify issues with state generation
- Create visual comparison reports

EXPECTED STATE CHANGES:
- Clock (time): idle → hover (soft glow) → click (enlarged, detailed)
- Cactus (status): idle → hover (slightly larger) → click (blooms with flower)
- Book (changelog): idle → hover (magical glow) → click (open with text)
- Poster (link): idle → hover (sparkles) → click (enhanced effects)
"""

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Paths
WORLD_TILES_DIR = Path("static/world")
WORLD_JSON = Path("static/world.json")
ANALYSIS_DIR = Path("analysis_results")
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


class TileStateAnalyzer:
    """Analyzes visual differences between tile states."""

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

            # Calculate color distribution
            if len(widget_area.shape) == 3:
                r_mean = np.mean(widget_area[:, :, 0])
                g_mean = np.mean(widget_area[:, :, 1])
                b_mean = np.mean(widget_area[:, :, 2])
            else:
                r_mean = g_mean = b_mean = brightness

            return {
                "brightness": float(brightness),
                "color_variance": float(color_variance),
                "contrast": float(contrast),
                "color_means": {
                    "red": float(r_mean),
                    "green": float(g_mean),
                    "blue": float(b_mean),
                },
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

            widget_results = {
                "widget_info": widget_info,
                "state_analysis": {},
                "state_changes": {},
            }

            for state, tile_path in tile_files.items():
                analysis = self.analyze_widget_area(tile_path, widget_info)
                widget_results["state_analysis"][state] = analysis
                print(
                    f"      {state}: brightness={analysis.get('brightness', 0):.1f}, contrast={analysis.get('contrast', 0):.1f}"
                )

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

    def check_expectations(self, location_id: str, analysis: Dict) -> Dict:
        """Check if generated tiles meet visual expectations."""
        print(f"\n📋 Checking visual expectations for: {location_id}")

        expectations = {
            "time": {
                "idle": {
                    "visible": True,
                    "description": "Clock should be visible showing time",
                },
                "hover": {
                    "brighter": True,
                    "description": "Clock should have glow effect",
                },
                "click": {
                    "larger_or_brighter": True,
                    "description": "Clock should be enhanced/detailed",
                },
            },
            "status": {
                "idle": {
                    "visible": True,
                    "description": "Cactus should be small and peaceful",
                },
                "hover": {
                    "brighter": True,
                    "description": "Cactus should appear more vibrant",
                },
                "click": {
                    "brighter": True,
                    "description": "Cactus should bloom with flower",
                },
            },
            "changelog": {
                "idle": {
                    "visible": True,
                    "description": "Book should be closed with visible spine",
                },
                "hover": {
                    "brighter": True,
                    "description": "Book should have magical glow",
                },
                "click": {"different": True, "description": "Book should appear open"},
            },
            "link": {
                "idle": {
                    "visible": True,
                    "description": "Poster should be visible on wall",
                },
                "hover": {
                    "brighter": True,
                    "description": "Poster should have sparkles",
                },
                "click": {
                    "brighter": True,
                    "description": "Poster should have enhanced effects",
                },
            },
        }

        widget_analysis = analysis.get("widget_analysis", {})
        expectation_results = {
            "location_id": location_id,
            "widget_expectations": {},
            "overall_status": "PASS",
            "issues_found": [],
        }

        for widget_id, widget_data in widget_analysis.items():
            widget_type = widget_data["widget_info"]["type"]

            if widget_type in expectations:
                widget_expectations = expectations[widget_type]
                state_changes = widget_data.get("state_changes", {})

                widget_result = {
                    "widget_type": widget_type,
                    "widget_name": widget_data["widget_info"]["name"],
                    "expectations_met": [],
                    "expectations_failed": [],
                }

                # Check hover state expectations
                if "idle_to_hover" in state_changes:
                    change = state_changes["idle_to_hover"]

                    if (
                        widget_expectations["hover"].get("brighter")
                        and change["significant_brightness_change"]
                    ):
                        widget_result["expectations_met"].append(
                            "Hover state is brighter than idle"
                        )
                    elif widget_expectations["hover"].get("brighter"):
                        widget_result["expectations_failed"].append(
                            "Hover state should be brighter than idle"
                        )

                # Check click state expectations
                if "hover_to_click" in state_changes:
                    change = state_changes["hover_to_click"]

                    if (
                        widget_expectations["click"].get("brighter")
                        and change["significant_brightness_change"]
                    ):
                        widget_result["expectations_met"].append(
                            "Click state is brighter than hover"
                        )
                    elif widget_expectations["click"].get("brighter"):
                        widget_result["expectations_failed"].append(
                            "Click state should be brighter than hover"
                        )

                    if widget_expectations["click"].get("larger_or_brighter") and (
                        change["significant_brightness_change"]
                        or change["significant_contrast_change"]
                    ):
                        widget_result["expectations_met"].append(
                            "Click state shows enhancement"
                        )
                    elif widget_expectations["click"].get("larger_or_brighter"):
                        widget_result["expectations_failed"].append(
                            "Click state should show enhancement"
                        )

                expectation_results["widget_expectations"][widget_id] = widget_result

                # Print results for this widget
                met_count = len(widget_result["expectations_met"])
                failed_count = len(widget_result["expectations_failed"])

                print(
                    f"   📊 {widget_id} ({widget_type}): {met_count} met, {failed_count} failed"
                )

                for expectation in widget_result["expectations_met"]:
                    print(f"      ✅ {expectation}")
                for expectation in widget_result["expectations_failed"]:
                    print(f"      ❌ {expectation}")
                    expectation_results["issues_found"].append(
                        f"{widget_id}: {expectation}"
                    )

        # Determine overall status
        if expectation_results["issues_found"]:
            expectation_results["overall_status"] = "FAIL"
            print(
                f"\n   ❌ OVERALL: {len(expectation_results['issues_found'])} expectation(s) failed"
            )
        else:
            print("\n   ✅ OVERALL: All expectations met!")

        return expectation_results

    def create_visual_comparison(self, location_id: str) -> Path:
        """Create visual comparison of tile states."""
        tile_files = {
            "idle": WORLD_TILES_DIR / f"{location_id}_idle.png",
            "hover": WORLD_TILES_DIR / f"{location_id}_hover.png",
            "click": WORLD_TILES_DIR / f"{location_id}_click.png",
        }

        # Check if all tiles exist
        missing = [state for state, path in tile_files.items() if not path.exists()]
        if missing:
            print(
                f"❌ Cannot create visual comparison - missing tiles: {', '.join(missing)}"
            )
            return None

        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            fig.suptitle(f"Tile State Comparison: {location_id}", fontsize=16)

            states = ["idle", "hover", "click"]

            for i, state in enumerate(states):
                ax = axes[i]
                img = Image.open(tile_files[state])
                ax.imshow(img)
                ax.set_title(f"{state.title()} State", fontsize=12)
                ax.axis("off")

                # Add widget annotations
                widgets = self.widget_positions.get(location_id, {})
                for widget_id, widget_info in widgets.items():
                    pos = widget_info["position"]
                    size = widget_info["size"]

                    # Draw rectangle around widget area
                    rect = patches.Rectangle(
                        (pos["x"], pos["y"]),
                        size["width"],
                        size["height"],
                        linewidth=1,
                        edgecolor="red",
                        facecolor="none",
                    )
                    ax.add_patch(rect)

                    # Add widget label
                    ax.text(
                        pos["x"] + size["width"] / 2,
                        pos["y"] - 5,
                        widget_id,
                        ha="center",
                        fontsize=8,
                        color="white",
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="black", alpha=0.7
                        ),
                    )

            plt.tight_layout()

            # Save comparison
            comparison_path = ANALYSIS_DIR / f"{location_id}_comparison.png"
            plt.savefig(comparison_path, dpi=150, bbox_inches="tight")
            plt.close()

            print(f"📸 Visual comparison saved: {comparison_path}")
            return comparison_path

        except Exception as e:
            print(f"❌ Error creating visual comparison: {e}")
            return None

    def save_analysis_report(
        self, location_id: str, analysis: Dict, expectations: Dict
    ) -> Path:
        """Save comprehensive analysis report."""
        report = {
            "analysis_timestamp": "2025-10-31T21:40:00Z",
            "location_id": location_id,
            "state_comparison_analysis": analysis.get("state_comparisons", {}),
            "widget_analysis": analysis.get("widget_analysis", {}),
            "full_tile_analysis": analysis.get("full_tile_analysis", {}),
            "expectation_check": expectations,
            "overall_status": expectations.get("overall_status", "UNKNOWN"),
            "recommendations": self._generate_recommendations(analysis, expectations),
        }

        report_path = ANALYSIS_DIR / f"{location_id}_analysis.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Analysis report saved: {report_path}")
        return report_path

    def _generate_recommendations(
        self, analysis: Dict, expectations: Dict
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Check state comparisons
        state_comparisons = analysis.get("state_comparisons", {})
        for comparison, data in state_comparisons.items():
            if not data.get("significant_difference", False):
                states = comparison.split("_vs_")
                recommendations.append(
                    f"States {states[0]} and {states[1]} are too similar - "
                    f"consider enhancing visual differences"
                )

        # Check widget state changes
        widget_analysis = analysis.get("widget_analysis", {})
        for widget_id, widget_data in widget_analysis.items():
            state_changes = widget_data.get("state_changes", {})

            if "idle_to_hover" in state_changes:
                change = state_changes["idle_to_hover"]
                if not change.get("significant_brightness_change", False):
                    recommendations.append(
                        f"Widget {widget_id} hover state needs more visual enhancement"
                    )

            if "hover_to_click" in state_changes:
                change = state_changes["hover_to_click"]
                if not (
                    change.get("significant_brightness_change", False)
                    or change.get("significant_contrast_change", False)
                ):
                    recommendations.append(
                        f"Widget {widget_id} click state needs more dramatic changes"
                    )

        # Check expectation failures
        issues = expectations.get("issues_found", [])
        if issues:
            recommendations.append(
                "Address expectation failures in widget state transitions"
            )

        if not recommendations:
            recommendations.append(
                "Tile generation quality is good - no major issues identified"
            )

        return recommendations


def main():
    """Run tile state analysis."""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "TILE STATE ANALYSIS" + " " * 12 + "║")
    print("║" + " " * 8 + "Manual Visual Examination" + " " * 8 + "║")
    print("╚" + "=" * 68 + "╝\n")

    analyzer = TileStateAnalyzer()

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
        analysis = analyzer.analyze_states(location_id)

        # Check expectations
        expectations = analyzer.check_expectations(location_id, analysis)

        # Create visual comparison
        comparison_path = analyzer.create_visual_comparison(location_id)

        # Save analysis report
        report_path = analyzer.save_analysis_report(location_id, analysis, expectations)

        # Print summary
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
        print(f"   Average State Similarity: {avg_similarity:.1f}%")
        print(f"   Overall Status: {expectations.get('overall_status', 'UNKNOWN')}")
        print(f"   Issues Found: {len(expectations.get('issues_found', []))}")
        print(
            f"   Visual Comparison: {'✅ Created' if comparison_path else '❌ Failed'}"
        )
        print(f"   Analysis Report: {'✅ Saved' if report_path else '❌ Failed'}")

    print("\n🎉 Tile State Analysis Complete!")


if __name__ == "__main__":
    main()
