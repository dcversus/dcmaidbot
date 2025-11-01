#!/usr/bin/env python3
"""
World Builder v2 - Production Implementation
============================================

Reads static/world.json and generates:
- static/world/*.png (all tiles)
- static/result.json (metadata)

Deterministic: same world.json = same output
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict

import openai
from dotenv import load_dotenv

# Import our new ImageCompositionManager
from image_composition_manager import ImageCompositionManager

load_dotenv()

# Paths
WORLD_JSON = Path("static/world.json")
RESULT_JSON = Path("static/result.json")
WORLD_TILES_DIR = Path("static/world")
WORLD_TILES_DIR.mkdir(parents=True, exist_ok=True)

# APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


class WorldBuilder:
    """Build world from JSON definition."""

    def __init__(self):
        """Load world.json."""
        with open(WORLD_JSON) as f:
            self.world = json.load(f)

        self.results = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "world_hash": self._hash_world(),
            "locations": [],
        }

        # Initialize ImageCompositionManager for advanced tile generation
        self.composition_manager = ImageCompositionManager()
        print("🎨 ImageCompositionManager initialized")

    def _hash_world(self) -> str:
        """Create hash of entire world definition."""
        world_str = json.dumps(self.world, sort_keys=True)
        return hashlib.sha256(world_str.encode()).hexdigest()[:16]

    def _hash_location(self, location: Dict) -> str:
        """Create hash of single location."""
        loc_str = json.dumps(location, sort_keys=True)
        return hashlib.sha256(loc_str.encode()).hexdigest()[:16]

    def _get_seed(self, location_id: str, floor: int, position: int) -> int:
        """Deterministic seed from location identity."""
        seed_str = f"{location_id}_{floor}_{position}"
        return int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

    async def build_world(self):
        """Generate all locations."""
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 20 + "WORLD BUILDER v2" + " " * 32 + "║")
        print("╚" + "=" * 68 + "╝\n")

        print(f"World: {self.world['world_name']}")
        print(f"Style: {self.world['style']['art_style']}")
        print(f"Locations: {len(self.world['locations'])}\n")

        for location in self.world["locations"]:
            await self.generate_location(location)

        # Save result.json
        with open(RESULT_JSON, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Result saved: {RESULT_JSON}")
        print("\n🎉 WORLD BUILD COMPLETE!")

    async def generate_location(self, location: Dict):
        """Generate tiles for one location using ImageCompositionManager."""
        loc_id = location["id"]
        seed = self._get_seed(loc_id, location["floor"], location["position"])

        print(f"\n{'=' * 70}")
        print(f"LOCATION: {location['name']} (floor {location['floor']})")
        print(f"Seed: {seed}")
        print(f"{'=' * 70}\n")

        print("🎨 Generating composites with ImageCompositionManager...")

        try:
            # Generate all states (idle, hover, click) using composition manager
            tiles = {}

            print("  📋 Generating idle state...")
            idle_path = await self.composition_manager.create_composite_tile(
                location, "idle"
            )
            tiles["idle"] = f"world/{loc_id}_idle.png"

            print("  📋 Generating hover state...")
            hover_path = await self.composition_manager.create_composite_tile(
                location, "hover"
            )
            tiles["hover"] = f"world/{loc_id}_hover.png"

            print("  📋 Generating click state...")
            click_path = await self.composition_manager.create_composite_tile(
                location, "click"
            )
            tiles["click"] = f"world/{loc_id}_click.png"

            print(f"✅ All states generated for {location['name']}")

            # Add to results with all tile states
            self.results["locations"].append(
                {
                    "id": loc_id,
                    "name": location["name"],
                    "floor": location["floor"],
                    "position": location["position"],
                    "tiles": tiles,
                    "generation_seed": seed,
                    "generation_method": "image_composition_manager",
                    "widgets": location.get("widgets", []),
                    "tile_metadata": {
                        "states": ["idle", "hover", "click"],
                        "composite_size": "1024x1024",
                        "widget_count": len(location.get("widgets", [])),
                    },
                }
            )

        except Exception as e:
            print(f"❌ Error generating composites: {e}")
            import traceback

            traceback.print_exc()

    def _build_location_prompt(self, location: Dict) -> str:
        """Build generation prompt from location definition."""

        style = self.world["style"]
        prompt = f"{style['art_style']} style, {style['camera']} view, "
        prompt += f"{location['description']}, "

        # Add connections
        for conn in location.get("connections", []):
            prompt += f"{conn['type']} at {conn['from_side']} edge, "

        # Add widgets
        widget_desc = []
        for widget in location.get("widgets", []):
            widget_desc.append(widget["description"])

        if widget_desc:
            prompt += f"includes: {', '.join(widget_desc)}, "

        prompt += "retro lofi kawaii aesthetic, pastel colors, 1024x1024"

        return prompt


async def main():
    """Run world builder."""
    builder = WorldBuilder()
    await builder.build_world()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
