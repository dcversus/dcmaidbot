#!/usr/bin/env python3
"""
World Builder - Deterministic Multi-Floor Location Generator
============================================================

Maintains world state in JSON and generates connected locations where:
- Doors/windows/stairs perfectly align between rooms
- Same prompt = same result (deterministic)
- Supports multiple floors
- Updates neighbor tiles when new location added

WORKFLOW:
1. Parse location description → Update world JSON
2. Check connections (doors to/from which rooms)
3. Generate location with connection constraints
4. Validate connections with GPT-4V
5. Update neighbor tiles if needed
6. Save world state

EXAMPLE:
world.add_location("Lilith's bedroom on floor 2, door at bottom leading to hall")
→ Generates bedroom with door at bottom
→ Updates hall (floor 1) to have door at top leading to bedroom
→ Perfect connection!
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

# Paths
WORLD_STATE_FILE = Path("static/world_state.json")
TILES_DIR = Path("static/world_tiles")
TILES_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Connection:
    """Connection between two locations."""

    from_location: str
    to_location: str
    connection_type: str  # "door", "stairs_up", "stairs_down", "window"
    from_side: str  # "top", "bottom", "left", "right"
    to_side: str


@dataclass
class Location:
    """A location in the world."""

    id: str
    name: str
    description: str
    floor: int
    grid_position: Tuple[int, int]  # (x, y) on floor
    tile_path: str
    connections: List[Connection]
    seed: int  # For deterministic generation


class WorldBuilder:
    """Maintains world state and generates connected locations."""

    def __init__(self):
        """Initialize or load existing world."""
        self.locations: Dict[str, Location] = {}
        self.load_world_state()

    def load_world_state(self):
        """Load existing world from JSON."""
        if WORLD_STATE_FILE.exists():
            with open(WORLD_STATE_FILE) as f:
                data = json.load(f)
                for loc_data in data.get("locations", []):
                    loc = Location(**loc_data)
                    self.locations[loc.id] = loc
            print(f"✅ Loaded {len(self.locations)} existing locations")
        else:
            print("🆕 Creating new world")

    def save_world_state(self):
        """Save world state to JSON."""
        data = {
            "locations": [asdict(loc) for loc in self.locations.values()],
            "floor_count": max(
                (loc.floor for loc in self.locations.values()), default=1
            ),
        }

        with open(WORLD_STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"💾 World state saved: {len(self.locations)} locations")

    def add_location(
        self,
        name: str,
        description: str,
        floor: int,
        grid_pos: Tuple[int, int],
        connections: List[Dict],
    ) -> Location:
        """
        Add new location to world.

        connections format:
        [
            {"to": "hall", "type": "door", "from_side": "bottom", "to_side": "top"},
            ...
        ]
        """
        print(f"\n{'=' * 70}")
        print(f"Adding location: {name} (floor {floor})")
        print(f"{'=' * 70}\n")

        # Create deterministic seed from name + floor + position
        seed_str = f"{name}_{floor}_{grid_pos[0]}_{grid_pos[1]}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

        loc_id = name.lower().replace(" ", "_").replace("'", "")

        # Build connection list
        conn_objs = []
        for conn in connections:
            conn_objs.append(
                Connection(
                    from_location=loc_id,
                    to_location=conn["to"],
                    connection_type=conn["type"],
                    from_side=conn["from_side"],
                    to_side=conn["to_side"],
                )
            )

        # Create location
        location = Location(
            id=loc_id,
            name=name,
            description=description,
            floor=floor,
            grid_position=grid_pos,
            tile_path=f"world_tiles/{loc_id}.png",
            connections=conn_objs,
            seed=seed,
        )

        # Generate tiles
        self._generate_location_tiles(location)

        # Add to world
        self.locations[loc_id] = location

        # Update neighbors
        for conn in connections:
            self._update_neighbor_connection(loc_id, conn)

        # Save
        self.save_world_state()

        return location

    def _generate_location_tiles(self, location: Location):
        """Generate tiles for this location."""
        print(f"🎨 Generating tiles for: {location.name}")
        print(f"   Seed: {location.seed}")
        print(f"   Description: {location.description[:80]}...")

        # Build prompt with connection constraints
        prompt = self._build_constrained_prompt(location)

        print(f"\n   Prompt: {prompt[:100]}...")
        print("\n   ⚠️  MANUAL GENERATION REQUIRED")
        print(f"   Use Leonardo MCP with this prompt and seed concept: {location.seed}")
        print(f"   Save as: {TILES_DIR / f'{location.id}.png'}")

        # TODO: Actual generation with Leonardo/DALL-E
        # For now, just print the command

    def _build_constrained_prompt(self, location: Location) -> str:
        """Build prompt with connection constraints."""

        # Base
        prompt = f"{location.description}, 16-bit pixel art top-down SNES RPG style, "

        # Add connection constraints
        for conn in location.connections:
            if conn.connection_type == "door":
                prompt += f"door opening at {conn.from_side} edge, "
            elif conn.connection_type == "stairs_up":
                prompt += f"stairs going up at {conn.from_side}, "
            elif conn.connection_type == "stairs_down":
                prompt += f"stairs going down at {conn.from_side}, "
            elif conn.connection_type == "window":
                prompt += f"window at {conn.from_side}, "

        prompt += "retro pixel aesthetic, lofi kawaii, 1024x1024"

        return prompt

    def _update_neighbor_connection(self, loc_id: str, connection: Dict):
        """Update neighbor location to have reciprocal connection."""
        neighbor_id = connection["to"]

        if neighbor_id in self.locations:
            neighbor = self.locations[neighbor_id]

            # Add reciprocal connection
            reciprocal = Connection(
                from_location=neighbor_id,
                to_location=loc_id,
                connection_type=connection["type"],
                from_side=connection["to_side"],
                to_side=connection["from_side"],
            )

            neighbor.connections.append(reciprocal)

            print(f"   🔗 Updated {neighbor.name} with reciprocal connection")

            # TODO: Regenerate neighbor's connecting edge tile
            print("   ⚠️  Neighbor tile regeneration needed")


def example_world_building():
    """Example: Build Lilith's house step by step."""

    world = WorldBuilder()

    # Location 1: Lilith's Room (starting point)
    world.add_location(
        name="Lilith's Room",
        description="cozy teenage bedroom with bed, desk, bookshelf, purple rug",
        floor=2,  # Second floor
        grid_pos=(0, 0),
        connections=[
            {"to": "hall", "type": "door", "from_side": "bottom", "to_side": "top"}
        ],
    )

    # Location 2: Hall (connects to Lilith's room)
    world.add_location(
        name="Hall",
        description="entrance hallway with coat rack, family photos on wall",
        floor=1,  # First floor
        grid_pos=(0, -1),  # Below Lilith's room
        connections=[
            {
                "to": "liliths_room",
                "type": "door",
                "from_side": "top",
                "to_side": "bottom",
            },
            {
                "to": "parents_room",
                "type": "stairs_up",
                "from_side": "left",
                "to_side": "right",
            },
            {
                "to": "sauna",
                "type": "stairs_down",
                "from_side": "bottom",
                "to_side": "top",
            },
        ],
    )

    # Location 3: Parents' Room (accessible from hall via stairs)
    world.add_location(
        name="Parents' Room",
        description="master bedroom with double bed, Daniil and Vasilisa sleeping",
        floor=2,  # Same floor as Lilith
        grid_pos=(-1, 0),  # Left of Lilith's room
        connections=[
            {
                "to": "hall",
                "type": "stairs_down",
                "from_side": "right",
                "to_side": "left",
            }
        ],
    )

    print("\n" + "=" * 70)
    print("🌍 WORLD BUILT!")
    print(f"   Locations: {len(world.locations)}")
    print(f"   Floors: {max(loc.floor for loc in world.locations.values())}")
    print("=" * 70)


if __name__ == "__main__":
    example_world_building()
