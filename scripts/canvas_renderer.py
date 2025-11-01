#!/usr/bin/env python3
"""
Canvas Rendering System for PRP-016 Interactive Location System

Provides dynamic canvas overlays for displaying real-time server data,
version information, and hash values on interactive tiles.

This system creates dynamic data overlays for tiles that need to display
live information like server time, version numbers, and build hashes.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont


@dataclass
class CanvasData:
    """Data for canvas rendering."""

    server_time: str
    version: str
    build_hash: str
    location_id: str
    tile_x: int
    tile_y: int
    widget_type: str
    custom_data: Dict[str, Any]


class CanvasRenderer:
    """
    Renders dynamic canvas overlays for tile widgets.

    This class provides methods to render real-time data on tiles,
    including server time, version information, and build hashes.
    """

    def __init__(self, tile_size: int = 256):
        self.tile_size = tile_size
        self.font_cache = {}
        self.cache_enabled = True
        self.render_cache = {}

        # Try to load fonts
        self._load_fonts()

    def _load_fonts(self):
        """Load fonts for canvas rendering."""
        try:
            # Try to use system fonts
            self.font_cache["default"] = ImageFont.load_default()

            # Try to load nicer fonts
            try:
                self.font_cache["small"] = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 12
                )
                self.font_cache["medium"] = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 16
                )
                self.font_cache["large"] = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 20
                )
            except (OSError, IOError):
                # Fallback to default font
                self.font_cache["small"] = self.font_cache["default"]
                self.font_cache["medium"] = self.font_cache["default"]
                self.font_cache["large"] = self.font_cache["default"]

        except Exception as e:
            print(f"⚠️  Font loading failed, using default: {e}")
            self.font_cache["default"] = ImageFont.load_default()
            self.font_cache["small"] = self.font_cache["default"]
            self.font_cache["medium"] = self.font_cache["default"]
            self.font_cache["large"] = self.font_cache["default"]

    def get_cache_key(self, data: CanvasData) -> str:
        """Generate cache key for canvas data."""
        content = (
            f"{data.server_time}-{data.version}-{data.build_hash}-{data.custom_data}"
        )
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def render_server_time_canvas(
        self, position: Tuple[int, int] = (0, 0), size: Tuple[int, int] = (100, 30)
    ) -> Image.Image:
        """
        Render a canvas showing current server time.

        Args:
            position: (x, y) position within the tile
            size: (width, height) of the canvas area

        Returns:
            PIL Image with rendered time display
        """
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Get current time
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%H:%M:%S UTC")

        # Draw background with slight transparency
        bg_color = (20, 20, 30, 180)  # Dark blue with transparency
        draw.rectangle(
            [0, 0, size[0], size[1]], fill=bg_color, outline=(100, 150, 255, 200)
        )

        # Draw time text
        try:
            font = self.font_cache["small"]
        except KeyError:
            font = self.font_cache["default"]

        # Center text
        bbox = draw.textbbox((0, 0), time_str, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size[0] - text_width) // 2
        text_y = (size[1] - text_height) // 2

        draw.text((text_x, text_y), time_str, fill=(200, 220, 255, 255), font=font)

        return canvas

    def render_version_info_canvas(
        self,
        version: str,
        build_hash: str,
        position: Tuple[int, int] = (0, 0),
        size: Tuple[int, int] = (120, 50),
    ) -> Image.Image:
        """
        Render a canvas showing version and build information.

        Args:
            version: Version string (e.g., "v0.1.0")
            build_hash: Git commit hash (shortened)
            position: (x, y) position within the tile
            size: (width, height) of the canvas area

        Returns:
            PIL Image with rendered version info
        """
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw background
        bg_color = (30, 20, 20, 180)  # Dark red with transparency
        draw.rectangle(
            [0, 0, size[0], size[1]], fill=bg_color, outline=(255, 150, 100, 200)
        )

        try:
            small_font = self.font_cache["small"]
            medium_font = self.font_cache["medium"]
        except KeyError:
            small_font = self.font_cache["default"]
            medium_font = self.font_cache["default"]

        # Draw version
        version_text = f"Version: {version}"
        bbox = draw.textbbox((0, 0), version_text, font=medium_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((size[0] - text_width) // 2, 8),
            version_text,
            fill=(255, 200, 150, 255),
            font=medium_font,
        )

        # Draw hash (shortened to 8 characters)
        hash_text = f"Hash: {build_hash[:8]}"
        bbox = draw.textbbox((0, 0), hash_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((size[0] - text_width) // 2, 28),
            hash_text,
            fill=(200, 180, 160, 255),
            font=small_font,
        )

        return canvas

    def render_status_canvas(
        self,
        status_text: str,
        status_color: Tuple[int, int, int] = (100, 255, 100),
        position: Tuple[int, int] = (0, 0),
        size: Tuple[int, int] = (80, 25),
    ) -> Image.Image:
        """
        Render a status indicator canvas.

        Args:
            status_text: Text to display (e.g., "ONLINE", "ERROR")
            status_color: RGB color for status indicator
            position: (x, y) position within the tile
            size: (width, height) of the canvas area

        Returns:
            PIL Image with rendered status
        """
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw background
        bg_color = (20, 30, 20, 180)  # Dark green with transparency
        draw.rectangle(
            [0, 0, size[0], size[1]], fill=bg_color, outline=status_color + (200,)
        )

        try:
            font = self.font_cache["small"]
        except KeyError:
            font = self.font_cache["default"]

        # Draw status text
        bbox = draw.textbbox((0, 0), status_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size[0] - text_width) // 2
        text_y = (size[1] - text_height) // 2

        draw.text((text_x, text_y), status_text, fill=status_color + (255,), font=font)

        return canvas

    def render_dynamic_data_canvas(
        self,
        data: CanvasData,
        position: Tuple[int, int] = (0, 0),
        size: Tuple[int, int] = (150, 80),
    ) -> Image.Image:
        """
        Render a comprehensive data canvas with multiple information types.

        Args:
            data: CanvasData object with all information
            position: (x, y) position within the tile
            size: (width, height) of the canvas area

        Returns:
            PIL Image with rendered dynamic data
        """
        # Check cache first
        if self.cache_enabled:
            cache_key = self.get_cache_key(data)
            if cache_key in self.render_cache:
                cached_image, timestamp = self.render_cache[cache_key]
                # Cache for 30 seconds
                if time.time() - timestamp < 30:
                    return cached_image

        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw background with gradient effect
        bg_color = (40, 30, 50, 200)  # Dark purple with transparency
        draw.rectangle(
            [0, 0, size[0], size[1]], fill=bg_color, outline=(150, 120, 255, 200)
        )

        try:
            small_font = self.font_cache["small"]
            medium_font = self.font_cache["medium"]
        except KeyError:
            small_font = self.font_cache["default"]
            medium_font = self.font_cache["default"]

        y_offset = 8

        # Draw server time
        time_label = "Server Time:"
        draw.text((8, y_offset), time_label, fill=(180, 180, 200, 255), font=small_font)
        y_offset += 12

        time_value = data.server_time
        draw.text(
            (8, y_offset), time_value, fill=(200, 220, 255, 255), font=medium_font
        )
        y_offset += 18

        # Draw version info
        if data.version:
            version_text = f"v{data.version}"
            draw.text(
                (8, y_offset), version_text, fill=(150, 200, 150, 255), font=small_font
            )
            y_offset += 12

        # Draw build hash
        if data.build_hash:
            hash_text = f"Hash: {data.build_hash[:8]}"
            draw.text(
                (8, y_offset), hash_text, fill=(180, 160, 140, 255), font=small_font
            )
            y_offset += 12

        # Draw location info
        location_text = f"Tile: {data.location_id} ({data.tile_x},{data.tile_y})"
        draw.text(
            (8, y_offset), location_text, fill=(160, 140, 180, 255), font=small_font
        )

        # Cache the result
        if self.cache_enabled:
            cache_key = self.get_cache_key(data)
            self.render_cache[cache_key] = (canvas, time.time())

            # Clean old cache entries
            if len(self.render_cache) > 100:
                current_time = time.time()
                self.render_cache = {
                    k: v
                    for k, v in self.render_cache.items()
                    if current_time - v[1] < 300  # Keep entries for 5 minutes
                }

        return canvas

    def create_canvas_overlay(
        self,
        base_tile: Image.Image,
        canvas_data: CanvasData,
        widget_position: Tuple[int, int],
        widget_size: Tuple[int, int],
    ) -> Image.Image:
        """
        Apply a canvas overlay to a base tile.

        Args:
            base_tile: Base tile image
            canvas_data: Data to render on canvas
            widget_position: (x, y) position of widget on tile
            widget_size: (width, height) of widget area

        Returns:
            Combined image with canvas overlay
        """
        # Create a copy of the base tile
        result = base_tile.copy()

        # Render the canvas based on widget type
        if canvas_data.widget_type == "time":
            canvas = self.render_server_time_canvas(
                position=widget_position, size=widget_size
            )
        elif canvas_data.widget_type == "version":
            canvas = self.render_version_info_canvas(
                version=canvas_data.version,
                build_hash=canvas_data.build_hash,
                position=widget_position,
                size=widget_size,
            )
        elif canvas_data.widget_type == "status":
            status_text = canvas_data.custom_data.get("status", "ONLINE")
            status_color = canvas_data.custom_data.get("status_color", (100, 255, 100))
            canvas = self.render_status_canvas(
                status_text=status_text,
                status_color=status_color,
                position=widget_position,
                size=widget_size,
            )
        else:
            # Default: render comprehensive data canvas
            canvas = self.render_dynamic_data_canvas(
                data=canvas_data, position=widget_position, size=widget_size
            )

        # Paste canvas onto base tile
        result.paste(canvas, widget_position, canvas)

        return result

    def get_current_server_data(
        self, location_id: str, tile_x: int, tile_y: int
    ) -> CanvasData:
        """
        Get current server data for canvas rendering.

        Args:
            location_id: ID of the location
            tile_x: X coordinate of tile
            tile_y: Y coordinate of tile

        Returns:
            CanvasData with current server information
        """
        # Get current time
        now = datetime.now(timezone.utc)
        server_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Get version from result.json or default
        try:
            with open("static/result.json", "r") as f:
                result_data = json.load(f)
                version = result_data.get("version", "0.1.0")
        except (FileNotFoundError, json.JSONDecodeError):
            version = "0.1.0"

        # Get build hash from git or generate one
        try:
            import subprocess

            build_hash = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()[:8]
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback hash
            build_hash = hashlib.md5(
                f"{location_id}-{tile_x}-{tile_y}".encode()
            ).hexdigest()[:8]

        return CanvasData(
            server_time=server_time,
            version=version,
            build_hash=build_hash,
            location_id=location_id,
            tile_x=tile_x,
            tile_y=tile_y,
            widget_type="dynamic",
            custom_data={},
        )


def main():
    """Test the canvas rendering system."""
    print("🎨 Canvas Rendering System Test")
    print("=" * 40)

    renderer = CanvasRenderer()

    # Test server time canvas
    print("🕐 Testing server time canvas...")
    time_canvas = renderer.render_server_time_canvas()
    time_canvas.save("test_time_canvas.png")
    print("   ✅ Saved to test_time_canvas.png")

    # Test version info canvas
    print("📦 Testing version info canvas...")
    version_canvas = renderer.render_version_info_canvas(
        version="0.1.0", build_hash="abc123def"
    )
    version_canvas.save("test_version_canvas.png")
    print("   ✅ Saved to test_version_canvas.png")

    # Test status canvas
    print("🟢 Testing status canvas...")
    status_canvas = renderer.render_status_canvas(
        status_text="ONLINE", status_color=(100, 255, 100)
    )
    status_canvas.save("test_status_canvas.png")
    print("   ✅ Saved to test_status_canvas.png")

    # Test dynamic data canvas
    print("📊 Testing dynamic data canvas...")
    canvas_data = renderer.get_current_server_data("liliths_room", 0, 0)
    dynamic_canvas = renderer.render_dynamic_data_canvas(canvas_data)
    dynamic_canvas.save("test_dynamic_canvas.png")
    print("   ✅ Saved to test_dynamic_canvas.png")

    # Test overlay on base tile
    print("🖼️  Testing canvas overlay...")
    try:
        base_tile = Image.open("static/world/liliths_room/tile_idle_0_0.png")
        overlay_tile = renderer.create_canvas_overlay(
            base_tile, canvas_data, widget_position=(50, 50), widget_size=(150, 80)
        )
        overlay_tile.save("test_overlay_tile.png")
        print("   ✅ Saved to test_overlay_tile.png")
    except FileNotFoundError:
        print("   ⚠️  Base tile not found, skipping overlay test")

    print("🎉 Canvas rendering tests completed!")


if __name__ == "__main__":
    main()
