#!/usr/bin/env python3
"""
Enhanced Status System Metrics Exporter

This module exports Prometheus metrics for the enhanced status system,
including health metrics, LLM usage, crypto thoughts, and business test results.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from prometheus_client.core import CollectorRegistry

from services.redis_service import RedisService
from services.status_service import StatusService

logger = logging.getLogger(__name__)


class EnhancedStatusMetrics:
    """Prometheus metrics for enhanced status system."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics.

        Args:
            registry: Prometheus registry (uses default if None)
        """
        self.registry = registry or CollectorRegistry()

        # System information
        self.build_info = Info(
            "dcmaidbot_build_info", "Build information", registry=self.registry
        )

        # System health metrics
        self.uptime = Gauge(
            "dcmaidbot_uptime_seconds",
            "System uptime in seconds",
            registry=self.registry,
        )

        self.database_connected = Gauge(
            "dcmaidbot_database_connected",
            "Database connection status (1=connected, 0=disconnected)",
            registry=self.registry,
        )

        self.redis_connected = Gauge(
            "dcmaidbot_redis_connected",
            "Redis connection status (1=connected, 0=disconnected)",
            registry=self.registry,
        )

        # Enhanced status features metrics
        self.version_thoughts_timestamp = Gauge(
            "dcmaidbot_version_thoughts_timestamp",
            "Timestamp of last version thoughts generation (Unix timestamp)",
            registry=self.registry,
        )

        self.self_check_thoughts_timestamp = Gauge(
            "dcmaidbot_self_check_thoughts_timestamp",
            "Timestamp of last self-check thoughts generation (Unix timestamp)",
            registry=self.registry,
        )

        self.self_check_duration = Gauge(
            "dcmaidbot_self_check_duration_seconds",
            "Duration of last self-check in seconds",
            registry=self.registry,
        )

        self.crypto_thoughts_timestamp = Gauge(
            "dcmaidbot_crypto_thoughts_timestamp",
            "Timestamp of last crypto thoughts generation (Unix timestamp)",
            registry=self.registry,
        )

        self.crypto_thoughts_duration = Gauge(
            "dcmaidbot_crypto_thoughts_duration_seconds",
            "Duration of last crypto thoughts generation in seconds",
            registry=self.registry,
        )

        self.crypto_thoughts_tokens = Gauge(
            "dcmaidbot_crypto_thoughts_tokens",
            "Number of tokens used in last crypto thoughts generation",
            registry=self.registry,
        )

        # LLM service metrics
        self.llm_requests_total = Counter(
            "dcmaidbot_llm_requests_total",
            "Total number of LLM requests",
            ["model", "endpoint"],
            registry=self.registry,
        )

        self.llm_errors_total = Counter(
            "dcmaidbot_llm_errors_total",
            "Total number of LLM errors",
            ["model", "error_type"],
            registry=self.registry,
        )

        self.llm_response_time = Histogram(
            "dcmaidbot_llm_response_time_seconds",
            "LLM response time in seconds",
            ["model", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        self.tokens_total = Counter(
            "dcmaidbot_tokens_total",
            "Total number of tokens used",
            ["model", "feature"],
            registry=self.registry,
        )

        # Business test metrics
        self.business_test_results = Gauge(
            "dcmaidbot_business_test_results",
            "Business test results",
            ["test_name", "result"],
            registry=self.registry,
        )

        self.business_test_pass_rate = Gauge(
            "dcmaidbot_business_test_pass_rate",
            "Business test pass rate (0-1)",
            registry=self.registry,
        )

        self.llm_judge_score = Gauge(
            "dcmaidbot_llm_judge_score",
            "LLM judge evaluation score (0-1)",
            ["evaluation_type"],
            registry=self.registry,
        )

        self.status_judge_passed = Gauge(
            "dcmaidbot_status_judge_passed",
            "Status judge validation result (1=passed, 0=failed)",
            registry=self.registry,
        )

        # System resource metrics
        self.memory_usage = Gauge(
            "dcmaidbot_memory_usage_bytes",
            "Memory usage in bytes",
            registry=self.registry,
        )

        self.memory_limit = Gauge(
            "dcmaidbot_memory_limit_bytes",
            "Memory limit in bytes",
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "dcmaidbot_cpu_usage_ratio", "CPU usage ratio (0-1)", registry=self.registry
        )

        # Notification metrics
        self.nudge_unread_count = Gauge(
            "dcmaidbot_nudge_unread_count",
            "Number of unread nudge messages",
            registry=self.registry,
        )

        self.nudge_last_read_timestamp = Gauge(
            "dcmaidbot_nudge_last_read_timestamp",
            "Timestamp of last nudge read (Unix timestamp)",
            registry=self.registry,
        )

        # Request metrics
        self.http_requests_total = Counter(
            "dcmaidbot_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.http_request_duration = Histogram(
            "dcmaidbot_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
            registry=self.registry,
        )


class MetricsCollector:
    """Collects and updates enhanced status system metrics."""

    def __init__(
        self,
        status_service: StatusService,
        redis_service: RedisService,
        metrics: Optional[EnhancedStatusMetrics] = None,
    ):
        """Initialize metrics collector.

        Args:
            status_service: Enhanced status service instance
            redis_service: Redis service instance
            metrics: Metrics instance (creates new if None)
        """
        self.status_service = status_service
        self.redis_service = redis_service
        self.metrics = metrics or EnhancedStatusMetrics()
        self.last_update = 0
        self.update_interval = 60  # Update every 60 seconds

    async def update_system_metrics(self):
        """Update basic system metrics."""
        try:
            # Update uptime
            uptime = self.status_service.get_system_info().get("uptime_seconds", 0)
            self.metrics.uptime.set(uptime)

            # Update database and Redis status
            db_status = await self.status_service.get_database_status()
            redis_status = await self.status_service.get_redis_status()

            self.metrics.database_connected.set(1 if db_status.get("connected") else 0)
            self.metrics.redis_connected.set(1 if redis_status.get("connected") else 0)

            # Update build info
            version_info = self.status_service.get_version_info()
            self.metrics.build_info.info(
                {
                    "version": version_info.get("version", "unknown"),
                    "git_commit": version_info.get("git_commit", "unknown"),
                    "image_tag": version_info.get("image_tag", "unknown"),
                    "build_time": version_info.get("build_time", "unknown"),
                }
            )

        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    async def update_enhanced_status_metrics(self):
        """Update enhanced status feature metrics."""
        try:
            # Get current status
            current_status = await self.status_service.get_full_status()

            # Update version thoughts timestamp if available
            if "version_thoughts" in current_status:
                # Extract timestamp from version thoughts
                version_thoughts = current_status.get("version_thoughts", [])
                if version_thoughts:
                    latest_thought = version_thoughts[
                        0
                    ]  # Assuming thoughts are sorted by timestamp
                    if "timestamp" in latest_thought:
                        try:
                            timestamp = datetime.fromisoformat(
                                latest_thought["timestamp"].replace("Z", "+00:00")
                            )
                            self.metrics.version_thoughts_timestamp.set(
                                timestamp.timestamp()
                            )
                        except ValueError:
                            logger.warning(
                                f"Invalid timestamp in version thoughts: {latest_thought.get('timestamp')}"
                            )

            # Update self-check thoughts metrics
            if "self_check_thoughts" in current_status:
                self_check_thoughts = current_status.get("self_check_thoughts", [])
                if self_check_thoughts:
                    latest_thought = self_check_thoughts[0]
                    if "timestamp" in latest_thought:
                        try:
                            timestamp = datetime.fromisoformat(
                                latest_thought["timestamp"].replace("Z", "+00:00")
                            )
                            self.metrics.self_check_thoughts_timestamp.set(
                                timestamp.timestamp()
                            )
                        except ValueError:
                            logger.warning(
                                f"Invalid timestamp in self-check thoughts: {latest_thought.get('timestamp')}"
                            )

                    # Update self-check duration if available
                    metadata = latest_thought.get("metadata", {})
                    if "self_check_time_sec" in metadata:
                        self.metrics.self_check_duration.set(
                            metadata["self_check_time_sec"]
                        )

            # Update crypto thoughts metrics
            if "crypto_thoughts" in current_status:
                crypto_thoughts = current_status.get("crypto_thoughts", {})
                if "crypto_thoughts_timestamp" in crypto_thoughts:
                    try:
                        timestamp = datetime.fromisoformat(
                            crypto_thoughts["crypto_thoughts_timestamp"].replace(
                                "Z", "+00:00"
                            )
                        )
                        self.metrics.crypto_thoughts_timestamp.set(
                            timestamp.timestamp()
                        )
                    except ValueError:
                        logger.warning(
                            f"Invalid crypto thoughts timestamp: {crypto_thoughts.get('crypto_thoughts_timestamp')}"
                        )

                if "crypto_thoughts_secs" in crypto_thoughts:
                    self.metrics.crypto_thoughts_duration.set(
                        crypto_thoughts["crypto_thoughts_secs"]
                    )

                if "crypto_thoughts_tokens" in crypto_thoughts:
                    self.metrics.crypto_thoughts_tokens.set(
                        crypto_thoughts["crypto_thoughts_tokens"]
                    )

                if "tokens_total" in crypto_thoughts:
                    self.metrics.tokens_total.labels(
                        model="gpt-4", feature="crypto_thoughts"
                    ).inc(crypto_thoughts["tokens_total"])

        except Exception as e:
            logger.error(f"Error updating enhanced status metrics: {e}")

    async def update_business_metrics(self):
        """Update business-related metrics."""
        try:
            # Try to get business test results from Redis cache
            if self.redis_service.redis:
                # Get latest business test results
                test_results = await self.redis_service.redis.get(
                    "business_test_results"
                )
                if test_results:
                    try:
                        results_data = json.loads(test_results)

                        # Update individual test results
                        for test_name, result in results_data.items():
                            if isinstance(result, dict) and "status" in result:
                                status = 1 if result["status"] == "passed" else 0
                                self.metrics.business_test_results.labels(
                                    test_name=test_name,
                                    result="passed" if status else "failed",
                                ).set(status)

                        # Calculate overall pass rate
                        if results_data:
                            passed = sum(
                                1
                                for r in results_data.values()
                                if isinstance(r, dict) and r.get("status") == "passed"
                            )
                            total = len(results_data)
                            pass_rate = passed / total if total > 0 else 0
                            self.metrics.business_test_pass_rate.set(pass_rate)

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error parsing business test results: {e}")

                # Get LLM judge results
                judge_results = await self.redis_service.redis.get("llm_judge_results")
                if judge_results:
                    try:
                        judge_data = json.loads(judge_results)

                        if "evaluation" in judge_data:
                            evaluation = judge_data["evaluation"]

                            # Update LLM judge scores
                            if "overall_score" in evaluation:
                                self.metrics.llm_judge_score.labels(
                                    evaluation_type="overall"
                                ).set(evaluation["overall_score"])

                            if "functionality_score" in evaluation:
                                self.metrics.llm_judge_score.labels(
                                    evaluation_type="functionality"
                                ).set(evaluation["functionality_score"])

                            if "performance_score" in evaluation:
                                self.metrics.llm_judge_score.labels(
                                    evaluation_type="performance"
                                ).set(evaluation["performance_score"])

                            if "is_acceptable" in evaluation:
                                self.metrics.status_judge_passed.set(
                                    1 if evaluation["is_acceptable"] else 0
                                )

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error parsing LLM judge results: {e}")

                # Get nudge system metrics
                nudge_unread = await self.redis_service.redis.get("nudge_unread_count")
                if nudge_unread:
                    try:
                        unread_count = int(nudge_unread)
                        self.metrics.nudge_unread_count.set(unread_count)
                    except ValueError:
                        logger.warning(f"Invalid nudge unread count: {nudge_unread}")

                nudge_last_read = await self.redis_service.redis.get(
                    "nudge_last_read_timestamp"
                )
                if nudge_last_read:
                    try:
                        timestamp = datetime.fromisoformat(
                            nudge_last_read.replace("Z", "+00:00")
                        )
                        self.metrics.nudge_last_read_timestamp.set(
                            timestamp.timestamp()
                        )
                    except ValueError:
                        logger.warning(
                            f"Invalid nudge last read timestamp: {nudge_last_read}"
                        )

        except Exception as e:
            logger.error(f"Error updating business metrics: {e}")

    async def update_resource_metrics(self):
        """Update system resource metrics."""
        try:
            import psutil

            # Get memory usage
            memory = psutil.virtual_memory()
            process = psutil.Process()

            self.metrics.memory_usage.set(process.memory_info().rss)
            self.metrics.memory_limit.set(memory.total)

            # Get CPU usage
            cpu_percent = process.cpu_percent() / 100.0
            self.metrics.cpu_usage.set(cpu_percent)

        except ImportError:
            logger.warning("psutil not available, resource metrics disabled")
        except Exception as e:
            logger.error(f"Error updating resource metrics: {e}")

    async def update_all_metrics(self):
        """Update all metrics."""
        current_time = time.time()

        # Rate limit updates
        if current_time - self.last_update < self.update_interval:
            return

        try:
            await asyncio.gather(
                self.update_system_metrics(),
                self.update_enhanced_status_metrics(),
                self.update_business_metrics(),
                self.update_resource_metrics(),
                return_exceptions=True,
            )

            self.last_update = current_time

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics.

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        self.metrics.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.metrics.http_request_duration.labels(
            method=method, endpoint=endpoint
        ).observe(duration)

    def record_llm_request(
        self,
        model: str,
        endpoint: str,
        response_time: float,
        tokens_used: int,
        error: Optional[str] = None,
    ):
        """Record LLM request metrics.

        Args:
            model: LLM model name
            endpoint: API endpoint
            response_time: Response time in seconds
            tokens_used: Number of tokens used
            error: Error type if request failed
        """
        self.metrics.llm_response_time.labels(model=model, endpoint=endpoint).observe(
            response_time
        )

        if error:
            self.metrics.llm_errors_total.labels(model=model, error_type=error).inc()

        self.metrics.tokens_total.labels(model=model, feature="llm_request").inc(
            tokens_used
        )


async def start_metrics_server(
    port: int = 8080,
    status_service: Optional[StatusService] = None,
    redis_service: Optional[RedisService] = None,
):
    """Start Prometheus metrics server.

    Args:
        port: Port to serve metrics on
        status_service: Status service for metrics collection
        redis_service: Redis service for metrics collection
    """
    logger.info(f"Starting metrics server on port {port}")

    # Create metrics collector if services provided
    collector = None
    if status_service and redis_service:
        collector = MetricsCollector(status_service, redis_service)

        # Start background task to update metrics
        async def update_metrics_task():
            while True:
                await collector.update_all_metrics()
                await asyncio.sleep(60)  # Update every minute

        asyncio.create_task(update_metrics_task())

    # Start HTTP server
    start_http_server(port, registry=collector.metrics.registry if collector else None)

    logger.info(f"Metrics server started on http://localhost:{port}/metrics")


# Example usage
if __name__ == "__main__":

    async def main():
        # Example metrics server startup
        await start_metrics_server(port=8080)

        # Keep the server running
        while True:
            await asyncio.sleep(1)

    asyncio.run(main())
