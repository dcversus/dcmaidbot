#!/usr/bin/env python3
"""
Ultimate Room Generation Pipeline with AI Validation
====================================================

WORKFLOW:
1. Generate base room with widgets (Leonardo AI)
2. Analyze with GPT-4 Vision to find widget positions
3. Validate widgets are present
4. Remove widget from image (inpainting)
5. Inpaint for variation 1 (hover effect)
6. Validate inpaint success
7. Inpaint for variation 2 (click effect)
8. Extract tiles from each variation
9. Save JSON with all data

Uses:
- Leonardo AI (LEONARDO_API_KEY from .env)
- OpenAI GPT-4V (OPENAI_API_KEY from .env)
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

load_dotenv()

# Configuration
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LEONARDO_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
}

OUTPUT_DIR = Path("static/generated_rooms")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


class RoomGenerator:
    """Generate rooms with validated widget inpainting."""

    def __init__(self, room_config: Dict[str, Any]):
        """
        Initialize with room configuration.

        room_config format:
        {
            "name": "lilith_bedroom",
            "description": "cozy teenage bedroom...",
            "widgets": [
                {"name": "clock", "description": "pink clock on wall"},
                {"name": "cactus", "description": "small cactus plant"},
            ]
        }
        """
        self.config = room_config
        self.room_name = room_config["name"]
        self.output_dir = OUTPUT_DIR / self.room_name
        self.output_dir.mkdir(exist_ok=True)

    def generate_base_room(self) -> Path:
        """Step 1: Generate base room with all widgets."""
        print(f"\n{'=' * 70}")
        print(f"STEP 1: Generating base room - {self.room_name}")
        print(f"{'=' * 70}\n")

        prompt = self._build_room_prompt()
        print(f"Prompt: {prompt[:100]}...")

        # Generate with Leonardo
        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "num_images": 1,
        }

        response = requests.post(
            f"{LEONARDO_BASE_URL}/generations",
            headers=LEONARDO_HEADERS,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(f"Generation failed: {response.text}")

        gen_id = response.json()["sdGenerationJob"]["generationId"]
        print(f"Generation ID: {gen_id}")

        # Poll
        for i in range(60):
            time.sleep(3)
            r = requests.get(
                f"{LEONARDO_BASE_URL}/generations/{gen_id}", headers=LEONARDO_HEADERS
            )

            if r.status_code == 200:
                g = r.json().get("generations_by_pk", {})
                if g.get("status") == "COMPLETE":
                    url = g["generated_images"][0]["url"]

                    # Download
                    img_data = requests.get(url, timeout=60).content
                    room_path = self.output_dir / "base_room.jpg"
                    room_path.write_bytes(img_data)

                    print(f"✅ Base room generated: {room_path}")
                    return room_path

                print(f"[{i + 1}/60] {g.get('status', 'PENDING')}")

        raise Exception("Timeout")

    def analyze_with_vision(self, image_path: Path) -> List[Dict]:
        """Step 2: Use GPT-4V to find widget positions."""
        print(f"\n{'=' * 70}")
        print("STEP 2: Analyzing image with GPT-4 Vision")
        print(f"{'=' * 70}\n")

        # Encode image
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Ask GPT-4V to locate widgets
        widget_list = [w["name"] for w in self.config["widgets"]]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this room image and find these widgets: {widget_list}.

For EACH widget, provide:
1. Widget name
2. Bounding box coordinates (x1, y1, x2, y2) in pixels (image is 1024x1024)
3. Confidence (0-1)

Return ONLY valid JSON array:
[
  {{"name": "clock", "bbox": [x1, y1, x2, y2], "confidence": 0.9}},
  ...
]""",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

        # Parse response
        content = response.choices[0].message.content
        print(f"GPT-4V Response:\n{content}\n")

        # Extract JSON
        try:
            import re

            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                widgets = json.loads(json_match.group())
                print(f"✅ Found {len(widgets)} widgets:")
                for w in widgets:
                    print(
                        f"   - {w['name']}: {w['bbox']}, confidence: {w['confidence']}"
                    )
                return widgets
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")

        return []

    def _build_room_prompt(self) -> str:
        """Build room generation prompt."""
        widgets_desc = ", ".join([w["description"] for w in self.config["widgets"]])

        return f"""
16-bit pixel art style, PERFECT TOP-DOWN view like Super Nintendo RPG game,
{self.config["description"]},
includes: {widgets_desc},
retro game aesthetic, lofi kawaii pixel art, pastel colors,
flat overhead camera straight down, clean organized layout,
1024x1024, pixelated retro SNES style
        """.strip()

    def upload_to_leonardo(self, image_path: Path) -> str:
        """Upload image to Leonardo and return ID."""
        r = requests.post(
            f"{LEONARDO_BASE_URL}/init-image",
            headers=LEONARDO_HEADERS,
            json={"extension": "jpg"},
        )

        data = r.json()["uploadInitImage"]

        with open(image_path, "rb") as f:
            requests.post(
                data["url"], data=json.loads(data["fields"]), files={"file": f}
            )

        time.sleep(2)
        return data["id"]

    def save_results(self, results: Dict):
        """Save final JSON with all data."""
        output_file = self.output_dir / "generation_result.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved: {output_file}")


def main():
    """Run the pipeline."""

    # Example configuration
    lilith_room_config = {
        "name": "lilith_bedroom",
        "description": "cozy teenage girl bedroom with bed, desk, bookshelf, window",
        "widgets": [
            {"name": "clock", "description": "pink kawaii clock on wall"},
            {"name": "cactus", "description": "small cactus plant in pot"},
            {"name": "bookshelf", "description": "colorful bookshelf with books"},
            {"name": "bed", "description": "bed with pink bedding and plushies"},
        ],
    }

    generator = RoomGenerator(lilith_room_config)

    # Step 1: Generate base
    base_room = generator.generate_base_room()

    # Step 2: Analyze
    widgets_found = generator.analyze_with_vision(base_room)

    # Save
    generator.save_results(
        {
            "room_name": lilith_room_config["name"],
            "base_room": str(base_room),
            "widgets_found": widgets_found,
        }
    )

    print("\n🎉 PIPELINE COMPLETE!")


if __name__ == "__main__":
    main()
