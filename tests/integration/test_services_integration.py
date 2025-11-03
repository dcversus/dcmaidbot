"""
Integration Tests for All Services
==================================

Integration tests that verify the actual implementation works correctly.
These tests are designed to work with the existing test infrastructure.
"""

import asyncio
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import all services
from core.services.friend_service import FriendService
from core.services.metrics_service import MetricsService, get_metrics_service
from core.services.rag_service import RAGService, get_rag_service
from core.services.tool_service import ToolService
from core.services.world_service import WorldService


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

    @pytest.mark.asyncio
    async def test_metrics_service_basic_functionality(self):
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


class TestFriendServiceIntegration:
    """Integration tests for FriendService."""

    @pytest.mark.asyncio
    async def test_friend_service_validation(self):
        """Test FriendService validation."""
        service = FriendService()

        # Test user ID validation
        assert service.validate_user_id(123) is True
        assert service.validate_user_id(1) is True
        assert service.validate_user_id(0) is False
        assert service.validate_user_id(-1) is False
        assert service.validate_user_id(None) is False

        # Test blocked users
        service.blocked_users.add(456)

        assert await service.is_blocked(123, 456) is True
        assert await service.is_blocked(123, 789) is False

        # Test interaction permissions
        assert await service.can_interact(123, 456) is False
        assert await service.can_interact(123, 789) is True

    @pytest.mark.asyncio
    async def test_friend_service_error_handling(self):
        """Test FriendService error handling."""
        service = FriendService()

        # Test operations without database
        await service.send_friend_request(123, 456)
        # Should handle gracefully without database

        await service.accept_friend_request(123, 456)
        # Should handle gracefully without database

        await service.get_friends_list(123)
        # Should handle gracefully without database

    @pytest.mark.asyncio
    async def test_friend_service_basic_operations(self):
        """Test FriendService basic operations."""
        service = FriendService()

        # Test adding self as friend
        result = await service.add_friend(123, 123)
        assert result["success"] is False
        assert "Cannot add yourself" in result["error"]

        # Test operations without database (should handle gracefully)
        result = await service.add_friend(123, 456)
        # Should not crash without database

        result = await service.get_friends(123)
        # Should not crash without database

        result = await service.remove_friend(123, 456)
        # Should not crash without database


class TestToolServiceIntegration:
    """Integration tests for ToolService."""

    @pytest.mark.asyncio
    async def test_tool_service_without_api_keys(self):
        """Test ToolService behavior without API keys."""
        service = ToolService()

        # Test search without SERPAPI key
        result = await service.web_search(123, "test query")
        # Should handle gracefully without API key

        # Test URL validation
        safe_urls = [
            "https://example.com",
            "https://httpbin.org/get",
            "https://jsonplaceholder.typicode.com/posts/1",
        ]

        for url in safe_urls:
            result = service.validate_url(url)
            assert result["valid"] is True

        # Test unsafe URLs
        unsafe_urls = [
            "file:///etc/passwd",
            "http://localhost:3000",
            "javascript:alert(1)",
            "not-a-url",
        ]

        for url in unsafe_urls:
            result = service.validate_url(url)
            assert result["valid"] is False

    def test_tool_service_basic_functionality(self):
        """Test ToolService basic functionality."""
        service = ToolService()

        # Test rate limiting
        user_id = 123
        result1 = service.check_rate_limit(user_id)
        assert result1["allowed"] is True
        assert result1["remaining"] > 0

        result2 = service.check_rate_limit(user_id)
        assert result2["allowed"] is True
        assert result2["remaining"] < result1["remaining"]

        # Test threat detection
        threats = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "; ls -la",
            "../../../etc/passwd",
        ]

        for threat in threats:
            result = service.detect_threats(threat)
            # Should detect basic threats
            assert isinstance(result, dict)
            assert "detected" in result

    def test_tool_service_url_validation(self):
        """Test URL validation in detail."""
        service = ToolService()

        # Valid URLs
        valid_urls = [
            "https://example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://api.example.com/v1/users",
            "https://jsonplaceholder.typicode.com/posts/1",
        ]

        for url in valid_urls:
            result = service.validate_url(url)
            assert result["valid"] is True, f"URL should be valid: {url}"

        # Invalid URLs
        invalid_urls = [
            "ftp://example.com",  # Unsupported protocol
            "file:///etc/passwd",
            "http://localhost:3000",
            "http://127.0.0.1:8080",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "not-a-url",
            "",
            None,
        ]

        for url in invalid_urls:
            if url is not None:
                result = service.validate_url(url)
                assert result["valid"] is False, f"URL should be invalid: {url}"


class TestServicesIntegration:
    """Integration tests for all services working together."""

    @pytest.mark.asyncio
    async def test_services_cooperation(self):
        """Test services working together."""
        # Create instances of all services
        rag_service = RAGService()
        metrics_service = MetricsService(port=0)
        world_service = WorldService()
        friend_service = FriendService()
        tool_service = ToolService()

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

        # Test friend service validation
        assert friend_service.validate_user_id(123) is True
        assert friend_service.validate_user_id(456) is True

        # Test tool service validation
        assert tool_service.validate_url("https://example.com")["valid"] is True
        assert tool_service.validate_url("file:///etc/passwd")["valid"] is False

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
            ToolService(),
        ]

        # All services should initialize without errors
        for service in services:
            assert service is not None

        # Services should handle invalid inputs gracefully
        for service in services:
            try:
                # Try basic operations that shouldn't raise exceptions
                if hasattr(service, "health_check"):
                    if asyncio.iscoroutinefunction(service.health_check):
                        # Skip async health checks in sync test
                        continue
                    health = service.health_check()
                    assert health is not None

                if hasattr(service, "validate_user_id"):
                    assert service.validate_user_id(123) is True
                    assert service.validate_user_id(-1) is False

                if hasattr(service, "validate_url"):
                    result = service.validate_url("https://example.com")
                    assert result is not None
            except Exception as e:
                pytest.fail(
                    f"Service {service.__class__.__name__} raised exception: {e}"
                )

    @pytest.mark.asyncio
    async def test_services_configuration(self):
        """Test services with different configurations."""
        # Test different configurations
        configs = [
            {"seed": 42, "chunk_size": 8},
            {"seed": 123, "chunk_size": 32},
            {"seed": 999, "chunk_size": 16},
        ]

        worlds = []
        for config in configs:
            world_service = WorldService()
            world_id = world_service.create_world(**config)
            worlds.append((world_service, world_id))

            # Verify configuration
            info = world_service.get_world_info(world_id)
            assert info["seed"] == config["seed"]

        # Clean up
        for world_service, world_id in worlds:
            world_service.delete_world(world_id)
