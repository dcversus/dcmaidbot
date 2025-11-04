"""
Metrics Service Implementation
=============================

Prometheus metrics collection and HTTP server.
Implements PRP-012 Analytics functionality.
"""

import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for metrics endpoint."""

    def __init__(self, metrics_service: "MetricsService", *args, **kwargs):
        self.metrics_service = metrics_service
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/health":
            self._handle_health()
        else:
            self._send_404()

    def _handle_metrics(self):
        """Handle /metrics endpoint."""
        try:
            metrics = self.metrics_service.get_prometheus_metrics()
            self._send_response(200, metrics, "text/plain")
        except Exception as e:
            logger.error(f"Error serving metrics: {e}")
            self._send_response(500, "Internal Server Error", "text/plain")

    def _handle_health(self):
        """Handle /health endpoint."""
        try:
            health = self.metrics_service.health_check()
            self._send_response(200, str(health), "application/json")
        except Exception as e:
            logger.error(f"Error serving health: {e}")
            self._send_response(500, "Internal Server Error", "application/json")

    def _send_response(self, code: int, body: str, content_type: str):
        """Send HTTP response."""
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def _send_404(self):
        """Send 404 response."""
        self._send_response(404, "Not Found", "text/plain")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class MetricsService:
    """Prometheus metrics collection service."""

    def __init__(self, port: int = 8000):
        """Initialize metrics service.

        Args:
            port: Port for HTTP server
        """
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False

        # Counters
        self.message_count = 0
        self.command_count = 0
        self.error_count = 0
        self.bot_starts = 0

        # Timing
        self.start_time = time.time()
        self.last_command_time = 0

        # Labels
        self.command_types = {}
        self.user_activity = {}

    async def start(self) -> None:
        """Start the HTTP server for metrics."""
        if self.running:
            logger.warning("Metrics server already running")
            return

        try:
            # Create HTTP server
            def create_handler(*args, **kwargs):
                return MetricsHandler(self, *args, **kwargs)

            self.server = HTTPServer(("0.0.0.0", self.port), create_handler)

            # Start server in background thread
            self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.running = True

            self.bot_starts += 1
            logger.info(f"Metrics server started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            self.running = False

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if not self.running:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                if self.server_thread:
                    self.server_thread.join(timeout=5)
                self.server = None
                self.server_thread = None
                self.running = False

            logger.info("Metrics server stopped")

        except Exception as e:
            logger.error(f"Error stopping metrics server: {e}")

    def increment_message_count(self) -> None:
        """Increment message counter."""
        self.message_count += 1

    def increment_command_count(self, command_type: str = "unknown") -> None:
        """Increment command counter.

        Args:
            command_type: Type of command executed
        """
        self.command_count += 1
        self.last_command_time = time.time()
        self.command_types[command_type] = self.command_types.get(command_type, 0) + 1

    def increment_error_count(self, error_type: str = "unknown") -> None:
        """Increment error counter.

        Args:
            error_type: Type of error
        """
        self.error_count += 1

    def record_user_activity(self, user_id: int) -> None:
        """Record user activity.

        Args:
            user_id: User identifier
        """
        self.user_activity[user_id] = time.time()

    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus metrics output.

        Returns:
            Prometheus-formatted metrics string
        """
        uptime = time.time() - self.start_time
        active_users = len(
            [
                uid
                for uid, last_seen in self.user_activity.items()
                if time.time() - last_seen < 3600  # Active in last hour
            ]
        )

        metrics = [
            "# HELP dcmaidbot_messages_total Total number of messages processed",
            "# TYPE dcmaidbot_messages_total counter",
            f"dcmaidbot_messages_total {self.message_count}",
            "",
            "# HELP dcmaidbot_commands_total Total number of commands executed",
            "# TYPE dcmaidbot_commands_total counter",
            f"dcmaidbot_commands_total {self.command_count}",
            "",
            "# HELP dcmaidbot_errors_total Total number of errors",
            "# TYPE dcmaidbot_errors_total counter",
            f"dcmaidbot_errors_total {self.error_count}",
            "",
            "# HELP dcmaidbot_bot_starts_total Number of bot starts",
            "# TYPE dcmaidbot_bot_starts_total counter",
            f"dcmaidbot_bot_starts_total {self.bot_starts}",
            "",
            "# HELP dcmaidbot_uptime_seconds Bot uptime in seconds",
            "# TYPE dcmaidbot_uptime_seconds gauge",
            f"dcmaidbot_uptime_seconds {uptime}",
            "",
            "# HELP dcmaidbot_active_users Number of active users (last hour)",
            "# TYPE dcmaidbot_active_users gauge",
            f"dcmaidbot_active_users {active_users}",
            "",
            "# HELP dcmaidbot_command_type_count Commands by type",
            "# TYPE dcmaidbot_command_type_count counter",
        ]

        for command_type, count in self.command_types.items():
            metrics.append(
                f'dcmaidbot_command_type_count{{command_type="{command_type}"}} {count}'
            )

        metrics.append("")
        metrics.append(
            "# HELP dcmaidbot_last_command_timestamp Unix timestamp of last command"
        )
        metrics.append("# TYPE dcmaidbot_last_command_timestamp gauge")
        metrics.append(f"dcmaidbot_last_command_timestamp {self.last_command_time}")

        return "\n".join(metrics)

    def health_check(self) -> Dict[str, Any]:
        """Check metrics service health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.running else "unhealthy",
            "server_running": self.running,
            "port": self.port,
            "uptime_seconds": time.time() - self.start_time,
            "metrics": {
                "messages_total": self.message_count,
                "commands_total": self.command_count,
                "errors_total": self.error_count,
                "active_users": len(
                    [
                        uid
                        for uid, last_seen in self.user_activity.items()
                        if time.time() - last_seen < 3600
                    ]
                ),
            },
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics.

        Returns:
            Metrics summary dictionary
        """
        uptime = time.time() - self.start_time
        messages_per_minute = (self.message_count / (uptime / 60)) if uptime > 0 else 0

        return {
            "uptime_seconds": uptime,
            "messages_total": self.message_count,
            "commands_total": self.command_count,
            "errors_total": self.error_count,
            "messages_per_minute": round(messages_per_minute, 2),
            "command_types": self.command_types.copy(),
            "active_users_1h": len(
                [
                    uid
                    for uid, last_seen in self.user_activity.items()
                    if time.time() - last_seen < 3600
                ]
            ),
            "active_users_24h": len(
                [
                    uid
                    for uid, last_seen in self.user_activity.items()
                    if time.time() - last_seen < 86400
                ]
            ),
        }


# Singleton instance
_metrics_service = None


async def get_metrics_service() -> MetricsService:
    """Get or create metrics service singleton."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
        await _metrics_service.start()
    return _metrics_service
