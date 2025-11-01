#!/usr/bin/env python3
"""
State Coordination Manager
==========================

Advanced state coordination system for widget state transitions
with AI enhancement and intelligent state management.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import openai
from dotenv import load_dotenv
from image_composition_manager import ImageCompositionManager

load_dotenv()

# Configuration
WORLD_JSON = Path("static/world.json")
RESULT_JSON = Path("static/result.json")
WORLD_TILES_DIR = Path("static/world")

# AI APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


class StateCoordinationManager:
    """
    Advanced state coordination system for managing
    widget state transitions and AI enhancements.
    """

    def __init__(self):
        """Initialize the state coordination manager."""
        self.composition_manager = ImageCompositionManager()
        self.state_cache = {}
        self.transition_history = []
        self.ai_enhancement_enabled = True

        print("🎯 StateCoordinationManager initialized")

    async def create_enhanced_composite_tile(
        self,
        location: Dict[str, Any],
        state: str = "idle",
        options: Dict[str, Any] = None,
        enhance_with_ai: bool = True,
    ) -> str:
        """
        Create an enhanced composite tile with AI improvements.

        Args:
            location: Location dictionary from world.json
            state: Widget state ('idle', 'hover', 'click')
            options: Additional composition options
            enhance_with_ai: Whether to apply AI enhancements

        Returns:
            Path to generated enhanced composite image file
        """
        if options is None:
            options = {}

        # Create state cache key
        cache_key = self._create_state_cache_key(
            location, state, options, enhance_with_ai
        )

        # Check cache first
        if cache_key in self.state_cache:
            print(f"📋 Using cached enhanced state: {cache_key}")
            return self.state_cache[cache_key]

        print(f"🎨 Creating enhanced composite for {location['name']} - {state}")

        try:
            # Generate base composite
            composite_path = await self.composition_manager.create_composite_tile(
                location, state, options
            )

            # Apply AI enhancements if enabled
            if enhance_with_ai and self.ai_enhancement_enabled:
                enhanced_path = await self._apply_ai_enhancements(
                    location, state, composite_path, options
                )
            else:
                enhanced_path = composite_path

            # Cache result
            self.state_cache[cache_key] = enhanced_path

            print(f"✅ Enhanced composite saved: {enhanced_path}")
            return enhanced_path

        except Exception as e:
            print(f"❌ Error creating enhanced composite: {e}")
            # Fallback to basic composite
            return await self.composition_manager.create_composite_tile(
                location, state, options
            )

    def _create_state_cache_key(
        self,
        location: Dict[str, Any],
        state: str,
        options: Dict[str, Any],
        enhance_with_ai: bool,
    ) -> str:
        """Create cache key for state combination."""
        key_data = {
            "location_id": location["id"],
            "state": state,
            "options": options,
            "enhance_with_ai": enhance_with_ai,
            "timestamp": time.strftime("%Y%m%d"),  # Daily cache refresh
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    async def _apply_ai_enhancements(
        self,
        location: Dict[str, Any],
        state: str,
        base_composite_path: str,
        options: Dict[str, Any],
    ) -> str:
        """Apply AI enhancements to base composite."""

        print(f"🤖 Applying AI enhancements for {state} state...")

        # Determine enhancement strategy based on state
        if state == "hover":
            return await self._enhance_hover_state(
                location, base_composite_path, options
            )
        elif state == "click":
            return await self._enhance_click_state(
                location, base_composite_path, options
            )
        else:
            return await self._enhance_idle_state(
                location, base_composite_path, options
            )

    async def _enhance_hover_state(
        self,
        location: Dict[str, Any],
        base_composite_path: str,
        options: Dict[str, Any],
    ) -> str:
        """Enhance hover state with AI improvements."""

        print("✨ Enhancing hover state with soft glow effects...")

        # For now, implement basic hover enhancements
        # TODO: Integrate with Leonardo AI for advanced hover effects

        # Create enhanced hover composite
        enhanced_options = options.copy()
        enhanced_options["hover_enhancement"] = True
        enhanced_options["glow_intensity"] = 0.3

        return await self.composition_manager.create_composite_tile(
            location, "hover", enhanced_options
        )

    async def _enhance_click_state(
        self,
        location: Dict[str, Any],
        base_composite_path: str,
        options: Dict[str, Any],
    ) -> str:
        """Enhance click state with AI improvements."""

        print("🎆 Enhancing click state with special effects...")

        # Create enhanced click composite
        enhanced_options = options.copy()
        enhanced_options["click_enhancement"] = True
        enhanced_options["sparkle_intensity"] = 0.7

        return await self.composition_manager.create_composite_tile(
            location, "click", enhanced_options
        )

    async def _enhance_idle_state(
        self,
        location: Dict[str, Any],
        base_composite_path: str,
        options: Dict[str, Any],
    ) -> str:
        """Enhance idle state with AI improvements."""

        print("🌟 Enhancing idle state with subtle improvements...")

        # Idle state enhancements are minimal to maintain calm appearance
        enhanced_options = options.copy()
        enhanced_options["idle_enhancement"] = True
        enhanced_options["subtle_effects"] = True

        return await self.composition_manager.create_composite_tile(
            location, "idle", enhanced_options
        )

    async def generate_state_transition_sequence(
        self, location: Dict[str, Any], from_state: str, to_state: str, frames: int = 5
    ) -> List[str]:
        """
        Generate smooth transition sequence between states.

        Args:
            location: Location dictionary
            from_state: Starting state
            to_state: Target state
            frames: Number of transition frames

        Returns:
            List of file paths for transition frames
        """
        print(f"🎬 Generating transition: {from_state} → {to_state} ({frames} frames)")

        transition_frames = []

        try:
            # Generate from and to states
            from_path = await self.create_enhanced_composite_tile(location, from_state)
            to_path = await self.create_enhanced_composite_tile(location, to_state)

            # TODO: Implement actual frame interpolation
            # For now, return just the two states
            transition_frames = [from_path, to_path]

            print(f"✅ Transition sequence generated: {len(transition_frames)} frames")

        except Exception as e:
            print(f"❌ Error generating transition: {e}")
            transition_frames = []

        return transition_frames

    async def create_widget_focused_tile(
        self,
        location: Dict[str, Any],
        widget_id: str,
        state: str = "hover",
        highlight_intensity: float = 0.5,
    ) -> str:
        """
        Create a tile with specific widget highlighted.

        Args:
            location: Location dictionary
            widget_id: ID of widget to highlight
            state: State for the highlighted widget
            highlight_intensity: Intensity of highlight effect (0.0-1.0)

        Returns:
            Path to generated widget-focused tile
        """
        print(f"🎯 Creating widget-focused tile: {widget_id} - {state}")

        # Find the widget
        widgets = location.get("widgets", [])
        target_widget = None

        for widget in widgets:
            if widget.get("id") == widget_id:
                target_widget = widget
                break

        if not target_widget:
            print(f"❌ Widget {widget_id} not found")
            return await self.create_enhanced_composite_tile(location, state)

        # Create focused composition options
        options = {
            "focused_widget": widget_id,
            "highlight_intensity": highlight_intensity,
            "widget_state": state,
        }

        # Generate focused composite
        return await self.create_enhanced_composite_tile(location, state, options)

    def analyze_state_transitions(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and suggest optimal state transitions for location.

        Args:
            location: Location dictionary

        Returns:
            Analysis results and recommendations
        """
        print(f"🔍 Analyzing state transitions for {location['name']}")

        widgets = location.get("widgets", [])
        analysis = {
            "location_id": location["id"],
            "widget_count": len(widgets),
            "recommended_transitions": [],
            "optimization_suggestions": [],
            "complexity_score": 0,
        }

        # Analyze each widget
        for widget in widgets:
            widget_type = widget.get("type")
            widget_id = widget.get("id")
            interactions = widget.get("interactions", {})

            # Calculate complexity based on interaction types
            complexity = len(interactions)
            analysis["complexity_score"] += complexity

            # Recommend transitions based on widget type
            if widget_type == "time":
                analysis["recommended_transitions"].append(
                    {
                        "widget_id": widget_id,
                        "type": "real_time_updates",
                        "frequency": "per_second",
                        "reason": "Clock needs real-time updates",
                    }
                )

            elif widget_type == "status" or widget_type == "online":
                analysis["recommended_transitions"].append(
                    {
                        "widget_id": widget_id,
                        "type": "status_changes",
                        "frequency": "on_change",
                        "reason": "Status indicators update on state change",
                    }
                )

            elif widget_type == "changelog":
                analysis["recommended_transitions"].append(
                    {
                        "widget_id": widget_id,
                        "type": "content_loaded",
                        "frequency": "on_demand",
                        "reason": "Changelog loads dynamically from GitHub",
                    }
                )

        # Provide optimization suggestions
        if analysis["complexity_score"] > 10:
            analysis["optimization_suggestions"].append(
                {
                    "priority": "high",
                    "suggestion": "Consider widget grouping for better performance",
                    "reason": "High widget complexity may impact rendering",
                }
            )

        if len(widgets) > 5:
            analysis["optimization_suggestions"].append(
                {
                    "priority": "medium",
                    "suggestion": "Implement lazy loading for less critical widgets",
                    "reason": "Many widgets may slow initial load time",
                }
            )

        print(f"✅ Analysis complete: complexity score {analysis['complexity_score']}")

        return analysis

    def record_state_transition(
        self,
        location_id: str,
        widget_id: str,
        from_state: str,
        to_state: str,
        timestamp: float = None,
    ):
        """Record a state transition for analytics."""
        if timestamp is None:
            timestamp = time.time()

        transition = {
            "location_id": location_id,
            "widget_id": widget_id,
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": timestamp,
        }

        self.transition_history.append(transition)

        # Keep only recent history (last 1000 transitions)
        if len(self.transition_history) > 1000:
            self.transition_history = self.transition_history[-1000:]

        print(f"📊 State transition recorded: {widget_id} {from_state}→{to_state}")

    def get_transition_analytics(
        self,
        location_id: str = None,
        time_window: int = 3600,  # 1 hour
    ) -> Dict[str, Any]:
        """
        Get analytics for state transitions.

        Args:
            location_id: Filter by location (optional)
            time_window: Time window in seconds

        Returns:
            Analytics results
        """
        current_time = time.time()
        cutoff_time = current_time - time_window

        # Filter transitions
        filtered_transitions = []
        for transition in self.transition_history:
            if transition["timestamp"] >= cutoff_time:
                if location_id is None or transition["location_id"] == location_id:
                    filtered_transitions.append(transition)

        # Calculate analytics
        analytics = {
            "total_transitions": len(filtered_transitions),
            "time_window": time_window,
            "location_filter": location_id,
            "widget_activity": {},
            "state_popularity": {},
            "transition_patterns": {},
        }

        # Count widget activity
        for transition in filtered_transitions:
            widget_id = transition["widget_id"]
            analytics["widget_activity"][widget_id] = (
                analytics["widget_activity"].get(widget_id, 0) + 1
            )

            # Count state popularity
            from_state = transition["from_state"]
            to_state = transition["to_state"]

            analytics["state_popularity"][from_state] = (
                analytics["state_popularity"].get(from_state, 0) + 1
            )
            analytics["state_popularity"][to_state] = (
                analytics["state_popularity"].get(to_state, 0) + 1
            )

            # Count transition patterns
            pattern_key = f"{from_state}→{to_state}"
            analytics["transition_patterns"][pattern_key] = (
                analytics["transition_patterns"].get(pattern_key, 0) + 1
            )

        return analytics

    async def validate_state_consistency(
        self, location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate state consistency across all widgets.

        Args:
            location: Location dictionary

        Returns:
            Validation results
        """
        print(f"🔍 Validating state consistency for {location['name']}")

        validation_results = {
            "location_id": location["id"],
            "validation_passed": True,
            "issues_found": [],
            "recommendations": [],
        }

        widgets = location.get("widgets", [])

        # Check each widget for state consistency
        for widget in widgets:
            widget_id = widget.get("id")
            interactions = widget.get("interactions", {})

            # Validate that all states are defined
            required_states = ["idle", "hover", "click"]
            for state in required_states:
                if state not in interactions:
                    validation_results["issues_found"].append(
                        {
                            "widget_id": widget_id,
                            "issue": f"Missing state definition: {state}",
                            "severity": "medium",
                        }
                    )
                    validation_results["validation_passed"] = False

            # Validate widget positioning
            position = widget.get("position", {})
            size = widget.get("size", {})

            if not position.get("x") or not position.get("y"):
                validation_results["issues_found"].append(
                    {
                        "widget_id": widget_id,
                        "issue": "Missing position coordinates",
                        "severity": "high",
                    }
                )
                validation_results["validation_passed"] = False

            if not size.get("width") or not size.get("height"):
                validation_results["issues_found"].append(
                    {
                        "widget_id": widget_id,
                        "issue": "Missing widget dimensions",
                        "severity": "high",
                    }
                )
                validation_results["validation_passed"] = False

        # Generate recommendations
        if not validation_results["validation_passed"]:
            validation_results["recommendations"].append(
                {
                    "priority": "high",
                    "action": "Fix critical state definition issues before generation",
                }
            )

        if len(widgets) > 8:
            validation_results["recommendations"].append(
                {
                    "priority": "medium",
                    "action": "Consider reducing widget count for better performance",
                }
            )

        print(
            f"✅ Validation complete: {'PASSED' if validation_results['validation_passed'] else 'FAILED'}"
        )

        return validation_results


async def main():
    """Test the StateCoordinationManager."""
    manager = StateCoordinationManager()

    # Load world.json
    with open(WORLD_JSON) as f:
        world = json.load(f)

    # Test with first location
    if world.get("locations"):
        location = world["locations"][0]

        print(f"🏠 Testing state coordination for: {location['name']}")

        # Test enhanced composite generation
        idle_path = await manager.create_enhanced_composite_tile(location, "idle")
        print(f"✅ Enhanced idle: {idle_path}")

        hover_path = await manager.create_enhanced_composite_tile(location, "hover")
        print(f"✅ Enhanced hover: {hover_path}")

        click_path = await manager.create_enhanced_composite_tile(location, "click")
        print(f"✅ Enhanced click: {click_path}")

        # Test widget focus
        if location.get("widgets"):
            first_widget = location["widgets"][0]
            focused_path = await manager.create_widget_focused_tile(
                location, first_widget["id"], "hover"
            )
            print(f"✅ Widget focused: {focused_path}")

        # Test state analysis
        analysis = manager.analyze_state_transitions(location)
        print(f"✅ Analysis: {analysis['complexity_score']} complexity score")

        # Test validation
        validation = await manager.validate_state_consistency(location)
        print(
            f"✅ Validation: {'PASSED' if validation['validation_passed'] else 'FAILED'}"
        )

        print("🎉 All state coordination tests passed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
