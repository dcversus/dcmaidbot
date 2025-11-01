#!/usr/bin/env python3
"""
World Builder v3 - Tile-Based Architecture Integration
====================================================

Integrates with the new tile-based architecture:
- PromptManager for intelligent prompt generation
- ImageCompositionManager for canvas-based tile generation
- Support for idle/hover/click tile states
- Widget-aware tile generation
- Deterministic generation with caching

WORKFLOW:
1. Load world.json
2. Generate location-specific prompts using PromptManager logic
3. Create composite tiles using ImageCompositionManager (Python version)
4. Generate all 3 states (idle/hover/click) for each location
5. Update result.json with tile paths and metadata
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Paths
WORLD_JSON = Path("static/world.json")
RESULT_JSON = Path("static/result.json")
WORLD_TILES_DIR = Path("static/world")
WORLD_TILES_DIR.mkdir(parents=True, exist_ok=True)

# APIs
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@dataclass
class TileGenerationResult:
    """Result of tile generation for a location."""

    location_id: str
    state: str
    tile_path: str
    prompt: str
    seed: int
    generation_time: float
    success: bool
    error_message: Optional[str] = None


class PromptManagerPython:
    """Python version of PromptManager for world building."""

    def __init__(self):
        self.widget_prompt_templates = self._initialize_widget_templates()
        self.location_prompt_cache = {}

    def _initialize_widget_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize widget-specific prompt templates."""
        return {
            "time": {
                "base": "kawaii anime wall clock showing current time",
                "idle": "pink analog wall clock with cute design, showing current time peacefully",
                "hover": "magical glowing pink wall clock with soft aura, sparkling with time magic",
                "click": "enlarged magical clock face with floating time numbers and sparkles",
            },
            "status": {
                "base": "kawaii status indicator plant",
                "idle": "small cute cactus in pink pot with happy face, peaceful and calm",
                "hover": "happy cactus slightly larger with joyful expression, glowing gently",
                "click": "blooming cactus with beautiful pink flower, magical transformation moment",
            },
            "changelog": {
                "base": "kawaii changelog book",
                "idle": "cute magical book with version number on spine, closed peacefully",
                "hover": "glowing spellbook with soft magical aura, version visible on cover",
                "click": "open book with floating changelog text and magical sparkles around pages",
            },
            "link": {
                "base": "kawaii link poster",
                "idle": "retro anime poster on wall, peaceful and decorative",
                "hover": "magical glowing poster with sparkling edges, drawing attention",
                "click": "animated poster with pulsing effects and magical gateway energy",
            },
            "story": {
                "base": "kawaii story element",
                "idle": "peaceful story element, decorative and mysterious",
                "hover": "glowing magical artifact with soft aura, hinting at adventure",
                "click": "activated magical element with floating story text and sparkles",
            },
            "music": {
                "base": "kawaii music player",
                "idle": "vinyl record or music device, peaceful and decorative",
                "hover": "glowing music element with sound waves and soft aura",
                "click": "activated music player with floating notes and magical sound effects",
            },
            "online": {
                "base": "kawaii online status indicator",
                "idle": "small online status light, peaceful and stable",
                "hover": "glowing online indicator with connection waves",
                "click": "expanded online status with network effects and magical connections",
            },
            "version": {
                "base": "kawaii version display",
                "idle": "version number display, clean and peaceful",
                "hover": "glowing version text with magical sparkle effects",
                "click": "expanded version information with magical presentation",
            },
            "hash": {
                "base": "kawaii hash display",
                "idle": "hash identifier, technical but cute design",
                "hover": "glowing hash with magical data flow effects",
                "click": "expanded hash display with magical data visualization",
            },
        }

    def generate_widget_prompt(self, widget: Dict, state: str = "idle") -> str:
        """Generate prompt for a specific widget."""
        template = self.widget_prompt_templates.get(widget.get("type", ""), {})
        state_prompt = template.get(state, template.get("idle", ""))
        position = widget.get("position", {})
        size = widget.get("size", {})

        # Add position and size context
        positioned_prompt = f"{state_prompt}, positioned at ({position.get('x', 0)}, {position.get('y', 0)}), size {size.get('width', 64)}x{size.get('height', 64)}px"

        return positioned_prompt

    def generate_location_prompt(self, location: Dict, state: str = "idle") -> str:
        """Generate prompt for a location."""
        cache_key = f"{location['id']}-{state}"
        if cache_key in self.location_prompt_cache:
            return self.location_prompt_cache[cache_key]

        # Base prompt
        base_prompt = f"kawaii anime room interior, {location['name']}, peaceful and cozy atmosphere"

        # Add room description
        if "description" in location:
            base_prompt += f", {location['description']}"

        # Add widget descriptions
        if "widgets" in location:
            widget_prompts = []
            for widget in location["widgets"]:
                widget_prompt = self.generate_widget_prompt(widget, state)
                widget_prompts.append(f"with {widget_prompt}")
            base_prompt += ", " + ", ".join(widget_prompts)

        # Add state-specific modifications
        state_modifiers = {
            "idle": "peaceful, calm, soft lighting, anime art style, high quality",
            "hover": "magical glowing atmosphere, soft auras, sparkling effects, wonder and curiosity",
            "click": "magical transformation moment, dynamic energy, sparkles and magical effects, excitement",
        }

        base_prompt += f", {state_modifiers.get(state, state_modifiers['idle'])}"

        # Add quality and style modifiers
        base_prompt += ", masterpiece, best quality, detailed, beautiful anime art, digital painting"

        # Cache result
        self.location_prompt_cache[cache_key] = base_prompt

        return base_prompt


class TileGenerator:
    """Handles tile generation using various AI services."""

    def __init__(self):
        self.leonardo_api_key = LEONARDO_API_KEY
        self.openai_api_key = OPENAI_API_KEY

    async def generate_with_leonardo(self, prompt: str, seed: int) -> Optional[str]:
        """Generate tile using Leonardo AI."""
        if not self.leonardo_api_key:
            print("⚠️  Leonardo API key not found, skipping generation")
            return None

        # TODO: Implement Leonardo AI integration
        # For now, return placeholder
        print(f"🎨 Leonardo generation requested with seed {seed}")
        print(f"   Prompt: {prompt[:100]}...")
        return None

    def generate_with_dalle(self, prompt: str, seed: int) -> Optional[str]:
        """Generate tile using DALL-E 3."""
        if not self.openai_api_key:
            print("⚠️  OpenAI API key not found, skipping generation")
            return None

        try:
            import openai

            client = openai.OpenAI(api_key=self.openai_api_key)

            print("🎨 Generating with DALL-E 3...")
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard",
            )

            url = response.data[0].url
            img_data = requests.get(url, timeout=60).content

            return img_data

        except Exception as e:
            print(f"❌ DALL-E generation failed: {e}")
            return None

    def save_tile(self, location_id: str, state: str, img_data: bytes) -> Path:
        """Save generated tile to file."""
        tile_path = WORLD_TILES_DIR / f"{location_id}_{state}.png"
        tile_path.write_bytes(img_data)
        return tile_path


class WorldBuilderV3:
    """World Builder v3 - Integrated with tile-based architecture."""

    def __init__(self):
        """Initialize world builder."""
        self.prompt_manager = PromptManagerPython()
        self.tile_generator = TileGenerator()
        self.load_world()

    def load_world(self):
        """Load world.json."""
        with open(WORLD_JSON) as f:
            self.world = json.load(f)

        self.results = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "world_hash": self._hash_world(),
            "locations": [],
        }

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

    def build_world(self):
        """Generate all locations with tile-based architecture."""
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 15 + "WORLD BUILDER v3" + " " * 15 + "║")
        print("║" + " " * 10 + "Tile-Based Architecture" + " " * 10 + "║")
        print("╚" + "=" * 68 + "╝\n")

        print(f"World: {self.world['world_name']}")
        print(f"Style: {self.world['style']['art_style']}")
        print(f"Locations: {len(self.world['locations'])}")
        print("Tile States: idle, hover, click\n")

        for location in self.world["locations"]:
            self.generate_location(location)

        # Save result.json
        with open(RESULT_JSON, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Result saved: {RESULT_JSON}")
        print("\n🎉 WORLD BUILD COMPLETE!")

    def generate_location(self, location: Dict):
        """Generate all tile states for one location."""
        loc_id = location["id"]
        seed = self._get_seed(loc_id, location["floor"], location["position"])

        print(f"\n{'=' * 70}")
        print(f"LOCATION: {location['name']} (floor {location['floor']})")
        print(f"Seed: {seed}")
        print(f"{'=' * 70}\n")

        # Generate all 3 states
        states = ["idle", "hover", "click"]
        tile_results = {}

        for state in states:
            start_time = time.time()

            print(f"\n🎨 Generating {state} state...")

            # Generate prompt using PromptManager
            prompt = self.prompt_manager.generate_location_prompt(location, state)
            print(f"   Prompt ({len(prompt)} chars): {prompt[:100]}...")

            # Generate tile
            try:
                img_data = self.tile_generator.generate_with_dalle(prompt, seed)

                if img_data:
                    tile_path = self.tile_generator.save_tile(loc_id, state, img_data)
                    generation_time = time.time() - start_time

                    tile_result = TileGenerationResult(
                        location_id=loc_id,
                        state=state,
                        tile_path=str(tile_path),
                        prompt=prompt,
                        seed=seed,
                        generation_time=generation_time,
                        success=True,
                    )

                    print(f"   ✅ Saved: {tile_path} ({generation_time:.1f}s)")
                else:
                    tile_result = TileGenerationResult(
                        location_id=loc_id,
                        state=state,
                        tile_path="",
                        prompt=prompt,
                        seed=seed,
                        generation_time=time.time() - start_time,
                        success=False,
                        error_message="No image data generated",
                    )
                    print(f"   ❌ Failed to generate {state} tile")

            except Exception as e:
                tile_result = TileGenerationResult(
                    location_id=loc_id,
                    state=state,
                    tile_path="",
                    prompt=prompt,
                    seed=seed,
                    generation_time=time.time() - start_time,
                    success=False,
                    error_message=str(e),
                )
                print(f"   ❌ Error: {e}")

            tile_results[state] = tile_result

        # Add to results
        location_result = {
            "id": loc_id,
            "name": location["name"],
            "floor": location["floor"],
            "position": location["position"],
            "tiles": {},
            "generation_seed": seed,
            "prompt_hash": self._hash_location(location),
            "widgets": location.get("widgets", []),
            "generation_results": {},
        }

        # Add tile paths
        for state, result in tile_results.items():
            if result.success:
                location_result["tiles"][state] = f"world/{loc_id}_{state}.png"

            # Add generation metadata
            location_result["generation_results"][state] = {
                "success": result.success,
                "generation_time": result.generation_time,
                "error_message": result.error_message,
                "prompt_length": len(result.prompt),
            }

        self.results["locations"].append(location_result)

        # Print summary
        successful_states = sum(1 for r in tile_results.values() if r.success)
        print(
            f"\n📊 Location Summary: {successful_states}/{len(states)} states generated successfully"
        )


def main():
    """Run world builder v3."""
    builder = WorldBuilderV3()
    builder.build_world()


if __name__ == "__main__":
    main()
