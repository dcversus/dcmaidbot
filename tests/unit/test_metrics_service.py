"""
Comprehensive Tests for MetricsService
======================================

Test suite for MetricsService functionality including HTTP server,
Prometheus metrics collection, and service lifecycle management.
"""

import asyncio
import json
import os

# Import the service we're testing
import sys
import threading
import time
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.services.metrics_service import (
    MetricsHandler,
    MetricsService,
    get_metrics_service,
)


class TestMetricsService:
    """Test suite for MetricsService functionality."""

    @pytest.fixture
    def metrics_service(self):
        """Create a fresh MetricsService instance for each test."""
        return MetricsService(port=0)  # Port 0 to avoid conflicts

    def test_initialization(self, metrics_service):
        """Test MetricsService initialization."""
        assert metrics_service.port == 0
        assert metrics_service.server is None
        assert metrics_service.server_thread is None
        assert metrics_service.running is False
        assert metrics_service.message_count == 0
        assert metrics_service.command_count == 0
        assert metrics_service.error_count == 0
        assert metrics_service.bot_starts == 0
        assert metrics_service.start_time > 0
        assert metrics_service.command_types == {}
        assert metrics_service.user_activity == {}

    def test_initialization_with_custom_port(self):
        """Test MetricsService initialization with custom port."""
        service = MetricsService(port=9999)
        assert service.port == 9999

    @pytest.mark.asyncio
    async def test_start_server(self, metrics_service):
        """Test starting the metrics HTTP server."""
        await metrics_service.start()

        assert metrics_service.running is True
        assert metrics_service.server is not None
        assert metrics_service.server_thread is not None
        assert metrics_service.bot_starts == 1

        # Clean up
        await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_start_server_already_running(self, metrics_service):
        """Test starting server when already running."""
        await metrics_service.start()
        initial_starts = metrics_service.bot_starts

        # Try to start again
        await metrics_service.start()

        # Should not increment starts
        assert metrics_service.bot_starts == initial_starts

        await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_start_server_error(self, metrics_service):
        """Test handling of server start errors."""
        with patch("services.metrics_service.HTTPServer") as mock_server:
            mock_server.side_effect = Exception("Port in use")

            await metrics_service.start()

            assert metrics_service.running is False
            assert metrics_service.server is None

    @pytest.mark.asyncio
    async def test_stop_server(self, metrics_service):
        """Test stopping the metrics HTTP server."""
        await metrics_service.start()
        assert metrics_service.running is True

        await metrics_service.stop()

        assert metrics_service.running is False
        assert metrics_service.server is None
        assert metrics_service.server_thread is None

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self, metrics_service):
        """Test stopping server when not running."""
        # Should not raise error
        await metrics_service.stop()

        assert metrics_service.running is False

    @pytest.mark.asyncio
    async def test_stop_server_error_handling(self, metrics_service):
        """Test handling of server stop errors."""
        await metrics_service.start()

        # Mock server to raise exception on shutdown
        with patch.object(
            metrics_service.server, "shutdown", side_effect=Exception("Stop error")
        ):
            # Should not raise exception
            await metrics_service.stop()

    def test_increment_message_count(self, metrics_service):
        """Test incrementing message counter."""
        initial_count = metrics_service.message_count
        metrics_service.increment_message_count()
        assert metrics_service.message_count == initial_count + 1

        # Increment multiple times
        for _ in range(10):
            metrics_service.increment_message_count()
        assert metrics_service.message_count == initial_count + 11

    def test_increment_command_count(self, metrics_service):
        """Test incrementing command counter with types."""
        initial_count = metrics_service.command_count
        initial_time = metrics_service.last_command_time

        # Test with default type
        metrics_service.increment_command_count()
        assert metrics_service.command_count == initial_count + 1
        assert metrics_service.command_types["unknown"] == 1
        assert metrics_service.last_command_time > initial_time

        # Test with custom type
        metrics_service.increment_command_count("start")
        assert metrics_service.command_count == initial_count + 2
        assert metrics_service.command_types["start"] == 1
        assert metrics_service.command_types["unknown"] == 1

        # Test multiple same type
        metrics_service.increment_command_count("start")
        metrics_service.increment_command_count("start")
        assert metrics_service.command_types["start"] == 3

    def test_increment_error_count(self, metrics_service):
        """Test incrementing error counter."""
        initial_count = metrics_service.error_count

        metrics_service.increment_error_count()
        assert metrics_service.error_count == initial_count + 1

        # Test with custom error type
        metrics_service.increment_error_count("timeout")
        assert metrics_service.error_count == initial_count + 2

    def test_record_user_activity(self, metrics_service):
        """Test recording user activity."""
        user_id = 12345

        metrics_service.record_user_activity(user_id)
        assert user_id in metrics_service.user_activity
        assert metrics_service.user_activity[user_id] > 0

        # Update same user
        time.sleep(0.01)
        metrics_service.record_user_activity(user_id)
        assert metrics_service.user_activity[user_id] > 0

        # Record multiple users
        for uid in [111, 222, 333]:
            metrics_service.record_user_activity(uid)

        assert len(metrics_service.user_activity) == 4

    def test_get_prometheus_metrics_format(self, metrics_service):
        """Test Prometheus metrics output format."""
        # Add some data
        metrics_service.increment_message_count()
        metrics_service.increment_message_count()
        metrics_service.increment_command_count("start")
        metrics_service.increment_command_count("help")
        metrics_service.record_user_activity(123)
        metrics_service.record_user_activity(456)

        metrics_output = metrics_service.get_prometheus_metrics()

        # Check required fields are present
        assert "dcmaidbot_messages_total" in metrics_output
        assert "dcmaidbot_commands_total" in metrics_output
        assert "dcmaidbot_errors_total" in metrics_output
        assert "dcmaidbot_bot_starts_total" in metrics_output
        assert "dcmaidbot_uptime_seconds" in metrics_output
        assert "dcmaidbot_active_users" in metrics_output
        assert "dcmaidbot_command_type_count" in metrics_output
        assert "dcmaidbot_last_command_timestamp" in metrics_output

        # Check HELP comments
        assert "# HELP" in metrics_output
        assert "# TYPE" in metrics_output

        # Check values
        assert "dcmaidbot_messages_total 2" in metrics_output
        assert "dcmaidbot_commands_total 2" in metrics_output
        assert 'dcmaidbot_command_type_count{command_type="start"} 1' in metrics_output
        assert 'dcmaidbot_command_type_count{command_type="help"} 1' in metrics_output

    def test_get_prometheus_metrics_empty(self, metrics_service):
        """Test Prometheus metrics with no data."""
        metrics_output = metrics_service.get_prometheus_metrics()

        # Should have all metric types with default values
        assert "dcmaidbot_messages_total 0" in metrics_output
        assert "dcmaidbot_commands_total 0" in metrics_output
        assert "dcmaidbot_errors_total 0" in metrics_output
        assert "dcmaidbot_bot_starts_total 0" in metrics_output

    def test_health_check_healthy(self, metrics_service):
        """Test health check when service is healthy."""
        # Add some data
        metrics_service.increment_message_count()
        metrics_service.increment_command_count("test")
        metrics_service.record_user_activity(123)

        health = metrics_service.health_check()

        assert health["status"] == "unhealthy"  # Not running yet
        assert health["server_running"] is False
        assert health["port"] == 0
        assert health["uptime_seconds"] >= 0
        assert "metrics" in health
        assert health["metrics"]["messages_total"] == 1
        assert health["metrics"]["commands_total"] == 1
        assert health["metrics"]["errors_total"] == 0
        assert health["metrics"]["active_users"] == 1

    @pytest.mark.asyncio
    async def test_health_check_running(self, metrics_service):
        """Test health check when server is running."""
        await metrics_service.start()

        health = metrics_service.health_check()

        assert health["status"] == "healthy"
        assert health["server_running"] is True

        await metrics_service.stop()

    def test_get_metrics_summary(self, metrics_service):
        """Test getting metrics summary."""
        # Add test data
        metrics_service.increment_message_count()
        metrics_service.increment_message_count()
        metrics_service.increment_command_count("start")
        metrics_service.increment_error_count("timeout")
        metrics_service.record_user_activity(123)

        summary = metrics_service.get_metrics_summary()

        assert "uptime_seconds" in summary
        assert "messages_total" in summary
        assert "commands_total" in summary
        assert "errors_total" in summary
        assert "messages_per_minute" in summary
        assert "command_types" in summary
        assert "active_users_1h" in summary
        assert "active_users_24h" in summary

        assert summary["messages_total"] == 2
        assert summary["commands_total"] == 1
        assert summary["errors_total"] == 1
        assert summary["command_types"] == {"start": 1}
        assert summary["active_users_1h"] == 1
        assert summary["active_users_24h"] == 1

    def test_active_users_calculation(self, metrics_service):
        """Test active users calculation with different time windows."""
        now = time.time()

        # Add users active at different times
        metrics_service.record_user_activity(111)
        metrics_service.record_user_activity(222)
        metrics_service.record_user_activity(333)

        # Mock time for testing
        with patch("time.time", return_value=now):
            summary = metrics_service.get_metrics_summary()
            assert summary["active_users_1h"] == 3
            assert summary["active_users_24h"] == 3

        # Mock time 2 hours later
        with patch("time.time", return_value=now + 7200):
            summary = metrics_service.get_metrics_summary()
            assert summary["active_users_1h"] == 0  # No users in last hour
            assert summary["active_users_24h"] == 3  # Still active in 24h

        # Mock time 2 days later
        with patch("time.time", return_value=now + 172800):
            summary = metrics_service.get_metrics_summary()
            assert summary["active_users_1h"] == 0
            assert summary["active_users_24h"] == 0

    def test_messages_per_minute_calculation(self, metrics_service):
        """Test messages per minute calculation."""
        # Add some messages
        for _ in range(30):
            metrics_service.increment_message_count()

        # Mock uptime
        with patch("time.time", return_value=metrics_service.start_time + 60):
            summary = metrics_service.get_metrics_summary()
            assert summary["messages_per_minute"] == 30.0

        # Mock uptime 2 minutes
        with patch("time.time", return_value=metrics_service.start_time + 120):
            summary = metrics_service.get_metrics_summary()
            assert summary["messages_per_minute"] == 15.0

    def test_singleton_pattern(self):
        """Test that get_metrics_service returns singleton instance."""

        async def test_singleton():
            service1 = await get_metrics_service()
            service2 = await get_metrics_service()

            assert service1 is service2
            assert isinstance(service1, MetricsService)

        asyncio.run(test_singleton())

    def test_concurrent_metric_updates(self, metrics_service):
        """Test thread safety of metric updates."""

        def update_metrics():
            for _ in range(100):
                metrics_service.increment_message_count()
                metrics_service.increment_command_count("test")
                metrics_service.record_user_activity(123)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=update_metrics)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all updates were recorded
        assert metrics_service.message_count == 1000
        assert metrics_service.command_count == 1000
        assert metrics_service.command_types["test"] == 1000


class TestMetricsHandler:
    """Test suite for MetricsHandler HTTP request handling."""

    @pytest.fixture
    def metrics_service(self):
        """Create a MetricsService instance for testing."""
        return MetricsService()

    def create_mock_request(self, path: str = "/metrics"):
        """Create a mock HTTP request."""
        request = Mock()
        request.path = path
        request.command = "GET"
        return request

    def test_metrics_endpoint_handling(self, metrics_service):
        """Test handling of /metrics endpoint."""
        # Add test data
        metrics_service.increment_message_count()
        metrics_service.increment_command_count("test")

        # Create handler
        handler_args = (self.create_mock_request("/metrics"), ("0.0.0.0", 0), Mock())

        handler = MetricsHandler(metrics_service, *handler_args)
        handler.wfile = Mock()

        # Send response
        handler._handle_metrics()

        # Verify response was sent
        handler.wfile.write.assert_called_once()
        call_args = handler.wfile.write.call_args[0][0]
        response = call_args.decode()

        assert "dcmaidbot_messages_total 1" in response
        assert 'dcmaidbot_command_type_count{command_type="test"} 1' in response

    def test_health_endpoint_handling(self, metrics_service):
        """Test handling of /health endpoint."""
        handler_args = (self.create_mock_request("/health"), ("0.0.0.0", 0), Mock())

        handler = MetricsHandler(metrics_service, *handler_args)
        handler.wfile = Mock()

        # Send response
        handler._handle_health()

        # Verify response was sent
        handler.wfile.write.assert_called_once()
        call_args = handler.wfile.write.call_args[0][0]
        response = call_args.decode()

        # Should be valid JSON
        health_data = json.loads(response)
        assert "status" in health_data
        assert "metrics" in health_data

    def test_404_handling(self, metrics_service):
        """Test handling of unknown endpoints."""
        handler_args = (self.create_mock_request("/unknown"), ("0.0.0.0", 0), Mock())

        handler = MetricsHandler(metrics_service, *handler_args)
        handler.wfile = Mock()

        # Send 404 response
        handler._send_404()

        # Verify 404 response
        handler.wfile.write.assert_called_once_with(b"Not Found")

    def test_error_handling_in_metrics(self, metrics_service):
        """Test error handling in metrics endpoint."""
        # Mock service to raise exception
        with patch.object(
            metrics_service,
            "get_prometheus_metrics",
            side_effect=Exception("Service error"),
        ):
            handler_args = (
                self.create_mock_request("/metrics"),
                ("0.0.0.0", 0),
                Mock(),
            )

            handler = MetricsHandler(metrics_service, *handler_args)
            handler.wfile = Mock()

            # Should handle error gracefully
            handler._handle_metrics()

            # Verify error response
            handler.wfile.write.assert_called_once_with(b"Internal Server Error")

    def test_error_handling_in_health(self, metrics_service):
        """Test error handling in health endpoint."""
        # Mock service to raise exception
        with patch.object(
            metrics_service, "health_check", side_effect=Exception("Service error")
        ):
            handler_args = (self.create_mock_request("/health"), ("0.0.0.0", 0), Mock())

            handler = MetricsHandler(metrics_service, *handler_args)
            handler.wfile = Mock()

            # Should handle error gracefully
            handler._handle_health()

            # Verify error response
            handler.wfile.write.assert_called_once_with(b"Internal Server Error")

    def test_do_get_routing(self, metrics_service):
        """Test GET request routing to correct handlers."""
        # Test metrics route
        handler = MetricsHandler(metrics_service, Mock(), Mock(), Mock())
        handler.path = "/metrics"
        handler._handle_metrics = Mock()

        handler.do_GET()
        handler._handle_metrics.assert_called_once()

        # Test health route
        handler.path = "/health"
        handler._handle_health = Mock()
        handler._handle_metrics.reset_mock()

        handler.do_GET()
        handler._handle_health.assert_called_once()

        # Test 404 route
        handler.path = "/unknown"
        handler._send_404 = Mock()
        handler._handle_health.reset_mock()

        handler.do_GET()
        handler._send_404.assert_called_once()


class TestMetricsServiceIntegration:
    """Integration tests for MetricsService with real HTTP server."""

    @pytest.mark.asyncio
    async def test_http_server_integration(self, metrics_service):
        """Test actual HTTP server functionality."""
        # Start server on random port
        await metrics_service.start()

        # Get actual port
        port = metrics_service.server.server_address[1]
        base_url = f"http://localhost:{port}"

        try:
            # Test metrics endpoint
            response = requests.get(f"{base_url}/metrics", timeout=5)
            assert response.status_code == 200
            assert "dcmaidbot_messages_total" in response.text
            assert response.headers["Content-Type"] == "text/plain"

            # Test health endpoint
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
            health_data = response.json()
            assert "status" in health_data
            assert health_data["server_running"] is True

            # Test 404 endpoint
            response = requests.get(f"{base_url}/unknown", timeout=5)
            assert response.status_code == 404

        finally:
            await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_metrics_updates_while_server_running(self, metrics_service):
        """Test updating metrics while server is running."""
        await metrics_service.start()

        try:
            # Update some metrics
            metrics_service.increment_message_count()
            metrics_service.increment_command_count("test")
            metrics_service.record_user_activity(123)

            # Get port
            port = metrics_service.server.server_address[1]

            # Verify metrics are reflected in HTTP response
            response = requests.get(f"http://localhost:{port}/metrics", timeout=5)
            assert "dcmaidbot_messages_total 1" in response.text
            assert (
                'dcmaidbot_command_type_count{command_type="test"} 1' in response.text
            )

        finally:
            await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_concurrent_http_requests(self, metrics_service):
        """Test handling multiple concurrent HTTP requests."""
        await metrics_service.start()

        try:
            port = metrics_service.server.server_address[1]
            base_url = f"http://localhost:{port}"

            # Make multiple concurrent requests
            def make_request():
                response = requests.get(f"{base_url}/metrics", timeout=5)
                return response.status_code == 200

            # Create multiple threads
            threads = []
            results = []

            for _ in range(20):
                result = {}
                thread = threading.Thread(
                    target=lambda r=result: r.update({"success": make_request()})
                )
                threads.append((thread, result))
                thread.start()

            # Wait for all requests
            for thread, result in threads:
                thread.join()
                results.append(result.get("success", False))

            # All requests should succeed
            assert all(results)

        finally:
            await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_server_restart_after_stop(self, metrics_service):
        """Test restarting server after stopping."""
        # Start, stop, then start again
        await metrics_service.start()
        await metrics_service.stop()

        await metrics_service.start()
        port2 = metrics_service.server.server_address[1]

        # Should be able to start again (might use different port)
        assert metrics_service.running is True

        try:
            # Verify server is working
            response = requests.get(f"http://localhost:{port2}/health", timeout=5)
            assert response.status_code == 200
        finally:
            await metrics_service.stop()

    @pytest.mark.asyncio
    async def test_large_metrics_output(self, metrics_service):
        """Test handling large metrics output."""
        # Generate a lot of data
        for i in range(100):
            metrics_service.increment_command_count(f"command_{i}")
            metrics_service.record_user_activity(i)

        await metrics_service.start()

        try:
            port = metrics_service.server.server_address[1]

            # Request should handle large output
            response = requests.get(f"http://localhost:{port}/metrics", timeout=10)
            assert response.status_code == 200

            # Verify data is present
            assert (
                'dcmaidbot_command_type_count{command_type="command_0"} 1'
                in response.text
            )
            assert (
                'dcmaidbot_command_type_count{command_type="command_99"} 1'
                in response.text
            )

        finally:
            await metrics_service.stop()
