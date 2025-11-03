"""
Comprehensive Tests for WorldService
====================================

Test suite for WorldService functionality including terrain generation,
world management, chunk handling, and coordinate validation.
"""

import asyncio
import os

# Import the service we're testing
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.world_service import Chunk, TerrainType, World, WorldService


class TestTerrainType:
    """Test suite for TerrainType enum functionality."""

    def test_terrain_type_values(self):
        """Test that all terrain types have required properties."""
        for terrain in TerrainType:
            assert hasattr(terrain.value, "emoji")
            assert hasattr(terrain.value, "walkable")
            assert hasattr(terrain.value, "color")
            assert isinstance(terrain.value.emoji, str)
            assert isinstance(terrain.value.walkable, bool)
            assert isinstance(terrain.value.color, str)

    def test_terrain_type_coverage(self):
        """Test that all expected terrain types exist."""
        expected_terrains = {
            "grass",
            "water",
            "forest",
            "mountain",
            "desert",
            "snow",
            "lava",
        }

        actual_terrains = {terrain.name for terrain in TerrainType}
        assert actual_terrains == expected_terrains

    def test_walkable_terrains(self):
        """Test walkable terrain identification."""
        walkable_terrains = {
            terrain for terrain in TerrainType if terrain.value.walkable
        }

        # Grass, forest, desert should be walkable
        assert TerrainType.GRASS in walkable_terrains
        assert TerrainType.FOREST in walkable_terrains
        assert TerrainType.DESERT in walkable_terrains

        # Water, mountain, snow, lava should not be walkable
        assert TerrainType.WATER not in walkable_terrains
        assert TerrainType.MOUNTAIN not in walkable_terrains
        assert TerrainType.SNOW not in walkable_terrains
        assert TerrainType.LAVA not in walkable_terrains


class TestChunk:
    """Test suite for Chunk class functionality."""

    def test_chunk_creation(self):
        """Test creating a new chunk."""
        chunk = Chunk(x=0, y=0, size=16)

        assert chunk.x == 0
        assert chunk.y == 0
        assert chunk.size == 16
        assert len(chunk.terrain) == 16
        assert len(chunk.terrain[0]) == 16

        # Verify terrain types are valid
        for row in chunk.terrain:
            for terrain in row:
                assert isinstance(terrain, TerrainType)

    def test_chunk_coordinates(self):
        """Test chunk coordinate calculations."""
        chunk = Chunk(x=2, y=3, size=16)

        # World coordinates of chunk origin
        assert chunk.get_world_x() == 32  # 2 * 16
        assert chunk.get_world_y() == 48  # 3 * 16

    def test_chunk_terrain_at_coordinate(self):
        """Test getting terrain at specific coordinates within chunk."""
        chunk = Chunk(x=0, y=0, size=16)

        # Test various coordinates
        terrain = chunk.get_terrain_at(0, 0)
        assert isinstance(terrain, TerrainType)

        terrain = chunk.get_terrain_at(15, 15)
        assert isinstance(terrain, TerrainType)

        # Test out of bounds
        terrain = chunk.get_terrain_at(-1, 0)
        assert terrain is None

        terrain = chunk.get_terrain_at(16, 0)
        assert terrain is None

    def test_chunk_serialization(self):
        """Test chunk serialization to dict."""
        chunk = Chunk(x=1, y=2, size=8)

        data = chunk.to_dict()

        assert data["x"] == 1
        assert data["y"] == 2
        assert data["size"] == 8
        assert "terrain" in data
        assert len(data["terrain"]) == 8

        # Verify terrain serialization
        for row in data["terrain"]:
            for terrain_str in row:
                assert terrain_str in [t.name for t in TerrainType]

    def test_chunk_deserialization(self):
        """Test chunk deserialization from dict."""
        data = {"x": 3, "y": 4, "size": 8, "terrain": [["GRASS"] * 8 for _ in range(8)]}

        chunk = Chunk.from_dict(data)

        assert chunk.x == 3
        assert chunk.y == 4
        assert chunk.size == 8
        assert chunk.terrain[0][0] == TerrainType.GRASS

    def test_chunk_render(self):
        """Test chunk rendering to string."""
        chunk = Chunk(x=0, y=0, size=4)

        rendered = chunk.render()
        lines = rendered.split("\n")

        assert len(lines) == 4
        for line in lines:
            assert len(line) == 4

        # Each character should be a terrain emoji
        for line in lines:
            for char in line.strip():
                terrain_emojis = {t.value.emoji for t in TerrainType}
                assert char in terrain_emojis


class TestWorld:
    """Test suite for World class functionality."""

    @pytest.fixture
    def world(self):
        """Create a fresh World instance for each test."""
        return World(seed=42, chunk_size=16)

    def test_world_creation(self, world):
        """Test creating a new world."""
        assert world.seed == 42
        assert world.chunk_size == 16
        assert len(world.chunks) == 0
        assert world.noise_scale == 0.1

    def test_world_creation_with_custom_params(self):
        """Test creating world with custom parameters."""
        world = World(seed=123, chunk_size=32, noise_scale=0.05)

        assert world.seed == 123
        assert world.chunk_size == 32
        assert world.noise_scale == 0.05

    def test_chunk_coordinate_conversion(self, world):
        """Test converting world coordinates to chunk coordinates."""
        # Test positive coordinates
        chunk_x, chunk_y = world.world_to_chunk(25, 40)
        assert chunk_x == 1  # 25 // 16
        assert chunk_y == 2  # 40 // 16

        # Test negative coordinates
        chunk_x, chunk_y = world.world_to_chunk(-1, -1)
        assert chunk_x == -1  # Floor division
        assert chunk_y == -1

    def test_local_coordinate_conversion(self, world):
        """Test converting world coordinates to local chunk coordinates."""
        local_x, local_y = world.world_to_local(25, 40)
        assert local_x == 9  # 25 % 16
        assert local_y == 8  # 40 % 16

    def test_chunk_generation(self, world):
        """Test generating new chunks."""
        chunk = world.get_or_generate_chunk(0, 0)

        assert chunk is not None
        assert chunk.x == 0
        assert chunk.y == 0
        assert chunk.size == 16
        assert (0, 0) in world.chunks

        # Verify chunk is cached
        chunk2 = world.get_or_generate_chunk(0, 0)
        assert chunk is chunk2

    def test_multiple_chunk_generation(self, world):
        """Test generating multiple chunks."""
        chunks = []

        for x in range(-1, 2):
            for y in range(-1, 2):
                chunk = world.get_or_generate_chunk(x, y)
                chunks.append(chunk)

        assert len(chunks) == 9
        assert len(world.chunks) == 9

        # All chunks should be different instances
        unique_chunks = set(chunks)
        assert len(unique_chunks) == 9

    def test_chunk_generation_deterministic(self, world):
        """Test that chunk generation is deterministic."""
        chunk1 = world.get_or_generate_chunk(5, 10)
        chunk2 = world.get_or_generate_chunk(5, 10)

        # Remove and regenerate
        del world.chunks[(5, 10)]
        chunk3 = world.get_or_generate_chunk(5, 10)

        # Chunks should be identical
        assert chunk1.terrain == chunk2.terrain
        assert chunk1.terrain == chunk3.terrain

    def test_terrain_at_world_coordinate(self, world):
        """Test getting terrain at world coordinates."""
        # Generate chunk at (0, 0)
        world.get_or_generate_chunk(0, 0)

        # Test terrain at various coordinates
        terrain = world.get_terrain_at(0, 0)
        assert isinstance(terrain, TerrainType)

        terrain = world.get_terrain_at(15, 15)
        assert isinstance(terrain, TerrainType)

        # Test coordinates in different chunk
        terrain = world.get_terrain_at(16, 16)
        assert isinstance(terrain, TerrainType)

        # Test negative coordinates
        world.get_or_generate_chunk(-1, -1)
        terrain = world.get_terrain_at(-1, -1)
        assert isinstance(terrain, TerrainType)

    def test_terrain_at_unloaded_chunk(self, world):
        """Test getting terrain in chunk that hasn't been generated."""
        # This should auto-generate the chunk
        terrain = world.get_terrain_at(100, 100)
        assert isinstance(terrain, TerrainType)

        # Chunk should now be loaded
        assert (6, 6) in world.chunks  # 100 // 16 = 6

    def test_world_rendering(self, world):
        """Test rendering a portion of the world."""
        # Generate some chunks
        world.get_or_generate_chunk(0, 0)
        world.get_or_generate_chunk(1, 0)

        # Render a 32x16 area
        rendered = world.render_area(0, 0, 32, 16)
        lines = rendered.split("\n")

        assert len(lines) == 16
        for line in lines:
            assert len(line) == 32

    def test_world_rendering_with_chunks(self, world):
        """Test rendering specific chunks."""
        # Generate chunks
        chunks = []
        for x in range(-1, 2):
            for y in range(-1, 2):
                chunks.append(world.get_or_generate_chunk(x, y))

        # Render all generated chunks
        rendered = world.render_chunks(chunks)
        lines = rendered.split("\n")

        # Should render 3 chunks high (48 lines) and 3 chunks wide (48 chars)
        assert len(lines) == 48
        for line in lines:
            assert len(line) == 48

    def test_find_nearest_terrain(self, world):
        """Test finding nearest terrain type."""
        # Generate chunk
        world.get_or_generate_chunk(0, 0)

        # Find nearest grass (should always find something)
        x, y = world.find_nearest_terrain(0, 0, TerrainType.GRASS, max_radius=50)
        assert x is not None
        assert y is not None

        # Find nearest water
        x, y = world.find_nearest_terrain(0, 0, TerrainType.WATER, max_radius=50)
        # Might not find water in small area
        if x is not None:
            assert y is not None

    def test_world_serialization(self, world):
        """Test world serialization to dict."""
        # Generate some chunks
        world.get_or_generate_chunk(0, 0)
        world.get_or_generate_chunk(1, 1)

        data = world.to_dict()

        assert data["seed"] == 42
        assert data["chunk_size"] == 16
        assert data["noise_scale"] == 0.1
        assert "chunks" in data
        assert len(data["chunks"]) == 2

    def test_world_deserialization(self, world):
        """Test world deserialization from dict."""
        # Create and serialize a world
        world.get_or_generate_chunk(0, 0)
        data = world.to_dict()

        # Create new world from data
        new_world = World.from_dict(data)

        assert new_world.seed == 42
        assert new_world.chunk_size == 16
        assert len(new_world.chunks) == 1
        assert (0, 0) in new_world.chunks

    def test_chunk_memory_management(self, world):
        """Test that chunks are properly cached."""
        # Generate many chunks
        for i in range(10):
            world.get_or_generate_chunk(i, i)

        assert len(world.chunks) == 10

        # Access existing chunks
        for i in range(10):
            chunk = world.get_or_generate_chunk(i, i)
            assert chunk.x == i
            assert chunk.y == i

        # Should still have 10 chunks (no duplicates)
        assert len(world.chunks) == 10


class TestWorldService:
    """Test suite for WorldService functionality."""

    @pytest.fixture
    def world_service(self):
        """Create a fresh WorldService instance for each test."""
        return WorldService()

    def test_service_initialization(self, world_service):
        """Test WorldService initialization."""
        assert world_service.worlds == {}
        assert world_service.default_world_size == 1024
        assert world_service.max_chunks_per_world == 100

    def test_create_world(self, world_service):
        """Test creating a new world."""
        world_id = world_service.create_world(seed=123)

        assert world_id is not None
        assert world_id in world_service.worlds
        assert world_service.worlds[world_id].seed == 123

    def test_create_multiple_worlds(self, world_service):
        """Test creating multiple worlds."""
        world1_id = world_service.create_world(seed=100)
        world2_id = world_service.create_world(seed=200)

        assert world1_id != world2_id
        assert len(world_service.worlds) == 2
        assert world_service.worlds[world1_id].seed == 100
        assert world_service.worlds[world2_id].seed == 200

    def test_create_world_with_parameters(self, world_service):
        """Test creating world with custom parameters."""
        world_id = world_service.create_world(seed=42, chunk_size=32, world_size=2048)

        world = world_service.worlds[world_id]
        assert world.seed == 42
        assert world.chunk_size == 32

    def test_get_world(self, world_service):
        """Test retrieving a world."""
        world_id = world_service.create_world(seed=123)

        world = world_service.get_world(world_id)
        assert world is not None
        assert world.seed == 123

        # Test non-existent world
        world = world_service.get_world("non-existent")
        assert world is None

    def test_delete_world(self, world_service):
        """Test deleting a world."""
        world_id = world_service.create_world(seed=123)

        assert world_id in world_service.worlds

        result = world_service.delete_world(world_id)
        assert result is True
        assert world_id not in world_service.worlds

        # Test deleting non-existent world
        result = world_service.delete_world("non-existent")
        assert result is False

    def test_get_world_info(self, world_service):
        """Test getting world information."""
        world_id = world_service.create_world(seed=123)
        world = world_service.worlds[world_id]

        # Generate some chunks
        world.get_or_generate_chunk(0, 0)
        world.get_or_generate_chunk(1, 1)

        info = world_service.get_world_info(world_id)

        assert info["world_id"] == world_id
        assert info["seed"] == 123
        assert info["chunk_size"] == 16
        assert info["loaded_chunks"] == 2
        assert "created_at" in info

        # Test non-existent world
        info = world_service.get_world_info("non-existent")
        assert info is None

    def test_generate_area(self, world_service):
        """Test generating area in world."""
        world_id = world_service.create_world(seed=42)

        area_data = world_service.generate_area(world_id, 0, 0, 32, 32)

        assert "x" in area_data
        assert "y" in area_data
        assert "width" in area_data
        assert "height" in area_data
        assert "rendered" in area_data
        assert "chunks_generated" in area_data

        assert area_data["x"] == 0
        assert area_data["y"] == 0
        assert area_data["width"] == 32
        assert area_data["height"] == 32
        assert len(area_data["rendered"].split("\n")) == 32
        assert area_data["chunks_generated"] >= 1

    def test_explore_location(self, world_service):
        """Test exploring a specific location."""
        world_id = world_service.create_world(seed=42)

        exploration = world_service.explore_location(world_id, 50, 50)

        assert "x" in exploration
        assert "y" in exploration
        assert "terrain" in exploration
        assert "chunk_x" in exploration
        assert "chunk_y" in exploration
        assert "local_x" in exploration
        assert "local_y" in exploration
        assert "surrounding_area" in exploration

        assert exploration["x"] == 50
        assert exploration["y"] == 50
        assert exploration["terrain"] in [t.name for t in TerrainType]
        assert exploration["chunk_x"] == 3  # 50 // 16
        assert exploration["chunk_y"] == 3  # 50 // 16
        assert exploration["local_x"] == 2  # 50 % 16
        assert exploration["local_y"] == 2  # 50 % 16

    def test_find_terrain(self, world_service):
        """Test finding specific terrain type."""
        world_id = world_service.create_world(seed=42)

        # Find nearest grass
        result = world_service.find_terrain(world_id, 0, 0, "GRASS", 100)

        assert "from_x" in result
        assert "from_y" in result
        assert "terrain_type" in result
        assert "found" in result
        assert "locations" in result

        assert result["from_x"] == 0
        assert result["from_y"] == 0
        assert result["terrain_type"] == "GRASS"

        if result["found"]:
            assert len(result["locations"]) > 0
            for location in result["locations"]:
                assert "x" in location
                assert "y" in location
                assert "distance" in location

    def test_world_statistics(self, world_service):
        """Test getting world statistics."""
        world_id = world_service.create_world(seed=42)
        world = world_service.worlds[world_id]

        # Generate some chunks
        for x in range(2):
            for y in range(2):
                world.get_or_generate_chunk(x, y)

        stats = world_service.get_world_statistics(world_id)

        assert "world_id" in stats
        assert "total_chunks" in stats
        assert "loaded_chunks" in stats
        assert "terrain_distribution" in stats
        assert "walkable_percentage" in stats

        assert stats["world_id"] == world_id
        assert stats["total_chunks"] == 4
        assert stats["loaded_chunks"] == 4

        # Check terrain distribution
        terrain_dist = stats["terrain_distribution"]
        for terrain_name in TerrainType.__members__:
            assert terrain_name in terrain_dist
            assert isinstance(terrain_dist[terrain_name], int)

        # Check walkable percentage
        assert 0 <= stats["walkable_percentage"] <= 100

    def test_cleanup_old_worlds(self, world_service):
        """Test cleanup of old worlds."""
        # Create some worlds
        world1_id = world_service.create_world(seed=1)
        world2_id = world_service.create_world(seed=2)

        assert len(world_service.worlds) == 2

        # Cleanup (keeping 1 world)
        cleaned = world_service.cleanup_old_worlds(keep_count=1)

        assert cleaned == 1
        assert len(world_service.worlds) == 1

        # Should keep the most recent world
        remaining_worlds = list(world_service.worlds.keys())
        assert world2_id in remaining_worlds
        assert world1_id not in remaining_worlds

    def test_terrain_validation(self, world_service):
        """Test terrain type validation."""
        # Valid terrain types
        for terrain_name in TerrainType.__members__:
            assert world_service._validate_terrain_type(terrain_name) is True

        # Invalid terrain types
        assert world_service._validate_terrain_type("invalid") is False
        assert world_service._validate_terrain_type("") is False
        assert world_service._validate_terrain_type(None) is False

    def test_coordinate_validation(self, world_service):
        """Test coordinate validation."""
        # Valid coordinates
        assert world_service._validate_coordinates(0, 0) is True
        assert world_service._validate_coordinates(100, 100) is True
        assert world_service._validate_coordinates(-100, -100) is True

        # Invalid coordinates
        assert world_service._validate_coordinates(None, 0) is False
        assert world_service._validate_coordinates(0, None) is False
        assert world_service._validate_coordinates("invalid", 0) is False

    def test_world_size_limits(self, world_service):
        """Test world size limits enforcement."""
        # Test within limits
        world_id = world_service.create_world(seed=42, world_size=100)
        assert world_id in world_service.worlds

        # Test exceeding limits (should work but warning logged)
        world_id = world_service.create_world(seed=43, world_size=10000)
        assert world_id in world_service.worlds

    def test_chunk_limit_enforcement(self, world_service):
        """Test chunk generation limits."""
        world_id = world_service.create_world(seed=42)
        world = world_service.worlds[world_id]

        # Generate chunks up to limit
        for i in range(world_service.max_chunks_per_world):
            world.get_or_generate_chunk(i, 0)

        assert len(world.chunks) == world_service.max_chunks_per_world

        # Try to generate one more (should be handled gracefully)
        world.get_or_generate_chunk(1000, 1000)
        # Implementation-dependent how this is handled

    def test_concurrent_world_access(self, world_service):
        """Test concurrent access to worlds."""
        world_id = world_service.create_world(seed=42)

        async def access_world():
            world = world_service.get_world(world_id)
            if world:
                return world.get_or_generate_chunk(0, 0)
            return None

        # Run concurrent access
        tasks = [access_world() for _ in range(10)]
        chunks = asyncio.run(asyncio.gather(*tasks))

        # All should succeed
        assert all(chunk is not None for chunk in chunks)

    def test_performance_large_area_rendering(self, world_service):
        """Test performance of rendering large areas."""
        world_id = world_service.create_world(seed=42)

        import time

        start_time = time.time()

        # Render large area
        area_data = world_service.generate_area(world_id, 0, 0, 256, 256)

        elapsed_time = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed_time < 2.0  # 2 seconds max
        assert len(area_data["rendered"].split("\n")) == 256

    def test_memory_usage_monitoring(self, world_service):
        """Test memory usage with many worlds."""
        initial_worlds = len(world_service.worlds)

        # Create many worlds
        world_ids = []
        for i in range(50):
            world_id = world_service.create_world(seed=i)
            world_ids.append(world_id)

        # Check all worlds are created
        assert len(world_service.worlds) == initial_worlds + 50

        # Generate chunks in each world
        for world_id in world_ids[:10]:  # Only first 10 to avoid excessive memory
            world_service.generate_area(world_id, 0, 0, 64, 64)

        # Cleanup
        world_service.cleanup_old_worlds(keep_count=5)
        assert len(world_service.worlds) <= 5

    def test_error_handling_invalid_world_id(self, world_service):
        """Test error handling with invalid world IDs."""
        # Test operations with non-existent world
        result = world_service.generate_area("invalid", 0, 0, 32, 32)
        assert result is None

        result = world_service.explore_location("invalid", 0, 0)
        assert result is None

        result = world_service.find_terrain("invalid", 0, 0, "GRASS", 100)
        assert result is None

        result = world_service.get_world_statistics("invalid")
        assert result is None

    def test_service_statistics(self, world_service):
        """Test getting overall service statistics."""
        # Create some worlds
        for i in range(3):
            world_service.create_world(seed=i)

        stats = world_service.get_service_statistics()

        assert "total_worlds" in stats
        assert "total_loaded_chunks" in stats
        assert "memory_usage_estimate" in stats
        assert "oldest_world_age" in stats

        assert stats["total_worlds"] == 3
        assert stats["total_loaded_chunks"] >= 0
        assert isinstance(stats["memory_usage_estimate"], int)
        assert isinstance(stats["oldest_world_age"], (int, float))


class TestWorldServiceIntegration:
    """Integration tests for WorldService with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_world_lifecycle(self, world_service):
        """Test complete world lifecycle."""
        # Create world
        world_id = world_service.create_world(seed=12345)

        # Generate initial area
        spawn_area = world_service.generate_area(world_id, 0, 0, 64, 64)
        assert spawn_area["chunks_generated"] >= 1

        # Explore locations
        exploration = world_service.explore_location(world_id, 32, 32)
        assert exploration["terrain"] in [t.name for t in TerrainType]

        # Find resources
        water_result = world_service.find_terrain(world_id, 0, 0, "WATER", 200)
        if water_result["found"]:
            assert len(water_result["locations"]) > 0

        # Get statistics
        stats = world_service.get_world_statistics(world_id)
        assert stats["loaded_chunks"] >= 1

        # Cleanup
        deleted = world_service.delete_world(world_id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_multi_world_scenario(self, world_service):
        """Test managing multiple worlds simultaneously."""
        # Create different types of worlds
        worlds = {
            "peaceful": world_service.create_world(seed=100, world_size=512),
            "mountainous": world_service.create_world(seed=200, world_size=1024),
            "desert": world_service.create_world(seed=300, world_size=512),
        }

        # Generate areas in each world
        for world_name, world_id in worlds.items():
            area = world_service.generate_area(world_id, 0, 0, 32, 32)
            assert area["chunks_generated"] >= 1

        # Verify all worlds exist
        assert len(world_service.worlds) == 3

        # Get info for all worlds
        for world_name, world_id in worlds.items():
            info = world_service.get_world_info(world_id)
            assert info is not None

        # Cleanup some worlds
        world_service.delete_world(worlds["desert"])
        assert len(world_service.worlds) == 2

    @pytest.mark.asyncio
    async def test_exploration_scenario(self, world_service):
        """Test a complete exploration scenario."""
        world_id = world_service.create_world(seed=999)

        # Start at origin
        current_x, current_y = 0, 0
        exploration_log = []

        # Explore in a pattern
        directions = [(16, 0), (0, 16), (-16, 0), (0, -16)]
        for dx, dy in directions * 3:
            current_x += dx
            current_y += dy

            # Explore current location
            exploration = world_service.explore_location(world_id, current_x, current_y)
            exploration_log.append(exploration)

            # Find water if current terrain is not walkable
            if exploration["terrain"] in ["WATER", "LAVA", "MOUNTAIN", "SNOW"]:
                water_result = world_service.find_terrain(
                    world_id, current_x, current_y, "GRASS", 50
                )
                if water_result["found"]:
                    # Move to nearest walkable terrain
                    nearest = water_result["locations"][0]
                    current_x, current_y = nearest["x"], nearest["y"]

        # Verify exploration progress
        assert len(exploration_log) > 0
        visited_terrains = {log["terrain"] for log in exploration_log}
        assert len(visited_terrains) > 1

    @pytest.mark.asyncio
    async def test_performance_load_test(self, world_service):
        """Test service performance under load."""
        # Create multiple worlds
        world_ids = []
        for i in range(5):
            world_ids.append(world_service.create_world(seed=i))

        import time

        start_time = time.time()

        # Perform concurrent operations
        tasks = []
        for world_id in world_ids:
            for _ in range(10):
                tasks.append(
                    asyncio.create_task(
                        asyncio.to_thread(
                            world_service.generate_area, world_id, 0, 0, 32, 32
                        )
                    )
                )

        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time

        # Verify all operations succeeded
        assert all(result is not None for result in results)
        assert elapsed_time < 5.0  # Should complete within 5 seconds

        # Verify service state
        assert len(world_service.worlds) == 5
        total_chunks = sum(len(world.chunks) for world in world_service.worlds.values())
        assert total_chunks > 0
