"""
World Service Implementation
==========================

Virtual world generation and management service.
Implements PRP-016 Animal Crossing World functionality.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Terrain types with emoji representations
TERRAIN_TYPES = {
    "grass": {"emoji": "🌿", "walkable": True, "color": "green"},
    "water": {"emoji": "💧", "walkable": False, "color": "blue"},
    "sand": {"emoji": "🏖️", "walkable": True, "color": "yellow"},
    "stone": {"emoji": "🪨", "walkable": True, "color": "gray"},
    "tree": {"emoji": "🌳", "walkable": False, "color": "darkgreen"},
    "flower": {"emoji": "🌻", "walkable": True, "color": "gold"},
    "house": {"emoji": "🏠", "walkable": False, "color": "brown"},
}


class WorldService:
    """Virtual world generation and management service."""

    def __init__(self):
        """Initialize world service."""
        self.worlds = {}  # Store generated worlds by ID
        self.terrain_distribution = {
            "grass": 0.4,
            "water": 0.15,
            "sand": 0.1,
            "stone": 0.1,
            "tree": 0.15,
            "flower": 0.05,
            "house": 0.05,
        }

    def generate_world(
        self, width: int, height: int, world_id: str = None
    ) -> Dict[str, Any]:
        """Generate a new virtual world.

        Args:
            width: World width in tiles
            height: World height in tiles
            world_id: Optional world identifier

        Returns:
            Generated world data
        """
        if world_id is None:
            world_id = f"world_{random.randint(1000, 9999)}"

        # Initialize terrain grid
        terrain = [[None for _ in range(width)] for _ in range(height)]

        # Generate terrain using cellular automata-like approach
        for y in range(height):
            for x in range(width):
                terrain[y][x] = self._select_terrain(x, y, width, height, terrain)

        # Add special features
        self._add_features(terrain, width, height)

        # Store world
        world_data = {
            "id": world_id,
            "width": width,
            "height": height,
            "terrain": terrain,
            "spawn_point": self._find_spawn_point(terrain, width, height),
            "features": self._identify_features(terrain),
            "created_at": "2025-11-03T00:00:00Z",  # Placeholder timestamp
        }

        self.worlds[world_id] = world_data
        logger.info(f"Generated world {world_id} with size {width}x{height}")

        return world_data

    def _select_terrain(
        self, x: int, y: int, width: int, height: int, terrain: List[List[str]]
    ) -> str:
        """Select terrain type for a specific tile.

        Args:
            x: X coordinate
            y: Y coordinate
            width: World width
            height: World height
            terrain: Current terrain grid

        Returns:
            Selected terrain type
        """
        # Edge bias - more water at edges
        if x == 0 or x == width - 1 or y == 0 or y == height - 1:
            if random.random() < 0.3:
                return "water"

        # Check neighbors for terrain clustering
        neighbors = self._get_neighbors(x, y, width, height, terrain)
        neighbor_counts = {}
        for n in neighbors:
            if n:
                neighbor_counts[n] = neighbor_counts.get(n, 0) + 1

        # If we have neighbors, tend to match them
        if neighbor_counts:
            most_common = max(neighbor_counts.items(), key=lambda x: x[1])
            if random.random() < 0.6:  # 60% chance to match neighbors
                return most_common[0]

        # Otherwise, use weighted random selection
        terrain_types = list(self.terrain_distribution.keys())
        weights = list(self.terrain_distribution.values())
        return random.choices(terrain_types, weights=weights)[0]

    def _get_neighbors(
        self, x: int, y: int, width: int, height: int, terrain: List[List[str]]
    ) -> List[str]:
        """Get terrain of neighboring tiles.

        Args:
            x: X coordinate
            y: Y coordinate
            width: World width
            height: World height
            terrain: Current terrain grid

        Returns:
            List of neighboring terrain types
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append(terrain[ny][nx])
        return neighbors

    def _add_features(self, terrain: List[List[str]], width: int, height: int) -> None:
        """Add special features to the world.

        Args:
            terrain: Terrain grid to modify
            width: World width
            height: World height
        """
        # Add clusters of flowers
        for _ in range(random.randint(3, 8)):
            cx, cy = random.randint(1, width - 2), random.randint(1, height - 2)
            if terrain[cy][cx] == "grass":
                terrain[cy][cx] = "flower"
                # Add flower cluster
                for _ in range(random.randint(2, 5)):
                    fx = cx + random.randint(-1, 1)
                    fy = cy + random.randint(-1, 1)
                    if 0 <= fx < width and 0 <= fy < height:
                        if terrain[fy][fx] == "grass" and random.random() < 0.5:
                            terrain[fy][fx] = "flower"

        # Add a few houses
        for _ in range(random.randint(2, 4)):
            x, y = random.randint(1, width - 2), random.randint(1, height - 2)
            if terrain[y][x] in ["grass", "sand"]:
                terrain[y][x] = "house"

    def _find_spawn_point(
        self, terrain: List[List[str]], width: int, height: int
    ) -> Tuple[int, int]:
        """Find a suitable spawn point.

        Args:
            terrain: Terrain grid
            width: World width
            height: World height

        Returns:
            Spawn point coordinates (x, y)
        """
        # Look for a grass or sand tile away from water
        for _ in range(100):  # Max attempts
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            if terrain[y][x] in ["grass", "sand"]:
                # Check if not surrounded by water
                neighbors = self._get_neighbors(x, y, width, height, terrain)
                water_count = sum(1 for n in neighbors if n == "water")
                if water_count < 4:  # Not completely surrounded by water
                    return x, y

        # Fallback to first walkable tile
        for y in range(height):
            for x in range(width):
                if terrain[y][x] in ["grass", "sand"]:
                    return x, y

        return 0, 0  # Last resort

    def _identify_features(self, terrain: List[List[str]]) -> Dict[str, Any]:
        """Identify and count features in the world.

        Args:
            terrain: Terrain grid

        Returns:
            Dictionary with feature counts
        """
        features = {}
        for row in terrain:
            for tile in row:
                features[tile] = features.get(tile, 0) + 1
        return features

    def get_world(self, world_id: str) -> Optional[Dict[str, Any]]:
        """Get world data by ID.

        Args:
            world_id: World identifier

        Returns:
            World data or None if not found
        """
        return self.worlds.get(world_id)

    def render_world(self, world_data: Dict[str, Any]) -> str:
        """Render world as emoji string.

        Args:
            world_data: World data

        Returns:
            String representation of world
        """
        terrain = world_data["terrain"]
        lines = []

        for row in terrain:
            line = ""
            for tile in row:
                line += TERRAIN_TYPES.get(tile, TERRAIN_TYPES["grass"])["emoji"]
            lines.append(line)

        return "\n".join(lines)

    def get_tile_info(self, world_id: str, x: int, y: int) -> Dict[str, Any]:
        """Get information about a specific tile.

        Args:
            world_id: World identifier
            x: X coordinate
            y: Y coordinate

        Returns:
            Tile information
        """
        world = self.get_world(world_id)
        if not world:
            return {"error": "World not found"}

        terrain = world["terrain"]
        if not (0 <= x < world["width"] and 0 <= y < world["height"]):
            return {"error": "Coordinates out of bounds"}

        tile_type = terrain[y][x]
        tile_info = TERRAIN_TYPES.get(tile_type, TERRAIN_TYPES["grass"])

        return {
            "coordinates": (x, y),
            "terrain_type": tile_type,
            "emoji": tile_info["emoji"],
            "walkable": tile_info["walkable"],
            "color": tile_info["color"],
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check world service health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "worlds_count": len(self.worlds),
            "terrain_types": len(TERRAIN_TYPES),
            "service_version": "1.0.0",
        }


# Singleton instance
_world_service = None


def get_world_service() -> WorldService:
    """Get or create world service singleton."""
    global _world_service
    if _world_service is None:
        _world_service = WorldService()
    return _world_service
