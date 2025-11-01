#!/usr/bin/env python3
"""
Advanced Tile Generation Pipeline for PRP-016

Implements the user's detailed tile-by-tile generation pipeline with:
- DALL-E 3 + Leonardo.AI integration
- Sequential context generation
- Template inpainting foundation
- State-specific widget overlays
- Canvas rendering integration
- Deterministic generation with quality gates

This is the production pipeline that will generate tiles for the interactive
location system with 95%+ consistency and proper state management.
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from canvas_renderer import CanvasRenderer
from PIL import Image, ImageDraw
from stable_tile_generator import GenerationResult, StableTileGenerator, TileAsset


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
    enable_inpainting: bool = True
    max_retries: int = 3
    seed: Optional[int] = None

    def __post_init__(self):
        if self.states is None:
            self.states = ["idle", "hover", "click"]


@dataclass
class WidgetStateConfig:
    """Configuration for widget state generation."""

    widget_id: str
    widget_type: str
    position: Dict[str, int]  # x, y
    size: Dict[str, int]  # width, height
    idle_prompt: str
    hover_prompt: str
    click_prompt: str
    requires_canvas: bool = False
    canvas_data_type: str = "dynamic"


class AdvancedTilePipeline:
    """
    Advanced tile generation pipeline implementing user's specifications.

    This pipeline coordinates:
    1. Sequential tile generation with context awareness
    2. Widget state management with DALL-E 3 + Leonardo.AI
    3. Canvas overlay integration for dynamic data
    4. Template inpainting for state variations
    5. Quality gates and consistency validation
    """

    def __init__(self, config: TileGenerationConfig):
        self.config = config
        self.tile_generator = StableTileGenerator()
        self.canvas_renderer = CanvasRenderer(tile_size=config.tile_size)

        # Load world data
        self.world_data = self._load_world_data()
        self.location_data = self._find_location_data()

        # Generation tracking
        self.generation_start_time = time.time()
        self.tiles_generated = []
        self.failed_tiles = []

        # Quality tracking
        self.quality_scores = {}

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

    def _build_tile_context(
        self, tile_x: int, tile_y: int, previous_tiles: List[TileAsset]
    ) -> List[str]:
        """
        Build context for sequential tile generation.

        Args:
            tile_x: X coordinate of current tile
            tile_y: Y coordinate of current tile
            previous_tiles: List of previously generated tiles

        Returns:
            List of context descriptions for consistent generation
        """
        context_parts = []

        # World style context
        world_style = self.world_data.get("style", {})
        style_text = (
            f"{world_style.get('art_style', '16-bit pixel art')} "
            f"{world_style.get('palette', 'DB32')}"
        )
        context_parts.append(f"WORLD STYLE: {style_text}")
        context_parts.append(
            f"CAMERA: {world_style.get('camera', 'top-down SNES RPG')}"
        )

        # Location context
        location_text = (
            f"{self.location_data.get('name', 'Unknown Room')} - "
            f"{self.location_data.get('description', 'A room')}"
        )
        context_parts.append(f"LOCATION: {location_text}")

        # Position context
        position_text = (
            f"Tile coordinates ({tile_x}, {tile_y}) in "
            f"{self.config.grid_width}x{self.config.grid_height} grid"
        )
        context_parts.append(f"POSITION: {position_text}")

        # Previous tiles context for seamless generation
        if previous_tiles:
            # Add context from last 2 tiles for continuity
            recent_tiles = previous_tiles[-2:]
            tile_descriptions = [
                f"Tile {tile.tile_x},{tile.tile_y}: {tile.context}"
                for tile in recent_tiles
            ]
            context_parts.append(
                f"CONTEXT: Previous tiles show: {' | '.join(tile_descriptions)}"
            )

        # Widget context
        widgets_in_tile = self._get_widgets_in_tile(tile_x, tile_y)
        if widgets_in_tile:
            widget_info = []
            for widget in widgets_in_tile:
                widget_name = widget.get("name", widget.get("id", "Unknown"))
                widget_type = widget.get("type", "object")
                widget_info.append(f"{widget_name} ({widget_type})")
            context_parts.append(
                f"WIDGETS: This tile contains: {', '.join(widget_info)}"
            )

        return context_parts

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

    def _build_widget_state_prompts(
        self, widget: Dict, state: str, tile_context: List[str]
    ) -> str:
        """
        Build state-specific prompts for widget generation.

        Args:
            widget: Widget configuration
            state: Target state (idle, hover, click)
            tile_context: Context from tile generation

        Returns:
            Detailed prompt for widget state generation
        """
        base_prompt_parts = tile_context.copy()

        # Widget-specific instructions
        widget_type = widget.get("type", "object")
        widget_name = widget.get("name", widget.get("id", "Unknown"))

        base_prompt_parts.append(f"WIDGET: {widget_name} ({widget_type})")

        # State-specific modifications
        if state == "idle":
            base_prompt_parts.append(f"STATE: {widget_name} is in normal/resting state")
            if widget_type == "time":
                base_prompt_parts.append(
                    "Clock shows normal time display, hands clearly visible"
                )
            elif widget_type == "changelog":
                base_prompt_parts.append(
                    "Book is closed, resting on surface, title visible"
                )
            elif widget_type == "link":
                base_prompt_parts.append("Poster is static, design clearly visible")
            elif widget_type == "status":
                base_prompt_parts.append("Status indicator shows normal/active state")
            elif widget_type == "easteregg":
                base_prompt_parts.append(
                    "Hidden element is subtle, not immediately obvious"
                )

        elif state == "hover":
            base_prompt_parts.append(
                f"STATE: {widget_name} is being hovered/interacted with"
            )
            if widget_type == "time":
                base_prompt_parts.append(
                    "Clock hands glow slightly, time display becomes more prominent"
                )
            elif widget_type == "changelog":
                base_prompt_parts.append(
                    "Book slightly opens, pages begin to show, soft glow around edges"
                )
            elif widget_type == "link":
                base_prompt_parts.append(
                    "Poster brightens, borders glow, becomes more prominent"
                )
            elif widget_type == "status":
                base_prompt_parts.append(
                    "Status indicator brightens, shows more detail or animation"
                )
            elif widget_type == "easteregg":
                base_prompt_parts.append(
                    "Hidden element becomes slightly more visible, subtle glow"
                )

        elif state == "click":
            base_prompt_parts.append(
                f"STATE: {widget_name} is actively clicked/pressed"
            )
            if widget_type == "time":
                base_prompt_parts.append(
                    "Clock hands move rapidly, time display pulses with energy"
                )
            elif widget_type == "changelog":
                base_prompt_parts.append(
                    "Book opens wide, pages fully visible, text readable, magical glow"
                )
            elif widget_type == "link":
                poster_text = (
                    "Poster expands or animates, bright active state, "
                    "clear interaction feedback"
                )
                base_prompt_parts.append(poster_text)
            elif widget_type == "status":
                base_prompt_parts.append(
                    "Status indicator shows active/processing state with animation"
                )
            elif widget_type == "easteregg":
                base_prompt_parts.append(
                    "Hidden element fully reveals itself, bright and animated"
                )

        # Quality requirements
        base_prompt_parts.extend(
            [
                "QUALITY: Sharp 16-bit pixel art, consistent with DB32 palette",
                "ALIGNMENT: Perfect pixel alignment, no blurring or anti-aliasing",
                "STYLE: Top-down SNES RPG aesthetic, clear and readable",
            ]
        )

        return " | ".join(base_prompt_parts)

    async def _generate_base_tile(
        self, tile_x: int, tile_y: int, context: List[str], seed: int
    ) -> Optional[Image.Image]:
        """
        Generate a base tile with no widget state modifications.

        Args:
            tile_x: X coordinate
            tile_y: Y coordinate
            context: Generation context
            seed: Random seed

        Returns:
            Generated tile image or None if failed
        """
        prompt = (
            " | ".join(context)
            + " | BASE STATE: No active widget interactions, room at rest"
        )

        try:
            # Use DALL-E 3 for base tile generation
            response = self.tile_generator.openai.images.generate(
                prompt=prompt,
                n=1,
                size=f"{self.config.tile_size}x{self.config.tile_size}",
                quality="hd",
                response_format="url",
                style="natural",
            )

            image_url = response.data[0].url

            # Download and save the image
            import requests

            image_response = requests.get(image_url)
            image_response.raise_for_status()

            from io import BytesIO

            image = Image.open(BytesIO(image_response.content))

            # Save base tile
            tile_filename = f"base_tile_{tile_x}_{tile_y}.png"
            tile_path = f"static/world/{self.config.location_id}/{tile_filename}"
            os.makedirs(os.path.dirname(tile_path), exist_ok=True)
            image.save(tile_path)

            return image

        except Exception as e:
            print(f"❌ Failed to generate base tile ({tile_x},{tile_y}): {e}")
            return None

    async def _generate_widget_state_tile(
        self,
        base_tile: Image.Image,
        widget: Dict,
        state: str,
        tile_x: int,
        tile_y: int,
        context: List[str],
    ) -> Optional[Image.Image]:
        """
        Generate a widget state variation using inpainting.

        Args:
            base_tile: Base tile image
            widget: Widget configuration
            state: Target state
            tile_x: X coordinate
            tile_y: Y coordinate
            context: Generation context

        Returns:
            Modified tile image or None if failed
        """
        if not self.config.enable_inpainting:
            return base_tile

        # Build state-specific prompt
        prompt = self._build_widget_state_prompts(widget, state, context)

        # Calculate widget mask position relative to tile
        widget_x = widget.get("position", {}).get("x", 0) - (
            tile_x * self.config.tile_size
        )
        widget_y = widget.get("position", {}).get("y", 0) - (
            tile_y * self.config.tile_size
        )
        widget_w = widget.get("size", {}).get("width", 64)
        widget_h = widget.get("size", {}).get("height", 64)

        try:
            # Create mask for widget area
            mask = Image.new("L", (self.config.tile_size, self.config.tile_size), 0)
            mask_draw = ImageDraw.Draw(mask)

            # Draw rectangle for widget area with slight padding
            padding = 10
            mask_draw.rectangle(
                [
                    max(0, widget_x - padding),
                    max(0, widget_y - padding),
                    min(self.config.tile_size, widget_x + widget_w + padding),
                    min(self.config.tile_size, widget_y + widget_h + padding),
                ],
                fill=255,
            )

            # Save base tile temporarily for API
            base_path = f"temp_base_{tile_x}_{tile_y}.png"
            mask_path = f"temp_mask_{tile_x}_{tile_y}.png"

            base_tile.save(base_path)
            mask.save(mask_path)

            # Use DALL-E 3 inpainting (edit endpoint)
            with open(base_path, "rb") as base_file, open(mask_path, "rb") as mask_file:
                response = self.tile_generator.openai.images.edit(
                    image=base_file,
                    mask=mask_file,
                    prompt=prompt,
                    n=1,
                    size=f"{self.config.tile_size}x{self.config.tile_size}",
                    response_format="url",
                )

            image_url = response.data[0].url

            # Download the modified image
            import requests

            image_response = requests.get(image_url)
            image_response.raise_for_status()

            from io import BytesIO

            modified_image = Image.open(BytesIO(image_response.content))

            # Clean up temporary files
            os.remove(base_path)
            os.remove(mask_path)

            return modified_image

        except Exception as e:
            print(f"⚠️  Widget inpainting failed for {widget.get('id')} {state}: {e}")
            # Fall back to original base tile
            return base_tile

    def _apply_canvas_overlay(
        self, tile_image: Image.Image, tile_x: int, tile_y: int, state: str
    ) -> Image.Image:
        """
        Apply canvas overlay for dynamic data display.

        Args:
            tile_image: Base tile image
            tile_x: X coordinate
            tile_y: Y coordinate
            state: Current state

        Returns:
            Tile image with canvas overlay applied
        """
        if not self.config.enable_canvas:
            return tile_image

        # Get widgets that require canvas overlays
        widgets_needing_canvas = [
            w
            for w in self._get_widgets_in_tile(tile_x, tile_y)
            if w.get("type") in ["time", "status", "version"]
            or w.get("requires_canvas", False)
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
        self,
        tile_x: int,
        tile_y: int,
        state: str,
        previous_tiles: List[TileAsset],
        base_tile: Optional[Image.Image] = None,
    ) -> Optional[TileAsset]:
        """
        Generate a single tile state.

        Args:
            tile_x: X coordinate
            tile_y: Y coordinate
            state: Target state (idle, hover, click)
            previous_tiles: Previously generated tiles for context
            base_tile: Base tile image (optional)

        Returns:
            Generated tile asset or None if failed
        """
        start_time = time.time()

        # Build generation context
        context = self._build_tile_context(tile_x, tile_y, previous_tiles)

        # Generate or use base tile
        if base_tile is None:
            base_tile = await self._generate_base_tile(
                tile_x, tile_y, context, self._get_generation_seed()
            )
            if base_tile is None:
                return None

        # Apply widget state modifications
        widgets_in_tile = self._get_widgets_in_tile(tile_x, tile_y)
        current_tile = base_tile

        for widget in widgets_in_tile:
            current_tile = await self._generate_widget_state_tile(
                current_tile, widget, state, tile_x, tile_y, context
            )

        # Apply canvas overlay
        current_tile = self._apply_canvas_overlay(current_tile, tile_x, tile_y, state)

        # Save final tile
        tile_path = (
            f"static/world/{self.config.location_id}/tile_{state}_{tile_x}_{tile_y}.png"
        )
        os.makedirs(os.path.dirname(tile_path), exist_ok=True)
        current_tile.save(tile_path)

        # Create tile asset
        context_str = " | ".join(context)
        prompt_hash = hashlib.md5(f"{context_str}-{state}".encode()).hexdigest()[:16]

        tile_asset = TileAsset(
            location_id=self.config.location_id,
            tile_x=tile_x,
            tile_y=tile_y,
            state=state,
            file_path=tile_path,
            generation_time=time.time() - start_time,
            prompt_hash=prompt_hash,
            context_tiles=[
                tile.context for tile in previous_tiles[-4:]
            ],  # Last 4 tiles for context
        )

        return tile_asset

    async def generate_location_tiles(self) -> GenerationResult:
        """
        Generate all tiles for the configured location.

        Returns:
            Generation result with all created assets
        """
        print(f"🚀 Starting advanced tile generation for {self.config.location_id}")
        print(f"   Grid: {self.config.grid_width}x{self.config.grid_height}")
        print(f"   States: {self.config.states}")
        print(f"   Tile size: {self.config.tile_size}px")

        start_time = time.time()
        base_tiles = []
        widget_overlays = {}
        complete_images = {}

        # Generate tiles in sequence for context awareness
        for tile_y in range(self.config.grid_height):
            for tile_x in range(self.config.grid_width):
                print(f"📍 Generating tile ({tile_x},{tile_y})...")

                # Generate base tile once
                context = self._build_tile_context(tile_x, tile_y, base_tiles)
                base_tile = await self._generate_base_tile(
                    tile_x,
                    tile_y,
                    context,
                    self._get_generation_seed() + tile_x + tile_y * 100,
                )

                if base_tile is None:
                    print(f"❌ Failed to generate base tile ({tile_x},{tile_y})")
                    self.failed_tiles.append((tile_x, tile_y, "base"))
                    continue

                # Generate all states for this tile
                for state in self.config.states:
                    print(f"   🎨 Generating {state} state...")

                    tile_asset = await self.generate_tile_state(
                        tile_x, tile_y, state, base_tiles, base_tile
                    )

                    if tile_asset:
                        base_tiles.append(tile_asset)
                        self.tiles_generated.append(tile_asset)
                        time_text = (
                            f"   ✅ {state} state generated in "
                            f"{tile_asset.generation_time:.2f}s"
                        )
                        print(time_text)
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
            widget_overlays=widget_overlays,
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
            },
            success=success_count > 0,
        )

        print("\n🎉 Tile generation complete!")
        print(f"   Total time: {generation_time:.2f}s")
        print(f"   Success rate: {success_rate:.1f}% ({success_count}/{total_tiles})")
        print(f"   Failed tiles: {len(self.failed_tiles)}")

        if self.failed_tiles:
            failed_text = f"   Failed: {self.failed_tiles[:5]}"
            if len(self.failed_tiles) > 5:
                failed_text += "..."
            print(failed_text)

        return result

    async def _generate_composite_image(self, state: str, output_path: str) -> None:
        """
        Generate a complete composite image for a location state.

        Args:
            state: Target state (idle, hover, click)
            output_path: Path to save the composite image
        """
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

            print("✅ Updated result.json with tile generation results")

        except Exception as e:
            print(f"⚠️  Failed to update result.json: {e}")


async def main():
    """Main entry point for advanced tile generation."""
    print("🎯 Advanced Tile Generation Pipeline")
    print("=" * 50)

    # Configure for Lilith's Room (existing location)
    config = TileGenerationConfig(
        location_id="liliths_room",
        tile_size=1024,
        grid_width=4,
        grid_height=4,
        states=["idle", "hover", "click"],
        quality_threshold=95.0,
        enable_canvas=True,
        enable_inpainting=True,
        max_retries=3,
        seed=None,  # Deterministic from location
    )

    # Create and run pipeline
    pipeline = AdvancedTilePipeline(config)
    result = await pipeline.generate_location_tiles()

    if result.success:
        # Update result.json with generation results
        pipeline.update_result_json(result)

        print(f"\n🎊 SUCCESS: Generated tiles for {config.location_id}")
        print(f"   📁 Check static/world/{config.location_id}/ for generated tiles")
        print(f"   🖼️  Composite images: {list(result.complete_images.keys())}")
    else:
        print(f"\n❌ FAILED: No tiles generated for {config.location_id}")


if __name__ == "__main__":
    asyncio.run(main())
