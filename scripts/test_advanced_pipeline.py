#!/usr/bin/env python3
"""
Test version of Advanced Tile Generation Pipeline for PRP-016

This version creates mock tiles for testing without requiring API keys.
It demonstrates the complete pipeline structure and can be used for
development and testing of the interactive location system.
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from canvas_renderer import CanvasRenderer
from PIL import Image, ImageDraw, ImageFont


@dataclass
class TileGenerationConfig:
    """Configuration for tile generation pipeline."""

    location_id: str
    tile_size: int = 1024
    grid_width: int = 4
    grid_height: int = 4
    states: List[str] = None
    quality_threshold: float = 95.0
    enable_canvas: bool = True
    max_retries: int = 3
    seed: Optional[int] = None

    def __post_init__(self):
        if self.states is None:
            self.states = ["idle", "hover", "click"]


@dataclass
class TileAsset:
    """Represents a generated tile asset."""

    location_id: str
    tile_x: int
    tile_y: int
    state: str
    file_path: str
    generation_time: float
    prompt_hash: str
    context_tiles: List[str]


@dataclass
class GenerationResult:
    """Result of tile generation process."""

    location_id: str
    base_tiles: List[TileAsset]
    complete_images: Dict[str, str]
    generation_metadata: Dict[str, any]
    success: bool
    error_message: Optional[str] = None


class MockAdvancedTilePipeline:
    """
    Mock version of the advanced tile generation pipeline.

    This creates tiles programmatically for testing without requiring API keys.
    It demonstrates the complete structure and can be used for development.
    """

    def __init__(self, config: TileGenerationConfig):
        self.config = config
        self.canvas_renderer = CanvasRenderer(tile_size=config.tile_size)

        # Load world data
        self.world_data = self._load_world_data()
        self.location_data = self._find_location_data()

        # Generation tracking
        self.generation_start_time = time.time()
        self.tiles_generated = []
        self.failed_tiles = []

    def _load_world_data(self) -> Dict:
        """Load world.json data."""
        try:
            with open("static/world.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load world.json: {e}")

    def _find_location_data(self) -> Dict:
        """Find location data for the configured location_id."""
        for location in self.world_data.get("locations", []):
            if location.get("id") == self.config.location_id:
                return location
        raise ValueError(
            f"Location '{self.config.location_id}' not found in world.json"
        )

    def _get_generation_seed(self) -> int:
        """Get deterministic seed for generation."""
        if self.config.seed is not None:
            return self.config.seed

        # Generate seed from location and world data for determinism
        seed_content = (
            f"{self.config.location_id}-{self.world_data.get('version', '1.0.0')}"
        )
        return int(hashlib.md5(seed_content.encode()).hexdigest()[:8], 16)

    def _get_widgets_in_tile(self, tile_x: int, tile_y: int) -> List[Dict]:
        """Get widgets that are positioned within the specified tile."""
        widgets_in_tile = []
        tile_pixel_x = tile_x * self.config.tile_size
        tile_pixel_y = tile_y * self.config.tile_size

        for widget in self.location_data.get("widgets", []):
            widget_x = widget.get("position", {}).get("x", 0)
            widget_y = widget.get("position", {}).get("y", 0)
            widget_w = widget.get("size", {}).get("width", 64)
            widget_h = widget.get("size", {}).get("height", 64)

            # Check if widget overlaps with this tile
            if (
                widget_x < tile_pixel_x + self.config.tile_size
                and widget_x + widget_w > tile_pixel_x
                and widget_y < tile_pixel_y + self.config.tile_size
                and widget_y + widget_h > tile_pixel_y
            ):
                widgets_in_tile.append(widget)

        return widgets_in_tile

    def _create_mock_base_tile(self, tile_x: int, tile_y: int) -> Image.Image:
        """Create a mock base tile for testing."""
        tile = Image.new(
            "RGB", (self.config.tile_size, self.config.tile_size), (240, 240, 250)
        )
        draw = ImageDraw.Draw(tile)

        # Add gradient background
        for i in range(0, self.config.tile_size, 4):
            color_value = 240 + (tile_x * 5) + (tile_y * 3) + (i // 10)
            color_value = min(255, color_value)
            color = (color_value, color_value - 10, color_value + 10)
            draw.rectangle([0, i, self.config.tile_size, i + 4], fill=color)

        # Add border
        border_color = (100, 150, 200)
        draw.rectangle(
            [0, 0, self.config.tile_size - 1, self.config.tile_size - 1],
            outline=border_color,
            width=8,
        )

        # Add coordinate text
        try:
            font = self.canvas_renderer.font_cache.get(
                "large", ImageFont.load_default()
            )
        except (OSError, IOError):
            font = ImageFont.load_default()

        coord_text = f"Tile ({tile_x},{tile_y})"
        bbox = draw.textbbox((0, 0), coord_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.config.tile_size - text_width) // 2
        text_y = (self.config.tile_size - text_height) // 2 - 100

        draw.text((text_x, text_y), coord_text, fill=(50, 50, 50), font=font)

        # Add location name
        location_text = self.location_data.get("name", "Unknown Room")
        bbox = draw.textbbox((0, 0), location_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (self.config.tile_size - text_width) // 2
        draw.text((text_x, 50), location_text, fill=(70, 70, 70), font=font)

        # Add world style info
        world_style = self.world_data.get("style", {})
        style_text = f"{world_style.get('art_style', '16-bit pixel art')} {world_style.get('palette', 'DB32')}"
        try:
            small_font = self.canvas_renderer.font_cache.get(
                "small", ImageFont.load_default()
            )
        except (OSError, IOError):
            small_font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), style_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = (self.config.tile_size - text_width) // 2
        draw.text(
            (text_x, self.config.tile_size - 50),
            style_text,
            fill=(90, 90, 90),
            font=small_font,
        )

        return tile

    def _add_widget_state_overlay(
        self, base_tile: Image.Image, widget: Dict, state: str, tile_x: int, tile_y: int
    ) -> Image.Image:
        """Add widget state overlay to the base tile."""
        result_tile = base_tile.copy()
        draw = ImageDraw.Draw(result_tile)

        # Calculate widget position relative to tile
        widget_x = widget.get("position", {}).get("x", 0) - (
            tile_x * self.config.tile_size
        )
        widget_y = widget.get("position", {}).get("y", 0) - (
            tile_y * self.config.tile_size
        )
        widget_w = widget.get("size", {}).get("width", 64)
        widget_h = widget.get("size", {}).get("height", 64)

        # Determine overlay color based on widget type and state
        widget_type = widget.get("type", "object")

        if state == "idle":
            if widget_type == "time":
                color = (100, 150, 200)
            elif widget_type == "changelog":
                color = (150, 100, 200)
            elif widget_type == "link":
                color = (200, 150, 100)
            elif widget_type == "status":
                color = (100, 200, 150)
            else:
                color = (150, 150, 150)
        elif state == "hover":
            # Brighter colors for hover
            color = tuple(min(255, c + 50) for c in [100, 150, 200])
        elif state == "click":
            # Even brighter for click
            color = tuple(min(255, c + 100) for c in [100, 150, 200])
        else:
            color = (150, 150, 150)

        # Draw widget overlay
        padding = 8
        draw.rectangle(
            [
                max(0, widget_x - padding),
                max(0, widget_y - padding),
                min(self.config.tile_size, widget_x + widget_w + padding),
                min(self.config.tile_size, widget_y + widget_h + padding),
            ],
            fill=color,
            outline=(255, 255, 255),
            width=2,
        )

        # Add widget type text
        try:
            small_font = self.canvas_renderer.font_cache.get(
                "small", ImageFont.load_default()
            )
        except (OSError, IOError):
            small_font = ImageFont.load_default()

        widget_text = widget.get("name", widget.get("id", "Unknown"))
        text_bbox = draw.textbbox(
            (0, 0), widget_text[:10], font=small_font
        )  # Truncate long text
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_x = max(
            0,
            min(
                widget_x + (widget_w - text_width) // 2,
                self.config.tile_size - text_width,
            ),
        )
        text_y = max(
            0,
            min(
                widget_y + (widget_h - text_height) // 2,
                self.config.tile_size - text_height,
            ),
        )

        draw.text(
            (text_x, text_y), widget_text[:10], fill=(255, 255, 255), font=small_font
        )

        return result_tile

    def _apply_canvas_overlay(
        self, tile_image: Image.Image, tile_x: int, tile_y: int, state: str
    ) -> Image.Image:
        """Apply canvas overlay for dynamic data display."""
        if not self.config.enable_canvas:
            return tile_image

        # Get widgets that require canvas overlays
        widgets_needing_canvas = [
            w
            for w in self._get_widgets_in_tile(tile_x, tile_y)
            if w.get("type") in ["time", "status", "version"]
        ]

        if not widgets_needing_canvas:
            return tile_image

        # Create canvas data
        canvas_data = self.canvas_renderer.get_current_server_data(
            self.config.location_id, tile_x, tile_y
        )

        result_image = tile_image.copy()

        for widget in widgets_needing_canvas:
            widget_x = widget.get("position", {}).get("x", 0) - (
                tile_x * self.config.tile_size
            )
            widget_y = widget.get("position", {}).get("y", 0) - (
                tile_y * self.config.tile_size
            )
            widget_w = widget.get("size", {}).get("width", 64)
            widget_h = widget.get("size", {}).get("height", 64)

            # Determine canvas type based on widget
            if widget.get("type") == "time":
                canvas_data.widget_type = "time"
            elif widget.get("type") == "status":
                canvas_data.widget_type = "status"
                canvas_data.custom_data = {
                    "status": "ONLINE",
                    "status_color": (100, 255, 100),
                }
            else:
                canvas_data.widget_type = "dynamic"

            # Generate and apply canvas overlay
            overlay_tile = self.canvas_renderer.create_canvas_overlay(
                result_image,
                canvas_data,
                widget_position=(widget_x, widget_y),
                widget_size=(widget_w, widget_h),
            )
            result_image = overlay_tile

        return result_image

    async def generate_tile_state(
        self, tile_x: int, tile_y: int, state: str
    ) -> Optional[TileAsset]:
        """Generate a single tile state."""
        start_time = time.time()

        # Generate base tile
        base_tile = self._create_mock_base_tile(tile_x, tile_y)

        # Apply widget state modifications
        widgets_in_tile = self._get_widgets_in_tile(tile_x, tile_y)
        current_tile = base_tile

        for widget in widgets_in_tile:
            current_tile = self._add_widget_state_overlay(
                current_tile, widget, state, tile_x, tile_y
            )

        # Apply canvas overlay
        current_tile = self._apply_canvas_overlay(current_tile, tile_x, tile_y, state)

        # Save final tile
        output_dir = f"static/world/{self.config.location_id}"
        os.makedirs(output_dir, exist_ok=True)

        tile_path = f"{output_dir}/tile_{state}_{tile_x}_{tile_y}.png"
        current_tile.save(tile_path)

        # Create tile asset
        prompt_hash = hashlib.md5(
            f"mock-{tile_x}-{tile_y}-{state}".encode()
        ).hexdigest()[:16]

        tile_asset = TileAsset(
            location_id=self.config.location_id,
            tile_x=tile_x,
            tile_y=tile_y,
            state=state,
            file_path=tile_path,
            generation_time=time.time() - start_time,
            prompt_hash=prompt_hash,
            context_tiles=[],
        )

        return tile_asset

    async def generate_location_tiles(self) -> GenerationResult:
        """Generate all tiles for the configured location."""
        print(f"🎨 Mock Tile Generation Pipeline for {self.config.location_id}")
        print(f"   Grid: {self.config.grid_width}x{self.config.grid_height}")
        print(f"   States: {self.config.states}")
        print(f"   Tile size: {self.config.tile_size}px")

        start_time = time.time()
        base_tiles = []
        complete_images = {}

        # Generate tiles in sequence
        for tile_y in range(self.config.grid_height):
            for tile_x in range(self.config.grid_width):
                print(f"📍 Generating tile ({tile_x},{tile_y})...")

                # Generate all states for this tile
                for state in self.config.states:
                    print(f"   🎨 Generating {state} state...")

                    tile_asset = await self.generate_tile_state(tile_x, tile_y, state)

                    if tile_asset:
                        base_tiles.append(tile_asset)
                        self.tiles_generated.append(tile_asset)
                        print(
                            f"   ✅ {state} state generated in {tile_asset.generation_time:.2f}s"
                        )
                    else:
                        print(f"   ❌ Failed to generate {state} state")
                        self.failed_tiles.append((tile_x, tile_y, state))

        # Generate complete composite images
        print("🖼️  Generating complete composite images...")
        for state in self.config.states:
            composite_path = (
                f"static/world/{self.config.location_id}/complete_{state}.png"
            )
            await self._generate_composite_image(state, composite_path)
            complete_images[state] = composite_path

        generation_time = time.time() - start_time

        # Calculate success rate
        total_tiles = (
            self.config.grid_width * self.config.grid_height * len(self.config.states)
        )
        success_count = len(self.tiles_generated)
        success_rate = (success_count / total_tiles) * 100 if total_tiles > 0 else 0

        # Create generation result
        result = GenerationResult(
            location_id=self.config.location_id,
            base_tiles=base_tiles,
            complete_images=complete_images,
            generation_metadata={
                "total_generation_time": generation_time,
                "tiles_generated": success_count,
                "tiles_failed": len(self.failed_tiles),
                "success_rate": success_rate,
                "grid_size": f"{self.config.grid_width}x{self.config.grid_height}",
                "states": self.config.states,
                "tile_size": self.config.tile_size,
                "failed_tiles": self.failed_tiles,
                "generation_type": "mock",
            },
            success=success_count > 0,
        )

        print("\n🎉 Mock tile generation complete!")
        print(f"   Total time: {generation_time:.2f}s")
        print(f"   Success rate: {success_rate:.1f}% ({success_count}/{total_tiles})")
        print(f"   Failed tiles: {len(self.failed_tiles)}")

        return result

    async def _generate_composite_image(self, state: str, output_path: str) -> None:
        """Generate a complete composite image for a location state."""
        composite_size = (
            self.config.grid_width * self.config.tile_size,
            self.config.grid_height * self.config.tile_size,
        )

        composite_image = Image.new("RGB", composite_size, (240, 240, 250))

        # Paste tiles into composite
        for tile_asset in self.tiles_generated:
            if tile_asset.state == state:
                tile_image = Image.open(tile_asset.file_path)
                x_pos = tile_asset.tile_x * self.config.tile_size
                y_pos = tile_asset.tile_y * self.config.tile_size
                composite_image.paste(tile_image, (x_pos, y_pos))

        # Save composite image
        composite_image.save(output_path)
        print(f"   ✅ Composite {state} image saved to {output_path}")

    def update_result_json(self, result: GenerationResult) -> None:
        """Update result.json with generation results."""
        try:
            with open("result.json", "r") as f:
                result_data = json.load(f)

            # Update location data
            for location in result_data.get("locations", []):
                if location.get("id") == self.config.location_id:
                    location["tiles"] = {
                        "grid_size": {
                            "width": self.config.grid_width,
                            "height": self.config.grid_height,
                        },
                        "tile_size": self.config.tile_size,
                        "states": {},
                    }

                    # Add tile paths for each state
                    for state in self.config.states:
                        state_tiles = []
                        for tile in result.base_tiles:
                            if tile.state == state:
                                state_tiles.append(
                                    {
                                        "x": tile.tile_x,
                                        "y": tile.tile_y,
                                        "path": tile.file_path,
                                    }
                                )
                        location["tiles"]["states"][state] = state_tiles

                    # Add composite images
                    location["tiles"]["composite_images"] = result.complete_images

                    # Add generation metadata
                    location["tiles"]["generation_metadata"] = (
                        result.generation_metadata
                    )

                    break

            # Save updated result.json
            with open("result.json", "w") as f:
                json.dump(result_data, f, indent=2)

            print("✅ Updated result.json with mock tile generation results")

        except Exception as e:
            print(f"⚠️  Failed to update result.json: {e}")


async def main():
    """Main entry point for mock tile generation."""
    print("🎯 Mock Advanced Tile Generation Pipeline")
    print("=" * 50)

    # Configure for Lilith's Room
    config = TileGenerationConfig(
        location_id="liliths_room",
        tile_size=1024,
        grid_width=4,
        grid_height=4,
        states=["idle", "hover", "click"],
        quality_threshold=95.0,
        enable_canvas=True,
        max_retries=3,
        seed=None,
    )

    # Create and run pipeline
    pipeline = MockAdvancedTilePipeline(config)
    result = await pipeline.generate_location_tiles()

    if result.success:
        # Update result.json with generation results
        pipeline.update_result_json(result)

        print(f"\n🎊 SUCCESS: Generated mock tiles for {config.location_id}")
        print(f"   📁 Check static/world/{config.location_id}/ for generated tiles")
        print(f"   🖼️  Composite images: {list(result.complete_images.keys())}")
    else:
        print(f"\n❌ FAILED: No tiles generated for {config.location_id}")


if __name__ == "__main__":
    asyncio.run(main())
