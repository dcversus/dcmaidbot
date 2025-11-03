"""
Unit tests for floor_continuity module
Tests neighborhood floor continuity inpainting functionality
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from floor_continuity import FloorContinuityManager


class TestFloorContinuityManager:
    """Test FloorContinuityManager class functionality"""

    def setup_method(self):
        """Setup test instances"""

        # Create mock prompt generator
        class MockPromptGenerator:
            def should_use_connection_inpainting(self):
                return True

            def should_use_gray_filter(self):
                return True

            def construct_connection_prompt(
                self, current_floor, adjacent_location, floor_difference
            ):
                return f"we are at {current_floor}, next to us is {adjacent_location} which is {floor_difference} floor(s) below"

        self.prompt_gen = MockPromptGenerator()
        self.manager = FloorContinuityManager(self.prompt_gen, tile_size=64)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test files"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def save_test_image(self, img_array: np.ndarray, filename: str) -> str:
        """Save test image and return path"""
        img = Image.fromarray(img_array)
        path = os.path.join(self.temp_dir, filename)
        img.save(path)
        return path

    def test_manager_initialization(self):
        """Test manager initialization"""
        assert self.manager.prompt_gen == self.prompt_gen
        assert self.manager.tile_size == 64

    def test_find_connected_locations_middle(self):
        """Test finding connected locations for middle location"""
        world_config = {
            "navigation": {
                "sequence": [
                    "house_main/house_f1_hall",
                    "house_main/house_f2_parents",
                    "house_main/house_f3_lilith",
                ]
            }
        }

        connected = self.manager.find_connected_locations(
            world_config, "house_main/house_f2_parents"
        )

        assert len(connected) == 2
        assert connected[0]["location_id"] == "house_main/house_f1_hall"
        assert connected[0]["direction"] == "left"
        assert connected[1]["location_id"] == "house_main/house_f3_lilith"
        assert connected[1]["direction"] == "right"

    def test_find_connected_locations_first(self):
        """Test finding connected locations for first location"""
        world_config = {
            "navigation": {
                "sequence": ["house_main/house_f1_hall", "house_main/house_f2_parents"]
            }
        }

        connected = self.manager.find_connected_locations(
            world_config, "house_main/house_f1_hall"
        )

        assert len(connected) == 1
        assert connected[0]["location_id"] == "house_main/house_f2_parents"
        assert connected[0]["direction"] == "right"

    def test_find_connected_locations_last(self):
        """Test finding connected locations for last location"""
        world_config = {
            "navigation": {
                "sequence": ["house_main/house_f1_hall", "house_main/house_f2_parents"]
            }
        }

        connected = self.manager.find_connected_locations(
            world_config, "house_main/house_f2_parents"
        )

        assert len(connected) == 1
        assert connected[0]["location_id"] == "house_main/house_f1_hall"
        assert connected[0]["direction"] == "left"

    def test_calculate_floor_difference(self):
        """Test floor difference calculation"""
        loc1 = {"id": "house_main/house_f1_hall"}
        loc2 = {"id": "house_main/house_f3_lilith"}
        loc3 = {"id": "house_main/house_f2_parents"}

        # Higher floor
        diff1 = self.manager.calculate_floor_difference(loc1, loc2)
        assert diff1 == 2  # F3 - F1 = 2

        # Lower floor
        diff2 = self.manager.calculate_floor_difference(loc2, loc1)
        assert diff2 == -2  # F1 - F3 = -2

        # Same floor
        diff3 = self.manager.calculate_floor_difference(loc2, loc3)
        assert diff3 == -1  # F2 - F2 = -1

    def test_create_connection_mask_left(self):
        """Test creating connection mask for left edge"""
        # Create test image
        test_img = np.full((100, 200, 3), 128, dtype=np.uint8)
        path = self.save_test_image(test_img, "test.png")

        mask = self.manager.create_connection_mask(path, "left", mask_width=20)

        assert mask.shape == (100, 200)
        assert mask.dtype == np.uint8

        # Check left edge is white (255)
        assert np.all(mask[:, :20] == 255)
        # Check right area is black (0)
        assert np.all(mask[:, 20:] == 0)

    def test_create_connection_mask_right(self):
        """Test creating connection mask for right edge"""
        # Create test image
        test_img = np.full((100, 200, 3), 128, dtype=np.uint8)
        path = self.save_test_image(test_img, "test.png")

        mask = self.manager.create_connection_mask(path, "right", mask_width=15)

        assert mask.shape == (100, 200)

        # Check right edge is white (255)
        assert np.all(mask[:, -15:] == 255)
        # Check left area is black (0)
        assert np.all(mask[:, :-15] == 0)

    def test_create_connection_mask_top_bottom(self):
        """Test creating connection mask for top and bottom edges"""
        # Create test image
        test_img = np.full((100, 200, 3), 128, dtype=np.uint8)
        path = self.save_test_image(test_img, "test.png")

        # Test top mask
        top_mask = self.manager.create_connection_mask(path, "top", mask_width=10)
        assert np.all(top_mask[:10, :] == 255)

        # Test bottom mask
        bottom_mask = self.manager.create_connection_mask(path, "bottom", mask_width=10)
        assert np.all(bottom_mask[-10:, :] == 255)

    def test_create_continuity_prompt(self):
        """Test continuity prompt creation"""
        loc1 = {
            "id": "house_main/house_f2_parents",
            "description_prompt": "cozy parents room",
        }
        loc2 = {"id": "house_main/house_f1_hall", "description_prompt": "entrance hall"}

        prompt = self.manager.create_continuity_prompt(
            base_location_info=loc1,
            connected_location_info=loc2,
            floor_difference=1,
            direction="left",
        )

        assert "we are at house_main/house_f2_parents" in prompt
        assert "next to us is unknown location which is 1 floor(s) below" in prompt
        assert "1 floor(s) below" in prompt
        assert "seamlessly continue from left edge" in prompt

    def test_apply_gray_filter_positive_difference(self):
        """Test gray filter application for positive floor difference"""
        # Create color image
        color_img = np.array(
            [
                [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                [[100, 200, 150], [50, 100, 200], [200, 50, 100]],
            ],
            dtype=np.uint8,
        )

        filtered = self.manager.apply_gray_filter_if_needed(color_img.copy(), 1)

        # Should be grayscaled
        assert filtered.shape == color_img.shape
        # Red channel should be reduced
        assert filtered[0, 0, 0] < color_img[0, 0, 0]
        # Should still be different from original
        assert not np.array_equal(filtered, color_img)

    def test_apply_gray_filter_zero_difference(self):
        """Test gray filter not applied for zero floor difference"""
        # Create color image
        color_img = np.array(
            [[[255, 0, 0], [0, 255, 0]], [[100, 200, 150], [50, 100, 200]]],
            dtype=np.uint8,
        )

        filtered = self.manager.apply_gray_filter_if_needed(color_img.copy(), 0)

        # Should be unchanged
        assert np.array_equal(filtered, color_img)

    def test_apply_gray_filter_negative_difference(self):
        """Test gray filter not applied for negative floor difference"""
        # Create color image
        color_img = np.array(
            [[[255, 0, 0], [0, 255, 0]], [[100, 200, 150], [50, 100, 200]]],
            dtype=np.uint8,
        )

        filtered = self.manager.apply_gray_filter_if_needed(color_img.copy(), -1)

        # Should be unchanged
        assert np.array_equal(filtered, color_img)


class TestFloorContinuityIntegration:
    """Test floor continuity integration functionality"""

    def setup_method(self):
        """Setup test instances"""

        # Create mock prompt generator
        class MockPromptGenerator:
            def should_use_connection_inpainting(self):
                return True

            def should_use_gray_filter(self):
                return True

            def construct_connection_prompt(
                self, current_floor, adjacent_location, floor_difference
            ):
                return f"continuity prompt: {current_floor} to {adjacent_location}"

            def get_provider_priority(self):
                return ["mock"]

        self.prompt_gen = MockPromptGenerator()
        self.manager = FloorContinuityManager(self.prompt_gen, tile_size=64)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test files"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def save_test_image(self, img_array: np.ndarray, filename: str) -> str:
        """Save test image and return path"""
        img = Image.fromarray(img_array)
        path = os.path.join(self.temp_dir, filename)
        img.save(path)
        return path

    def test_process_location_connections_disabled(self):
        """Test processing connections when disabled"""

        # Create prompt generator that returns False
        class DisabledPromptGen:
            def should_use_connection_inpainting(self):
                return False

        manager = FloorContinuityManager(DisabledPromptGen())

        world_config = {"navigation": {"sequence": ["loc1", "loc2"]}}
        location_info = {"id": "loc1"}
        base_path = self.save_test_image(
            np.zeros((100, 100, 3), dtype=np.uint8), "base.png"
        )

        results = manager.process_location_connections(
            world_config=world_config,
            location_info=location_info,
            base_path=base_path,
            provider_priority=["mock"],
        )

        assert results == []

    def test_process_location_connections_no_connected_locations(self):
        """Test processing when no connected locations found"""
        world_config = {"navigation": {"sequence": []}}  # Empty sequence
        location_info = {"id": "isolated_loc"}
        base_path = self.save_test_image(
            np.zeros((100, 100, 3), dtype=np.uint8), "base.png"
        )

        results = self.manager.process_location_connections(
            world_config=world_config,
            location_info=location_info,
            base_path=base_path,
            provider_priority=["mock"],
        )

        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
