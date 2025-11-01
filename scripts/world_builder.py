"""
Deterministic World Builder for PRP-016 Multi-Room Interactive House Exploration

This module implements the core pipeline for generating deterministic tile-based
worlds with AI-powered asset generation and content-addressed caching.

Key Features:
- Deterministic seed-based generation
- Content-addressed caching system
- Multi-provider AI service fallback
- Pixel-perfect mask generation for widget overlays
"""

import json
import logging
import hashlib
import os
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path

from scripts.providers import (
    pick_provider,
    stable_hash,
    content_key,
    load_json,
    save_json,
    ensure_dir
)

logger = logging.getLogger(__name__)


class WorldBuilder:
    """Deterministic world builder with AI-powered asset generation."""

    def __init__(self, config_path: str = "static/world.json"):
        """Initialize world builder with configuration.

        Args:
            config_path: Path to world configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.cache_db = load_json("static/cache/hashes.json", {"cache_entries": {}})
        self.stats = {
            "generated_images": 0,
            "cache_hits": 0,
            "errors": 0
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load world configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load world config from {self.config_path}: {e}")
            raise

    def _cells_to_px(self, cells: List[List[int]], tile: int) -> Tuple[int, int, int, int]:
        """Convert grid cells to pixel coordinates.

        Args:
            cells: List of [x, y] grid cell coordinates
            tile: Tile size in pixels

        Returns:
            Tuple of (x, y, width, height) in pixels
        """
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        return x0 * tile, y0 * tile, (x1 - x0 + 1) * tile, (y1 - y0 + 1) * tile

    def _make_mask_cells(self, grid_cells: List[List[int]], tile: int,
                        canvas_size: Tuple[int, int], out: str) -> None:
        """Generate pixel-perfect mask for grid cells.

        Args:
            grid_cells: List of [x, y] grid cell coordinates
            tile: Tile size in pixels
            canvas_size: Tuple of (width, height) for canvas
            out: Output path for mask PNG
        """
        try:
            from PIL import Image, ImageDraw

            W, H = canvas_size
            # Create black canvas
            mask = Image.new('L', (W, H), 0)
            draw = ImageDraw.Draw(mask)

            # Draw white rectangles for each cell
            for cell in grid_cells:
                x, y = cell
                draw.rectangle([x * tile, y * tile, (x + 1) * tile, (y + 1) * tile],
                             fill=255)

            # Ensure directory exists
            ensure_dir(str(Path(out).parent))
            mask.save(out)
            logger.info(f"Generated mask: {out}")

        except Exception as e:
            logger.error(f"Failed to generate mask {out}: {e}")
            raise

    def _make_mask_full(self, w: int, h: int, out: str) -> None:
        """Generate full-canvas white mask.

        Args:
            w: Width in pixels
            h: Height in pixels
            out: Output path for mask PNG
        """
        try:
            from PIL import Image

            mask = Image.new('L', (w, h), 255)
            ensure_dir(str(Path(out).parent))
            mask.save(out)
            logger.info(f"Generated full mask: {out}")

        except Exception as e:
            logger.error(f"Failed to generate full mask {out}: {e}")
            raise

    async def _generate_base_scene(self, floor: Dict, location: Dict) -> str:
        """Generate base scene for a location.

        Args:
            floor: Floor configuration
            location: Location configuration

        Returns:
            Path to generated base image
        """
        try:
            # Extract configuration
            defaults = self.config["render"]["defaults"]
            base_seed = defaults["seed"]
            steps = defaults["steps"]
            cfg_scale = defaults["cfg"]
            provider_priority = self.config["render"]["provider_priority"]

            # Calculate deterministic parameters
            tile = self.config["style"]["tile_size"]
            cols = location["bounds"]["cols"]
            rows = location["bounds"]["rows"]
            W, H = cols * tile, rows * tile

            # Generate deterministic seed
            loc_seed = base_seed + floor.get("seed_offset", 0) + stable_hash(location["id"])
            base_prompt = location["description_prompt"]

            # Generate cache key
            cache_key = content_key(
                "base",
                self.config["world_name"],
                floor["id"],
                location["id"],
                base_prompt,
                loc_seed,
                W, H,
                steps,
                cfg_scale
            )

            # Check cache
            if cache_hit(self.cache_db["cache_entries"], cache_key):
                self.stats["cache_hits"] += 1
                cached_path = self.cache_db["cache_entries"][cache_key]["path"]
                logger.info(f"Cache hit for base scene: {cached_path}")
                return cached_path

            # Generate new image
            out_dir = f"static/output/floors/{floor['id']}/{location['id']}"
            ensure_dir(out_dir)
            base_path = f"{out_dir}/base.png"

            provider = pick_provider("txt2img", provider_priority)
            generated_path = await provider.txt2img(
                prompt=base_prompt,
                size=(W, H),
                seed=loc_seed,
                steps=steps,
                cfg=cfg_scale,
                outfile=base_path
            )

            # Update cache
            cache_put(self.cache_db["cache_entries"], cache_key, generated_path, {
                "prompt": base_prompt,
                "seed": loc_seed,
                "size": (W, H),
                "provider": provider.get_provider_name()
            })

            self.stats["generated_images"] += 1
            logger.info(f"Generated base scene: {generated_path}")
            return generated_path

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to generate base scene for {location['id']}: {e}")
            raise

    async def _generate_widget_overlays(self, floor: Dict, location: Dict, base_path: str) -> List[Dict]:
        """Generate overlay images for all widgets in a location.

        Args:
            floor: Floor configuration
            location: Location configuration
            base_path: Path to base scene image

        Returns:
            List of widget metadata with overlay information
        """
        try:
            widget_data = []
            defaults = self.config["render"]["defaults"]
            base_seed = defaults["seed"]
            steps = defaults["steps"]
            cfg_scale = defaults["cfg"]
            provider_priority = self.config["render"]["provider_priority"]
            tile = self.config["style"]["tile_size"]

            out_dir = f"static/output/floors/{floor['id']}/{location['id']}/overlays"
            ensure_dir(out_dir)

            for widget in location.get("widgets", []):
                widget_entry = {"id": widget["id"], "states": []}
                grid = widget["grid"]  # x, y, w, h in cells

                # Calculate all cells for this widget
                cells = [[grid["x"] + dx, grid["y"] + dy]
                        for dy in range(grid["h"])
                        for dx in range(grid["w"])]

                # Default region if state doesn't specify one
                default_region = {"mode": "cells", "cells": cells}

                for state in widget.get("states", []):
                    state_name = state["state"]
                    region = state.get("region", default_region)
                    prompt = state.get("prompt", widget.get("prompt_base", ""))
                    seed = base_seed + floor.get("seed_offset", 0) + stable_hash(f"{location['id']}|{widget['id']}|{state_name}")

                    out_name = f"{widget['id']}__{state_name}.png"
                    out_path = f"{out_dir}/{out_name}"

                    # Generate cache key
                    if region["mode"] == "full":
                        # Full canvas replacement
                        cols = location["bounds"]["cols"]
                        rows = location["bounds"]["rows"]
                        W, H = cols * tile, rows * tile

                        cache_key = content_key(
                            "full", floor["id"], location["id"], widget["id"],
                            state_name, prompt, seed, W, H, steps, cfg_scale
                        )

                        if cache_hit(self.cache_db["cache_entries"], cache_key):
                            self.stats["cache_hits"] += 1
                            cached_path = self.cache_db["cache_entries"][cache_key]["path"]
                            bbox = [0, 0, W, H]
                        else:
                            # Generate new full image
                            provider = pick_provider("txt2img", provider_priority)
                            generated_path = await provider.txt2img(
                                prompt=prompt, size=(W, H), seed=seed,
                                steps=steps, cfg=cfg_scale, outfile=out_path
                            )

                            cache_put(self.cache_db["cache_entries"], cache_key, generated_path, {
                                "prompt": prompt, "seed": seed, "size": (W, H),
                                "provider": provider.get_provider_name()
                            })

                            self.stats["generated_images"] += 1
                            bbox = [0, 0, W, H]

                    else:
                        # Region-based inpainting
                        mask_path = f"static/cache/widgets/{floor['id']}__{location['id']}__{widget['id']}__{state_name}.mask.png"
                        self._make_mask_cells(region["cells"], tile,
                                          (location["bounds"]["cols"] * tile, location["bounds"]["rows"] * tile),
                                          mask_path)

                        # Calculate bounding box
                        x, y, w, h = self._cells_to_px(region["cells"], tile)
                        bbox = [x, y, w, h]

                        cache_key = content_key(
                            "inpaint", floor["id"], location["id"], widget["id"],
                            state_name, prompt, seed,
                            (location["bounds"]["cols"] * tile, location["bounds"]["rows"] * tile),
                            steps, cfg_scale, open(mask_path, 'rb').read()
                        )

                        if cache_hit(self.cache_db["cache_entries"], cache_key):
                            self.stats["cache_hits"] += 1
                            cached_path = self.cache_db["cache_entries"][cache_key]["path"]
                        else:
                            # Generate inpainted image
                            provider = pick_provider("inpaint", provider_priority)
                            generated_path = await provider.inpaint(
                                base_path=base_path, mask_path=mask_path, prompt=prompt,
                                seed=seed, steps=steps, cfg=cfg_scale, outfile=out_path
                            )

                            cache_put(self.cache_db["cache_entries"], cache_key, generated_path, {
                                "prompt": prompt, "seed": seed, "base_path": base_path,
                                "mask_path": mask_path, "provider": provider.get_provider_name()
                            })

                            self.stats["generated_images"] += 1

                    # Add state metadata
                    widget_entry["states"].append({
                        "state": state_name,
                        "overlay": f"overlays/{out_name}",
                        "bbox": bbox,
                        "render_text": state.get("render_text"),
                        "region": region
                    })

                widget_data.append(widget_entry)

            return widget_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to generate widget overlays for {location['id']}: {e}")
            raise

    async def generate_world(self) -> Dict[str, Any]:
        """Generate the complete world with all floors and locations.

        Returns:
            Generation statistics and metadata
        """
        try:
            logger.info(f"Starting world generation for {self.config['world_name']}")

            for floor in self.config["floors"]:
                logger.info(f"Processing floor: {floor['name']}")

                for location in floor["locations"]:
                    logger.info(f"Generating location: {location['name']}")

                    # Generate base scene
                    base_path = await self._generate_base_scene(floor, location)

                    # Generate widget overlays
                    widget_data = await self._generate_widget_overlays(floor, location, base_path)

                    # Create location metadata
                    tile = self.config["style"]["tile_size"]
                    meta = {
                        "W": location["bounds"]["cols"] * tile,
                        "H": location["bounds"]["rows"] * tile,
                        "tile": tile,
                        "widgets": widget_data,
                        "base_image": "base.png",
                        "world_name": self.config["world_name"],
                        "floor_name": floor["name"],
                        "location_name": location["name"],
                        "generated_at": str(Path().resolve())
                    }

                    # Save metadata
                    out_dir = f"static/output/floors/{floor['id']}/{location['id']}"
                    meta_path = f"{out_dir}/map.meta.json"
                    save_json(meta_path, meta)

                    logger.info(f"Completed location: {location['name']}")

            # Save updated cache
            self._save_cache()

            # Log final statistics
            logger.info(f"World generation complete!")
            logger.info(f"Images generated: {self.stats['generated_images']}")
            logger.info(f"Cache hits: {self.stats['cache_hits']}")
            logger.info(f"Errors: {self.stats['errors']}")

            return {
                "success": True,
                "stats": self.stats,
                "world_name": self.config["world_name"],
                "floors_processed": len(self.config["floors"]),
                "locations_processed": sum(len(f["locations"]) for f in self.config["floors"])
            }

        except Exception as e:
            logger.error(f"World generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats
            }

    def _save_cache(self) -> None:
        """Save updated cache database."""
        # Update statistics
        self.cache_db["statistics"]["total_entries"] = len(self.cache_db["cache_entries"])
        self.cache_db["statistics"]["cache_hits"] = self.stats["cache_hits"]
        self.cache_db["statistics"]["cache_misses"] = self.stats["generated_images"]

        save_json("static/cache/hashes.json", self.cache_db)


# Utility functions moved from providers.py for compatibility
def cache_hit(cache_db: Dict, key: str) -> bool:
    """Check if cache key exists and file is present."""
    return key in cache_db and os.path.exists(cache_db[key]["path"])


def cache_put(cache_db: Dict, key: str, path: str, meta: Dict) -> None:
    """Add entry to cache database."""
    cache_db[key] = {"path": path, "meta": meta}


async def main():
    """Main entry point for world generation."""
    import asyncio

    logging.basicConfig(level=logging.INFO)

    builder = WorldBuilder()
    result = await builder.generate_world()

    if result["success"]:
        print(f"✅ {result['world_name']} generated successfully!")
        print(f"📊 Processed {result['floors_processed']} floors, {result['locations_processed']} locations")
        print(f"🖼️  Generated {result['stats']['generated_images']} new images")
        print(f"💾 Cache hits: {result['stats']['cache_hits']}")
    else:
        print(f"❌ Generation failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())