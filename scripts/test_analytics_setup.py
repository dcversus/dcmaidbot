#!/usr/bin/env python3
"""
Analytics Setup Testing Script (PRP-012)

Test script to verify that the analytics and observability infrastructure
is working correctly for dcmaidbot.
"""

import asyncio
import json
from typing import Any, Dict

import aiohttp


class AnalyticsTester:
    """Test analytics setup and functionality"""

    def __init__(self):
        self.metrics_url = "http://localhost:8080/metrics"
        self.health_url = "http://localhost:8080/health"
        self.grafana_url = "http://localhost:3000"
        self.prometheus_url = "http://localhost:9090"

    async def test_metrics_endpoint(self) -> Dict[str, Any]:
        """Test that the /metrics endpoint is working"""
        print("🔍 Testing /metrics endpoint...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.metrics_url) as response:
                    if response.status == 200:
                        metrics_data = await response.text()

                        # Check for expected dcmaidbot metrics
                        expected_metrics = [
                            "dcmaidbot_messages_total",
                            "dcmaidbot_commands_total",
                            "dcmaidbot_active_users_total",
                            "dcmaidbot_jokes_told_total",
                        ]

                        found_metrics = []
                        for metric in expected_metrics:
                            if metric in metrics_data:
                                found_metrics.append(metric)

                        return {
                            "status": "success",
                            "found_metrics": found_metrics,
                            "total_metrics": len(metrics_data.split("\n")),
                            "sample": metrics_data[:500] + "..."
                            if len(metrics_data) > 500
                            else metrics_data,
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}",
                            "response": await response.text(),
                        }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test that the /health endpoint is working"""
        print("🔍 Testing /health endpoint...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_url) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        return {"status": "success", "data": health_data}
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def test_prometheus_scraping(self) -> Dict[str, Any]:
        """Test that Prometheus is successfully scraping dcmaidbot metrics"""
        print("🔍 Testing Prometheus scraping...")

        try:
            # Query Prometheus for dcmaidbot metrics
            query_url = f"{self.prometheus_url}/api/v1/query"

            async with aiohttp.ClientSession() as session:
                # Test if Prometheus has any dcmaidbot metrics
                params = {"query": "dcmaidbot_messages_total"}
                async with session.get(query_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data["status"] == "success" and data["data"]["result"]:
                            return {
                                "status": "success",
                                "metrics_found": len(data["data"]["result"]),
                                "sample_metric": data["data"]["result"][0]
                                if data["data"]["result"]
                                else None,
                            }
                        else:
                            return {
                                "status": "warning",
                                "message": "No dcmaidbot metrics found in Prometheus",
                            }
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def test_prometheus_targets(self) -> Dict[str, Any]:
        """Test Prometheus targets configuration"""
        print("🔍 Testing Prometheus targets...")

        try:
            targets_url = f"{self.prometheus_url}/api/v1/targets"

            async with aiohttp.ClientSession() as session:
                async with session.get(targets_url) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Look for dcmaidbot targets
                        dcmaidbot_targets = []
                        for target in data["data"]["activeTargets"]:
                            if "dcmaidbot" in target.get("labels", {}).get("job", ""):
                                dcmaidbot_targets.append(
                                    {
                                        "job": target["labels"]["job"],
                                        "health": target["health"],
                                        "lastError": target.get("lastError", "none"),
                                    }
                                )

                        return {
                            "status": "success",
                            "dcmaidbot_targets": dcmaidbot_targets,
                            "total_targets": len(data["data"]["activeTargets"]),
                        }
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def generate_test_metrics(self) -> Dict[str, Any]:
        """Generate some test metrics by making test requests"""
        print("🔍 Generating test metrics...")

        try:
            # Make multiple requests to generate metrics
            async with aiohttp.ClientSession() as session:
                tasks = []
                for i in range(10):
                    task = session.get(self.health_url)
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                successful_requests = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.status == 200
                )

                return {
                    "status": "success",
                    "test_requests": len(tasks),
                    "successful_requests": successful_requests,
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all analytics tests"""
        print("🚀 Starting Analytics Setup Tests...")
        print("=" * 50)

        tests = {
            "metrics_endpoint": await self.test_metrics_endpoint(),
            "health_endpoint": await self.test_health_endpoint(),
            "prometheus_scraping": await self.test_prometheus_scraping(),
            "prometheus_targets": await self.test_prometheus_targets(),
            "test_metrics_generation": await self.generate_test_metrics(),
        }

        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)

        for test_name, result in tests.items():
            status_emoji = (
                "✅"
                if result["status"] == "success"
                else "⚠️"
                if result["status"] == "warning"
                else "❌"
            )
            print(f"{status_emoji} {test_name}: {result['status']}")

            if result["status"] == "error":
                print(f"   Error: {result.get('error', 'Unknown error')}")

        # Overall assessment
        successful_tests = sum(1 for t in tests.values() if t["status"] == "success")
        total_tests = len(tests)

        print(f"\n📈 Overall: {successful_tests}/{total_tests} tests passed")

        if successful_tests == total_tests:
            print("🎉 All analytics tests passed! Infrastructure is working correctly.")
        elif successful_tests >= total_tests * 0.8:
            print("⚠️  Most tests passed. Some minor issues to investigate.")
        else:
            print("❌ Multiple test failures. Analytics setup needs attention.")

        return tests


async def main():
    """Main test function"""
    tester = AnalyticsTester()
    results = await tester.run_all_tests()

    # Save results to file for later review
    with open("analytics_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Detailed results saved to: analytics_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
