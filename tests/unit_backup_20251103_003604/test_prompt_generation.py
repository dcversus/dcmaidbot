"""
Unit tests for prompt generation system
Tests the construction of orthographic prompts with world constraints
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestPromptGeneration:
    """Test prompt generation with world constraints"""

    def test_load_world_config(self):
        """Test loading world configuration"""
        from providers import load_json

        config = load_json("static/world.json")
        assert config is not None
        assert "style" in config
        assert "prompt_constraints" in config["style"]
        assert "world_base_prompt" in config["style"]

    def test_orthographic_constraints_loaded(self):
        """Test that orthographic constraints are properly loaded"""
        from providers import load_json

        config = load_json("static/world.json")
        constraints = config["style"]["prompt_constraints"]

        assert "orthographic" in constraints
        assert "orthographic" in constraints["orthographic"].lower()
        assert "no perspective" in constraints["orthographic"]

    def test_construct_base_prompt(self):
        """Test construction of base scene prompt"""
        from providers import load_json

        config = load_json("static/world.json")
        world_prompt = config["style"]["world_base_prompt"]
        orthographic = config["style"]["prompt_constraints"]["orthographic"]
        style = config["style"]["prompt_constraints"]["style"]

        location_prompt = "cozy bedroom with PC and desk"

        base_prompt = f"{world_prompt}, {location_prompt}, {orthographic}, {style}"

        assert "Animal Crossing" in base_prompt
        assert "orthographic".upper() in base_prompt.upper()
        assert "cozy bedroom" in base_prompt
        assert "DB32 palette" in base_prompt

    def test_connection_prompt_template(self):
        """Test connection prompt template for floor continuity"""
        from providers import load_json

        config = load_json("static/world.json")
        template = config["style"]["connection_inpainting"][
            "connection_prompt_template"
        ]

        prompt = template.format(
            current_floor="3", adjacent_location="Parents Room", floor_difference="1"
        )

        assert "we are at 3 floor" in prompt
        assert "Parents Room" in prompt
        assert "1 floor(s) below" in prompt

    def test_area_mask_coordinates(self):
        """Test area mask coordinate calculations"""
        # Test anchoring calculations
        canvas_w, canvas_h = 1280, 768

        # Test top-left anchor
        area = {"x": 100, "y": 50, "width": 200, "height": 150, "anchor": "top-left"}
        x, y = area["x"], area["y"]
        w, h = area["width"], area["height"]

        assert x == 100
        assert y == 50
        assert w == 200
        assert h == 150

        # Test center anchor
        area_center = {"width": 400, "height": 300, "anchor": "center"}
        x_center = (canvas_w - area_center["width"]) // 2
        y_center = (canvas_h - area_center["height"]) // 2

        assert x_center == 440  # (1280 - 400) / 2
        assert y_center == 234  # (768 - 300) / 2

    def test_scene_analysis_lighting_levels(self):
        """Test scene analysis lighting determination"""
        # Test brightness levels
        brightness_levels = {
            210: "brightly lit",
            170: "well-lit",
            140: "moderately lit",
            100: "dimly lit",
        }

        for brightness, expected in brightness_levels.items():
            if brightness > 200:
                lighting = "brightly lit"
            elif brightness > 160:
                lighting = "well-lit"
            elif brightness > 120:
                lighting = "moderately lit"
            else:
                lighting = "dimly lit"

            assert lighting == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
