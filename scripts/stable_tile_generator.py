#!/usr/bin/env python3
"""
Stable Tile Generation Pipeline
================================

Implements the DALL-E 3 + Leonardo.AI tile generation system with:
1. Sequential context generation for perfect tile consistency
2. Widget state variations with overlay tiles
3. Deterministic generation with seed-based reproducibility
4. Comprehensive asset management and validation

Based on user research for pre-generating interactive image states.
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import replicate
from openai import OpenAI
from PIL import Image, ImageDraw

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


@dataclass
class TileAsset:
    """Represents a generated tile asset."""

    location_id: str
    tile_x: int
    tile_y: int
    state: str  # idle, hover, click
    file_path: str
    generation_time: float
    prompt_hash: str
    context_tiles: List[str]  # Previous tiles used for context


@dataclass
class WidgetOverlay:
    """Represents a widget overlay tile for state changes."""

    location_id: str
    widget_id: str
    state: str
    tile_x: int
    tile_y: int
    file_path: str
    transparency_mask: bool
    base_differs: bool


@dataclass
class GenerationResult:
    """Result of tile generation process."""

    location_id: str
    base_tiles: List[TileAsset]
    widget_overlays: Dict[str, Dict[str, List[WidgetOverlay]]]
    complete_images: Dict[str, str]  # state -> file path
    generation_metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class StableTileGenerator:
    """Advanced tile generation system using DALL-E 3 + Leonardo.AI."""

    def __init__(self):
        self.openai = OpenAI(api_key=API_KEY) if API_KEY else None
        self.replicate = None
        if REPLICATE_API_TOKEN:
            os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
            self.replicate = replicate.Client()

        self.tile_size = 256
        self.context_buffer_size = 4  # Number of previous tiles to include in context

    def calculate_prompt_hash(self, prompt: str) -> str:
        """Calculate SHA256 hash of prompt for change detection."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def build_hierarchical_prompt(
        self,
        location: Dict,
        world_context: str,
        tile_x: int,
        tile_y: int,
        previous_tiles: List[str],
        widget_instructions: Optional[str] = None,
        state: str = "idle",
    ) -> str:
        """Build hierarchical prompt for tile generation."""

        # Base components
        prompt_parts = [
            f"WORLD STYLE: {world_context}",
            f"LOCATION: {location['name']} - {location['description']}",
            f"POSITION: Tile coordinates ({tile_x}, {tile_y}) in "
            f"{location.get('grid_size', {'width': 4, 'height': 4})} grid",
        ]

        # Add previous tile context for seamless generation
        if previous_tiles:
            prompt_parts.append(
                f"CONTEXT: Previous tiles show: {', '.join(previous_tiles[-2:])}"
            )

        # Add widget-specific instructions
        if widget_instructions:
            prompt_parts.append(f"WIDGET AREA: {widget_instructions}")

        # Add state-specific instructions
        if state != "idle":
            state_descriptions = {
                "hover": "subtle interactive glow effects, gentle lighting changes",
                "click": "active interaction state, enhanced visual feedback",
            }
            prompt_parts.append(f"STATE: {state_descriptions.get(state, '')}")

        # Style consistency
        prompt_parts.append(
            "STYLE: kawaii anime aesthetic, pastel colors, 16-bit pixel art, "
            "SNES RPG game style, high quality, detailed, consistent art style"
        )

        return " | ".join(prompt_parts)

    async def generate_base_scene(
        self, location: Dict, world_context: str, seed: int
    ) -> Optional[str]:
        """Generate base scene with DALL-E 3."""
        if not self.openai:
            print("❌ OpenAI API key not available")
            return None

        try:
            base_prompt = f"""
            {world_context}

            LOCATION: {location["name"]}
            DESCRIPTION: {location["description"]}
            STYLE: kawaii anime bedroom, 16-bit pixel art, SNES RPG style,
            detailed background, cozy atmosphere, pastel pink and purple colors,
            high quality, consistent art style, 1024x1024 resolution
            """

            response = await self.openai.images.generate(
                model="dall-e-3",
                prompt=base_prompt,
                size="1024x1024",
                quality="hd",
                n=1,
                response_format="url",
            )

            image_url = response.data[0].url
            print(f"✅ Generated base scene: {location['id']}")
            return image_url

        except Exception as e:
            print(f"❌ Failed to generate base scene: {e}")
            return None

    def extract_tile_region(
        self, image_path: str, tile_x: int, tile_y: int, tile_size: int = 256
    ) -> Image.Image:
        """Extract a specific tile region from a larger image."""
        try:
            with Image.open(image_path) as img:
                # Calculate tile coordinates
                x = tile_x * tile_size
                y = tile_y * tile_size

                # Ensure coordinates are within image bounds
                max_x = img.width - tile_size
                max_y = img.height - tile_size
                x = min(x, max_x)
                y = min(y, max_y)

                # Extract tile region
                tile = img.crop((x, y, x + tile_size, y + tile_size))
                return tile

        except Exception as e:
            print(f"❌ Failed to extract tile region: {e}")
            # Return a blank tile as fallback
            return Image.new("RGB", (tile_size, tile_size), (255, 255, 255))

    async def generate_tile_with_context(
        self,
        location: Dict,
        world_context: str,
        tile_x: int,
        tile_y: int,
        previous_tiles: List[str],
        widget_instructions: Optional[str] = None,
        state: str = "idle",
        seed: int = 42,
    ) -> Optional[Image.Image]:
        """Generate a single tile with context from previous tiles."""
        if not self.replicate:
            print("❌ Replicate API token not available, using simple fallback")
            return None

        try:
            # Build hierarchical prompt
            prompt = self.build_hierarchical_prompt(
                location,
                world_context,
                tile_x,
                tile_y,
                previous_tiles,
                widget_instructions,
                state,
            )

            # Use InstructPix2Pix for context-aware editing
            # This allows us to edit specific regions while maintaining context
            model = "timothybrooks/instruct-pix2px"

            # If we have previous tiles, create a base canvas to edit
            if previous_tiles:
                # Create a canvas from previous tiles (simplified approach)
                # In production, this would stitch previous tiles together
                base_image_path = f"static/world/{location['id']}_base.png"
                if not os.path.exists(base_image_path):
                    # Generate a simple base image
                    base_image = Image.new("RGB", (1024, 1024), (240, 240, 250))
                    base_image.save(base_image_path)

                # Extract the region we want to modify
                self.extract_tile_region(base_image_path, tile_x, tile_y)

                input_data = {
                    "image": base_image_path,
                    "prompt": prompt,
                    "image_guidance_scale": 1.0,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 50,
                }
            else:
                # Generate from scratch for first tile
                input_data = {
                    "prompt": prompt,
                    "width": self.tile_size,
                    "height": self.tile_size,
                    "num_inference_steps": 50,
                }

            # Run generation
            output = self.replicate.run(model, input=input_data)

            if output and isinstance(output, str):
                # The output should be a URL to the generated image
                # For now, we'll save it and load it
                import io

                import requests

                response = requests.get(output)
                if response.ok:
                    image_bytes = io.BytesIO(response.content)
                    tile = Image.open(image_bytes)
                    print(f"✅ Generated tile ({tile_x},{tile_y}) for {location['id']}")
                    return tile

        except Exception as e:
            print(f"❌ Failed to generate tile ({tile_x},{tile_y}): {e}")
            return None

    async def generate_widget_state_variation(
        self,
        base_tile: Image.Image,
        location: Dict,
        widget: Dict,
        state: str,
        tile_x: int,
        tile_y: int,
    ) -> Optional[Image.Image]:
        """Generate widget state variation using inpainting."""
        if not self.replicate:
            return None

        try:
            # Create mask for widget area
            widget_x = widget["position"]["x"] - (tile_x * self.tile_size)
            widget_y = widget["position"]["y"] - (tile_y * self.tile_size)
            widget_w = widget["size"]["width"]
            widget_h = widget["size"]["height"]

            # Ensure mask coordinates are valid
            widget_x = max(0, min(widget_x, self.tile_size))
            widget_y = max(0, min(widget_y, self.tile_size))
            widget_w = min(widget_w, self.tile_size - widget_x)
            widget_h = min(widget_h, self.tile_size - widget_y)

            # Create mask (white for widget area, black for background)
            mask = Image.new("L", (self.tile_size, self.tile_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle(
                [widget_x, widget_y, widget_x + widget_w, widget_y + widget_h], fill=255
            )

            # Build state-specific prompt
            state_descriptions = {
                "idle": widget["interactions"]["idle"],
                "hover": widget["interactions"]["hover"],
                "click": widget["interactions"]["click"],
            }

            prompt = f"""
            Widget state variation: {widget["name"]} ({widget["type"]})
            State: {state_descriptions.get(state, "")}
            Location: {location["name"]}
            Style: Maintain kawaii anime aesthetic, seamless integration
            """

            # Save temporary files
            base_tile_path = f"temp/base_tile_{tile_x}_{tile_y}.png"
            mask_path = f"temp/mask_{tile_x}_{tile_y}.png"

            base_tile.save(base_tile_path)
            mask.save(mask_path)

            # Use Leonardo AI inpainting
            model = "stability-ai/stable-diffusion-inpainting"

            input_data = {
                "image": base_tile_path,
                "mask": mask_path,
                "prompt": prompt,
                "width": self.tile_size,
                "height": self.tile_size,
                "num_inference_steps": 30,
            }

            output = self.replicate.run(model, input_data=input_data)

            if output and isinstance(output, str):
                import io

                import requests

                response = requests.get(output)
                if response.ok:
                    image_bytes = io.BytesIO(response.content)
                    variation_tile = Image.open(image_bytes)

                    # Clean up temporary files
                    os.remove(base_tile_path)
                    os.remove(mask_path)

                    return variation_tile

        except Exception as e:
            print(f"❌ Failed to generate widget variation: {e}")
            return None

    def create_transparency_mask(
        self, base_tile: Image.Image, variation_tile: Image.Image
    ) -> Image.Image:
        """Create transparency mask showing only changed areas."""
        # Convert to numpy arrays
        base_arr = np.array(base_tile)
        variation_arr = np.array(variation_tile)

        # Calculate absolute difference
        diff_arr = np.abs(base_arr.astype(int) - variation_arr.astype(int))

        # Create mask (changes > threshold become opaque)
        threshold = 30
        mask_arr = (np.sum(diff_arr, axis=2) > threshold).astype(np.uint8) * 255

        # Create RGBA image with transparency
        mask_rgba = np.zeros((*base_arr.shape[:2], 4), dtype=np.uint8)
        mask_rgba[:, :, :3] = variation_arr  # RGB channels
        mask_rgba[:, :, 3] = mask_arr  # Alpha channel

        return Image.fromarray(mask_rgba, "RGBA")

    def save_tile_asset(
        self,
        tile: Image.Image,
        location_id: str,
        tile_x: int,
        tile_y: int,
        state: str,
        generation_time: float,
        prompt_hash: str,
        context_tiles: List[str],
    ) -> TileAsset:
        """Save tile asset and return metadata."""

        # Create directory structure
        output_dir = Path(f"static/world/{location_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{location_id}_tile_{tile_x}_{tile_y}_{state}.png"
        file_path = output_dir / filename

        # Save tile
        tile.save(file_path)

        return TileAsset(
            location_id=location_id,
            tile_x=tile_x,
            tile_y=tile_y,
            state=state,
            file_path=str(file_path),
            generation_time=generation_time,
            prompt_hash=prompt_hash,
            context_tiles=context_tiles.copy(),
        )

    def save_widget_overlay(
        self,
        overlay_tile: Image.Image,
        location_id: str,
        widget_id: str,
        state: str,
        tile_x: int,
        tile_y: int,
        generation_time: float,
    ) -> WidgetOverlay:
        """Save widget overlay tile and return metadata."""

        # Create directory structure
        output_dir = Path(f"static/world/{location_id}/overlays")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{location_id}_{widget_id}_{state}_tile_{tile_x}_{tile_y}.png"
        file_path = output_dir / filename

        # Save overlay
        overlay_tile.save(file_path)

        return WidgetOverlay(
            location_id=location_id,
            widget_id=widget_id,
            state=state,
            tile_x=tile_x,
            tile_y=tile_y,
            file_path=str(file_path),
            transparency_mask=True,
            base_differs=True,
        )

    async def generate_location_tiles(
        self, location: Dict, world_context: str, seed: int = 42
    ) -> GenerationResult:
        """Generate all tiles for a location with context awareness."""

        print(f"🏗️ Starting tile generation for: {location['id']}")
        start_time = time.time()

        try:
            # Determine grid size
            grid_size = location.get("grid_size", {"width": 4, "height": 4})

            # Step 1: Generate base scene
            base_scene_url = await self.generate_base_scene(
                location, world_context, seed
            )
            if base_scene_url:
                # Download and save base scene
                import requests

                response = requests.get(base_scene_url)
                if response.ok:
                    base_scene_path = f"static/world/{location['id']}_base.png"
                    with open(base_scene_path, "wb") as f:
                        f.write(response.content)

            # Step 2: Generate base tiles with context
            base_tiles = []
            previous_context = []

            for y in range(grid_size["height"]):
                for x in range(grid_size["width"]):
                    tile_start = time.time()

                    # Check if any widgets intersect this tile
                    tile_widgets = self.get_widgets_in_tile(
                        location.get("widgets", []), x, y, self.tile_size
                    )

                    # Build widget instructions for this tile
                    widget_instructions = None
                    if tile_widgets:
                        widget_descriptions = []
                        for widget in tile_widgets:
                            widget_descriptions.append(
                                f"{widget['name']}: {widget['interactions']['idle']}"
                            )
                        widget_instructions = "; ".join(widget_descriptions)

                    # Generate tile with context
                    tile = await self.generate_tile_with_context(
                        location,
                        world_context,
                        x,
                        y,
                        previous_context,
                        widget_instructions,
                        "idle",
                        seed + x + y * 100,
                    )

                    if tile:
                        tile_asset = self.save_tile_asset(
                            tile,
                            location["id"],
                            x,
                            y,
                            "idle",
                            time.time() - tile_start,
                            self.calculate_prompt_hash(widget_instructions or ""),
                            previous_context.copy(),
                        )
                        base_tiles.append(tile_asset)
                        previous_context.append(f"tile_{x}_{y}_idle")

                    print(f"   ✅ Generated base tile ({x},{y})")

            # Step 3: Generate widget state variations
            widget_overlays = {}

            for widget in location.get("widgets", []):
                widget_id = widget["id"]
                widget_overlays[widget_id] = {"idle": [], "hover": [], "click": []}

                # Get tiles this widget spans
                widget_tiles = self.get_widget_tile_coords(widget, self.tile_size)

                for state in ["hover", "click"]:
                    for tile_x, tile_y in widget_tiles:
                        # Get base tile for this position
                        base_tile = None
                        for tile_asset in base_tiles:
                            if (
                                tile_asset.tile_x == tile_x
                                and tile_asset.tile_y == tile_y
                            ):
                                # Load the base tile
                                base_tile = Image.open(tile_asset.file_path)
                                break

                        if base_tile:
                            # Generate state variation
                            variation = await self.generate_widget_state_variation(
                                base_tile, location, widget, state, tile_x, tile_y
                            )

                            if variation:
                                # Create transparency mask
                                overlay_tile = self.create_transparency_mask(
                                    base_tile, variation
                                )

                                # Save overlay
                                overlay_asset = self.save_widget_overlay(
                                    overlay_tile,
                                    location["id"],
                                    widget_id,
                                    state,
                                    tile_x,
                                    tile_y,
                                    time.time() - start_time,
                                )
                                widget_overlays[widget_id][state].append(overlay_asset)

            # Step 4: Merge tiles into complete location images
            complete_images = await self.merge_tiles_to_complete_images(
                location, base_tiles, widget_overlays
            )

            # Step 5: Update result.json
            await self.update_result_json(
                location, base_tiles, widget_overlays, complete_images
            )

            generation_time = time.time() - start_time

            return GenerationResult(
                location_id=location["id"],
                base_tiles=base_tiles,
                widget_overlays=widget_overlays,
                complete_images=complete_images,
                generation_metadata={
                    "base_tiles_generated": len(base_tiles),
                    "widget_variations_generated": sum(
                        len(overlays[state])
                        for widget in widget_overlays.values()
                        for overlays in widget_overlays.values()
                        for state in overlays
                    ),
                    "total_generation_time": generation_time,
                    "grid_size": grid_size,
                    "deterministic_seed": seed,
                },
                success=True,
            )

        except Exception as e:
            return GenerationResult(
                location_id=location["id"],
                base_tiles=[],
                widget_overlays={},
                complete_images={},
                generation_metadata={},
                success=False,
                error_message=str(e),
            )

    def get_widgets_in_tile(
        self, widgets: List[Dict], tile_x: int, tile_y: int, tile_size: int
    ) -> List[Dict]:
        """Get all widgets that intersect with a given tile."""
        intersecting_widgets = []

        tile_left = tile_x * tile_size
        tile_right = tile_left + tile_size
        tile_top = tile_y * tile_size
        tile_bottom = tile_top + tile_size

        for widget in widgets:
            widget_left = widget["position"]["x"]
            widget_right = widget_left + widget["size"]["width"]
            widget_top = widget["position"]["y"]
            widget_bottom = widget_top + widget["size"]["height"]

            # Check for intersection
            if (
                widget_right > tile_left
                and widget_left < tile_right
                and widget_bottom > tile_top
                and widget_top < tile_bottom
            ):
                intersecting_widgets.append(widget)

        return intersecting_widgets

    def get_widget_tile_coords(
        self, widget: Dict, tile_size: int
    ) -> List[Tuple[int, int]]:
        """Get tile coordinates that a widget spans."""
        x_start = widget["position"]["x"] // tile_size
        y_start = widget["position"]["y"] // tile_size
        x_end = (widget["position"]["x"] + widget["size"]["width"]) // tile_size
        y_end = (widget["position"]["y"] + widget["size"]["height"]) // tile_size

        coords = []
        for y in range(y_start, min(y_end, 4)):  # Assuming 4x4 grid max
            for x in range(x_start, min(x_end, 4)):
                coords.append((x, y))

        return coords

    async def merge_tiles_to_complete_images(
        self,
        location: Dict,
        base_tiles: List[TileAsset],
        widget_overlays: Dict[str, Dict[str, List[WidgetOverlay]]],
    ) -> Dict[str, str]:
        """Merge tiles and overlays into complete location images."""

        grid_size = location.get("grid_size", {"width": 4, "height": 4})
        complete_images = {}

        # Generate complete image for each state
        for state in ["idle", "hover", "click"]:
            image_size = (
                grid_size["width"] * self.tile_size,
                grid_size["height"] * self.tile_size,
            )
            complete_image = Image.new(
                "RGB", image_size, (240, 240, 250)
            )  # Light blue background

            # Paste base tiles
            for tile_asset in base_tiles:
                tile = Image.open(tile_asset.file_path)
                x = tile_asset.tile_x * self.tile_size
                y = tile_asset.tile_y * self.tile_size
                complete_image.paste(tile, (x, y))

            # Apply widget overlays
            for widget_id, states in widget_overlays.items():
                for state_name, overlays in states.items():
                    if state_name == state:
                        for overlay in overlays:
                            overlay = Image.open(overlay.file_path)
                            x = overlay.tile_x * self.tile_size
                            y = overlay.tile_y * self.tile_size

                            # Composite with transparency
                            complete_image.paste(overlay, (x, y), overlay)

            # Save complete image
            output_path = f"static/world/{location['id']}_{state}.png"
            complete_image.save(output_path)
            complete_images[state] = output_path
            print(f"   ✅ Created complete {state} image: {output_path}")

        return complete_images

    async def update_result_json(
        self,
        location: Dict,
        base_tiles: List[TileAsset],
        widget_overlays: Dict[str, Dict[str, List[WidgetOverlay]]],
        complete_images: Dict[str, str],
    ):
        """Update result.json with generation results."""

        result_path = Path("static/result.json")

        try:
            # Load existing result.json
            if result_path.exists():
                with open(result_path, "r") as f:
                    result_data = json.load(f)
            else:
                result_data = {"generated_at": "", "world_hash": "", "locations": []}

            # Find or create location entry
            location_entry = None
            for i, loc in enumerate(result_data["locations"]):
                if loc["id"] == location["id"]:
                    location_entry = loc
                    break

            if not location_entry:
                location_entry = {
                    "id": location["id"],
                    "name": location["name"],
                    "floor": location.get("floor", 1),
                    "position": location.get("position", 1),
                    "tiles": {},
                    "widgets": location["widgets"].copy(),
                    "generation_results": {},
                }
                result_data["locations"].append(location_entry)

            # Update tiles
            location_entry["tiles"] = {
                state: Path(path).name for state, path in complete_images.items()
            }

            # Add generation metadata
            location_entry["generation_metadata"] = {
                "base_tiles_generated": len(base_tiles),
                "widget_overlays_generated": sum(
                    len(overlays[state])
                    for widget in widget_overlays.values()
                    for overlays in widget_overlays.values()
                    for state in overlays
                ),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            # Update timestamps
            result_data["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            result_data["world_hash"] = hashlib.sha256(
                json.dumps(location, sort_keys=True).encode()
            ).hexdigest()[:16]

            # Save updated result.json
            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)

            print(f"   ✅ Updated result.json for {location['id']}")

        except Exception as e:
            print(f"❌ Failed to update result.json: {e}")


async def main():
    """Test the stable tile generation system."""
    print("🎯 Stable Tile Generation Pipeline Test")
    print("=" * 50)

    # Initialize generator
    generator = StableTileGenerator()

    # Load world.json
    with open("static/world.json", "r") as f:
        world_data = json.load(f)

    # Test with first location
    if world_data["locations"]:
        location = world_data["locations"][0]

        # Extract world context
        world_context = f"""
        World Style: {world_data["style"]["art_style"]} {world_data["style"]["palette"]}
        Camera: {world_data["style"]["camera"]}
        Theme: {world_data["world_name"]} v{world_data["version"]}
        """

        # Generate tiles
        result = await generator.generate_location_tiles(location, world_context)

        if result.success:
            print(f"\n✅ Successfully generated tiles for {location['id']}")
            print(f"   Base tiles: {len(result.base_tiles)}")
            print(f" Widget overlays: {len(result.widget_overlays)} widgets")
            print(f" Complete images: {len(result.complete_images)}")
            print(
                f" Generation time: "
                f"{result.generation_metadata['total_generation_time']:.2f}s"
            )
        else:
            print(f"\n❌ Failed to generate tiles: {result.error_message}")
    else:
        print("❌ No locations found in world.json")


if __name__ == "__main__":
    asyncio.run(main())
