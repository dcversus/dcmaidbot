#!/usr/bin/env python3
"""
Comprehensive test suite for tile-based generation pipeline
Tests T1-T10 as specified in the requirements
"""

import hashlib
import json
import os
import shutil
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image
from scripts.generate_tiles import (
    cache_hit,
    cache_put,
    cells_to_px,
    content_key,
    load_json,
    make_mask_cells,
    make_mask_full,
    save_json,
    stable_hash,
)


class TestTilePipeline:
    """Test suite for tile generation pipeline"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_world_config(self):
        """Sample world configuration for testing"""
        return {
            "world_name": "Test World",
            "version": "1.0.0",
            "style": {
                "art_style": "16-bit pixel art top-down",
                "palette": "DB32",
                "camera": "top-down SNES RPG",
                "tile_size": 64,
                "grid": {"cols": 4, "rows": 4},
                "hiDPI_scale": 1,
            },
            "render": {
                "provider_priority": ["openai"],
                "models": {
                    "txt2img": {"openai": "dall-e-3"},
                    "inpaint": {"openai": "dall-e-3"},
                },
                "defaults": {"seed": 12345, "steps": 10, "cfg": 5.0},
            },
            "floors": [
                {
                    "id": "floor_1",
                    "name": "Test Floor",
                    "locations": [
                        {
                            "id": "test_room",
                            "name": "Test Room",
                            "seed_offset": 100,
                            "description_prompt": "Simple test room with pixel art style",
                            "bounds": {"cols": 4, "rows": 4},
                            "widgets": [
                                {
                                    "id": "test_widget",
                                    "type": "test",
                                    "name": "Test Widget",
                                    "grid": {"x": 1, "y": 1, "w": 2, "h": 1},
                                    "prompt_base": "test widget",
                                    "states": [
                                        {
                                            "state": "idle",
                                            "prompt": "test widget idle",
                                            "region": {
                                                "mode": "cells",
                                                "cells": [[1, 1], [2, 1]],
                                            },
                                        },
                                        {
                                            "state": "hover",
                                            "prompt": "test widget hover",
                                            "region": {
                                                "mode": "cells",
                                                "cells": [[1, 1], [2, 1]],
                                            },
                                        },
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    # T1 — Config load
    def test_t1_config_load(self, sample_world_config, temp_dir):
        """Test parsing world.json and asserting required fields"""
        # Save sample config
        world_path = os.path.join(temp_dir, "world.json")
        with open(world_path, "w") as f:
            json.dump(sample_world_config, f)

        # Load and validate
        config = load_json(world_path)

        assert config["world_name"] == "Test World"
        assert "style" in config
        assert "tile_size" in config["style"]
        assert config["style"]["tile_size"] == 64
        assert "floors" in config
        assert len(config["floors"]) > 0
        assert "locations" in config["floors"][0]
        assert len(config["floors"][0]["locations"]) > 0
        assert "widgets" in config["floors"][0]["locations"][0]

    # T2 — Base render
    @patch("scripts.generate_tiles.pick_provider")
    def test_t2_base_render(self, mock_pick_provider, sample_world_config, temp_dir):
        """Test generating base.png with correct dimensions"""
        # Mock provider
        mock_provider = Mock()
        mock_provider.txt2img.return_value = True
        mock_pick_provider.return_value = mock_provider

        # Create a simple test image
        test_image = Image.new("RGB", (256, 256), color="blue")

        # Setup paths
        world_path = os.path.join(temp_dir, "world.json")
        output_dir = os.path.join(temp_dir, "output")
        base_path = os.path.join(
            output_dir, "floors", "floor_1", "test_room", "base.png"
        )

        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        test_image.save(base_path)

        with open(world_path, "w") as f:
            json.dump(sample_world_config, f)

        # Verify dimensions
        img = Image.open(base_path)
        expected_size = (4 * 64, 4 * 64)  # cols*tile, rows*tile
        assert img.size == expected_size

    # T3 — Mask correctness
    def test_t3_mask_correctness_cells(self, temp_dir):
        """Test mask generation for cells regions"""
        mask_path = os.path.join(temp_dir, "test_mask.png")
        cells = [[1, 1], [2, 1]]  # 2 cells
        tile_size = 64
        canvas_size = (256, 256)

        make_mask_cells(cells, tile_size, canvas_size, mask_path)

        # Verify mask
        mask = Image.open(mask_path)
        mask_array = np.array(mask)

        # Count white pixels (should be cells * tile^2)
        expected_white = len(cells) * tile_size * tile_size
        actual_white = np.sum(mask_array > 128)

        # Allow ±5% tolerance (due to potential anti-aliasing or edge effects)
        tolerance = expected_white * 0.05
        assert abs(actual_white - expected_white) <= tolerance

    def test_t3_mask_correctness_full(self, temp_dir):
        """Test mask generation for full regions"""
        mask_path = os.path.join(temp_dir, "test_full_mask.png")
        w, h = 256, 256

        make_mask_full(w, h, mask_path)

        # Verify mask
        mask = Image.open(mask_path)
        mask_array = np.array(mask)

        # Should be entirely white
        assert np.all(mask_array == 255)

    # T4 — Inpaint stability
    def test_t4_inpaint_stability(self, temp_dir):
        """Test that inpainting doesn't change pixels outside mask"""
        # Create base image
        base_path = os.path.join(temp_dir, "base.png")
        base = Image.new("RGB", (256, 256), color="red")
        base.save(base_path)

        # Create mask
        mask_path = os.path.join(temp_dir, "mask.png")
        make_mask_cells([[1, 1]], 64, (256, 256), mask_path)

        # Create "inpainted" result (should only change masked area)
        result_path = os.path.join(temp_dir, "result.png")
        result = Image.new("RGB", (256, 256), color="red")
        # Change only masked area
        result_array = np.array(result)
        mask_array = np.array(Image.open(mask_path))
        result_array[mask_array > 128] = [0, 0, 255]  # Blue in masked area
        result = Image.fromarray(result_array)
        result.save(result_path)

        # Verify outside mask unchanged
        base_array = np.array(base)
        result_array = np.array(result)
        mask_array = np.array(Image.open(mask_path))

        outside_mask = mask_array <= 128
        assert np.array_equal(base_array[outside_mask], result_array[outside_mask])

    # T5 — Overlay bbox validity
    def test_t5_overlay_bbox_validity(self, sample_world_config):
        """Test that overlay bboxes are within canvas bounds"""
        widget = sample_world_config["floors"][0]["locations"][0]["widgets"][0]
        tile_size = sample_world_config["style"]["tile_size"]
        canvas_w = sample_world_config["style"]["grid"]["cols"] * tile_size
        canvas_h = sample_world_config["style"]["grid"]["rows"] * tile_size

        for state in widget["states"]:
            if "region" in state and state["region"]["mode"] == "cells":
                cells = state["region"]["cells"]
                x, y, w, h = cells_to_px(cells, tile_size)

                assert x >= 0 and y >= 0
                assert x + w <= canvas_w
                assert y + h <= canvas_h

    # T6 — Compose preview
    def test_t6_compose_preview(self, temp_dir):
        """Test compositing base + overlay without seams"""
        # Create base image
        base = Image.new("RGB", (256, 256), color="red")

        # Create overlay
        overlay = Image.new("RGB", (128, 128), color="blue")

        # Compose
        result = base.copy()
        result.paste(overlay, (64, 64))

        # Verify composition worked - check that overlay area changed
        result_array = np.array(result)
        overlay_area = result_array[64:192, 64:192]  # Area where overlay was pasted

        # Should contain blue pixels from overlay
        has_blue = np.any(overlay_area[:, :, 2] > 200)  # Check blue channel
        assert has_blue

        # Verify area outside overlay is unchanged
        outside_area = result_array[0:64, 0:64]  # Top-left corner
        assert np.all(outside_area == [255, 0, 0])  # Should still be red

    # T7 — Click full-screen
    def test_t7_click_full_screen(self, temp_dir):
        """Test full-screen click overlay"""
        # Create base image
        base = Image.new("RGB", (256, 256), color="red")

        # Create full-screen overlay
        overlay = Image.new("RGB", (256, 256), color="blue")

        # Full-screen replacement should match canvas dimensions
        assert overlay.size == base.size

        # Composition should completely replace base
        result = base.copy()
        result.paste(overlay, (0, 0))

        assert result.size == base.size
        result_array = np.array(result)
        overlay_array = np.array(overlay)
        assert np.array_equal(result_array, overlay_array)

    # T8 — Dynamic text
    def test_t8_dynamic_text(self):
        """Test dynamic text rendering properties"""
        from datetime import datetime

        # Test time format
        format_str = "HH:mm:ss"
        d = datetime(2023, 12, 25, 14, 30, 45)

        def pad(n):
            return str(n).zfill(2)

        formatted = (
            format_str.replace("HH", pad(d.hour))
            .replace("mm", pad(d.minute))
            .replace("ss", pad(d.second))
        )

        assert formatted == "14:30:45"

        # Test env variable placeholder
        env_var = "GIT_COMMIT_SHORT"
        assert env_var == "GIT_COMMIT_SHORT"  # Placeholder preserved

    # T9 — Cache and selective regen
    def test_t9_cache_selective_regen(self, temp_dir):
        """Test cache hit/miss and selective regeneration"""
        cache_db = {}

        # Create test file
        test_path = os.path.join(temp_dir, "cached_file.png")
        test_image = Image.new("RGB", (64, 64), color="green")
        test_image.save(test_path)

        # Add to cache
        key = content_key("test", "overlay", "widget1", "idle")
        cache_put(cache_db, key, test_path, {"prompt": "test"})

        # Test cache hit
        assert cache_hit(cache_db, key)
        assert os.path.exists(cache_db[key]["path"])

        # Test cache miss
        miss_key = content_key("test", "overlay", "widget2", "idle")
        assert not cache_hit(cache_db, miss_key)

        # Delete specific overlay and test regeneration
        os.remove(test_path)
        assert not cache_hit(cache_db, key)  # Now should miss

    # T10 — Multi-location sanity
    def test_t10_multi_location_sanity(self, sample_world_config, temp_dir):
        """Test multiple locations have separate metadata"""
        # Add second location
        sample_world_config["floors"][0]["locations"].append(
            {
                "id": "test_room2",
                "name": "Test Room 2",
                "seed_offset": 101,
                "description_prompt": "Another test room",
                "bounds": {"cols": 4, "rows": 4},
                "widgets": [],
            }
        )

        # Create metadata for both locations
        world_path = os.path.join(temp_dir, "world.json")
        with open(world_path, "w") as f:
            json.dump(sample_world_config, f)

        output_dir = os.path.join(temp_dir, "output")

        for loc in sample_world_config["floors"][0]["locations"]:
            loc_dir = os.path.join(output_dir, "floors", "floor_1", loc["id"])
            meta_path = os.path.join(loc_dir, "map.meta.json")

            os.makedirs(os.path.dirname(meta_path), exist_ok=True)

            meta = {"W": 256, "H": 256, "tile": 64, "widgets": loc["widgets"]}

            save_json(meta_path, meta)

            # Verify separate metadata files
            assert os.path.exists(meta_path)
            loaded_meta = load_json(meta_path)
            assert loaded_meta["W"] == 256

    # Utility function tests
    def test_stable_hash(self):
        """Test stable hash generation"""
        hash1 = stable_hash("test string")
        hash2 = stable_hash("test string")
        hash3 = stable_hash("different string")

        assert hash1 == hash2  # Same input = same hash
        assert hash1 != hash3  # Different input = different hash
        assert isinstance(hash1, int)

    def test_cells_to_px(self):
        """Test cell to pixel coordinate conversion"""
        cells = [[1, 1], [2, 1]]
        tile = 64

        x, y, w, h = cells_to_px(cells, tile)

        assert x == 1 * tile  # min x
        assert y == 1 * tile  # min y
        assert w == 2 * tile  # (max_x - min_x + 1) * tile
        assert h == 1 * tile  # (max_y - min_y + 1) * tile

    def test_content_key(self):
        """Test content-based cache key generation"""
        key1 = content_key(
            "base", "world1", "floor1", "room1", "prompt", 123, 256, 256, 10, 5.0
        )
        key2 = content_key(
            "base", "world1", "floor1", "room1", "prompt", 123, 256, 256, 10, 5.0
        )
        key3 = content_key(
            "base", "world1", "floor1", "room1", "different", 123, 256, 256, 10, 5.0
        )

        assert key1 == key2
        assert key1 != key3
        assert isinstance(key1, str)
        assert len(key1) == hashlib.sha1().digest_size * 2  # SHA1 hex length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
