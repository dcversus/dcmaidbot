"""
Performance monitoring and optimization service for dcmaidbot.

This service provides comprehensive performance analysis, monitoring, and optimization
capabilities including database query optimization, Redis caching performance,
response time tracking, and resource utilization monitoring.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.services.redis_service import RedisService


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_usage_mb: float
    disk_usage_percent: float
    response_time_ms: float
    database_connection_time_ms: float
    redis_connection_time_ms: Optional[float]
    cache_hit_rate: Optional[float]
    active_connections: int
    requests_per_second: float
    error_rate: float


@dataclass
class CachePerformanceMetrics:
    """Redis cache performance metrics."""

    hit_rate: float
    miss_rate: float
    avg_response_time_ms: float
    total_operations: int
    memory_usage_bytes: int
    connected_clients: int


class PerformanceService:
    """Comprehensive performance monitoring and optimization service."""

    def __init__(self, db_engine: AsyncEngine, redis_service: RedisService):
        """Initialize performance service.

        Args:
            db_engine: SQLAlchemy async engine instance
            redis_service: Redis service instance
        """
        self.db_engine = db_engine
        self.redis_service = redis_service
        self.metrics_history: List[PerformanceMetrics] = []
        self.request_times: List[float] = []
        self.error_count = 0
        self.total_requests = 0
        self.start_time = time.time()

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics.

        Returns:
            Dictionary containing system performance data
        """
        try:
            # CPU and Memory metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_usage_mb": process_memory.rss / (1024**2),
                "memory_percent_process": process.memory_percent(),
                "disk_usage_percent": disk.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "process_cpu_percent": process.cpu_percent(),
                "process_num_threads": process.num_threads(),
                "process_num_fds": process.num_fds()
                if hasattr(process, "num_fds")
                else 0,
            }
        except Exception as e:
            print(f"⚠️  Error collecting system metrics: {e}")
            return {}

    async def test_database_performance(self) -> Dict[str, Any]:
        """Test database connection and query performance.

        Returns:
            Dictionary containing database performance metrics
        """
        try:
            # Test connection time
            start_time = time.time()
            async with self.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            connection_time_ms = (time.time() - start_time) * 1000

            # Test query performance
            start_time = time.time()
            async with self.db_engine.connect() as conn:
                result = await conn.execute(
                    text("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    LIMIT 10
                """)
                )
                rows = result.fetchall()
            query_time_ms = (time.time() - start_time) * 1000

            # Test transaction performance
            start_time = time.time()
            async with self.db_engine.begin() as conn:
                await conn.execute(
                    text("CREATE TEMPORARY TABLE perf_test (id INTEGER)")
                )
                await conn.execute(
                    text("INSERT INTO perf_test (id) VALUES (1), (2), (3)")
                )
                await conn.execute(text("SELECT * FROM perf_test"))
                await conn.execute(text("DROP TABLE perf_test"))
            transaction_time_ms = (time.time() - start_time) * 1000

            # Connection pool stats
            pool = self.db_engine.pool
            pool_stats = (
                {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }
                if pool
                else {}
            )

            return {
                "connection_time_ms": round(connection_time_ms, 3),
                "query_time_ms": round(query_time_ms, 3),
                "transaction_time_ms": round(transaction_time_ms, 3),
                "rows_returned": len(rows),
                "pool_stats": pool_stats,
                "status": "healthy",
            }

        except Exception as e:
            return {
                "connection_time_ms": 0,
                "query_time_ms": 0,
                "transaction_time_ms": 0,
                "error": str(e),
                "status": "error",
            }

    async def test_redis_performance(self) -> Dict[str, Any]:
        """Test Redis connection and caching performance.

        Returns:
            Dictionary containing Redis performance metrics
        """
        if not self.redis_service.redis:
            return {
                "connection_time_ms": 0,
                "hit_rate": 0,
                "avg_response_time_ms": 0,
                "status": "not_connected",
            }

        try:
            # Test connection time
            start_time = time.time()
            await self.redis_service.redis.ping()
            connection_time_ms = (time.time() - start_time) * 1000

            # Test basic operations performance
            operations = []
            test_key = f"perf_test_{int(time.time())}"

            # Test SET operation
            start_time = time.time()
            await self.redis_service.redis.set(test_key, "test_value", ex=60)
            operations.append((time.time() - start_time) * 1000)

            # Test GET operation
            start_time = time.time()
            await self.redis_service.redis.get(test_key)
            operations.append((time.time() - start_time) * 1000)

            # Test DELETE operation
            start_time = time.time()
            await self.redis_service.redis.delete(test_key)
            operations.append((time.time() - start_time) * 1000)

            avg_response_time_ms = sum(operations) / len(operations)

            # Get Redis info
            info = await self.redis_service.redis.info()

            return {
                "connection_time_ms": round(connection_time_ms, 3),
                "avg_response_time_ms": round(avg_response_time_ms, 3),
                "hit_rate": info.get("keyspace_hits", 0)
                / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)),
                "total_operations": info.get("total_commands_processed", 0),
                "memory_usage_bytes": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "status": "healthy",
            }

        except Exception as e:
            return {
                "connection_time_ms": 0,
                "avg_response_time_ms": 0,
                "hit_rate": 0,
                "error": str(e),
                "status": "error",
            }

    async def test_application_performance(self) -> Dict[str, Any]:
        """Test application-level performance metrics.

        Returns:
            Dictionary containing application performance data
        """
        try:
            # Test import performance
            start_time = time.time()
            from core.services.llm_service import LLMService
            from core.services.memory_service import MemoryService

            import_time_ms = (time.time() - start_time) * 1000

            # Test service instantiation
            start_time = time.time()
            MemoryService()  # Test instantiation
            LLMService()  # Test instantiation
            instantiation_time_ms = (time.time() - start_time) * 1000

            return {
                "import_time_ms": round(import_time_ms, 3),
                "instantiation_time_ms": round(instantiation_time_ms, 3),
                "services_loaded": 2,
                "status": "healthy",
            }

        except Exception as e:
            return {
                "import_time_ms": 0,
                "instantiation_time_ms": 0,
                "error": str(e),
                "status": "error",
            }

    async def record_request(
        self, response_time_ms: float, is_error: bool = False
    ) -> None:
        """Record a request for performance tracking.

        Args:
            response_time_ms: Response time in milliseconds
            is_error: Whether the request resulted in an error
        """
        self.request_times.append(response_time_ms)
        self.total_requests += 1
        if is_error:
            self.error_count += 1

        # Keep only last 1000 requests in memory
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]

    def calculate_performance_summary(self) -> Dict[str, Any]:
        """Calculate performance summary from collected metrics.

        Returns:
            Dictionary containing performance summary statistics
        """
        if not self.request_times:
            return {
                "avg_response_time_ms": 0,
                "p50_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "p99_response_time_ms": 0,
                "requests_per_second": 0,
                "error_rate": 0,
                "uptime_seconds": time.time() - self.start_time,
            }

        sorted_times = sorted(self.request_times)
        uptime_seconds = time.time() - self.start_time

        return {
            "avg_response_time_ms": round(
                sum(self.request_times) / len(self.request_times), 3
            ),
            "p50_response_time_ms": round(sorted_times[len(sorted_times) // 2], 3),
            "p95_response_time_ms": round(
                sorted_times[int(len(sorted_times) * 0.95)], 3
            ),
            "p99_response_time_ms": round(
                sorted_times[int(len(sorted_times) * 0.99)], 3
            ),
            "requests_per_second": round(self.total_requests / uptime_seconds, 3)
            if uptime_seconds > 0
            else 0,
            "error_rate": round(
                (self.error_count / max(1, self.total_requests)) * 100, 3
            ),
            "total_requests": self.total_requests,
            "uptime_seconds": uptime_seconds,
        }

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Returns:
            Dictionary containing complete performance analysis
        """
        # Collect all metrics
        system_metrics = await self.collect_system_metrics()
        db_metrics = await self.test_database_performance()
        redis_metrics = await self.test_redis_performance()
        app_metrics = await self.test_application_performance()
        performance_summary = self.calculate_performance_summary()

        # Performance recommendations
        recommendations = []

        if system_metrics.get("cpu_percent", 0) > 80:
            recommendations.append(
                "High CPU usage detected. Consider scaling or optimizing CPU-intensive operations."
            )

        if system_metrics.get("memory_percent", 0) > 85:
            recommendations.append(
                "High memory usage detected. Consider implementing memory optimization strategies."
            )

        if db_metrics.get("connection_time_ms", 0) > 100:
            recommendations.append(
                "Slow database connection detected. Consider connection pooling optimization."
            )

        if redis_metrics.get("hit_rate", 0) < 0.8:
            recommendations.append(
                "Low Redis cache hit rate. Consider cache strategy optimization."
            )

        if performance_summary.get("avg_response_time_ms", 0) > 500:
            recommendations.append(
                "High average response time. Review performance bottlenecks."
            )

        if performance_summary.get("error_rate", 0) > 5:
            recommendations.append(
                "High error rate detected. Review error handling and system stability."
            )

        return {
            "timestamp": time.time(),
            "system_metrics": system_metrics,
            "database_metrics": db_metrics,
            "redis_metrics": redis_metrics,
            "application_metrics": app_metrics,
            "performance_summary": performance_summary,
            "recommendations": recommendations,
            "overall_health": "healthy"
            if len(recommendations) == 0
            else "warning"
            if len(recommendations) <= 3
            else "critical",
        }

    async def start_monitoring(self, interval_seconds: int = 60) -> None:
        """Start continuous performance monitoring.

        Args:
            interval_seconds: Monitoring interval in seconds
        """
        print(f"🚀 Starting performance monitoring with {interval_seconds}s interval")

        while True:
            try:
                report = await self.generate_performance_report()

                # Log summary
                health = report["overall_health"]
                health_emoji = (
                    "✅"
                    if health == "healthy"
                    else "⚠️"
                    if health == "warning"
                    else "🚨"
                )

                print(
                    f"{health_emoji} Performance Report [{time.strftime('%H:%M:%S')}]"
                )
                print(f"   CPU: {report['system_metrics'].get('cpu_percent', 0):.1f}%")
                print(
                    f"   Memory: {report['system_metrics'].get('memory_percent', 0):.1f}%"
                )
                print(
                    f"   Response Time: {report['performance_summary'].get('avg_response_time_ms', 0):.1f}ms"
                )
                print(
                    f"   Error Rate: {report['performance_summary'].get('error_rate', 0):.1f}%"
                )

                if report["recommendations"]:
                    print(
                        f"   Recommendations: {len(report['recommendations'])} issues found"
                    )

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                print(f"⚠️  Error in performance monitoring: {e}")
                await asyncio.sleep(interval_seconds)


# Performance optimization utilities
class PerformanceOptimizer:
    """Performance optimization utilities and recommendations."""

    @staticmethod
    def get_database_optimization_recommendations(
        db_metrics: Dict[str, Any],
    ) -> List[str]:
        """Get database optimization recommendations.

        Args:
            db_metrics: Database performance metrics

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        if db_metrics.get("connection_time_ms", 0) > 100:
            recommendations.append("Enable connection pooling with optimal pool size")
            recommendations.append("Consider using connection keep-alive settings")

        if db_metrics.get("query_time_ms", 0) > 200:
            recommendations.append("Add appropriate database indexes")
            recommendations.append("Optimize slow queries with EXPLAIN ANALYZE")
            recommendations.append("Consider query result caching")

        pool_stats = db_metrics.get("pool_stats", {})
        if pool_stats.get("overflow", 0) > 5:
            recommendations.append("Increase database connection pool size")

        return recommendations

    @staticmethod
    def get_redis_optimization_recommendations(
        redis_metrics: Dict[str, Any],
    ) -> List[str]:
        """Get Redis optimization recommendations.

        Args:
            redis_metrics: Redis performance metrics

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        if redis_metrics.get("hit_rate", 0) < 0.8:
            recommendations.append("Review cache TTL settings")
            recommendations.append("Implement cache warming strategies")
            recommendations.append("Optimize cache key patterns")

        if redis_metrics.get("avg_response_time_ms", 0) > 10:
            recommendations.append("Consider Redis memory optimization")
            recommendations.append("Review Redis configuration for performance tuning")

        if redis_metrics.get("memory_usage_bytes", 0) > 1024 * 1024 * 1024:  # 1GB
            recommendations.append("Implement Redis memory eviction policies")
            recommendations.append("Consider Redis clustering for high memory usage")

        return recommendations

    @staticmethod
    def get_system_optimization_recommendations(
        system_metrics: Dict[str, Any],
    ) -> List[str]:
        """Get system optimization recommendations.

        Args:
            system_metrics: System performance metrics

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        if system_metrics.get("cpu_percent", 0) > 80:
            recommendations.append("Scale horizontally with load balancing")
            recommendations.append("Optimize CPU-intensive operations")
            recommendations.append("Consider process priority adjustments")

        if system_metrics.get("memory_percent", 0) > 85:
            recommendations.append("Implement memory leak detection")
            recommendations.append("Optimize memory usage patterns")
            recommendations.append("Consider adding swap space")

        if system_metrics.get("disk_usage_percent", 0) > 90:
            recommendations.append("Implement log rotation and cleanup")
            recommendations.append("Consider disk space optimization")

        return recommendations
