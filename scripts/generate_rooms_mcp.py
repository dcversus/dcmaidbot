#!/usr/bin/env python3
"""
Room Generator using Leonardo MCP + GPT-4V Validation
======================================================

Uses Claude Code's MCP tools for generation.
This script prepares prompts and processes results.
"""

# Room configurations
ROOMS = {
    "lilith_bedroom": {
        "states": {
            "idle": "16-bit pixel art teenage bedroom, perfect top-down view like SNES RPG, desk with pink clock top-left, window with small cactus top-right, colorful bookshelf bottom-left, cozy bed with plushies bottom-right, purple gradient rug center, wooden floor, pastel pink purple blue, retro game aesthetic, lofi kawaii pixel art, organized space, 1024x1024",
            "hover": "SAME 16-bit pixel art bedroom BUT clock GLOWING with soft pink aura and sparkles, EXACT same layout and camera, retro pixel art style, 1024x1024",
            "click": "SAME 16-bit pixel art bedroom BUT clock SUPER GLOWING bright pink magical aura, many sparkles, EXACT same layout, retro pixel art, 1024x1024",
        },
        "widgets": ["clock", "cactus", "bookshelf", "bed", "rug"],
    },
    "garden": {
        "states": {
            "idle": "16-bit pixel art garden top-down like SNES RPG, 2x2 vegetable beds, top-left tomatoes, top-right strawberries, bottom-left watermelon, bottom-right mandarin tree, brown soil, green grass, garden tools, retro pixel art, lofi aesthetic, 1024x1024",
            "hover": "SAME pixel art garden BUT tomatoes GLOWING green healthy aura, EXACT same layout, retro pixel style, 1024x1024",
            "click": "SAME pixel art garden BUT tomatoes RIPE glowing bright red, ready harvest, EXACT same layout, retro style, 1024x1024",
        },
        "widgets": ["tomatoes", "strawberries", "watermelon", "mandarin"],
    },
}


def print_generation_commands():
    """Print MCP commands for manual execution."""

    print("=" * 70)
    print("LEONARDO MCP GENERATION COMMANDS")
    print("=" * 70)

    for room_name, config in ROOMS.items():
        print(f"\n## {room_name.upper()}\n")

        for state, prompt in config["states"].items():
            print(f"### {state.upper()}:")
            print(f'''
mcp__leonardoai__high_definition_generalist(
    prompt="{prompt}",
    width=1024,
    height=1024,
    style='RETRO'
)
''')
            print(f"Save as: static/generated_rooms/{room_name}/room_{state}.jpg\n")


if __name__ == "__main__":
    print_generation_commands()
