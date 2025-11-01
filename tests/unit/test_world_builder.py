"""Unit tests for World Builder deterministic pipeline."""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil

from scripts.world_builder import WorldBuilder


class TestWorldBuilder:
    """Test cases for World Builder functionality."""

    @pytest.fixture
    def test_config(self):
        """Test world configuration."""
        return {
            "world_name": "Test World",
            "version": "1.0.0",
            "style": {
                "art_style": "16-bit pixel art top-down",
                "palette": "DB32",
                "camera": "top-down SNES RPG",
                "tile_size": 64,
                "grid": {"cols": 20, "rows": 20}
            },
            "render": {
                "provider_priority": ["openai", "huggingface", "leonardo"],
                "defaults": {
                    "seed": 424242,
                    "steps": 30,
                    "cfg": 5.0
                }
            },
            "floors": [
                {
                    "id": "floor_1",
                    "name": "First Floor",
                    "seed_offset": 100,
                    "locations": [
                        {
                            "id": "test_room",
                            "name": "Test Room",
                            "seed_offset": 10,
                            "description_prompt": "A cozy test room with pixel art style",
                            "bounds": {"cols": 10, "rows": 10},
                            "widgets": [
                                {
                                    "id": "test_widget",
                                    "type": "test",
                                    "name": "Test Widget",
                                    "grid": {"x": 2, "y": 2, "w": 2, "h": 1},
                                    "prompt_base": "test widget base",
                                    "states": [
                                        {
                                            "state": "idle",
                                            "prompt": "test widget idle",
                                            "region": {"mode": "cells", "cells": [[2, 2], [3, 2]]}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    @pytest.fixture
    def world_builder(self, test_config, tmp_path):
        """Create WorldBuilder instance with test config."""
        config_path = tmp_path / "test_world.json"
        with open(config_path, 'w') as f:
            json.dump(test_config, f)

        return WorldBuilder(str(config_path))

    def test_world_builder_initialization(self, world_builder):
        """Test WorldBuilder initialization."""
        assert world_builder.config["world_name"] == "Test World"
        assert world_builder.config["style"]["tile_size"] == 64
        assert "cache_entries" in world_builder.cache_db
        assert world_builder.stats["generated_images"] == 0

    def test_cells_to_px_conversion(self, world_builder):
        """Test grid cell to pixel coordinate conversion."""
        cells = [[2, 2], [3, 2]]
        tile = 64
        x, y, w, h = world_builder._cells_to_px(cells, tile)

        assert x == 2 * 64  # 128
        assert y == 2 * 64  # 128
        assert w == 2 * 64  # 128 (2 cells wide)
        assert h == 1 * 64  # 64 (1 cell high)

    def test_make_mask_cells(self, world_builder, tmp_path):
        """Test mask generation for grid cells."""
        from PIL import Image

        cells = [[1, 1], [2, 1]]
        tile = 64
        canvas_size = (200, 200)
        mask_path = tmp_path / "test_mask.png"

        world_builder._make_mask_cells(cells, tile, canvas_size, str(mask_path))

        # Verify mask was created
        assert mask_path.exists()

        # Check mask properties
        mask = Image.open(mask_path)
        assert mask.size == canvas_size
        assert mask.mode == 'L'  # Grayscale

    def test_make_mask_full(self, world_builder, tmp_path):
        """Test full canvas mask generation."""
        from PIL import Image

        w, h = 200, 150
        mask_path = tmp_path / "full_mask.png"

        world_builder._make_mask_full(w, h, str(mask_path))

        # Verify mask was created
        assert mask_path.exists()

        # Check mask properties
        mask = Image.open(mask_path)
        assert mask.size == (w, h)
        assert mask.mode == 'L'  # Grayscale

    @pytest.mark.asyncio
    async def test_generate_base_scene_cached(self, world_builder):
        """Test base scene generation with cache hit."""
        floor = world_builder.config["floors"][0]
        location = floor["locations"][0]

        # Mock cache hit
        cache_key = "test_cache_key"
        world_builder.cache_db["cache_entries"][cache_key] = {
            "path": "static/cache/test_cached_image.png"
        }

        with patch('os.path.exists', return_value=True):
            with patch.object(world_builder, '_load_config') as mock_load:
                mock_load.return_value = world_builder.config

                # Mock the content_key function to return our test key
                with patch('scripts.world_builder.content_key', return_value=cache_key):
                    result = await world_builder._generate_base_scene(floor, location)

        assert world_builder.stats["cache_hits"] == 1
        assert result == "static/cache/test_cached_image.png"

    @pytest.mark.asyncio
    async def test_generate_base_scene_new_generation(self, world_builder):
        """Test base scene generation with new image creation."""
        floor = world_builder.config["floors"][0]
        location = floor["locations"][0]

        with patch('scripts.world_builder.pick_provider') as mock_pick_provider:
            mock_provider = AsyncMock()
            mock_provider.txt2img.return_value = "static/output/floors/floor_1/test_room/base.png"
            mock_provider.get_provider_name.return_value = "TestProvider"
            mock_pick_provider.return_value = mock_provider

            with patch('scripts.world_builder.ensure_dir'):
                result = await world_builder._generate_base_scene(floor, location)

        assert world_builder.stats["generated_images"] == 1
        assert result == "static/output/floors/floor_1/test_room/base.png"
        mock_provider.txt2img.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_widget_overlays(self, world_builder):
        """Test widget overlay generation."""
        floor = world_builder.config["floors"][0]
        location = floor["locations"][0]
        base_path = "test_base.png"

        with patch('scripts.world_builder.pick_provider') as mock_pick_provider:
            mock_provider = AsyncMock()
            mock_provider.txt2img.return_value = "test_overlay.png"
            mock_provider.get_provider_name.return_value = "TestProvider"
            mock_pick_provider.return_value = mock_provider

            with patch.object(world_builder, '_make_mask_cells'):
                with patch('scripts.world_builder.ensure_dir'):
                    result = await world_builder._generate_widget_overlays(floor, location, base_path)

        assert len(result) == 1
        assert result[0]["id"] == "test_widget"
        assert len(result[0]["states"]) == 1
        assert result[0]["states"][0]["state"] == "idle"

    def test_content_key_deterministic(self):
        """Test content key generation is deterministic."""
        from scripts.world_builder import content_key

        key1 = content_key("test", "input", 123)
        key2 = content_key("test", "input", 123)
        key3 = content_key("test", "different", 123)

        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 40  # SHA1 hex length

    def test_cache_operations(self):
        """Test cache database operations."""
        from scripts.world_builder import cache_hit, cache_put

        cache_db = {}

        # Test cache miss
        assert not cache_hit(cache_db, "nonexistent_key")

        # Test cache put and hit
        cache_put(cache_db, "test_key", "test_path.png", {"prompt": "test"})
        assert cache_hit(cache_db, "test_key")
        assert cache_db["test_key"]["path"] == "test_path.png"

    def test_world_builder_error_handling(self, world_builder):
        """Test error handling in world builder."""
        # Test with invalid config file
        with pytest.raises(Exception):
            WorldBuilder("nonexistent_config.json")

    @pytest.mark.asyncio
    async def test_generate_world_success(self, world_builder):
        """Test successful world generation."""
        with patch.object(world_builder, '_generate_base_scene', new_callable=AsyncMock) as mock_base:
            with patch.object(world_builder, '_generate_widget_overlays', new_callable=AsyncMock) as mock_overlays:
                with patch.object(world_builder, '_save_cache'):
                    mock_base.return_value = "test_base.png"
                    mock_overlays.return_value = [{"id": "test_widget", "states": []}]

                    result = await world_builder.generate_world()

        assert result["success"] is True
        assert result["world_name"] == "Test World"
        assert result["floors_processed"] == 1
        assert result["locations_processed"] == 1

    @pytest.mark.asyncio
    async def test_generate_world_with_errors(self, world_builder):
        """Test world generation with errors."""
        with patch.object(world_builder, '_generate_base_scene', side_effect=Exception("Test error")):
            result = await world_builder.generate_world()

        assert result["success"] is False
        assert "Test error" in result["error"]
        assert world_builder.stats["errors"] == 1

    def test_save_cache(self, world_builder, tmp_path):
        """Test cache saving functionality."""
        world_builder.cache_db["cache_entries"]["test_key"] = {
            "path": "test.png",
            "meta": {"prompt": "test"}
        }
        world_builder.stats["generated_images"] = 5
        world_builder.stats["cache_hits"] = 3

        cache_path = tmp_path / "test_cache.json"
        world_builder.config_path = str(tmp_path / "dummy_config.json")

        with patch('scripts.world_builder.save_json') as mock_save:
            world_builder._save_cache()

            # Verify save was called with updated statistics
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0]
            saved_data = call_args[1]
            assert saved_data["statistics"]["total_entries"] == 1
            assert saved_data["statistics"]["cache_hits"] == 3
            assert saved_data["statistics"]["cache_misses"] == 5

    def test_directory_structure_validation(self, world_builder):
        """Test required directory structure exists."""
        required_dirs = [
            "static/cache",
            "static/cache/tiles",
            "static/cache/widgets",
            "static/output",
            "web/app",
            "web/loader",
            "web/types"
        ]

        for dir_path in required_dirs:
            assert Path(dir_path).exists(), f"Directory {dir_path} should exist"

    def test_config_validation(self, world_builder):
        """Test world configuration validation."""
        config = world_builder.config

        # Required top-level keys
        assert "world_name" in config
        assert "style" in config
        assert "render" in config
        assert "floors" in config

        # Style configuration
        assert "tile_size" in config["style"]
        assert "grid" in config["style"]

        # Render configuration
        assert "provider_priority" in config["render"]
        assert "defaults" in config["render"]
        assert "seed" in config["render"]["defaults"]

        # Floors structure
        assert len(config["floors"]) > 0
        for floor in config["floors"]:
            assert "id" in floor
            assert "locations" in floor
            for location in floor["locations"]:
                assert "id" in location
                assert "bounds" in location
                assert "description_prompt" in location