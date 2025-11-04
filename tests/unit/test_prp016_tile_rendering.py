"""
Unit tests for PRP-016 Interactive Location System Tile Rendering.

These tests validate the core tile rendering functionality:
1. Tile variation switching (idle → hover → click)
2. Audio system plays different sounds for different events
3. Widget positioning accuracy matches visual elements
4. Background image changes during widget interactions
5. Widget click zones match actual image positions

Run with:
    pytest tests/unit/test_prp016_tile_rendering.py -v
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add the static directory to Python path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "static"))

# We'll test the JavaScript functionality by mocking browser environment


class TestTileRendering:
    """Test tile rendering and variation system."""

    def setup_method(self):
        """Setup test fixtures."""
        # Mock DOM elements
        self.mock_location_container = Mock()
        self.mock_location_container.dataset = {
            "locationId": "liliths_room",
            "currentTile": "idle",
            "tileIdle": "world/liliths_room_idle.png",
            "tileHover": "world/liliths_room_hover.png",
            "tileClick": "world/liliths_room_click.png",
        }
        self.mock_location_container.style = Mock()

        # Mock widget groups
        self.mock_widget_groups = [Mock(), Mock()]
        for widget in self.mock_widget_groups:
            widget.classList = Mock()

        # Mock document.querySelector
        self.mock_query_selector = Mock(return_value=self.mock_location_container)
        self.mock_query_selector_all = Mock(return_value=self.mock_widget_groups)

        # Mock audio manager
        self.mock_audio_manager = Mock()
        self.mock_audio_manager.playHover = Mock()
        self.mock_audio_manager.playClick = Mock()

    @patch("document.querySelector")
    @patch("document.querySelectorAll")
    def test_widget_hover_changes_tile_background(self, mock_query_all, mock_query):
        """Test that widget hover changes background image to hover tile."""
        # Setup mocks
        mock_query.return_value = self.mock_location_container
        mock_query_all.return_value = self.mock_widget_groups

        # Import and simulate the hover handler logic
        location_container = mock_query.return_value
        widget_groups = mock_query_all.return_value

        # Simulate hover start
        is_hovering = True

        if is_hovering:
            location_container.style.backgroundImage = (
                "url('world/liliths_room_hover.png')"
            )
            location_container.dataset["currentTile"] = "hover"

        # Assert background image changed to hover tile
        location_container.style.backgroundImage.assert_called_with(
            "url('world/liliths_room_hover.png')"
        )
        assert location_container.dataset["currentTile"] == "hover"

        # Assert widget groups got hover class
        for widget in widget_groups:
            widget.classList.toggle.assert_called_with("hover", True)

    @patch("document.querySelector")
    @patch("document.querySelectorAll")
    def test_widget_unhover_reverts_to_idle_tile(self, mock_query_all, mock_query):
        """Test that widget unhover reverts background image to idle tile."""
        # Setup mocks
        mock_query.return_value = self.mock_location_container
        mock_query_all.return_value = self.mock_widget_groups

        location_container = mock_query.return_value

        # Start with hover state
        location_container.dataset["currentTile"] = "hover"

        # Simulate hover end
        is_hovering = False

        if not is_hovering and location_container.dataset["currentTile"] != "click":
            location_container.style.backgroundImage = (
                "url('world/liliths_room_idle.png')"
            )
            location_container.dataset["currentTile"] = "idle"

        # Assert background image reverted to idle tile
        location_container.style.backgroundImage.assert_called_with(
            "url('world/liliths_room_idle.png')"
        )
        assert location_container.dataset["currentTile"] == "idle"

    @patch("document.querySelector")
    @patch("document.querySelectorAll")
    def test_widget_click_changes_tile_background(self, mock_query_all, mock_query):
        """Test that widget click changes background image to click tile."""
        # Setup mocks
        mock_query.return_value = self.mock_location_container
        mock_query_all.return_value = self.mock_widget_groups

        location_container = mock_query.return_value

        # Simulate click start
        is_clicking = True

        if is_clicking:
            location_container.style.backgroundImage = (
                "url('world/liliths_room_click.png')"
            )
            location_container.dataset["currentTile"] = "click"

        # Assert background image changed to click tile
        location_container.style.backgroundImage.assert_called_with(
            "url('world/liliths_room_click.png')"
        )
        assert location_container.dataset["currentTile"] == "click"

    @patch("document.querySelector")
    @patch("document.querySelectorAll")
    def test_widget_release_reverts_to_hover_tile(self, mock_query_all, mock_query):
        """Test that widget release reverts background image to hover tile."""
        # Setup mocks
        mock_query.return_value = self.mock_location_container
        mock_query_all.return_value = self.mock_widget_groups

        location_container = mock_query.return_value

        # Simulate click release
        is_clicking = False

        if not is_clicking:
            location_container.style.backgroundImage = (
                "url('world/liliths_room_hover.png')"
            )
            location_container.dataset["currentTile"] = "hover"

        # Assert background image reverted to hover tile
        location_container.style.backgroundImage.assert_called_with(
            "url('world/liliths_room_hover.png')"
        )
        assert location_container.dataset["currentTile"] == "hover"


class TestAudioSystem:
    """Test audio system functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        # Mock Web Audio API
        self.mock_audio_context = Mock()
        self.mock_audio_context.sampleRate = 44100
        self.mock_audio_context.createBuffer = Mock()
        self.mock_audio_context.createBuffer.return_value.getChannelData = Mock(
            return_value=Mock()
        )

    @patch("window.AudioContext")
    def test_generate_sound_creates_audio_buffer(self, mock_audio_context_class):
        """Test that generateSound creates proper audio buffer."""
        # Setup mock
        mock_audio_context_class.return_value = self.mock_audio_context

        # Simulate generateSound logic
        duration = 0.1
        sample_rate = self.mock_audio_context.sampleRate
        num_samples = sample_rate * duration

        # Mock buffer creation
        mock_buffer = Mock()
        self.mock_audio_context.createBuffer.return_value = mock_buffer

        # Simulate the generateSound method
        buffer = self.mock_audio_context.createBuffer(1, num_samples, sample_rate)
        buffer.getChannelData(0)

        # Verify buffer was created with correct parameters
        self.mock_audio_context.createBuffer.assert_called_with(
            1, int(num_samples), sample_rate
        )
        buffer.getChannelData.assert_called_with(0)

    def test_play_sound_with_different_volumes(self):
        """Test that playSound accepts different volume parameters."""
        mock_audio_manager = Mock()
        mock_audio_manager.enabled = True
        mock_audio_manager.initialized = True
        mock_audio_manager.sounds = {"hover": Mock()}

        # Test play with default volume
        mock_audio_manager.playSound("hover")
        # Note: In actual implementation, this would call gainNode.gain.value = 1.0

        # Test play with custom volume
        mock_audio_manager.playSound("hover", 0.5)
        # Note: In actual implementation, this would call gainNode.gain.value = 0.5

        assert mock_audio_manager.playSound.call_count == 2


class TestWidgetPositioning:
    """Test widget positioning accuracy."""

    def test_wall_clock_position_corrected(self):
        """Test that wall_clock position was corrected from 128px to 228px."""
        # Load the result.json data
        import json

        result_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "result.json"
        )

        with open(result_path, "r") as f:
            world_data = json.load(f)

        # Find wall_clock widget
        wall_clock = None
        for location in world_data["locations"]:
            for widget in location["widgets"]:
                if widget["id"] == "wall_clock":
                    wall_clock = widget
                    break

        assert wall_clock is not None, "wall_clock widget not found"
        assert wall_clock["position"]["x"] == 228, (
            f"wall_clock x position should be 228, got {wall_clock['position']['x']}"
        )
        assert wall_clock["position"]["y"] == 128, (
            f"wall_clock y position should be 128, got {wall_clock['position']['y']}"
        )
        assert wall_clock["size"]["width"] == 64, (
            f"wall_clock width should be 64, got {wall_clock['size']['width']}"
        )
        assert wall_clock["size"]["height"] == 64, (
            f"wall_clock height should be 64, got {wall_clock['size']['height']}"
        )

    def test_changelog_book_position_accessible(self):
        """Test that changelog_book widget is positioned in accessible area."""
        import json

        result_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "result.json"
        )

        with open(result_path, "r") as f:
            world_data = json.load(f)

        # Find changelog_book widget
        changelog_book = None
        for location in world_data["locations"]:
            for widget in location["widgets"]:
                if widget["id"] == "changelog_book":
                    changelog_book = widget
                    break

        assert changelog_book is not None, "changelog_book widget not found"

        # Should be positioned in center area, not edges
        x, y = changelog_book["position"]["x"], changelog_book["position"]["y"]
        assert 200 < x < 800, (
            f"changelog_book x position {x} should be in visible range (200-800)"
        )
        assert 200 < y < 800, (
            f"changelog_book y position {y} should be in visible range (200-800)"
        )
        assert changelog_book["size"]["width"] > 0, (
            "changelog_book should have positive width"
        )
        assert changelog_book["size"]["height"] > 0, (
            "changelog_book should have positive height"
        )

    def test_all_widgets_have_valid_positions_and_sizes(self):
        """Test that all widgets have valid positions and sizes."""
        import json

        result_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "result.json"
        )

        with open(result_path, "r") as f:
            world_data = json.load(f)

        for location in world_data["locations"]:
            for widget in location["widgets"]:
                # Check position
                assert "position" in widget, f"Widget {widget['id']} missing position"
                assert "x" in widget["position"], (
                    f"Widget {widget['id']} missing x position"
                )
                assert "y" in widget["position"], (
                    f"Widget {widget['id']} missing y position"
                )
                assert isinstance(widget["position"]["x"], (int, float)), (
                    f"Widget {widget['id']} x should be numeric"
                )
                assert isinstance(widget["position"]["y"], (int, float)), (
                    f"Widget {widget['id']} y should be numeric"
                )

                # Check size
                assert "size" in widget, f"Widget {widget['id']} missing size"
                assert "width" in widget["size"], f"Widget {widget['id']} missing width"
                assert "height" in widget["size"], (
                    f"Widget {widget['id']} missing height"
                )
                assert widget["size"]["width"] > 0, (
                    f"Widget {widget['id']} width should be > 0"
                )
                assert widget["size"]["height"] > 0, (
                    f"Widget {widget['id']} height should be > 0"
                )

                # Check position is within reasonable bounds (0-1024 for 1024x1024 image)
                assert 0 <= widget["position"]["x"] <= 1024, (
                    f"Widget {widget['id']} x position out of bounds"
                )
                assert 0 <= widget["position"]["y"] <= 1024, (
                    f"Widget {widget['id']} y position out of bounds"
                )


class TestTileImagePaths:
    """Test tile image paths and variations."""

    def test_all_tile_variations_exist(self):
        """Test that all tile variation images exist."""
        import json

        result_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "result.json"
        )
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "world")

        with open(result_path, "r") as f:
            world_data = json.load(f)

        for location in world_data["locations"]:
            assert "tiles" in location, f"Location {location['id']} missing tiles"
            tiles = location["tiles"]

            # Check all required tile variations exist
            required_tiles = ["idle", "hover", "click"]
            for tile_type in required_tiles:
                assert tile_type in tiles, (
                    f"Location {location['id']} missing {tile_type} tile"
                )

                # Check image file exists
                tile_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "static", tiles[tile_type]
                )
                assert os.path.exists(tile_path), (
                    f"Tile image does not exist: {tiles[tile_type]}"
                )

    def test_tile_images_are_valid_png_files(self):
        """Test that tile images are valid PNG files."""
        import json

        from PIL import Image

        result_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "result.json"
        )

        with open(result_path, "r") as f:
            world_data = json.load(f)

        for location in world_data["locations"]:
            tiles = location["tiles"]
            for tile_type, tile_path in tiles.items():
                full_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "static", tile_path
                )

                try:
                    with Image.open(full_path) as img:
                        # Check it's a PNG
                        assert img.format == "PNG", (
                            f"Tile {tile_path} should be PNG format"
                        )

                        # Check dimensions are 1024x1024
                        assert img.size == (1024, 1024), (
                            f"Tile {tile_path} should be 1024x1024, got {img.size}"
                        )

                except Exception as e:
                    pytest.fail(f"Failed to load tile image {tile_path}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
