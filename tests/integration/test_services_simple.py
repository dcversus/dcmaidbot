"""
Simple Integration Tests for Services
====================================

Integration tests that work with the actual service implementations.
"""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import services that don't require complex setup
from services.friend_service import FriendService
from services.metrics_service import MetricsService, get_metrics_service
from services.rag_service import RAGService, get_rag_service
from services.world_service import WorldService


class TestRAGServiceIntegration:
    """Integration tests for RAGService."""

    @pytest.mark.asyncio
    async def test_rag_service_without_chromadb(self):
        """Test RAGService works without ChromaDB."""
        service = RAGService()
        await service.initialize()

        assert service.initialized is True
        assert service.client is None
        assert service.collection is None

        # Should return False for operations when not available
        result = await service.add_document("test", "content")
        assert result is False

        results = await service.search("query")
        assert results == []

        health = await service.health_check()
        assert health["status"] == "healthy"
        assert health["chromadb_available"] is False

    @pytest.mark.asyncio
    async def test_rag_service_singleton(self):
        """Test RAGService singleton pattern."""
        service1 = await get_rag_service()
        service2 = await get_rag_service()

        assert service1 is service2


class TestMetricsServiceIntegration:
    """Integration tests for MetricsService."""

    def test_metrics_service_basic_functionality(self):
        """Test MetricsService basic functionality without starting server."""
        service = MetricsService(port=0)  # Port 0 for testing

        # Test initial state
        assert service.running is False
        assert service.message_count == 0
        assert service.command_count == 0

        # Test incrementing counters
        service.increment_message_count()
        service.increment_message_count()
        assert service.message_count == 2

        service.increment_command_count("test")
        assert service.command_count == 1
        assert service.command_types["test"] == 1

        service.increment_error_count("timeout")
        assert service.error_count == 1

        service.record_user_activity(123)
        assert 123 in service.user_activity

        # Test health check
        health = service.health_check()
        assert health["status"] == "unhealthy"
        assert health["server_running"] is False
        assert health["metrics"]["messages_total"] == 2

        # Test metrics output
        metrics = service.get_prometheus_metrics()
        assert "dcmaidbot_messages_total 2" in metrics
        assert "dcmaidbot_commands_total 1" in metrics
        assert "dcmaidbot_errors_total 1" in metrics

        # Test metrics summary
        summary = service.get_metrics_summary()
        assert summary["messages_total"] == 2
        assert summary["commands_total"] == 1
        assert summary["errors_total"] == 1
        assert "uptime_seconds" in summary

    @pytest.mark.asyncio
    async def test_metrics_service_singleton(self):
        """Test MetricsService singleton pattern."""
        service1 = await get_metrics_service()
        service2 = await get_metrics_service()

        assert service1 is service2


class TestWorldServiceIntegration:
    """Integration tests for WorldService."""

    def test_world_service_basic_functionality(self):
        """Test WorldService basic functionality."""
        service = WorldService()

        # Test creating worlds
        world_id = service.create_world(seed=42)
        assert world_id is not None
        assert world_id in service.worlds

        world = service.get_world(world_id)
        assert world is not None
        assert world.seed == 42

        # Test world info
        info = service.get_world_info(world_id)
        assert info is not None
        assert info["world_id"] == world_id
        assert info["seed"] == 42
        assert info["loaded_chunks"] == 0

        # Test generating area
        area_data = service.generate_area(world_id, 0, 0, 32, 32)
        assert area_data is not None
        assert area_data["x"] == 0
        assert area_data["y"] == 0
        assert area_data["width"] == 32
        assert area_data["height"] == 32
        assert "rendered" in area_data
        assert "chunks_generated" in area_data

        # Test exploring location
        exploration = service.explore_location(world_id, 16, 16)
        assert exploration is not None
        assert exploration["x"] == 16
        assert exploration["y"] == 16
        assert "terrain" in exploration
        assert "chunk_x" in exploration
        assert "chunk_y" in exploration

        # Test world statistics
        stats = service.get_world_statistics(world_id)
        assert stats is not None
        assert "terrain_distribution" in stats
        assert "walkable_percentage" in stats

        # Test finding terrain
        result = service.find_terrain(world_id, 0, 0, "GRASS", 100)
        assert result is not None
        assert "from_x" in result
        assert "from_y" in result
        assert "terrain_type" in result
        assert "found" in result

        # Test service statistics
        service_stats = service.get_service_statistics()
        assert service_stats is not None
        assert "total_worlds" in service_stats
        assert service_stats["total_worlds"] == 1

        # Test cleanup
        deleted = service.delete_world(world_id)
        assert deleted is True
        assert world_id not in service.worlds

    def test_world_service_terrain_validation(self):
        """Test terrain type validation."""
        service = WorldService()

        # Valid terrain types
        assert service._validate_terrain_type("GRASS") is True
        assert service._validate_terrain_type("WATER") is True
        assert service._validate_terrain_type("FOREST") is True
        assert service._validate_terrain_type("MOUNTAIN") is True
        assert service._validate_terrain_type("DESERT") is True
        assert service._validate_terrain_type("SNOW") is True
        assert service._validate_terrain_type("LAVA") is True

        # Invalid terrain types
        assert service._validate_terrain_type("INVALID") is False
        assert service._validate_terrain_type("") is False
        assert service._validate_terrain_type(None) is False

    def test_world_service_coordinate_validation(self):
        """Test coordinate validation."""
        service = WorldService()

        # Valid coordinates
        assert service._validate_coordinates(0, 0) is True
        assert service._validate_coordinates(100, 100) is True
        assert service._validate_coordinates(-100, -100) is True

        # Invalid coordinates
        assert service._validate_coordinates(None, 0) is False
        assert service._validate_coordinates(0, None) is False

    def test_world_service_multiple_worlds(self):
        """Test managing multiple worlds."""
        service = WorldService()

        # Create multiple worlds
        world_ids = []
        for i in range(3):
            world_id = service.create_world(seed=i)
            world_ids.append(world_id)

        assert len(world_ids) == 3
        assert len(service.worlds) == 3

        # Generate areas in each world
        for world_id in world_ids:
            area = service.generate_area(world_id, 0, 0, 16, 16)
            assert area is not None

        # Cleanup all worlds
        for world_id in world_ids:
            service.delete_world(world_id)

        assert len(service.worlds) == 0


class TestFriendServiceIntegration:
    """Integration tests for FriendService."""

    @pytest.mark.asyncio
    async def test_friend_service_validation(self):
        """Test FriendService validation."""
        service = FriendService()

        # Test adding self as friend
        result = await service.add_friend(123, 123)
        assert result["success"] is False
        assert "Cannot add yourself" in result["error"]

        # Test adding another user (without database)
        result = await service.add_friend(123, 456)
        # Should handle gracefully without database

        # Test getting friends (without database)
        result = await service.get_friends(123)
        # Should handle gracefully without database

    def test_friend_service_basic_state(self):
        """Test FriendService basic state management."""
        service = FriendService()

        # Should initialize with empty state
        assert hasattr(service, "pending_requests")
        assert isinstance(service.pending_requests, dict)


class TestServicesCooperation:
    """Test services working together."""

    @pytest.mark.asyncio
    async def test_services_basic_cooperation(self):
        """Test basic services cooperation."""
        # Create services
        rag_service = RAGService()
        metrics_service = MetricsService(port=0)
        world_service = WorldService()
        friend_service = FriendService()

        # Initialize RAG service
        await rag_service.initialize()
        assert rag_service.initialized is True

        # Use metrics service to track operations
        metrics_service.increment_message_count()
        metrics_service.increment_command_count("start")
        metrics_service.record_user_activity(123)

        # Create world for user
        world_id = world_service.create_world(seed=12345)
        assert world_id is not None

        # Generate area in world
        area_data = world_service.generate_area(world_id, 0, 0, 32, 32)
        assert area_data is not None
        metrics_service.increment_command_count("world_generate")

        # Test friend service
        await friend_service.add_friend(123, 456)
        # Should not crash

        # Get final metrics
        summary = metrics_service.get_metrics_summary()
        assert summary["messages_total"] == 1
        assert summary["commands_total"] == 2
        assert summary["active_users_1h"] == 1

        # Clean up
        world_service.delete_world(world_id)

    def test_services_error_resilience(self):
        """Test services are resilient to errors."""
        services = [
            RAGService(),
            MetricsService(port=0),
            WorldService(),
            FriendService(),
        ]

        # All services should initialize without errors
        for service in services:
            assert service is not None

        # Services should handle basic operations
        for service in services:
            try:
                # Basic operations that shouldn't raise exceptions
                if hasattr(service, "validate_user_id"):
                    result = service.validate_user_id(123)
                    assert isinstance(result, bool)
            except AttributeError:
                # Service doesn't have this method, that's OK
                pass
            except Exception as e:
                pytest.fail(
                    f"Service {service.__class__.__name__} raised exception: {e}"
                )

    def test_world_service_performance(self):
        """Test WorldService performance with larger areas."""
        service = WorldService()
        world_id = service.create_world(seed=42)

        import time

        start_time = time.time()

        # Generate larger area
        area_data = service.generate_area(world_id, 0, 0, 64, 64)

        elapsed_time = time.time() - start_time

        assert area_data is not None
        assert elapsed_time < 2.0  # Should complete within 2 seconds

        # Clean up
        service.delete_world(world_id)
