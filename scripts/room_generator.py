#!/usr/bin/env python3
"""
PRP-016 Room Generator - Production Pipeline
============================================

Generates pixel art rooms with GPT-4V validation and tile extraction.

WORKFLOW:
1. Generate pixel art room with widgets (Leonardo AI)
2. Analyze with GPT-4V to validate widgets present
3. Generate hover variation (complete room)
4. Generate click variation (complete room)
5. Cut all 3 into 2x2 tiles
6. Save JSON configuration

Uses:
- Leonardo AI MCP (via API)
- OpenAI GPT-4V (for validation)
- PIL (for tile cutting)
"""

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import openai
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# API Configuration
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LEONARDO_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
}

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Output
OUTPUT_BASE = Path("static/generated_rooms")
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)


def generate_room(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate room using Leonardo AI and return image URL."""

    print("🎨 Generating room...")
    print(f"   Prompt: {prompt[:80]}...")

    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_images": 1,
    }

    r = requests.post(
        f"{LEONARDO_BASE_URL}/generations",
        headers=LEONARDO_HEADERS,
        json=payload,
        timeout=30,
    )

    if r.status_code != 200:
        raise Exception(f"Generation failed: {r.text}")

    gen_id = r.json()["sdGenerationJob"]["generationId"]
    print(f"   Generation ID: {gen_id}")

    # Poll
    for i in range(60):
        time.sleep(3)
        s = requests.get(
            f"{LEONARDO_BASE_URL}/generations/{gen_id}", headers=LEONARDO_HEADERS
        )

        if s.status_code == 200:
            g = s.json().get("generations_by_pk", {})
            if g.get("status") == "COMPLETE":
                url = g["generated_images"][0]["url"]
                print("   ✅ Complete!")
                return url

            print(f"   [{i + 1}/60] {g.get('status', 'PENDING')}")

    raise Exception("Timeout")


def validate_with_gpt4v(image_path: Path, expected_widgets: List[str]) -> Dict:
    """Use GPT-4V to validate widgets are present."""

    print("\n🔍 Validating with GPT-4 Vision...")

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this pixel art room image.

Expected widgets: {expected_widgets}

For each widget, confirm if present and estimate position (top-left, top-right, bottom-left, bottom-right, or center).

Return JSON:
{{
  "widgets_found": [
    {{"name": "clock", "present": true, "position": "top-left"}},
    ...
  ],
  "overall_quality": "description",
  "camera_angle": "description"
}}""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    content = response.choices[0].message.content
    print(f"   GPT-4V Response:\n{content}\n")

    # Try to parse JSON
    import re

    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())

    return {"raw_response": content}


def cut_into_tiles(image_path: Path, output_dir: Path, prefix: str) -> List[Path]:
    """Cut 1024x1024 image into 2x2 grid of 512x512 tiles."""

    print("\n✂️  Cutting into 2x2 tiles...")

    img = Image.open(image_path)
    tiles = []

    for row in range(2):
        for col in range(2):
            tile = img.crop((col * 512, row * 512, (col + 1) * 512, (row + 1) * 512))
            tile_path = output_dir / f"{prefix}_{row}_{col}.jpg"
            tile.save(tile_path, quality=95)
            tiles.append(tile_path)
            print(f"   ✅ Tile [{row},{col}]: {tile_path.name}")

    return tiles


def generate_room_with_variations(config: Dict[str, Any]) -> Dict:
    """
    Complete pipeline for one room.

    config format:
    {
        "name": "lilith_bedroom",
        "base_prompt": "16-bit pixel art bedroom...",
        "hover_addition": "clock glowing",
        "click_addition": "clock super glowing",
        "expected_widgets": ["clock", "bed", "desk", "bookshelf"]
    }
    """

    room_name = config["name"]
    output_dir = OUTPUT_BASE / room_name
    output_dir.mkdir(exist_ok=True)

    print(f"\n{'=' * 70}")
    print(f"GENERATING ROOM: {room_name}")
    print(f"{'=' * 70}\n")

    results = {
        "room_name": room_name,
        "states": {},
        "tiles": {},
    }

    # Generate 3 states
    for state in ["idle", "hover", "click"]:
        print(f"\n--- STATE: {state.upper()} ---")

        if state == "idle":
            prompt = config["base_prompt"]
        elif state == "hover":
            prompt = config["base_prompt"] + f", {config['hover_addition']}"
        else:  # click
            prompt = config["base_prompt"] + f", {config['click_addition']}"

        # Generate
        url = generate_room(prompt)

        # Download
        img_data = requests.get(url, timeout=60).content
        room_path = output_dir / f"room_{state}.jpg"
        room_path.write_bytes(img_data)
        print(f"   💾 Saved: {room_path}")

        # Validate with GPT-4V (only for idle)
        if state == "idle":
            validation = validate_with_gpt4v(room_path, config["expected_widgets"])
            results["validation"] = validation

        # Cut into tiles
        tiles = cut_into_tiles(room_path, output_dir, f"tile_{state}")

        results["states"][state] = str(room_path)
        results["tiles"][state] = [str(t) for t in tiles]

    # Save JSON
    json_path = output_dir / "room_data.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Configuration saved: {json_path}")
    print(f"\n🎉 ROOM COMPLETE: {room_name}")
    print("   States: 3 (idle, hover, click)")
    print("   Tiles: 12 (2x2 × 3)")

    return results


# Example room configurations
LILITH_ROOM = {
    "name": "lilith_bedroom",
    "base_prompt": "16-bit pixel art teenage bedroom, perfect top-down view like SNES RPG, desk with pink clock top-left, window with small cactus top-right, colorful bookshelf bottom-left, cozy bed with plushies bottom-right, purple gradient rug in center, wooden floor, pastel pink purple blue colors, retro game aesthetic, lofi kawaii pixel art, organized cute space, 1024x1024",
    "hover_addition": "clock GLOWING with soft pink aura and sparkles",
    "click_addition": "clock SUPER GLOWING with bright pink magical aura, many sparkles",
    "expected_widgets": ["clock", "cactus", "bookshelf", "bed", "rug"],
}

GARDEN_ROOM = {
    "name": "garden",
    "base_prompt": "16-bit pixel art garden top-down view like SNES RPG, 2x2 vegetable beds layout, top-left tomato plants, top-right strawberry patch, bottom-left watermelon vines, bottom-right mandarin tree, brown soil, green grass borders, garden tools, retro game aesthetic, lofi pixel art, organized farm layout, 1024x1024",
    "hover_addition": "tomato plants glowing with healthy green aura",
    "click_addition": "tomatoes RIPE and glowing bright red, ready to harvest",
    "expected_widgets": ["tomatoes", "strawberries", "watermelon", "mandarin"],
}


def main():
    """Generate both rooms."""

    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "ROOM GENERATOR PIPELINE" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")

    # Generate Lilith's room
    lilith_results = generate_room_with_variations(LILITH_ROOM)

    # Generate Garden
    garden_results = generate_room_with_variations(GARDEN_ROOM)

    print("\n" + "=" * 70)
    print("🎉 ALL ROOMS GENERATED!")
    print("=" * 70)
    print(f"\nOutput: {OUTPUT_BASE}")
    print(f"- Lilith: {len(lilith_results['tiles']['idle'])} tiles × 3 states")
    print(f"- Garden: {len(garden_results['tiles']['idle'])} tiles × 3 states")


if __name__ == "__main__":
    main()
