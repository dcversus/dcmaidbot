"""
Unit tests for inpaint_validator module
Tests pixel comparison and validation functionality
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

from inpaint_validator import InpaintValidator, validate_neighborhood_floors


class TestInpaintValidator:
    """Test InpaintValidator class functionality"""

    def setup_method(self):
        """Setup test instances"""
        self.validator = InpaintValidator(similarity_threshold=90.0)
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

    def test_validator_initialization(self):
        """Test validator initialization"""
        assert self.validator.similarity_threshold == 90.0

        validator_low = InpaintValidator(similarity_threshold=75.0)
        assert validator_low.similarity_threshold == 75.0

    def test_load_image_success(self):
        """Test successful image loading"""
        # Create test image
        test_array = np.full((50, 50, 3), 128, dtype=np.uint8)
        path = self.save_test_image(test_array, "test.png")

        # Load image
        loaded = self.validator.load_image(path)

        assert loaded.shape == (50, 50, 3)
        assert loaded.dtype == np.uint8
        assert np.mean(loaded) == 128

    def test_load_image_failure(self):
        """Test image loading failure"""
        with pytest.raises(Exception):
            self.validator.load_image("nonexistent.png")

    def test_calculate_pixel_similarity_identical(self):
        """Test similarity calculation with identical images"""
        img1 = np.full((30, 30, 3), [100, 150, 200], dtype=np.uint8)
        img2 = img1.copy()

        similarity = self.validator.calculate_pixel_similarity(img1, img2)
        assert similarity == 100.0

    def test_calculate_pixel_similarity_different(self):
        """Test similarity calculation with different images"""
        img1 = np.full((30, 30, 3), [100, 150, 200], dtype=np.uint8)
        img2 = np.full((30, 30, 3), [200, 100, 100], dtype=np.uint8)

        similarity = self.validator.calculate_pixel_similarity(img1, img2)
        assert similarity < 80.0  # Should be quite different

    def test_calculate_pixel_similarity_different_shapes(self):
        """Test similarity calculation with different image shapes"""
        img1 = np.full((30, 30, 3), [100, 150, 200], dtype=np.uint8)
        img2 = np.full((20, 40, 3), [100, 150, 200], dtype=np.uint8)

        similarity = self.validator.calculate_pixel_similarity(img1, img2)
        assert 0.0 <= similarity <= 100.0

    def test_extract_floor_border_regions(self):
        """Test floor border region extraction"""
        # Create test floor with different colored borders
        floor = np.full((100, 200, 3), [128, 128, 128], dtype=np.uint8)  # Gray center
        floor[:10, :] = [200, 100, 100]  # Red top border
        floor[-10:, :] = [100, 200, 100]  # Green bottom border
        floor[:, :10] = [100, 100, 200]  # Blue left border
        floor[:, -10:] = [200, 200, 100]  # Yellow right border

        borders = self.validator.extract_floor_border_region(floor, border_width=10)

        # Check all borders exist
        assert "top" in borders
        assert "bottom" in borders
        assert "left" in borders
        assert "right" in borders

        # Check border shapes
        assert borders["top"].shape == (10, 200, 3)
        assert borders["bottom"].shape == (10, 200, 3)
        assert borders["left"].shape == (100, 10, 3)
        assert borders["right"].shape == (100, 10, 3)

        # Check border colors (allowing for some variation due to overlap)
        assert np.mean(borders["top"][:, :, 0]) > 150  # Red channel high
        assert np.mean(borders["bottom"][:, :, 1]) > 150  # Green channel high

    def test_validate_floor_continuity_horizontal_pass(self):
        """Test floor continuity validation - horizontal connection (should pass)"""
        # Create two floors with matching edges
        floor1 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)
        floor2 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)

        # Add matching edges
        edge_pattern = np.array([100, 150, 100], dtype=np.uint8)
        floor1[:, -10:] = edge_pattern  # Right edge
        floor2[:, :10] = edge_pattern  # Left edge (should match)

        # Save images
        path1 = self.save_test_image(floor1, "floor1.png")
        path2 = self.save_test_image(floor2, "floor2.png")

        # Validate
        result = self.validator.validate_floor_continuity(path1, path2, "horizontal")

        assert result["passed"]
        assert result["similarity"] == 100.0
        assert result["connection_type"] == "horizontal"

    def test_validate_floor_continuity_horizontal_fail(self):
        """Test floor continuity validation - horizontal connection (should fail)"""
        # Create two floors with different edges
        floor1 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)
        floor2 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)

        # Add different edges
        floor1[:, -10:] = [200, 100, 100]  # Red edge
        floor2[:, :10] = [100, 100, 200]  # Blue edge (different)

        # Save images
        path1 = self.save_test_image(floor1, "floor1.png")
        path2 = self.save_test_image(floor2, "floor2.png")

        # Validate with high threshold
        validator_strict = InpaintValidator(similarity_threshold=95.0)
        result = validator_strict.validate_floor_continuity(path1, path2, "horizontal")

        assert not result["passed"]
        assert result["similarity"] < 95.0

    def test_validate_floor_continuity_vertical(self):
        """Test floor continuity validation - vertical connection"""
        # Create two floors with matching edges
        floor1 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)
        floor2 = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)

        # Add matching edges
        edge_pattern = np.array([100, 150, 100], dtype=np.uint8)
        floor1[-10:, :] = edge_pattern  # Bottom edge
        floor2[:10, :] = edge_pattern  # Top edge (should match)

        # Save images
        path1 = self.save_test_image(floor1, "floor1.png")
        path2 = self.save_test_image(floor2, "floor2.png")

        # Validate
        result = self.validator.validate_floor_continuity(path1, path2, "vertical")

        assert result["passed"]
        assert result["connection_type"] == "vertical"

    def test_validate_widget_integration(self):
        """Test widget integration validation"""
        # Create base scene
        base_scene = np.full((100, 100, 3), [160, 160, 160], dtype=np.uint8)

        # Create widget scene with integrated widget
        widget_scene = base_scene.copy()
        widget_scene[40:60, 40:60] = [100, 120, 200]  # Blue widget

        # Create widget mask
        widget_mask = np.zeros((100, 100), dtype=np.uint8)
        widget_mask[40:60, 40:60] = 255

        # Save images
        base_path = self.save_test_image(base_scene, "base.png")
        widget_path = self.save_test_image(widget_scene, "widget.png")
        mask_path = self.save_test_image(widget_mask, "mask.png")

        # Validate
        result = self.validator.validate_widget_integration(
            base_path, widget_path, mask_path
        )

        # Should pass because borders are similar (both gray)
        assert result["passed"]
        assert result["border_pixels_count"] > 0
        assert "similarity" in result

    def test_create_test_report(self):
        """Test validation report creation"""
        validations = [
            {"passed": True, "similarity": 95.0, "description": "Floor continuity"},
            {"passed": False, "similarity": 70.0, "description": "Widget integration"},
            {"passed": True, "similarity": 88.0, "description": "Another test"},
        ]

        report = self.validator.create_test_report(validations)

        assert "Inpainting Validation Report" in report
        assert "Total Tests: 3" in report
        assert "Passed: 2" in report
        assert "Failed: 1" in report
        assert "66.7%" in report

    def test_save_comparison_images(self):
        """Test saving comparison images"""
        # Create test images
        img1 = np.full((50, 50, 3), [255, 0, 0], dtype=np.uint8)  # Red
        img2 = np.full((50, 50, 3), [0, 255, 0], dtype=np.uint8)  # Green

        # Save comparison
        output_path = os.path.join(self.temp_dir, "comparison.png")
        self.validator.save_comparison_images(img1, img2, output_path, "Test")

        # Check file was created
        assert os.path.exists(output_path)

        # Load and check comparison
        comparison = Image.open(output_path)
        assert comparison.size == (100, 50)  # Side by side


class TestValidateNeighborhoodFloors:
    """Test neighborhood floor validation function"""

    def setup_method(self):
        """Setup test instances"""
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

    def test_validate_neighborhood_floors_success(self):
        """Test neighborhood floor validation with good continuity"""
        # Create three floors with good continuity
        floors = []
        for i in range(3):
            floor = np.full((100, 100, 3), [128 + i * 10, 128, 128], dtype=np.uint8)

            # Add matching edges for horizontal continuity
            edge_pattern = np.array([100, 150, 100], dtype=np.uint8)
            floor[:, -10:] = edge_pattern  # Right edge

            if i > 0:
                floor[:, :10] = (
                    edge_pattern  # Left edge (matches previous floor's right)
                )

            path = self.save_test_image(floor, f"floor_{i}.png")
            floors.append(path)

        # Validate
        output_dir = os.path.join(self.temp_dir, "validation")
        result = validate_neighborhood_floors(floors, output_dir)

        # Check results
        assert result["total_validations"] == 2  # 3 floors = 2 connections
        assert result["passed_validations"] == 2  # All should pass
        assert len(result["validations"]) == 2

        # Check report was created
        assert os.path.exists(
            os.path.join(output_dir, "neighborhood_validation_report.txt")
        )

    def test_validate_neighborhood_floors_mixed(self):
        """Test neighborhood floor validation with mixed results"""
        # Create floors with mixed continuity
        floors = []
        for i in range(3):
            floor = np.full((100, 100, 3), [128, 128, 128], dtype=np.uint8)

            if i == 0:
                # First floor - red edge
                floor[:, -10:] = [200, 100, 100]
            elif i == 1:
                # Second floor - different left edge, same right edge
                floor[:, :10] = [100, 100, 200]  # Different from previous
                floor[:, -10:] = [100, 200, 100]  # New edge
            else:
                # Third floor - matches previous
                floor[:, :10] = [100, 200, 100]  # Matches previous right edge

            path = self.save_test_image(floor, f"floor_{i}.png")
            floors.append(path)

        # Validate with lower threshold
        output_dir = os.path.join(self.temp_dir, "validation")
        result = validate_neighborhood_floors(floors, output_dir)

        # Check results
        assert result["total_validations"] == 2
        # Results depend on similarity threshold
        assert "passed_validations" in result
        assert "validations" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
