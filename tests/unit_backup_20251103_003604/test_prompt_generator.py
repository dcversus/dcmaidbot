"""
Unit tests for prompt_generator module
Tests Animal Crossing style prompt construction with world constraints
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from prompt_generator import (
    PromptGenerator,
    analyze_scene_context,
    calculate_area_position,
)


class TestPromptGenerator:
    """Test prompt generation with world constraints"""

    def setup_method(self):
        """Setup test instances"""
        self.prompt_gen = PromptGenerator()

    def test_load_world_config(self):
        """Test loading world configuration"""
        assert self.prompt_gen.config is not None
        assert "style" in self.prompt_gen.config
        assert "world_base_prompt" in self.prompt_gen.style_config

    def test_construct_base_prompt(self):
        """Test construction of base scene prompt"""
        location_desc = "cozy bedroom with PC and desk"
        prompt = self.prompt_gen.construct_base_prompt(location_desc)

        assert "Animal Crossing" in prompt
        assert "ORTHOGRAPHIC" in prompt.upper()
        assert "cozy bedroom" in prompt
        assert "DB32 palette" in prompt

    def test_construct_connection_prompt(self):
        """Test construction of connection prompt"""
        prompt = self.prompt_gen.construct_connection_prompt("3", "Parents Room", 1)

        assert "we are at 3 floor" in prompt
        assert "Parents Room" in prompt
        assert "1 floor(s) below" in prompt

    def test_construct_widget_prompt(self):
        """Test construction of widget prompt"""
        base_prompt = "cozy bedroom"
        widget_desc = "digital clock on desk"
        context = {"surface_type": "wooden desk", "lighting": "warm lamp light"}

        prompt = self.prompt_gen.construct_widget_prompt(
            base_prompt, widget_desc, context
        )

        assert "digital clock" in prompt
        assert "wooden desk" in prompt
        assert "SEAMLESS INTEGRATION" in prompt

    def test_get_provider_priority(self):
        """Test provider priority retrieval"""
        providers = self.prompt_gen.get_provider_priority()
        assert isinstance(providers, list)
        assert len(providers) > 0
        assert "hf" in providers  # Should prioritize HF now

    def test_connection_inpainting_settings(self):
        """Test connection inpainting configuration"""
        assert self.prompt_gen.should_use_connection_inpainting()
        assert self.prompt_gen.should_match_floors()
        assert self.prompt_gen.should_use_gray_filter()


class TestSceneAnalysis:
    """Test scene context analysis"""

    def test_analyze_scene_context_lighting(self):
        """Test lighting level analysis"""
        import numpy as np

        # Test bright scene
        bright_scene = np.full((100, 100, 3), 220)  # High brightness
        result = analyze_scene_context(bright_scene)
        assert result["lighting"] == "brightly lit"

        # Test dim scene
        dim_scene = np.full((100, 100, 3), 100)  # Low brightness
        result = analyze_scene_context(dim_scene)
        assert result["lighting"] == "dimly lit"

    def test_analyze_scene_context_surface(self):
        """Test surface type analysis"""
        import numpy as np

        # Test high variance (detailed surface)
        detailed_scene = np.random.randint(0, 255, (100, 100, 3))
        result = analyze_scene_context(detailed_scene)
        assert "detailed" in result["surface"] or "textured" in result["surface"]

        # Test low variance (smooth surface)
        smooth_scene = np.full((100, 100, 3), 128)
        result = analyze_scene_context(smooth_scene)
        assert result["surface"] == "smooth surface"

    def test_analyze_scene_context_color_temperature(self):
        """Test color temperature analysis"""
        import numpy as np

        # Warm scene (more red)
        warm_scene = np.full((100, 100, 3), [200, 100, 100])
        result = analyze_scene_context(warm_scene)
        assert result["color_temp"] == "warm lighting"

        # Cool scene (more blue)
        cool_scene = np.full((100, 100, 3), [100, 100, 200])
        result = analyze_scene_context(cool_scene)
        assert result["color_temp"] == "cool lighting"


class TestAreaPositionCalculation:
    """Test area position calculations"""

    def test_top_left_anchor(self):
        """Test top-left anchor positioning"""
        area_config = {
            "x": 100,
            "y": 50,
            "width": 200,
            "height": 150,
            "anchor": "top-left",
        }
        canvas_size = (1280, 768)

        x, y, w, h = calculate_area_position(area_config, canvas_size)

        assert x == 100
        assert y == 50
        assert w == 200
        assert h == 150

    def test_center_anchor(self):
        """Test center anchor positioning"""
        area_config = {"width": 400, "height": 300, "anchor": "center"}
        canvas_size = (1280, 768)

        x, y, w, h = calculate_area_position(area_config, canvas_size)

        assert x == 440  # (1280 - 400) / 2
        assert y == 234  # (768 - 300) / 2
        assert w == 400
        assert h == 300

    def test_bottom_right_anchor(self):
        """Test bottom-right anchor positioning"""
        area_config = {
            "x": 20,
            "y": 30,
            "width": 200,
            "height": 150,
            "anchor": "bottom-right",
        }
        canvas_size = (1280, 768)

        x, y, w, h = calculate_area_position(area_config, canvas_size)

        assert x == 1060  # 1280 - 200 - 20
        assert y == 588  # 768 - 150 - 30
        assert w == 200
        assert h == 150

    def test_bounds_enforcement(self):
        """Test that areas are kept within canvas bounds"""
        # Area that would exceed canvas bounds
        area_config = {
            "x": 1200,
            "y": 700,
            "width": 200,
            "height": 200,
            "anchor": "top-left",
        }
        canvas_size = (1280, 768)

        x, y, w, h = calculate_area_position(area_config, canvas_size)

        assert x >= 0
        assert y >= 0
        assert x + w <= canvas_size[0]
        assert y + h <= canvas_size[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
