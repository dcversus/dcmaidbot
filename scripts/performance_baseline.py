#!/usr/bin/env python3
"""
Performance baseline testing script for dcmaidbot.

This script establishes comprehensive performance baselines including:
- System resource utilization
- Database connection and query performance
- Redis caching performance
- Application-level performance metrics
- Response time benchmarks

Usage:
    python scripts/performance_baseline.py [--output json|table] [--iterations N]
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path before importing project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules after path setup
# ruff: noqa: E402
from database import engine
from services.performance_service import PerformanceService
from services.redis_service import RedisService


class PerformanceBaselineTester:
    """Comprehensive performance baseline tester."""

    def __init__(self):
        """Initialize baseline tester."""
        self.redis_service = RedisService()
        self.performance_service = PerformanceService(engine, self.redis_service)
        self.results: List[Dict[str, Any]] = []

    async def setup(self) -> None:
        """Setup test environment."""
        print("🔧 Setting up performance baseline test...")
        await self.redis_service.connect()
        print("✅ Setup complete")

    async def cleanup(self) -> None:
        """Cleanup test environment."""
        print("🧹 Cleaning up...")
        await self.redis_service.disconnect()
        print("✅ Cleanup complete")

    async def run_single_test(self, test_id: int) -> Dict[str, Any]:
        """Run a single performance test iteration.

        Args:
            test_id: Test iteration identifier

        Returns:
            Dictionary containing test results
        """
        print(f"📊 Running test iteration {test_id}...")

        # Generate comprehensive performance report
        report = await self.performance_service.generate_performance_report()

        # Add test metadata
        report["test_id"] = test_id
        report["test_timestamp"] = time.time()

        return report

    async def run_baseline_tests(self, iterations: int = 5) -> List[Dict[str, Any]]:
        """Run multiple baseline test iterations.

        Args:
            iterations: Number of test iterations to run

        Returns:
            List of test results
        """
        print(f"🚀 Running {iterations} baseline test iterations...")

        results = []
        for i in range(iterations):
            try:
                result = await self.run_single_test(i + 1)
                results.append(result)
                print(f"✅ Test {i + 1}/{iterations} completed")
            except Exception as e:
                print(f"❌ Test {i + 1}/{iterations} failed: {e}")
                # Continue with next test

        return results

    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze and aggregate test results.

        Args:
            results: List of test result dictionaries

        Returns:
            Dictionary containing aggregated analysis
        """
        if not results:
            return {"error": "No test results to analyze"}

        print("📈 Analyzing test results...")

        # Extract metrics for analysis
        cpu_usage = [r["system_metrics"].get("cpu_percent", 0) for r in results]
        memory_usage = [r["system_metrics"].get("memory_percent", 0) for r in results]
        db_connection_time = [
            r["database_metrics"].get("connection_time_ms", 0) for r in results
        ]
        db_query_time = [r["database_metrics"].get("query_time_ms", 0) for r in results]
        redis_response_time = [
            r["redis_metrics"].get("avg_response_time_ms", 0)
            for r in results
            if r["redis_metrics"].get("status") == "healthy"
        ]
        redis_hit_rate = [
            r["redis_metrics"].get("hit_rate", 0)
            for r in results
            if r["redis_metrics"].get("status") == "healthy"
        ]
        app_import_time = [
            r["application_metrics"].get("import_time_ms", 0) for r in results
        ]

        # Calculate statistics
        def calculate_stats(values: List[float]) -> Dict[str, float]:
            """Calculate basic statistics for a list of values."""
            if not values:
                return {
                    "count": 0,
                    "mean": 0,
                    "min": 0,
                    "max": 0,
                    "median": 0,
                    "std": 0,
                }

            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
            }

        analysis = {
            "test_summary": {
                "total_tests": len(results),
                "successful_tests": len(
                    [r for r in results if r.get("overall_health") != "critical"]
                ),
                "test_duration_seconds": time.time() - results[0]["test_timestamp"]
                if results
                else 0,
                "health_distribution": {
                    "healthy": len(
                        [r for r in results if r.get("overall_health") == "healthy"]
                    ),
                    "warning": len(
                        [r for r in results if r.get("overall_health") == "warning"]
                    ),
                    "critical": len(
                        [r for r in results if r.get("overall_health") == "critical"]
                    ),
                },
            },
            "system_performance": {
                "cpu_usage_percent": calculate_stats(cpu_usage),
                "memory_usage_percent": calculate_stats(memory_usage),
            },
            "database_performance": {
                "connection_time_ms": calculate_stats(db_connection_time),
                "query_time_ms": calculate_stats(db_query_time),
            },
            "redis_performance": {
                "response_time_ms": calculate_stats(redis_response_time),
                "hit_rate": calculate_stats(redis_hit_rate),
            },
            "application_performance": {
                "import_time_ms": calculate_stats(app_import_time),
            },
            "performance_targets": {
                "cpu_usage_target": 70.0,
                "memory_usage_target": 80.0,
                "db_connection_time_target": 100.0,
                "db_query_time_target": 200.0,
                "redis_response_time_target": 10.0,
                "redis_hit_rate_target": 0.8,
                "app_import_time_target": 1000.0,
            },
        }

        # Calculate target compliance
        analysis["target_compliance"] = {
            "cpu_usage_compliance": analysis["system_performance"]["cpu_usage_percent"][
                "mean"
            ]
            <= analysis["performance_targets"]["cpu_usage_target"],
            "memory_usage_compliance": analysis["system_performance"][
                "memory_usage_percent"
            ]["mean"]
            <= analysis["performance_targets"]["memory_usage_target"],
            "db_connection_compliance": analysis["database_performance"][
                "connection_time_ms"
            ]["mean"]
            <= analysis["performance_targets"]["db_connection_time_target"],
            "db_query_compliance": analysis["database_performance"]["query_time_ms"][
                "mean"
            ]
            <= analysis["performance_targets"]["db_query_time_target"],
            "redis_response_compliance": analysis["redis_performance"][
                "response_time_ms"
            ]["mean"]
            <= analysis["performance_targets"]["redis_response_time_target"]
            if redis_response_time
            else False,
            "redis_hit_rate_compliance": analysis["redis_performance"]["hit_rate"][
                "mean"
            ]
            >= analysis["performance_targets"]["redis_hit_rate_target"]
            if redis_hit_rate
            else False,
            "app_import_compliance": analysis["application_performance"][
                "import_time_ms"
            ]["mean"]
            <= analysis["performance_targets"]["app_import_time_target"],
        }

        # Overall compliance score
        compliance_values = list(analysis["target_compliance"].values())
        analysis["overall_compliance_score"] = (
            sum(compliance_values) / len(compliance_values) * 100
        )

        return analysis

    def format_table_output(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results as a table.

        Args:
            analysis: Analysis results dictionary

        Returns:
            Formatted table string
        """
        output = []
        output.append("=" * 80)
        output.append("📊 PERFORMANCE BASELINE TEST RESULTS")
        output.append("=" * 80)

        # Test summary
        summary = analysis["test_summary"]
        output.append("\n📋 Test Summary:")
        output.append(f"   Total Tests: {summary['total_tests']}")
        output.append(f"   Successful: {summary['successful_tests']}")
        output.append(f"   Duration: {summary['test_duration_seconds']:.2f}s")
        output.append(
            f"   Health Distribution: ✅ {summary['health_distribution']['healthy']} ⚠️ {summary['health_distribution']['warning']} 🚨 {summary['health_distribution']['critical']}"
        )

        # Performance metrics
        def format_metric(
            name: str, stats: Dict[str, float], unit: str = "", target: float = None
        ) -> str:
            """Format a metric with statistics."""
            if stats["count"] == 0:
                return f"   {name}: N/A (no data)"

            mean_val = stats["mean"]
            status_emoji = "✅" if target is None or mean_val <= target else "⚠️"
            target_info = f" (target: {target}{unit})" if target else ""

            return (
                f"   {name}: {mean_val:.2f}{unit} ±{stats['std']:.2f}{unit} "
                f"[min: {stats['min']:.2f}{unit}, max: {stats['max']:.2f}{unit}] "
                f"{status_emoji}{target_info}"
            )

        output.append("\n🖥️  System Performance:")
        output.append(
            format_metric(
                "CPU Usage",
                analysis["system_performance"]["cpu_usage_percent"],
                "%",
                70,
            )
        )
        output.append(
            format_metric(
                "Memory Usage",
                analysis["system_performance"]["memory_usage_percent"],
                "%",
                80,
            )
        )

        output.append("\n🗄️  Database Performance:")
        output.append(
            format_metric(
                "Connection Time",
                analysis["database_performance"]["connection_time_ms"],
                "ms",
                100,
            )
        )
        output.append(
            format_metric(
                "Query Time",
                analysis["database_performance"]["query_time_ms"],
                "ms",
                200,
            )
        )

        output.append("\n⚡ Redis Performance:")
        if analysis["redis_performance"]["response_time_ms"]["count"] > 0:
            output.append(
                format_metric(
                    "Response Time",
                    analysis["redis_performance"]["response_time_ms"],
                    "ms",
                    10,
                )
            )
            output.append(
                format_metric(
                    "Hit Rate", analysis["redis_performance"]["hit_rate"], "", 0.8
                )
            )
        else:
            output.append("   Redis: Not connected")

        output.append("\n🚀 Application Performance:")
        output.append(
            format_metric(
                "Import Time",
                analysis["application_performance"]["import_time_ms"],
                "ms",
                1000,
            )
        )

        # Compliance summary
        compliance = analysis["target_compliance"]
        output.append("\n📈 Target Compliance:")
        for metric, is_compliant in compliance.items():
            metric_name = metric.replace("_compliance", "").replace("_", " ").title()
            emoji = "✅" if is_compliant else "❌"
            output.append(f"   {metric_name}: {emoji}")

        overall_score = analysis["overall_compliance_score"]
        score_emoji = (
            "🏆"
            if overall_score >= 90
            else "✅"
            if overall_score >= 70
            else "⚠️"
            if overall_score >= 50
            else "❌"
        )
        output.append(
            f"\n🎯 Overall Compliance Score: {overall_score:.1f}% {score_emoji}"
        )

        output.append("\n" + "=" * 80)
        return "\n".join(output)

    def save_results(
        self, results: List[Dict[str, Any]], analysis: Dict[str, Any], filename: str
    ) -> None:
        """Save results and analysis to file.

        Args:
            results: Raw test results
            analysis: Analyzed results
            filename: Output filename
        """
        output_data = {
            "timestamp": time.time(),
            "test_results": results,
            "analysis": analysis,
            "summary": {
                "total_tests": len(results),
                "overall_compliance_score": analysis["overall_compliance_score"],
                "health_status": analysis["test_summary"]["health_distribution"],
            },
        }

        with open(filename, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        print(f"💾 Results saved to {filename}")

    async def run(self, iterations: int = 5, output_format: str = "table") -> None:
        """Run complete baseline test suite.

        Args:
            iterations: Number of test iterations
            output_format: Output format (table or json)
        """
        print("🚀 Starting Performance Baseline Test Suite")
        print(f"   Iterations: {iterations}")
        print(f"   Output Format: {output_format}")
        print()

        try:
            await self.setup()

            # Run tests
            results = await self.run_baseline_tests(iterations)
            self.results = results

            if not results:
                print("❌ No test results obtained")
                return

            # Analyze results
            analysis = self.analyze_results(results)

            # Output results
            if output_format == "json":
                print(json.dumps(analysis, indent=2, default=str))
            else:
                print(self.format_table_output(analysis))

            # Save results
            timestamp = int(time.time())
            self.save_results(
                results, analysis, f"performance_baseline_{timestamp}.json"
            )

            # Show recommendations
            print("\n💡 Performance Recommendations:")
            recommendations = set()
            for result in results:
                recommendations.update(result.get("recommendations", []))

            if recommendations:
                for i, rec in enumerate(sorted(recommendations), 1):
                    print(f"   {i}. {rec}")
            else:
                print("   ✅ All performance targets met!")

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Performance baseline testing for dcmaidbot"
    )
    parser.add_argument(
        "--iterations", "-i", type=int, default=5, help="Number of test iterations"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--continuous", "-c", action="store_true", help="Run continuous monitoring"
    )

    args = parser.parse_args()

    tester = PerformanceBaselineTester()

    if args.continuous:
        print("🔄 Starting continuous performance monitoring...")
        await tester.performance_service.start_monitoring(interval_seconds=60)
    else:
        await tester.run(iterations=args.iterations, output_format=args.output)


if __name__ == "__main__":
    asyncio.run(main())
