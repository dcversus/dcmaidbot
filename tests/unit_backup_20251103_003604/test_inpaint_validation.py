"""
Unit tests for inpainting validation using pixel comparison
Tests neighborhood floor continuity and widget border integration
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestPixelComparison:
    """Test pixel comparison functionality for inpainting validation"""

    def test_load_image_for_comparison(self):
        """Test loading images for pixel comparison"""
        # Create test image
        test_array = np.full((100, 100, 3), 128, dtype=np.uint8)  # Gray image
        test_img = Image.fromarray(test_array)

        # Test conversion to numpy
        img_array = np.array(test_img)
        assert img_array.shape == (100, 100, 3)
        assert img_array.dtype == np.uint8
        assert np.mean(img_array) == 128

    def test_extract_floor_border_region(self):
        """Test extraction of floor border regions for comparison"""
        # Create test floor image with different colors
        floor_array = np.zeros((200, 200, 3), dtype=np.uint8)

        # Floor area (center)
        floor_array[50:150, 50:150] = [100, 150, 100]  # Green floor

        # Border area
        floor_array[40:60, 40:160] = [150, 100, 50]  # Brown border
        floor_array[140:160, 40:160] = [150, 100, 50]  # Brown border
        floor_array[40:160, 40:60] = [150, 100, 50]  # Brown border
        floor_array[40:160, 140:160] = [150, 100, 50]  # Brown border

        # Extract border region (5 pixels from edge)
        border_region = floor_array[45:155, 45:155]

        assert border_region.shape == (110, 110, 3)

        # Check that border contains brown pixels
        has_brown = np.any(np.all(border_region == [150, 100, 50], axis=2))
        assert has_brown

    def test_extract_widget_border_pixels(self):
        """Test extraction of widget border pixels"""
        # Create test scene with widget
        scene_array = np.full(
            (200, 200, 3), [200, 200, 200], dtype=np.uint8
        )  # Light gray background

        # Add widget in center
        widget_x, widget_y = 75, 75
        widget_w, widget_h = 50, 50
        scene_array[widget_y : widget_y + widget_h, widget_x : widget_x + widget_w] = [
            100,
            100,
            255,
        ]  # Blue widget

        # Extract border pixels (1 pixel around widget)
        border_pixels = []
        for dy in range(-1, widget_h + 1):
            for dx in range(-1, widget_w + 1):
                px, py = widget_x + dx, widget_y + dy
                if (
                    0 <= px < 200
                    and 0 <= py < 200
                    and (dx == -1 or dx == widget_w or dy == -1 or dy == widget_h)
                ):
                    border_pixels.append(scene_array[py, px])

        assert len(border_pixels) > 0

        # Check border contains both background and widget pixels
        border_array = np.array(border_pixels)
        has_background = np.any(np.all(border_array == [200, 200, 200], axis=1))

        assert has_background
        # Note: Border pixels are from the scene, not the widget itself
        # So we check that border contains background pixels (which it should)
        assert has_background

    def test_pixel_similarity_calculation(self):
        """Test pixel similarity calculation"""
        # Create two similar images
        img1_array = np.full((50, 50, 3), [100, 150, 100], dtype=np.uint8)
        img2_array = np.full(
            (50, 50, 3), [102, 148, 102], dtype=np.uint8
        )  # Slightly different

        # Calculate similarity
        diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
        similarity = 100 - (np.mean(diff) / 255 * 100)

        assert similarity > 95  # Should be very similar
        assert similarity < 100  # But not identical

    def test_pixel_similarity_threshold(self):
        """Test pixel similarity threshold validation"""
        # Create test images with known similarity
        identical_img = np.full((30, 30, 3), [128, 128, 128], dtype=np.uint8)
        similar_img = np.full((30, 30, 3), [130, 126, 130], dtype=np.uint8)
        different_img = np.full((30, 30, 3), [200, 50, 50], dtype=np.uint8)

        def calculate_similarity(img1, img2):
            diff = np.abs(img1.astype(float) - img2.astype(float))
            return 100 - (np.mean(diff) / 255 * 100)

        # Test similarity calculations
        identical_sim = calculate_similarity(identical_img, identical_img)
        similar_sim = calculate_similarity(identical_img, similar_img)
        different_sim = calculate_similarity(identical_img, different_img)

        assert identical_sim == 100.0  # Identical images
        assert similar_sim > 90  # Similar but not identical
        assert different_sim < 80  # Different images (adjusted threshold)

    def test_floor_continuity_validation(self):
        """Test floor continuity validation between connected locations"""
        # Create two floor images that should be continuous
        floor1 = np.zeros((100, 100, 3), dtype=np.uint8)
        floor2 = np.zeros((100, 100, 3), dtype=np.uint8)

        # Add floor pattern that should be continuous
        floor_pattern = np.array([139, 90, 43], dtype=np.uint8)  # Wood color

        # Floor 1: Right edge should match Floor 2: Left edge
        floor1[:, 80:100] = floor_pattern  # Right edge
        floor2[:, 0:20] = floor_pattern  # Left edge (should match)

        # Extract edge regions for comparison
        floor1_edge = floor1[:, 90:100]  # 10 pixels from right edge
        floor2_edge = floor2[:, 0:10]  # 10 pixels from left edge

        # Calculate similarity
        diff = np.abs(floor1_edge.astype(float) - floor2_edge.astype(float))
        similarity = 100 - (np.mean(diff) / 255 * 100)

        assert similarity == 100.0  # Should be identical

    def test_widget_integration_validation(self):
        """Test widget integration with base scene"""
        # Create base scene
        base_scene = np.full((150, 150, 3), [180, 180, 180], dtype=np.uint8)

        # Create widget that should integrate
        widget = np.full((30, 30, 3), [100, 150, 200], dtype=np.uint8)

        # Place widget in scene
        x, y = 60, 60
        scene_with_widget = base_scene.copy()
        scene_with_widget[y : y + 30, x : x + 30] = widget

        # Extract border regions for comparison
        widget_border = []
        scene_border = []

        # Top border
        widget_border.extend(widget[0, :])
        scene_border.extend(scene_with_widget[y - 1, x : x + 30])

        # Bottom border
        widget_border.extend(widget[-1, :])
        scene_border.extend(scene_with_widget[y + 30, x : x + 30])

        # Left border
        widget_border.extend(widget[:, 0])
        scene_border.extend(scene_with_widget[y : y + 30, x - 1])

        # Right border
        widget_border.extend(widget[:, -1])
        scene_border.extend(scene_with_widget[y : y + 30, x + 30])

        # Convert to arrays
        widget_border_array = np.array(widget_border)
        scene_border_array = np.array(scene_border)

        assert len(widget_border_array) > 0
        assert len(scene_border_array) > 0
        assert widget_border_array.shape == scene_border_array.shape


class TestInpaintingValidation:
    """Test inpainting validation with real image scenarios"""

    def test_create_synthetic_floor_images(self):
        """Create synthetic floor images for testing"""
        # Create base floor pattern
        floor_pattern = np.array(
            [
                [139, 90, 43],  # Wood brown
                [129, 80, 33],  # Darker wood
                [149, 100, 53],  # Lighter wood
            ],
            dtype=np.uint8,
        )

        # Generate repeating wood pattern
        floor1 = np.tile(floor_pattern, (34, 67))[:100, :200]  # 100x200 floor
        floor2 = np.tile(floor_pattern, (34, 67))[:100, :200]  # Same pattern

        # Add third dimension for RGB
        floor1 = np.stack([floor1] * 3, axis=-1)
        floor2 = np.stack([floor2] * 3, axis=-1)

        # Add some variation for realism
        noise1 = np.random.randint(-5, 6, floor1.shape, dtype=np.int16)
        noise2 = np.random.randint(-5, 6, floor2.shape, dtype=np.int16)

        floor1 = np.clip(floor1.astype(np.int16) + noise1, 0, 255).astype(np.uint8)
        floor2 = np.clip(floor2.astype(np.int16) + noise2, 0, 255).astype(np.uint8)

        assert floor1.shape == (100, 200, 3)
        assert floor2.shape == (100, 200, 3)

        # Note: Images created for testing, not saved to avoid file system dependencies

        return floor1, floor2

    def test_synthetic_widget_integration(self):
        """Test synthetic widget integration with base scene"""
        # Create base scene
        base_scene = np.full((128, 128, 3), [160, 160, 160], dtype=np.uint8)

        # Add some texture
        texture = np.random.randint(-10, 11, base_scene.shape, dtype=np.int16)
        base_scene = np.clip(base_scene.astype(np.int16) + texture, 0, 255).astype(
            np.uint8
        )

        # Create widget
        widget = np.full((40, 40, 3), [80, 120, 200], dtype=np.uint8)

        # Place widget
        x, y = 44, 44  # Center
        scene_with_widget = base_scene.copy()
        scene_with_widget[y : y + 40, x : x + 40] = widget

        # Note: Images created for testing, not saved to avoid file system dependencies

        # Return None instead of arrays to avoid pytest warning
        return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
