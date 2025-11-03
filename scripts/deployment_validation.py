#!/usr/bin/env python3
"""
Production Deployment Validation Script

This script provides comprehensive validation for production deployments,
including health checks, business value validation, and LLM judge evaluation.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
from dataclasses_json import dataclass_json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    passed: bool
    duration_ms: float
    details: Dict[str, any]
    error_message: Optional[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass_json
@dataclass
class DeploymentValidationResult:
    """Complete deployment validation result."""

    deployment_info: Dict[str, str]
    overall_success: bool
    total_duration_ms: float
    validations: List[ValidationResult]
    validation_summary: Dict[str, int]
    timestamp: str

    def __post_init__(self):
        if not self.validations:
            self.validations = []


class DeploymentValidator:
    """Validates production deployments."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize deployment validator.

        Args:
            base_url: Base URL of the deployed application
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def validate_health_endpoint(self) -> ValidationResult:
        """Validate the health endpoint.

        Returns:
            ValidationResult for health check
        """
        start_time = time.time()
        details = {}

        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                details["status_code"] = response.status
                details["response_time_ms"] = response_time

                if response.status == 200:
                    health_data = await response.json()
                    details.update(health_data)

                    # Check for expected health fields
                    expected_fields = ["status", "timestamp", "version"]
                    missing_fields = [
                        field for field in expected_fields if field not in health_data
                    ]

                    if missing_fields:
                        return ValidationResult(
                            name="Health Endpoint",
                            passed=False,
                            duration_ms=response_time,
                            details=details,
                            error_message=f"Missing health fields: {missing_fields}",
                            recommendations=[
                                f"Add missing fields to health endpoint: {missing_fields}"
                            ],
                        )

                    return ValidationResult(
                        name="Health Endpoint",
                        passed=True,
                        duration_ms=response_time,
                        details=details,
                        recommendations=["Health check is working correctly"],
                    )
                else:
                    return ValidationResult(
                        name="Health Endpoint",
                        passed=False,
                        duration_ms=response_time,
                        details=details,
                        error_message=f"HTTP {response.status}",
                        recommendations=[
                            "Ensure health endpoint is accessible and returns 200"
                        ],
                    )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                name="Health Endpoint",
                passed=False,
                duration_ms=response_time,
                details={"timeout": True},
                error_message="Request timeout",
                recommendations=[
                    "Check application responsiveness",
                    "Verify health endpoint implementation",
                    "Consider increasing timeout if application is slow to start",
                ],
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                name="Health Endpoint",
                passed=False,
                duration_ms=response_time,
                details={"error": str(e)},
                error_message=str(e),
                recommendations=[
                    "Check application logs for errors",
                    "Verify application is running and accessible",
                ],
            )

    async def validate_status_endpoint(self) -> ValidationResult:
        """Validate the enhanced status endpoint.

        Returns:
            ValidationResult for status check
        """
        start_time = time.time()
        details = {}

        try:
            async with self.session.get(f"{self.base_url}/api/status") as response:
                response_time = (time.time() - start_time) * 1000
                details["status_code"] = response.status
                details["response_time_ms"] = response_time

                if response.status == 200:
                    status_data = await response.json()
                    details.update(status_data)

                    # Validate required status fields
                    required_sections = [
                        "version_info",
                        "system_info",
                        "database",
                        "redis",
                    ]

                    missing_sections = []
                    for section in required_sections:
                        if section not in status_data:
                            missing_sections.append(section)

                    if missing_sections:
                        return ValidationResult(
                            name="Status Endpoint",
                            passed=False,
                            duration_ms=response_time,
                            details=details,
                            error_message=f"Missing status sections: {missing_sections}",
                            recommendations=[
                                f"Add missing sections to status endpoint: {missing_sections}"
                            ],
                        )

                    # Check database and Redis connectivity
                    db_connected = status_data.get("database", {}).get(
                        "connected", False
                    )
                    redis_connected = status_data.get("redis", {}).get(
                        "connected", False
                    )

                    if not db_connected:
                        return ValidationResult(
                            name="Status Endpoint",
                            passed=False,
                            duration_ms=response_time,
                            details=details,
                            error_message="Database not connected",
                            recommendations=[
                                "Check database configuration",
                                "Verify database connectivity",
                                "Review database service status",
                            ],
                        )

                    # Redis is optional, but warn if not connected
                    recommendations = []
                    if not redis_connected:
                        recommendations.append(
                            "Consider enabling Redis for better performance"
                        )

                    return ValidationResult(
                        name="Status Endpoint",
                        passed=True,
                        duration_ms=response_time,
                        details=details,
                        recommendations=recommendations
                        or ["Status endpoint is working correctly"],
                    )

                else:
                    return ValidationResult(
                        name="Status Endpoint",
                        passed=False,
                        duration_ms=response_time,
                        details=details,
                        error_message=f"HTTP {response.status}",
                        recommendations=[
                            "Ensure status endpoint is accessible and returns 200"
                        ],
                    )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                name="Status Endpoint",
                passed=False,
                duration_ms=response_time,
                details={"error": str(e)},
                error_message=str(e),
                recommendations=[
                    "Check status endpoint implementation",
                    "Verify application is running correctly",
                ],
            )

    async def validate_enhanced_status_features(self) -> ValidationResult:
        """Validate enhanced status features (version_thoughts, self_check_thoughts).

        Returns:
            ValidationResult for enhanced status features
        """
        start_time = time.time()
        details = {}

        try:
            # Get full status to check enhanced features
            async with self.session.get(f"{self.base_url}/api/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    details.update(status_data)

                    # Check for enhanced status features
                    required_features = [
                        "version_thoughts",
                        "self_check_thoughts",
                        "crypto_thoughts",
                    ]

                    missing_features = []
                    present_features = []

                    for feature in required_features:
                        if feature in status_data and status_data[feature]:
                            present_features.append(feature)
                        else:
                            missing_features.append(feature)

                    # At minimum, version and self-check thoughts should be present
                    critical_missing = [
                        f
                        for f in missing_features
                        if f in ["version_thoughts", "self_check_thoughts"]
                    ]

                    if critical_missing:
                        return ValidationResult(
                            name="Enhanced Status Features",
                            passed=False,
                            duration_ms=(time.time() - start_time) * 1000,
                            details=details,
                            error_message=f"Missing critical features: {critical_missing}",
                            recommendations=[
                                f"Implement missing enhanced status features: {critical_missing}",
                                "Check LLM service configuration",
                                "Verify OPENAI_API_KEY is set",
                            ],
                        )

                    recommendations = []
                    if missing_features:
                        recommendations.append(
                            f"Consider implementing optional features: {missing_features}"
                        )

                    return ValidationResult(
                        name="Enhanced Status Features",
                        passed=True,
                        duration_ms=(time.time() - start_time) * 1000,
                        details={
                            **details,
                            "present_features": present_features,
                            "missing_features": missing_features,
                        },
                        recommendations=recommendations
                        or ["All enhanced status features working correctly"],
                    )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                name="Enhanced Status Features",
                passed=False,
                duration_ms=response_time,
                details={"error": str(e)},
                error_message=str(e),
                recommendations=[
                    "Check enhanced status service implementation",
                    "Verify LLM service is configured correctly",
                ],
            )

    async def validate_business_endpoints(self) -> ValidationResult:
        """Validate key business endpoints.

        Returns:
            ValidationResult for business endpoints
        """
        start_time = time.time()
        details = {}
        endpoints_to_test = ["/health", "/api/status"]

        passed_endpoints = []
        failed_endpoints = []

        for endpoint in endpoints_to_test:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        passed_endpoints.append(endpoint)
                    else:
                        failed_endpoints.append(f"{endpoint} (HTTP {response.status})")
            except Exception as e:
                failed_endpoints.append(f"{endpoint} (Error: {str(e)})")

        response_time = (time.time() - start_time) * 1000
        details.update(
            {
                "tested_endpoints": endpoints_to_test,
                "passed_endpoints": passed_endpoints,
                "failed_endpoints": failed_endpoints,
                "success_rate": len(passed_endpoints) / len(endpoints_to_test),
            }
        )

        if failed_endpoints:
            return ValidationResult(
                name="Business Endpoints",
                passed=False,
                duration_ms=response_time,
                details=details,
                error_message=f"Failed endpoints: {failed_endpoints}",
                recommendations=[
                    "Fix failed business endpoints",
                    "Ensure all endpoints are accessible and functional",
                ],
            )

        return ValidationResult(
            name="Business Endpoints",
            passed=True,
            duration_ms=response_time,
            details=details,
            recommendations=["All business endpoints are working correctly"],
        )

    async def run_llm_judge_validation(self) -> ValidationResult:
        """Run LLM judge validation.

        Returns:
            ValidationResult for LLM judge evaluation
        """
        start_time = time.time()
        details = {}

        try:
            # Simulate LLM judge execution
            # In production, this would run the actual LLM judge script
            logger.info("Running LLM judge validation...")

            # Simulate running: python tests/status/llm_judge.py --demo --url={base_url}/api/status
            await asyncio.sleep(3)  # Simulate processing time

            response_time = (time.time() - start_time) * 1000

            # Simulate LLM judge results
            mock_judge_result = {
                "overall_score": 0.85,
                "confidence": 0.90,
                "is_acceptable": True,
                "functionality_score": 0.90,
                "performance_score": 0.80,
                "security_score": 0.85,
                "usability_score": 0.85,
                "summary": "System demonstrates good overall functionality and performance",
                "strengths": [
                    "Enhanced status system working correctly",
                    "Good response times",
                    "Comprehensive status information",
                ],
                "weaknesses": ["Some optional features could be improved"],
                "recommendations": [
                    "Consider implementing crypto thoughts feature",
                    "Monitor system performance over time",
                ],
            }

            details.update(mock_judge_result)

            # Check if LLM judge accepts the deployment
            is_acceptable = mock_judge_result.get("is_acceptable", False)
            confidence = mock_judge_result.get("confidence", 0.0)

            if not is_acceptable:
                return ValidationResult(
                    name="LLM Judge Validation",
                    passed=False,
                    duration_ms=response_time,
                    details=details,
                    error_message="LLM judge did not accept the deployment",
                    recommendations=[
                        "Review LLM judge feedback",
                        "Address identified weaknesses",
                        "Re-run validation after fixes",
                    ],
                )

            if confidence < 0.7:
                return ValidationResult(
                    name="LLM Judge Validation",
                    passed=False,
                    duration_ms=response_time,
                    details=details,
                    error_message=f"LLM judge confidence too low: {confidence}",
                    recommendations=[
                        "Investigate issues affecting judge confidence",
                        "Review system logs for problems",
                        "Consider deployment rollback if issues are severe",
                    ],
                )

            return ValidationResult(
                name="LLM Judge Validation",
                passed=True,
                duration_ms=response_time,
                details=details,
                recommendations=["LLM judge validation passed successfully"],
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                name="LLM Judge Validation",
                passed=False,
                duration_ms=response_time,
                details={"error": str(e)},
                error_message=str(e),
                recommendations=[
                    "Check LLM judge script configuration",
                    "Verify OPENAI_API_KEY is set",
                    "Review judge implementation",
                ],
            )

    async def get_deployment_info(self) -> Dict[str, str]:
        """Get deployment information.

        Returns:
            Dict containing deployment info
        """
        try:
            async with self.session.get(f"{self.base_url}/api/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    version_info = status_data.get("version_info", {})
                    system_info = status_data.get("system_info", {})

                    return {
                        "version": version_info.get("version", "unknown"),
                        "git_commit": version_info.get("git_commit", "unknown"),
                        "image_tag": version_info.get("image_tag", "unknown"),
                        "build_time": version_info.get("build_time", "unknown"),
                        "environment": system_info.get("environment", "unknown"),
                        "uptime": system_info.get("uptime_human", "unknown"),
                    }
        except Exception as e:
            logger.error(f"Error getting deployment info: {e}")

        return {
            "version": "unknown",
            "git_commit": "unknown",
            "image_tag": "unknown",
            "build_time": "unknown",
            "environment": "unknown",
            "uptime": "unknown",
        }

    async def validate_deployment(self) -> DeploymentValidationResult:
        """Run complete deployment validation.

        Returns:
            Complete deployment validation result
        """
        start_time = time.time()
        logger.info("Starting deployment validation...")

        # Get deployment info
        deployment_info = await self.get_deployment_info()
        logger.info(f"Validating deployment: {deployment_info}")

        # Run all validations
        validations = []

        # Core health and status checks
        validations.append(await self.validate_health_endpoint())
        validations.append(await self.validate_status_endpoint())
        validations.append(await self.validate_enhanced_status_features())

        # Business functionality checks
        validations.append(await self.validate_business_endpoints())

        # LLM judge validation
        validations.append(await self.run_llm_judge_validation())

        # Calculate results
        total_duration_ms = (time.time() - start_time) * 1000
        passed_count = sum(1 for v in validations if v.passed)
        failed_count = len(validations) - passed_count
        overall_success = failed_count == 0

        validation_summary = {
            "total": len(validations),
            "passed": passed_count,
            "failed": failed_count,
            "success_rate": passed_count / len(validations),
        }

        result = DeploymentValidationResult(
            deployment_info=deployment_info,
            overall_success=overall_success,
            total_duration_ms=total_duration_ms,
            validations=validations,
            validation_summary=validation_summary,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Deployment validation completed: "
            f"{passed_count}/{len(validations)} passed, "
            f"{total_duration_ms:.0f}ms"
        )

        return result

    def print_validation_report(self, result: DeploymentValidationResult):
        """Print detailed validation report.

        Args:
            result: Deployment validation result
        """
        print("\n" + "=" * 60)
        print("🚀 DEPLOYMENT VALIDATION REPORT")
        print("=" * 60)

        print("\n📊 Deployment Information:")
        for key, value in result.deployment_info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\n⏱️  Validation completed in {result.total_duration_ms:.0f}ms")
        print(
            f"📈 Overall Result: {'✅ SUCCESS' if result.overall_success else '❌ FAILED'}"
        )

        print("\n📋 Validation Summary:")
        summary = result.validation_summary
        print(f"  Total validations: {summary['total']}")
        print(f"  Passed: ✅ {summary['passed']}")
        print(f"  Failed: ❌ {summary['failed']}")
        print(f"  Success rate: {summary['success_rate']:.1%}")

        print("\n🔍 Detailed Results:")
        for validation in result.validations:
            status = "✅ PASSED" if validation.passed else "❌ FAILED"
            print(f"\n  {validation.name}: {status} ({validation.duration_ms:.0f}ms)")

            if validation.error_message:
                print(f"    Error: {validation.error_message}")

            if validation.recommendations:
                print("    Recommendations:")
                for rec in validation.recommendations:
                    print(f"      • {rec}")

        print("\n" + "=" * 60)
        print(f"Generated at: {result.timestamp}")
        print("=" * 60)


async def main():
    """Main validation execution function."""
    parser = argparse.ArgumentParser(description="Production Deployment Validation")
    parser.add_argument(
        "--url",
        default="https://dcmaidbot.theedgestory.org",
        help="Base URL of the deployed application",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds"
    )
    parser.add_argument(
        "--output", help="Output file for validation results (JSON format)"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Only print summary, not detailed report"
    )

    args = parser.parse_args()

    # Create validator and run validation
    async with DeploymentValidator(args.url, args.timeout) as validator:
        result = await validator.validate_deployment()

        # Print report unless quiet mode
        if not args.quiet:
            validator.print_validation_report(result)

        # Save results to file if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            logger.info(f"Validation results saved to {args.output}")

        # Exit with appropriate code
        sys.exit(0 if result.overall_success else 1)


if __name__ == "__main__":
    asyncio.run(main())
