#!/usr/bin/env python3
"""
Image Composition Manager - Python Implementation
==============================================

Python version of the JavaScript ImageCompositionManager for
WorldBuilderV2 integration. Provides tile-based composition
with widget state management and AI generation pipeline.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import openai
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

load_dotenv()

# Configuration
WORLD_JSON = Path("static/world.json")
RESULT_JSON = Path("static/result.json")
WORLD_TILES_DIR = Path("static/world")
WORLD_TILES_DIR.mkdir(parents=True, exist_ok=True)

# AI APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


class ImageCompositionManager:
    """
    Python implementation of ImageCompositionManager for
    server-side tile generation and composition.
    """

    def __init__(self):
        """Initialize the composition manager."""
        self.canvas_cache = {}
        self.layer_stack = []
        self.composition_queue = []
        self.is_processing = False
        self.max_canvas_size = 2048

        # Widget type definitions
        self.widget_types = {
            "time": self._render_time_widget,
            "status": self._render_status_widget,
            "version": self._render_version_widget,
            "hash": self._render_hash_widget,
            "online": self._render_online_widget,
            "changelog": self._render_changelog_widget,
            "link": self._render_link_widget,
            "story": self._render_story_widget,
            "music": self._render_music_widget,
        }

    async def create_composite_tile(
        self,
        location: Dict[str, Any],
        state: str = "idle",
        options: Dict[str, Any] = None,
    ) -> str:
        """
        Create a composite tile for a location with specific state.

        Args:
            location: Location dictionary from world.json
            state: Widget state ('idle', 'hover', 'click')
            options: Additional composition options

        Returns:
            Path to generated composite image file
        """
        if options is None:
            options = {}

        cache_key = f"{location['id']}-{state}-{hashlib.md5(json.dumps(options, sort_keys=True).encode()).hexdigest()[:8]}"

        # Check cache first
        if cache_key in self.canvas_cache:
            print(f"📋 Using cached composite: {cache_key}")
            return self.canvas_cache[cache_key]

        print(f"🎨 Creating composite tile for {location['name']} - {state}")

        try:
            # Create base composition
            composite = await self._create_base_composition(location, state)

            # Apply widget layers
            composite = await self._apply_widget_layers(location, state, composite)

            # Apply state effects
            composite = await self._apply_state_effects(location, state, composite)

            # Save composite tile
            output_path = WORLD_TILES_DIR / f"{location['id']}_{state}.png"
            composite.save(output_path, "PNG", optimize=True)

            # Cache result
            self.canvas_cache[cache_key] = str(output_path)

            print(f"✅ Composite tile saved: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"❌ Error creating composite tile: {e}")
            raise

    async def _create_base_composition(
        self, location: Dict[str, Any], state: str
    ) -> Image.Image:
        """Create base composition for location."""

        # Create high-quality canvas
        canvas_size = 1024
        composite = Image.new("RGB", (canvas_size, canvas_size), (255, 255, 255))
        draw = ImageDraw.Draw(composite)

        # Draw room structure
        composite = await self._draw_room_structure(location, composite, draw)

        # Draw floor and walls
        composite = await self._draw_room_interior(location, composite, draw)

        return composite

    async def _draw_room_structure(
        self,
        location: Dict[str, Any],
        composite: Image.Image,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        """Draw basic room structure (walls, floor, windows)."""

        # Room color scheme based on location type
        room_colors = {
            "liliths_room": {
                "wall": (255, 192, 203),  # Pink walls
                "floor": (255, 228, 225),  # Light pink floor
                "accent": (255, 105, 180),  # Hot pink accents
                "window": (135, 206, 235),  # Sky blue windows
            },
            "default": {
                "wall": (240, 240, 240),  # Light gray walls
                "floor": (220, 220, 220),  # Gray floor
                "accent": (150, 150, 150),  # Dark gray accents
                "window": (135, 206, 235),  # Sky blue windows
            },
        }

        colors = room_colors.get(location.get("id", "default"), room_colors["default"])

        # Draw walls
        wall_margin = 50
        draw.rectangle(
            [wall_margin, wall_margin, 1024 - wall_margin, 1024 - wall_margin],
            fill=colors["wall"],
            outline=colors["accent"],
            width=5,
        )

        # Draw floor
        floor_margin = 100
        draw.rectangle(
            [floor_margin, floor_margin, 1024 - floor_margin, 1024 - floor_margin],
            fill=colors["floor"],
        )

        # Draw window
        window_size = 200
        window_x = 1024 - wall_margin - window_size - 20
        window_y = wall_margin + 20
        draw.rectangle(
            [window_x, window_y, window_x + window_size, window_y + window_size],
            fill=colors["window"],
            outline=colors["accent"],
            width=3,
        )

        # Draw window panes
        pane_size = window_size // 2
        draw.line(
            [
                window_x + pane_size,
                window_y,
                window_x + pane_size,
                window_y + window_size,
            ],
            fill=colors["accent"],
            width=2,
        )
        draw.line(
            [
                window_x,
                window_y + pane_size,
                window_x + window_size,
                window_y + pane_size,
            ],
            fill=colors["accent"],
            width=2,
        )

        # Draw door
        door_width = 120
        door_height = 200
        door_x = wall_margin + 20
        door_y = 1024 - wall_margin - door_height
        draw.rectangle(
            [door_x, door_y, door_x + door_width, door_y + door_height],
            fill=(139, 69, 19),  # Brown door
            outline=colors["accent"],
            width=3,
        )

        # Door knob
        knob_x = door_x + door_width - 20
        knob_y = door_y + door_height // 2
        draw.ellipse(
            [knob_x - 5, knob_y - 5, knob_x + 5, knob_y + 5],
            fill=(255, 215, 0),  # Gold knob
        )

        return composite

    async def _draw_room_interior(
        self,
        location: Dict[str, Any],
        composite: Image.Image,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        """Draw room interior elements (furniture, decorations)."""

        # Add room-specific interior elements
        if location.get("id") == "liliths_room":
            composite = await self._draw_liliths_room_interior(composite, draw)

        return composite

    async def _draw_liliths_room_interior(
        self, composite: Image.Image, draw: ImageDraw.ImageDraw
    ) -> Image.Image:
        """Draw Lilith's room specific interior elements."""

        # Draw bed
        bed_x, bed_y = 150, 600
        bed_width, bed_height = 300, 200
        draw.rectangle(
            [bed_x, bed_y, bed_x + bed_width, bed_y + bed_height],
            fill=(255, 182, 193),  # Light pink bed
            outline=(219, 112, 147),  # Medium pink outline
            width=3,
        )

        # Draw pillow
        pillow_width, pillow_height = 80, 60
        pillow_x = bed_x + (bed_width - pillow_width) // 2
        pillow_y = bed_y + 20
        draw.rectangle(
            [pillow_x, pillow_y, pillow_x + pillow_width, pillow_y + pillow_height],
            fill=(255, 218, 224),  # Very light pink
            outline=(219, 112, 147),
            width=2,
        )

        # Draw desk
        desk_x, desk_y = 500, 400
        desk_width, desk_height = 200, 120
        draw.rectangle(
            [desk_x, desk_y, desk_x + desk_width, desk_y + desk_height],
            fill=(222, 184, 135),  # Burlywood wood desk
            outline=(160, 82, 45),  # Sienna outline
            width=3,
        )

        # Draw desk chair
        chair_x, chair_y = 550, 530
        chair_width, chair_height = 80, 80
        draw.rectangle(
            [chair_x, chair_y, chair_x + chair_width, chair_y + chair_height],
            fill=(205, 133, 63),  # Peru chair
            outline=(160, 82, 45),
            width=2,
        )

        # Draw bookshelf
        shelf_x, shelf_y = 750, 300
        shelf_width, shelf_height = 150, 300
        draw.rectangle(
            [shelf_x, shelf_y, shelf_x + shelf_width, shelf_y + shelf_height],
            fill=(139, 90, 43),  # Dark wood bookshelf
            outline=(101, 67, 33),
            width=3,
        )

        # Draw shelf divisions
        for i in range(1, 4):
            shelf_y_pos = shelf_y + i * 75
            draw.line(
                [shelf_x, shelf_y_pos, shelf_x + shelf_width, shelf_y_pos],
                fill=(101, 67, 33),
                width=2,
            )

        return composite

    async def _apply_widget_layers(
        self, location: Dict[str, Any], state: str, composite: Image.Image
    ) -> Image.Image:
        """Apply widget layers to composite based on location and state."""

        widgets = location.get("widgets", [])

        for widget in widgets:
            widget_type = widget.get("type")
            position = widget.get("position", {})

            if widget_type in self.widget_types:
                print(
                    f"🎯 Rendering widget: {widget.get('id')} ({widget_type}) - {state}"
                )

                # Get widget-specific rendering function
                render_func = self.widget_types[widget_type]

                # Render widget
                widget_layer = await render_func(widget, state, composite)

                # Composite widget onto main image
                if widget_layer:
                    composite = await self._composite_widget(
                        composite, widget_layer, position, widget, state
                    )

        return composite

    async def _composite_widget(
        self,
        base_image: Image.Image,
        widget_layer: Image.Image,
        position: Dict[str, int],
        widget: Dict[str, Any],
        state: str,
    ) -> Image.Image:
        """Composite widget layer onto base image."""

        # Convert to RGBA for proper alpha compositing
        base_rgba = base_image.convert("RGBA")
        widget_rgba = widget_layer.convert("RGBA")

        # Position widget
        x = position.get("x", 0)
        y = position.get("y", 0)

        # Apply state-based transformations
        if state == "hover":
            # Add glow effect
            widget_rgba = await self._add_glow_effect(
                widget_rgba, (255, 215, 0)
            )  # Gold glow
        elif state == "click":
            # Add sparkle effect
            widget_rgba = await self._add_sparkle_effect(widget_rgba)

        # Composite widget onto base
        base_rgba.paste(widget_rgba, (x, y), widget_rgba)

        return base_rgba.convert("RGB")

    async def _apply_state_effects(
        self, location: Dict[str, Any], state: str, composite: Image.Image
    ) -> Image.Image:
        """Apply state-based effects to entire composite."""

        if state == "hover":
            # Add subtle brightness increase
            enhancer = ImageEnhance.Brightness(composite)
            composite = enhancer.enhance(1.1)

            # Add slight color saturation
            enhancer = ImageEnhance.Color(composite)
            composite = enhancer.enhance(1.1)

        elif state == "click":
            # Add dramatic lighting effect
            enhancer = ImageEnhance.Brightness(composite)
            composite = enhancer.enhance(1.2)

            # Add contrast
            enhancer = ImageEnhance.Contrast(composite)
            composite = enhancer.enhance(1.15)

        return composite

    async def _add_glow_effect(
        self, image: Image.Image, glow_color: Tuple[int, int, int]
    ) -> Image.Image:
        """Add glow effect to image."""

        # Create glow layer
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)

        # Draw glow outline
        for i in range(3, 0, -1):
            alpha = 50 - i * 15
            glow_color_with_alpha = (*glow_color, alpha)

            # Simple glow by expanding the image
            expanded = image.filter(ImageFilter.MaxFilter(3 + i * 2))
            glow.paste(expanded, (0, 0), expanded)

        # Composite glow with original
        result = Image.alpha_composite(image.convert("RGBA"), glow)

        return result

    async def _add_sparkle_effect(self, image: Image.Image) -> Image.Image:
        """Add sparkle effect to image."""

        # Create sparkle overlay
        sparkle = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(sparkle)

        # Add random sparkles
        import random

        random.seed(42)  # Deterministic sparkles

        for _ in range(20):
            x = random.randint(0, image.width)
            y = random.randint(0, image.height)
            size = random.randint(2, 6)

            # Draw star sparkle
            draw.polygon(
                [(x, y - size), (x + size // 2, y), (x, y + size), (x - size // 2, y)],
                fill=(255, 255, 255, 200),
            )

        # Composite sparkles with image
        result = Image.alpha_composite(image.convert("RGBA"), sparkle)

        return result

    # Widget rendering methods
    async def _render_time_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render time widget (wall clock)."""

        size = widget.get("size", {"width": 100, "height": 100})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw clock face
        center_x, center_y = size["width"] // 2, size["height"] // 2
        radius = min(size["width"], size["height"]) // 2 - 5

        # Clock background
        draw.ellipse(
            [
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ],
            fill=(255, 255, 224),  # Light yellow clock face
            outline=(139, 69, 19),  # Brown clock border
            width=3,
        )

        # Draw clock numbers
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()

        for hour in range(1, 13):
            angle = (hour - 3) * 30  # Convert to radians
            x = center_x + int(radius * 0.8 * np.cos(np.radians(angle)))
            y = center_y + int(radius * 0.8 * np.sin(np.radians(angle)))

            draw.text((x - 5, y - 8), str(hour), fill=(0, 0, 0), font=font)

        # Draw clock hands
        current_time = time.localtime()

        # Hour hand
        hour_angle = ((current_time.tm_hour % 12) + current_time.tm_min / 60) * 30 - 90
        hour_x = center_x + int(radius * 0.5 * np.cos(np.radians(hour_angle)))
        hour_y = center_y + int(radius * 0.5 * np.sin(np.radians(hour_angle)))
        draw.line([center_x, center_y, hour_x, hour_y], fill=(0, 0, 0), width=4)

        # Minute hand
        minute_angle = current_time.tm_min * 6 - 90
        minute_x = center_x + int(radius * 0.7 * np.cos(np.radians(minute_angle)))
        minute_y = center_y + int(radius * 0.7 * np.sin(np.radians(minute_angle)))
        draw.line([center_x, center_y, minute_x, minute_y], fill=(0, 0, 0), width=2)

        # Center dot
        draw.ellipse(
            [center_x - 3, center_y - 3, center_x + 3, center_y + 3], fill=(0, 0, 0)
        )

        return canvas

    async def _render_status_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render status widget."""

        size = widget.get("size", {"width": 80, "height": 30})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Status indicator
        status_color = (0, 255, 0)  # Green for online

        # Draw status background
        draw.rectangle(
            [0, 0, size["width"], size["height"]],
            fill=(240, 240, 240),
            outline=status_color,
            width=2,
        )

        # Draw status indicator circle
        draw.ellipse([10, 10, 20, 20], fill=status_color)

        return canvas

    async def _render_version_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render version widget."""

        size = widget.get("size", {"width": 100, "height": 30})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Version display
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except:
            font = ImageFont.load_default()

        # Get version from result.json or default
        version = "v0.1.0"

        # Draw version background
        draw.rectangle(
            [0, 0, size["width"], size["height"]],
            fill=(255, 255, 255),
            outline=(100, 100, 100),
            width=1,
        )

        # Draw version text
        draw.text((5, 8), version, fill=(0, 0, 0), font=font)

        return canvas

    async def _render_hash_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render hash widget."""

        size = widget.get("size", {"width": 80, "height": 20})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Short hash display
        try:
            font = ImageFont.truetype("arial.ttf", 8)
        except:
            font = ImageFont.load_default()

        # Draw hash background
        draw.rectangle(
            [0, 0, size["width"], size["height"]],
            fill=(240, 248, 255),  # Alice blue
            outline=(70, 130, 180),  # Steel blue
            width=1,
        )

        # Draw hash (shortened)
        short_hash = "abc123"
        draw.text((2, 4), short_hash, fill=(0, 0, 139), font=font)

        return canvas

    async def _render_online_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render online status widget."""

        size = widget.get("size", {"width": 60, "height": 20})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Online indicator
        online_color = (0, 255, 0)  # Green

        # Draw online indicator
        draw.rectangle(
            [0, 0, size["width"], size["height"]],
            fill=(240, 255, 240),  # Honeydew
            outline=online_color,
            width=1,
        )

        # Draw status dot
        draw.ellipse([8, 8, 12, 12], fill=online_color)

        # Draw "ONLINE" text
        try:
            font = ImageFont.truetype("arial.ttf", 8)
        except:
            font = ImageFont.load_default()

        draw.text((16, 6), "ONLINE", fill=(0, 128, 0), font=font)

        return canvas

    async def _render_changelog_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render changelog widget (book)."""

        size = widget.get("size", {"width": 60, "height": 80})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Book cover
        if state == "click":
            # Open book
            draw.rectangle(
                [0, 0, size["width"], size["height"]],
                fill=(255, 248, 220),  # Cornsilk (open pages)
                outline=(139, 69, 19),  # Brown
                width=2,
            )

            # Draw spine
            draw.line(
                [size["width"] // 2, 0, size["width"] // 2, size["height"]],
                fill=(139, 69, 19),
                width=3,
            )
        else:
            # Closed book
            draw.rectangle(
                [5, 5, size["width"] - 5, size["height"] - 5],
                fill=(178, 34, 34),  # Firebrick book cover
                outline=(139, 0, 0),  # Dark red
                width=2,
            )

            # Book title
            try:
                font = ImageFont.truetype("arial.ttf", 8)
            except:
                font = ImageFont.load_default()

            draw.text((8, 30), "CHANGELOG", fill=(255, 255, 255), font=font)

        return canvas

    async def _render_link_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render link widget (poster/logo)."""

        size = widget.get("size", {"width": 120, "height": 80})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Poster/frame
        draw.rectangle(
            [2, 2, size["width"] - 2, size["height"] - 2],
            fill=(255, 250, 205),  # Lemon chiffon
            outline=(184, 134, 11),  # Dark goldenrod
            width=3,
        )

        # Draw simple logo text
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()

        draw.text((10, 25), "THE EDGE", fill=(139, 69, 19), font=font)

        draw.text((25, 40), "STORY", fill=(139, 69, 19), font=font)

        return canvas

    async def _render_story_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render story widget (photo frame)."""

        size = widget.get("size", {"width": 100, "height": 120})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Photo frame
        frame_width = 8
        draw.rectangle(
            [0, 0, size["width"], size["height"]],
            fill=(139, 90, 43),  # Dark wood frame
        )

        draw.rectangle(
            [
                frame_width,
                frame_width,
                size["width"] - frame_width,
                size["height"] - frame_width,
            ],
            fill=(255, 255, 255),  # White photo background
            outline=(101, 67, 33),
            width=2,
        )

        # Simple heart drawing in photo
        heart_x, heart_y = size["width"] // 2, size["height"] // 2
        heart_size = 15

        # Draw heart shape
        draw.polygon(
            [
                (heart_x, heart_y + heart_size // 2),
                (heart_x - heart_size // 2, heart_y),
                (heart_x - heart_size // 4, heart_y - heart_size // 4),
                (heart_x, heart_y - heart_size // 3),
                (heart_x + heart_size // 4, heart_y - heart_size // 4),
                (heart_x + heart_size // 2, heart_y),
            ],
            fill=(255, 105, 180),
        )  # Hot pink heart

        return canvas

    async def _render_music_widget(
        self, widget: Dict[str, Any], state: str, composite: Image.Image
    ) -> Optional[Image.Image]:
        """Render music widget (vinyl record)."""

        size = widget.get("size", {"width": 80, "height": 80})
        canvas = Image.new("RGBA", (size["width"], size["height"]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Vinyl record
        center_x, center_y = size["width"] // 2, size["height"] // 2
        radius = min(size["width"], size["height"]) // 2 - 5

        # Black vinyl
        draw.ellipse(
            [
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ],
            fill=(20, 20, 20),  # Very dark gray
            outline=(0, 0, 0),
            width=2,
        )

        # Record grooves (concentric circles)
        for i in range(3, radius, 5):
            draw.ellipse(
                [center_x - i, center_y - i, center_x + i, center_y + i],
                outline=(40, 40, 40),
                width=1,
            )

        # Center label
        label_radius = 15
        draw.ellipse(
            [
                center_x - label_radius,
                center_y - label_radius,
                center_x + label_radius,
                center_y + label_radius,
            ],
            fill=(255, 0, 0),  # Red label
            outline=(139, 0, 0),
            width=2,
        )

        # Label text
        try:
            font = ImageFont.truetype("arial.ttf", 6)
        except:
            font = ImageFont.load_default()

        draw.text(
            (center_x - 8, center_y - 4), "LO-FI", fill=(255, 255, 255), font=font
        )

        return canvas


async def main():
    """Test the ImageCompositionManager."""
    manager = ImageCompositionManager()

    # Load world.json
    with open(WORLD_JSON) as f:
        world = json.load(f)

    # Test composite generation for first location
    if world.get("locations"):
        location = world["locations"][0]

        print(f"🏠 Testing composite generation for: {location['name']}")

        # Generate idle state
        idle_path = await manager.create_composite_tile(location, "idle")
        print(f"✅ Idle composite: {idle_path}")

        # Generate hover state
        hover_path = await manager.create_composite_tile(location, "hover")
        print(f"✅ Hover composite: {hover_path}")

        # Generate click state
        click_path = await manager.create_composite_tile(location, "click")
        print(f"✅ Click composite: {click_path}")

        print("🎉 All composites generated successfully!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
