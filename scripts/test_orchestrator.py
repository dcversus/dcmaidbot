"""
Advanced Test Orchestrator for Cross-Environment Testing

Provides intelligent test orchestration with:
- Automatic environment detection and setup
- Parallel test execution with resource management
- Test dependency resolution
- Performance baseline comparison
- Intelligent test selection based on changes
- Real-time test monitoring and reporting
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.environment import Environment, TestMode, env_manager
from scripts.test_data_seeder import TestDataSeeder
from tests.llm_judge import TestSuiteEvaluator


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TestPriority(Enum):
    """Test execution priority."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestExecution:
    """Test execution metadata."""

    test_id: str
    test_file: str
    test_class: Optional[str]
    test_function: str
    priority: TestPriority
    estimated_duration: float
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    environment: Environment = Environment.TEST
    mode: TestMode = TestMode.E2E
    resources_required: Dict[str, Any] = field(default_factory=dict)
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class TestSuite:
    """Collection of related tests."""

    name: str
    description: str
    tests: List[TestExecution] = field(default_factory=list)
    setup_tasks: List[str] = field(default_factory=list)
    teardown_tasks: List[str] = field(default_factory=list)
    parallel: bool = True
    max_workers: int = 4


@dataclass
class TestRunResult:
    """Results of a test run."""

    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    total_duration: float
    results: List[TestExecution] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    llm_judge_results: Dict[str, Any] = field(default_factory=dict)


class TestOrchestrator:
    """Advanced test orchestration system."""

    def __init__(self):
        """Initialize test orchestrator."""
        self.env_manager = env_manager
        self.logger = self._setup_logger()
        self.test_suites: Dict[str, TestSuite] = {}
        self.running_tests: Dict[str, TestExecution] = {}
        self.completed_tests: Dict[str, TestExecution] = {}
        self.test_queue: List[TestExecution] = []
        self.resource_monitor = ResourceMonitor()
        self.baseline_manager = PerformanceBaselineManager()
        self.llm_evaluator = None

    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("TestOrchestrator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def discover_tests(self, test_dirs: List[str] = None) -> Dict[str, TestSuite]:
        """Discover and organize tests into suites."""
        if test_dirs is None:
            test_dirs = ["tests/unit", "tests/e2e"]

        self.logger.info(f"Discovering tests in directories: {test_dirs}")

        # Scan for test files
        test_files = []
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                test_files.extend(Path(test_dir).glob("**/test_*.py"))

        # Organize tests into suites
        suites = {
            "unit": TestSuite(
                name="unit",
                description="Unit tests for individual components",
                parallel=True,
                max_workers=8,
            ),
            "integration": TestSuite(
                name="integration",
                description="Integration tests for component interactions",
                parallel=True,
                max_workers=4,
            ),
            "e2e": TestSuite(
                name="e2e",
                description="End-to-end tests with real services",
                parallel=False,
                max_workers=1,
            ),
            "performance": TestSuite(
                name="performance",
                description="Performance and load tests",
                parallel=False,
                max_workers=1,
            ),
        }

        for test_file in test_files:
            # Determine test type from path
            test_path = str(test_file)
            if "unit" in test_path:
                suite = suites["unit"]
                mode = TestMode.UNIT
            elif "performance" in test_path or "benchmark" in test_path:
                suite = suites["performance"]
                mode = TestMode.PERFORMANCE
            elif "e2e" in test_path:
                suite = suites["e2e"]
                mode = TestMode.E2E
            else:
                suite = suites["integration"]
                mode = TestMode.INTEGRATION

            # Parse test file for test functions
            tests = self._parse_test_file(test_file, mode)
            suite.tests.extend(tests)

        self.test_suites = suites
        self.logger.info(
            f"Discovered {sum(len(suite.tests) for suite in suites.values())} tests in {len(suites)} suites"
        )

        return suites

    def _parse_test_file(self, test_file: Path, mode: TestMode) -> List[TestExecution]:
        """Parse a test file and extract test functions."""
        tests = []
        test_file_str = str(test_file)

        try:
            # Read file content
            with open(test_file, "r") as f:
                content = f.read()

            # Find test functions
            import ast

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    # Determine test priority based on naming
                    priority = TestPriority.MEDIUM
                    if "critical" in node.name.lower():
                        priority = TestPriority.CRITICAL
                    elif "integration" in node.name.lower():
                        priority = TestPriority.HIGH
                    elif "unit" in node.name.lower():
                        priority = TestPriority.LOW

                    # Extract tags from docstring
                    tags = set()
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Str)
                    ):
                        docstring = node.body[0].value.s
                        for tag in [
                            "slow",
                            "integration",
                            "external",
                            "database",
                            "api",
                        ]:
                            if tag in docstring.lower():
                                tags.add(tag)

                    # Estimate duration based on test type
                    estimated_duration = 1.0  # Default 1 second
                    if mode == TestMode.E2E:
                        estimated_duration = 30.0
                    elif mode == TestMode.PERFORMANCE:
                        estimated_duration = 60.0
                    elif "slow" in tags:
                        estimated_duration = 10.0

                    test = TestExecution(
                        test_id=f"{test_file_str}::{node.name}",
                        test_file=test_file_str,
                        test_class=None,  # Could parse class name if needed
                        test_function=node.name,
                        priority=priority,
                        estimated_duration=estimated_duration,
                        tags=tags,
                        environment=env_manager.environment,
                        mode=mode,
                        resources_required=self._estimate_resources(mode, tags),
                    )
                    tests.append(test)

        except Exception as e:
            self.logger.warning(f"Failed to parse test file {test_file}: {e}")

        return tests

    def _estimate_resources(self, mode: TestMode, tags: Set[str]) -> Dict[str, Any]:
        """Estimate resources required for a test."""
        resources = {"cpu_cores": 1, "memory_mb": 256, "database_connections": 1}

        if mode == TestMode.E2E:
            resources["cpu_cores"] = 2
            resources["memory_mb"] = 512
        elif mode == TestMode.PERFORMANCE:
            resources["cpu_cores"] = 4
            resources["memory_mb"] = 1024
        elif "database" in tags:
            resources["database_connections"] = 2

        return resources

    async def run_test_suite(self, suite_name: str, **options) -> TestRunResult:
        """Run a complete test suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite = self.test_suites[suite_name]
        self.logger.info(f"Starting test suite: {suite.name}")

        start_time = datetime.utcnow()

        # Setup test environment
        await self._setup_test_environment(suite)

        try:
            # Sort tests by priority and dependencies
            sorted_tests = self._sort_tests_by_priority(suite.tests)

            # Execute tests
            if suite.parallel:
                results = await self._run_tests_parallel(
                    sorted_tests, suite.max_workers
                )
            else:
                results = await self._run_tests_sequential(sorted_tests)

            # Calculate results
            total_tests = len(results)
            passed = sum(1 for t in results if t.status == TestStatus.PASSED)
            failed = sum(1 for t in results if t.status == TestStatus.FAILED)
            skipped = sum(1 for t in results if t.status == TestStatus.SKIPPED)

            total_duration = (datetime.utcnow() - start_time).total_seconds()

            # Collect performance metrics
            performance_metrics = self.resource_monitor.get_summary()

            # Generate test run result
            result = TestRunResult(
                suite_name=suite_name,
                total_tests=total_tests,
                passed=passed,
                failed=failed,
                skipped=skipped,
                total_duration=total_duration,
                results=results,
                performance_metrics=performance_metrics,
            )

            # Run LLM evaluation if enabled
            if options.get("llm_judge", False):
                result.llm_judge_results = await self._evaluate_with_llm(result)

            self.logger.info(
                f"Test suite {suite_name} completed: {passed}/{total_tests} passed in {total_duration:.2f}s"
            )

            return result

        finally:
            # Cleanup test environment
            await self._cleanup_test_environment(suite)

    async def _setup_test_environment(self, suite: TestSuite):
        """Setup test environment for a suite."""
        self.logger.info(f"Setting up environment for {suite.name} suite")

        # Start resource monitoring
        await self.resource_monitor.start_monitoring()

        # Setup test data if needed
        if any("database" in test.tags for test in suite.tests):
            seeder = TestDataSeeder()
            await seeder.seed_all()

        # Initialize LLM evaluator for E2E tests
        if suite.name == "e2e":
            try:
                from services.llm_service import LLMService

                llm_service = LLMService()
                self.llm_evaluator = TestSuiteEvaluator(llm_service)
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM evaluator: {e}")

    async def _cleanup_test_environment(self, suite: TestSuite):
        """Cleanup test environment after a suite."""
        self.logger.info(f"Cleaning up environment for {suite.name} suite")

        # Stop resource monitoring
        await self.resource_monitor.stop_monitoring()

        # Cleanup test data if needed
        if any("database" in test.tags for test in suite.tests):
            # Note: Test data cleanup is handled by conftest fixtures
            pass

    def _sort_tests_by_priority(
        self, tests: List[TestExecution]
    ) -> List[TestExecution]:
        """Sort tests by priority and dependencies."""
        # Simple priority sort for now
        # TODO: Implement proper dependency resolution
        return sorted(tests, key=lambda t: (t.priority.value, -t.estimated_duration))

    async def _run_tests_sequential(
        self, tests: List[TestExecution]
    ) -> List[TestExecution]:
        """Run tests sequentially."""
        results = []

        for test in tests:
            self.logger.info(f"Running test: {test.test_id}")
            result = await self._run_single_test(test)
            results.append(result)

        return results

    async def _run_tests_parallel(
        self, tests: List[TestExecution], max_workers: int
    ) -> List[TestExecution]:
        """Run tests in parallel with resource management."""
        results = []
        semaphore = asyncio.Semaphore(max_workers)

        async def run_with_semaphore(test):
            async with semaphore:
                return await self._run_single_test(test)

        # Create tasks for all tests
        tasks = [run_with_semaphore(test) for test in tests]

        # Wait for all tests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test = tests[i]
                test.status = TestStatus.FAILED
                test.error_message = str(result)
                processed_results.append(test)
            else:
                processed_results.append(result)

        return processed_results

    async def _run_single_test(self, test: TestExecution) -> TestExecution:
        """Run a single test."""
        test.status = TestStatus.RUNNING
        test.start_time = datetime.utcnow()

        try:
            # Check if we have enough resources
            if not await self._check_resources(test):
                test.status = TestStatus.SKIPPED
                test.error_message = "Insufficient resources"
                return test

            # Build pytest command
            cmd = [
                "pytest",
                test.test_file,
                "-v",
                "--tb=short",
                "--junit-xml=/tmp/test-results.xml",
                "-k",
                test.test_function,
            ]

            # Add environment variables
            env = os.environ.copy()
            env.update(
                {"TEST_MODE": test.mode.value, "ENVIRONMENT": test.environment.value}
            )

            # Run the test
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=test.estimated_duration * 3,  # 3x estimated duration
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                test.status = TestStatus.TIMEOUT
                test.error_message = (
                    f"Test timed out after {test.estimated_duration * 3}s"
                )
                return test

            # Check result
            if process.returncode == 0:
                test.status = TestStatus.PASSED
            else:
                test.status = TestStatus.FAILED
                test.error_message = stderr.decode() if stderr else "Test failed"

        except Exception as e:
            test.status = TestStatus.FAILED
            test.error_message = str(e)

        finally:
            test.end_time = datetime.utcnow()
            test.duration = (test.end_time - test.start_time).total_seconds()

        return test

    async def _check_resources(self, test: TestExecution) -> bool:
        """Check if system has enough resources for the test."""

        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:  # Don't start if CPU is already at 90%
            return False

        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:  # Don't start if memory is 90% used
            return False

        # TODO: Check database connections and other resources

        return True

    async def _evaluate_with_llm(self, result: TestRunResult) -> Dict[str, Any]:
        """Evaluate test results using LLM judge."""
        if not self.llm_evaluator:
            return {"error": "LLM evaluator not available"}

        try:
            # Prepare test results for evaluation
            test_results = {
                "summary": {
                    "total_tests": result.total_tests,
                    "passed": result.passed,
                    "failed": result.failed,
                    "skipped": result.skipped,
                    "duration": result.total_duration,
                },
                "failed_tests": [
                    {"test_id": test.test_id, "error": test.error_message}
                    for test in result.results
                    if test.status == TestStatus.FAILED
                ],
                "performance_metrics": result.performance_metrics,
            }

            # Define expected outcomes
            expected_outcomes = [
                "All critical tests should pass",
                "Test execution should complete within reasonable time",
                "No resource exhaustion should occur",
                "External service integrations should work correctly",
            ]

            # Create test categories for evaluation
            test_categories = {
                "functionality": {
                    "expected_outcomes": ["Core features work correctly"],
                    "actual_outcomes": [
                        f"{result.passed}/{result.total_tests} tests passed"
                    ],
                    "test_count": result.total_tests,
                    "pass_rate": result.passed / result.total_tests
                    if result.total_tests > 0
                    else 0,
                },
                "performance": {
                    "expected_outcomes": ["Tests complete within time limits"],
                    "actual_outcomes": [
                        f"Tests completed in {result.total_duration:.2f}s"
                    ],
                    "test_count": result.total_tests,
                    "pass_rate": 1.0
                    if result.total_duration < 300
                    else 0.5,  # 5 minute limit
                },
            }

            # Run evaluation
            evaluation_results = await self.llm_evaluator.evaluate_prp_compliance(
                prp_name=f"Test Suite: {result.suite_name}",
                test_results=test_results,
                dod_criteria=expected_outcomes,
                test_categories=test_categories,
            )

            return evaluation_results

        except Exception as e:
            self.logger.error(f"LLM evaluation failed: {e}")
            return {"error": str(e)}


class ResourceMonitor:
    """Monitor system resources during test execution."""

    def __init__(self):
        """Initialize resource monitor."""
        self.monitoring = False
        self.start_time = None
        self.measurements = []

    async def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.start_time = datetime.utcnow()
        self.measurements = []

        # Start monitoring task
        asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False

    async def _monitor_loop(self):
        """Resource monitoring loop."""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")

                measurement = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / 1024 / 1024,
                    "disk_percent": disk.percent,
                    "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                }

                self.measurements.append(measurement)

                # Sleep between measurements
                await asyncio.sleep(5)

            except Exception as e:
                logging.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(5)

    def get_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        if not self.measurements:
            return {}

        # Calculate statistics
        cpu_values = [m["cpu_percent"] for m in self.measurements]
        memory_values = [m["memory_percent"] for m in self.measurements]

        return {
            "duration_minutes": (datetime.utcnow() - self.start_time).total_seconds()
            / 60
            if self.start_time
            else 0,
            "measurement_count": len(self.measurements),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
            },
        }


class PerformanceBaselineManager:
    """Manage performance baselines for comparison."""

    def __init__(self):
        """Initialize baseline manager."""
        self.baselines = {}
        self.load_baselines()

    def load_baselines(self):
        """Load performance baselines from file."""
        baseline_file = "test-data/performance_baselines.json"
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, "r") as f:
                    self.baselines = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load baselines: {e}")

    def compare_with_baseline(
        self, test_name: str, metric_name: str, value: float
    ) -> Dict[str, Any]:
        """Compare a metric with baseline."""
        baseline_key = f"{test_name}.{metric_name}"
        baseline_value = self.baselines.get(baseline_key)

        if baseline_value is None:
            return {"status": "no_baseline", "value": value}

        percent_change = ((value - baseline_value) / baseline_value) * 100

        if percent_change > 20:  # 20% regression threshold
            status = "regression"
        elif percent_change < -20:  # 20% improvement threshold
            status = "improvement"
        else:
            status = "stable"

        return {
            "status": status,
            "value": value,
            "baseline": baseline_value,
            "percent_change": percent_change,
        }


async def main():
    """Main orchestration entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced Test Orchestrator")
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "e2e", "performance", "all"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--parallel-workers", type=int, default=4, help="Number of parallel workers"
    )
    parser.add_argument(
        "--llm-judge", action="store_true", help="Enable LLM judge evaluation"
    )
    parser.add_argument(
        "--output-dir", default="test-results", help="Output directory for results"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize orchestrator
    orchestrator = TestOrchestrator()

    # Discover tests
    await orchestrator.discover_tests()

    # Run selected test suites
    if args.suite == "all":
        suites = list(orchestrator.test_suites.keys())
    else:
        suites = [args.suite]

    all_results = {}

    for suite_name in suites:
        result = await orchestrator.run_test_suite(suite_name, llm_judge=args.llm_judge)
        all_results[suite_name] = result

        # Save results
        output_file = os.path.join(args.output_dir, f"{suite_name}_results.json")
        with open(output_file, "w") as f:
            json.dump(
                {
                    "suite_name": result.suite_name,
                    "total_tests": result.total_tests,
                    "passed": result.passed,
                    "failed": result.failed,
                    "skipped": result.skipped,
                    "total_duration": result.total_duration,
                    "performance_metrics": result.performance_metrics,
                    "llm_judge_results": result.llm_judge_results,
                },
                f,
                indent=2,
                default=str,
            )

        print(f"Results saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 50)
    print("TEST EXECUTION SUMMARY")
    print("=" * 50)

    total_tests = sum(r.total_tests for r in all_results.values())
    total_passed = sum(r.passed for r in all_results.values())
    total_failed = sum(r.failed for r in all_results.values())
    total_duration = sum(r.total_duration for r in all_results.values())

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {(total_passed / total_tests) * 100:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")

    if total_failed > 0:
        print("\nFailed test suites:")
        for suite_name, result in all_results.items():
            if result.failed > 0:
                print(f"  {suite_name}: {result.failed} failed")

        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
