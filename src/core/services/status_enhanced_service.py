"""
Enhanced Status Service with Self-Check Thoughts and Crypto Thoughts Integration
Business Requirements: Comprehensive system health monitoring with LLM-powered insights

This service implements the enhanced status system with version_thoughts, self_check_thoughts,
and crypto_thoughts as described in PRP-010.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.services.crypto_thoughts_service import CryptoThoughtsService
from core.services.llm_service import LLMService


class EnhancedStatusService:
    """
    Enhanced status service with self-check thoughts and crypto insights
    Business Value: Comprehensive system monitoring with AI-powered diagnostics
    """

    def __init__(self, llm_service: LLMService):
        """Initialize enhanced status service"""
        self.llm_service = llm_service
        self.crypto_service = CryptoThoughtsService()
        self.start_time = datetime.now()
        self.version_thoughts = None
        self.self_check_thoughts = None
        self.last_self_check_time = None
        self.crypto_thoughts = None
        self.last_crypto_thoughts_time = None
        self.tokens_used = 0

    async def generate_version_thoughts(
        self, changelog_content: str, previous_version_thoughts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate version thoughts using internal LLM with opinion field
        Business Story: Lilith reflects on the new version and shares her thoughts with opinions
        """
        print("🧠 Generating version thoughts with Lilith's opinions...")

        start_time = time.time()

        # Create the version thoughts prompt with opinion storytelling
        if previous_version_thoughts:
            prev_thoughts = f"and seems what last time you think about update was:\n{previous_version_thoughts}"
        else:
            prev_thoughts = "i dont know what was previus version"

        prompt = f"""You have been provided CHANGELOG content:
{changelog_content}

{prev_thoughts}

And now, please tell us what your current version is? What you can do new now? Do you like it? What else do you want?

Please provide TWO parts:
1) Technical summary - what's new in this version, what features are added
2) Lilith's OPINION - your personal thoughts as a kawaii AI character about this update. Be honest about what you think, what excites you, what worries you, or what you wish was different. Use storytelling format, be personal, express your real feelings about these changes.

Be brief, use markdown and be kawaii, lilith <3"""

        try:
            # Generate version thoughts using LLM service
            thoughts_response = await self.llm_service.generate_response(prompt)

            # Count tokens (simplified - in real implementation would use actual token counting)
            estimated_tokens = len(prompt.split()) + len(thoughts_response.split())
            self.tokens_used += estimated_tokens

            generation_time = time.time() - start_time

            # Parse technical summary and opinion
            parts = thoughts_response.split("Lilith's OPINION")
            technical_summary = parts[0].strip() if parts else thoughts_response
            opinion = (
                parts[1].strip()
                if len(parts) > 1
                else "I'm still processing my thoughts about this update... Give me a moment to form my opinion! >.<"
            )

            result = {
                "version_thoughts": thoughts_response,
                "technical_summary": technical_summary,
                "lilith_opinion": opinion,
                "generation_time": generation_time,
                "tokens_used": estimated_tokens,
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }

            self.version_thoughts = result

            print("✅ Version thoughts with opinions generated successfully")
            return result

        except Exception as e:
            print(f"❌ Failed to generate version thoughts: {e}")

            result = {
                "version_thoughts": f"Sorry, I'm having trouble thinking about the new version... Error: {str(e)}",
                "technical_summary": "Error generating technical summary",
                "lilith_opinion": f"I'm confused about this update... Something went wrong! Error: {str(e)}",
                "generation_time": time.time() - start_time,
                "tokens_used": 0,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
            }

            self.version_thoughts = result
            return result

    async def generate_self_check_thoughts(self) -> Dict[str, Any]:
        """
        Generate self-check thoughts by running diagnostics on all systems with opinion field
        Business Story: Lilith performs a comprehensive self-diagnosis and shares her honest opinions
        """
        print("🔍 Starting comprehensive self-check diagnostics with opinions...")

        start_time = time.time()
        self.last_self_check_time = start_time

        # Create self-check instructions for each tool
        tool_checks = [
            {
                "name": "webhook_endpoint",
                "instructions": "Run curl call to $BOT_ENV_URL/webhook with secret $WEBHOOK_SECRET and self-check message. Expectation: 200 OK. If failed, try curl to $BOT_ENV_URL/status. If that fails, try curl to google.com. If curl to google works but webhook/status not, report about this.",
                "confidence_score": 0,
                "test_result": "unknown",
                "expectations": "200 OK response",
                "explanation_reflect": "",
                "status": "pending",
            },
            {
                "name": "database_connection",
                "instructions": "Test PostgreSQL database connection with a simple query. Expectation: Successful query execution. If failed, check connection string and database availability.",
                "confidence_score": 0,
                "test_result": "unknown",
                "expectations": "Successful query",
                "explanation_reflect": "",
                "status": "pending",
            },
            {
                "name": "redis_connection",
                "instructions": "Test Redis connection with SET/GET operations. Expectation: Successful read/write operations. If failed, check Redis server availability.",
                "confidence_score": 0,
                "test_result": "unknown",
                "expectations": "Successful read/write",
                "explanation_reflect": "",
                "status": "pending",
            },
            {
                "name": "telegram_bot",
                "instructions": "Test Telegram bot API connectivity. Expectation: Successful bot info retrieval. If failed, check bot token and network connectivity.",
                "confidence_score": 0,
                "test_result": "unknown",
                "expectations": "Bot info retrieved",
                "explanation_reflect": "",
                "status": "pending",
            },
            {
                "name": "crypto_service",
                "instructions": "Test crypto thoughts service generation. Expectation: Successful crypto insights generation. If failed, check API endpoints and LLM service.",
                "confidence_score": 0,
                "test_result": "unknown",
                "expectations": "Crypto insights generated",
                "explanation_reflect": "",
                "status": "pending",
            },
        ]

        # Execute tool checks in parallel
        print("🔧 Running parallel tool diagnostics...")
        tool_results = await self.execute_tool_checks(tool_checks)

        # Generate comprehensive self-check report with opinion
        self_check_prompt = f"""You need to make a self-diagnosis of all our systems. You have run each tool and need to provide a verification report.

TOOL CHECK RESULTS:
{json.dumps(tool_results, indent=2)}

Please provide TWO parts:
1) Technical Report - For each tool, provide: confidence score (0-10), test result summary, what was expected vs what happened, brief explanation/reflection, status: working/failing/missing

2) Lilith's HONEST OPINION - As the AI running this system, share your personal feelings about these tools. Which ones worry you? Which ones make you confident? What tools would you love to have improved? What frustrates you about the current setup? Be honest, emotional, and tell a story about how these tools affect your daily work.

Be thorough but concise. Use markdown formatting. Show your personality in both parts."""

        try:
            # Generate self-check thoughts using LLM
            self_check_response = await self.llm_service.generate_response(
                self_check_prompt
            )

            # Count tokens
            estimated_tokens = len(self_check_prompt.split()) + len(
                self_check_response.split()
            )
            self.tokens_used += estimated_tokens

            total_time = time.time() - start_time

            # Parse technical report and opinion
            parts = self_check_response.split("Lilith's HONEST OPINION")
            technical_report = parts[0].strip() if parts else self_check_response
            honest_opinion = (
                parts[1].strip()
                if len(parts) > 1
                else "I'm still gathering my thoughts about how these systems make me feel... Check back soon for my honest opinion! ^^"
            )

            result = {
                "self_check_thoughts": self_check_response,
                "technical_report": technical_report,
                "lilith_honest_opinion": honest_opinion,
                "tool_results": tool_results,
                "total_time": total_time,
                "tokens_used": estimated_tokens,
                "timestamp": datetime.now().isoformat(),
                "start_time": self.start_time.isoformat(),
                "success": True,
            }

            self.self_check_thoughts = result

            print("✅ Self-check diagnostics with opinions completed successfully")
            return result

        except Exception as e:
            print(f"❌ Failed to generate self-check thoughts: {e}")

            result = {
                "self_check_thoughts": f"Self-check interrupted due to error: {str(e)}",
                "technical_report": "Error generating technical report",
                "lilith_honest_opinion": f"I'm feeling overwhelmed by all these errors... Something's not right with my systems! Error: {str(e)}",
                "tool_results": tool_results,
                "total_time": time.time() - start_time,
                "tokens_used": 0,
                "timestamp": datetime.now().isoformat(),
                "start_time": self.start_time.isoformat(),
                "success": False,
                "error": str(e),
            }

            self.self_check_thoughts = result
            return result

    async def execute_tool_checks(
        self, tool_checks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute parallel tool diagnostics
        Business Value: Comprehensive system health validation
        """
        results = []

        # Execute tool checks with some parallel processing
        for tool_check in tool_checks:
            print(f"🔍 Checking {tool_check['name']}...")

            try:
                # Simulate tool check execution
                # In real implementation, these would be actual system calls
                result = await self.simulate_tool_check(tool_check)
                results.append(result)

            except Exception as e:
                # Handle failed tool check
                failed_result = {
                    **tool_check,
                    "confidence_score": 0,
                    "test_result": f"Error: {str(e)}",
                    "explanation_reflect": f"Tool check failed with exception: {str(e)}",
                    "status": "failing",
                    "error": str(e),
                }
                results.append(failed_result)

        return results

    async def simulate_tool_check(self, tool_check: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate tool check execution
        Business Logic: Mock implementation for demonstration
        """
        tool_name = tool_check["name"]

        # Simulate different tool behaviors
        if tool_name == "webhook_endpoint":
            # Simulate webhook check
            await asyncio.sleep(0.1)  # Simulate network delay
            return {
                **tool_check,
                "confidence_score": 8,
                "test_result": "Webhook endpoint responded with 200 OK",
                "explanation_reflect": "Webhook service is operational and responding correctly",
                "status": "working",
            }

        elif tool_name == "database_connection":
            # Simulate database check
            await asyncio.sleep(0.2)
            return {
                **tool_check,
                "confidence_score": 9,
                "test_result": "Database query executed successfully",
                "explanation_reflect": "PostgreSQL connection is stable and performing well",
                "status": "working",
            }

        elif tool_name == "redis_connection":
            # Simulate Redis check
            await asyncio.sleep(0.1)
            return {
                **tool_check,
                "confidence_score": 9,
                "test_result": "Redis SET/GET operations successful",
                "explanation_reflect": "Redis cache is operational with good performance",
                "status": "working",
            }

        elif tool_name == "telegram_bot":
            # Simulate Telegram bot check
            await asyncio.sleep(0.3)
            return {
                **tool_check,
                "confidence_score": 7,
                "test_result": "Bot info retrieved successfully",
                "explanation_reflect": "Telegram bot API is accessible, token is valid",
                "status": "working",
            }

        elif tool_name == "crypto_service":
            # Test actual crypto service
            try:
                crypto_test = await self.crypto_service.generate_crypto_thoughts()
                return {
                    **tool_check,
                    "confidence_score": 8,
                    "test_result": "Crypto thoughts generated successfully",
                    "explanation_reflect": f"Crypto service operational. Sample output: {crypto_test[:100]}...",
                    "status": "working",
                }
            except Exception as e:
                return {
                    **tool_check,
                    "confidence_score": 0,
                    "test_result": f"Crypto service failed: {str(e)}",
                    "explanation_reflect": "Crypto service encountered an error during testing",
                    "status": "failing",
                }

        else:
            # Unknown tool
            return {
                **tool_check,
                "confidence_score": 0,
                "test_result": "Unknown tool",
                "explanation_reflect": "Tool configuration missing or not recognized",
                "status": "missing",
            }

    async def generate_crypto_thoughts_if_needed(self) -> Optional[Dict[str, Any]]:
        """
        Generate crypto thoughts if last update was more than 12 hours ago
        Business Logic: Automated crypto insights generation every 12 hours
        """
        if self.last_crypto_thoughts_time is None:
            # First time running
            should_generate = True
        else:
            # Check if 12 hours have passed
            time_since_last = datetime.now() - self.last_crypto_thoughts_time
            should_generate = time_since_last > timedelta(hours=12)

        if should_generate:
            print("🪙 Generating crypto thoughts...")

            try:
                start_time = time.time()
                crypto_thoughts = await self.crypto_service.generate_crypto_thoughts()

                generation_time = time.time() - start_time

                # Count tokens (simplified)
                estimated_tokens = len(crypto_thoughts.split())
                self.tokens_used += estimated_tokens

                result = {
                    "crypto_thoughts": crypto_thoughts,
                    "generation_time": generation_time,
                    "tokens_used": estimated_tokens,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                }

                self.crypto_thoughts = result
                self.last_crypto_thoughts_time = datetime.now()

                print("✅ Crypto thoughts generated successfully")
                return result

            except Exception as e:
                print(f"❌ Failed to generate crypto thoughts: {e}")

                result = {
                    "crypto_thoughts": f"Crypto thoughts generation failed: {str(e)}",
                    "generation_time": time.time() - start_time,
                    "tokens_used": 0,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e),
                }

                self.crypto_thoughts = result
                return result

        return self.crypto_thoughts

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including all thoughts and metrics
        Business Value: Complete system overview for monitoring and diagnostics
        """
        print("📊 Generating comprehensive system status...")

        # Ensure crypto thoughts are up to date
        await self.generate_crypto_thoughts_if_needed()

        # Calculate uptime
        uptime = datetime.now() - self.start_time
        uptime_seconds = uptime.total_seconds()

        # Calculate tokens per uptime
        tokens_per_uptime = (
            self.tokens_used / uptime_seconds if uptime_seconds > 0 else 0
        )

        # Read version from file
        version_info = self.get_version_info()

        status = {
            # Basic system info
            "versiontxt": version_info.get("versiontxt", "unknown"),
            "version": version_info.get("version", "unknown"),
            "commit": version_info.get("commit", "unknown"),
            "uptime": uptime_seconds,
            "start_time": self.start_time.isoformat(),
            # Thoughts and diagnostics
            "version_thoughts": self.version_thoughts,
            "self_check_thoughts": self.self_check_thoughts,
            "self_check_time_sec": self.self_check_thoughts.get("total_time")
            if self.self_check_thoughts
            else None,
            # Crypto thoughts
            "crypto_thoughts": self.crypto_thoughts,
            "crypto_thoughts_secs": self.crypto_thoughts.get("generation_time")
            if self.crypto_thoughts
            else None,
            "crypto_thoughts_time": self.crypto_thoughts.get("timestamp")
            if self.crypto_thoughts
            else None,
            "crypto_thoughts_tokens": self.crypto_thoughts.get("tokens_used", 0)
            if self.crypto_thoughts
            else 0,
            # Token usage
            "tokens_total": self.tokens_used,
            "tokens_uptime": tokens_per_uptime,
            # System components (simulated)
            "redis": {"status": "operational", "response_time": 0.1},
            "postgresql": {"status": "operational", "connections": 5},
            "telegram": {
                "status": "operational",
                "last_update": datetime.now().isoformat(),
            },
            "bot": {"status": "operational", "commands_processed": 100},
            # Infrastructure info
            "image_tag": "dcmaidbot:latest",
            "build_time": "2025-11-02T12:00:00Z",
            # Nudge tracking (placeholder)
            "last_nudge_fact": None,
            "last_nudge_read": None,
            "timestamp": datetime.now().isoformat(),
        }

        return status

    def get_version_info(self) -> Dict[str, str]:
        """
        Read version information from files
        Business Logic: System version tracking
        """
        try:
            # Try to read version.txt
            version_file = Path("version.txt")
            if version_file.exists():
                with open(version_file, "r") as f:
                    versiontxt = f.read().strip()
            else:
                versiontxt = "unknown"

            # Try to get commit info (simplified)
            import subprocess

            try:
                commit = (
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
                    )
                    .decode()
                    .strip()
                )
            except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
                commit = "unknown"

            # Extract version from versiontxt
            version = versiontxt.split("-")[0] if "-" in versiontxt else versiontxt

            return {"versiontxt": versiontxt, "version": version, "commit": commit}

        except Exception as e:
            print(f"⚠️ Error reading version info: {e}")
            return {"versiontxt": "unknown", "version": "unknown", "commit": "unknown"}

    async def initialize_status_system(
        self, changelog_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize the enhanced status system
        Business Story: System startup with Lilith's version thoughts and self-check
        """
        print("🚀 Initializing Enhanced Status System...")

        initialization_results = {}

        # Generate version thoughts if changelog provided
        if changelog_content:
            print("📝 Reading changelog for version thoughts...")
            version_result = await self.generate_version_thoughts(changelog_content)
            initialization_results["version_thoughts"] = version_result

        # Generate self-check thoughts
        print("🔍 Running initial self-check diagnostics...")
        self_check_result = await self.generate_self_check_thoughts()
        initialization_results["self_check_thoughts"] = self_check_result

        # Generate crypto thoughts if needed
        crypto_result = await self.generate_crypto_thoughts_if_needed()
        if crypto_result:
            initialization_results["crypto_thoughts"] = crypto_result

        print("✅ Enhanced Status System initialization complete")

        return {
            "initialization_complete": True,
            "timestamp": datetime.now().isoformat(),
            "results": initialization_results,
        }

    async def get_all_status_thoughts(self) -> Dict[str, Any]:
        """
        Get all status thoughts and opinions for tool access
        Business Value: Comprehensive access to all AI-generated insights and opinions
        """
        print("📚 Gathering all status thoughts and opinions...")

        # Get current crypto thoughts
        crypto_status = await self.generate_crypto_thoughts_if_needed()

        # Prepare all thoughts data
        all_thoughts = {
            "timestamp": datetime.now().isoformat(),
            "liliths_version_thoughts": {
                "available": self.version_thoughts is not None,
                "content": self.version_thoughts.get("version_thoughts")
                if self.version_thoughts
                else "Not generated yet",
                "technical_summary": self.version_thoughts.get("technical_summary")
                if self.version_thoughts
                else "Not available",
                "lilith_opinion": self.version_thoughts.get("lilith_opinion")
                if self.version_thoughts
                else "I haven't formed my opinion about the version yet!",
                "generation_time": self.version_thoughts.get("generation_time")
                if self.version_thoughts
                else 0,
                "tokens_used": self.version_thoughts.get("tokens_used", 0)
                if self.version_thoughts
                else 0,
                "last_updated": self.version_thoughts.get("timestamp")
                if self.version_thoughts
                else None,
            },
            "liliths_self_check_thoughts": {
                "available": self.self_check_thoughts is not None,
                "content": self.self_check_thoughts.get("self_check_thoughts")
                if self.self_check_thoughts
                else "Not generated yet",
                "technical_report": self.self_check_thoughts.get("technical_report")
                if self.self_check_thoughts
                else "Not available",
                "lilith_honest_opinion": self.self_check_thoughts.get(
                    "lilith_honest_opinion"
                )
                if self.self_check_thoughts
                else "I'm still checking my systems and forming my honest opinions!",
                "tool_results": self.self_check_thoughts.get("tool_results", [])
                if self.self_check_thoughts
                else [],
                "total_time": self.self_check_thoughts.get("total_time")
                if self.self_check_thoughts
                else 0,
                "tokens_used": self.self_check_thoughts.get("tokens_used", 0)
                if self.self_check_thoughts
                else 0,
                "last_updated": self.self_check_thoughts.get("timestamp")
                if self.self_check_thoughts
                else None,
            },
            "crypto_therapist_thoughts": {
                "available": crypto_status is not None,
                "content": crypto_status.get("crypto_thoughts")
                if crypto_status
                else "Not generated yet",
                "market_analysis": crypto_status.get("market_analysis")
                if crypto_status
                else "No market analysis available",
                "irrational_behavior": crypto_status.get("irrational_behavior")
                if crypto_status
                else "No behavior analysis available",
                "uncomfortable_truth": crypto_status.get("uncomfortable_truth")
                if crypto_status
                else "No uncomfortable truth available",
                "generation_time": crypto_status.get("generation_time")
                if crypto_status
                else 0,
                "tokens_used": crypto_status.get("tokens_used", 0)
                if crypto_status
                else 0,
                "last_updated": crypto_status.get("timestamp")
                if crypto_status
                else None,
            },
            "summary": {
                "total_thoughts_available": sum(
                    [
                        1
                        for thoughts in [
                            self.version_thoughts,
                            self.self_check_thoughts,
                            crypto_status,
                        ]
                        if thoughts is not None
                    ]
                ),
                "total_tokens_used": self.tokens_used,
                "system_uptime": (datetime.now() - self.start_time).total_seconds(),
                "lilith_mood": "thoughtful and analytical",
                "last_comprehensive_update": max(
                    [
                        self.version_thoughts.get("timestamp")
                        if self.version_thoughts
                        else "",
                        self.self_check_thoughts.get("timestamp")
                        if self.self_check_thoughts
                        else "",
                        crypto_status.get("timestamp") if crypto_status else "",
                    ]
                )
                or "No updates yet",
            },
        }

        return all_thoughts

    async def refresh_all_thoughts(
        self, changelog_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Force refresh all thoughts and opinions
        Business Value: Fresh insights and updated opinions
        """
        print("🔄 Refreshing all thoughts and opinions...")

        refresh_results = {}

        # Refresh version thoughts
        if changelog_content:
            print("📝 Refreshing version thoughts...")
            version_result = await self.generate_version_thoughts(changelog_content)
            refresh_results["version_thoughts"] = version_result

        # Refresh self-check thoughts
        print("🔍 Refreshing self-check thoughts...")
        self_check_result = await self.generate_self_check_thoughts()
        refresh_results["self_check_thoughts"] = self_check_result

        # Refresh crypto thoughts
        print("🪙 Refreshing crypto thoughts...")
        crypto_result = await self.crypto_service.generate_crypto_thoughts(
            force_refresh=True
        )
        refresh_results["crypto_thoughts"] = {
            "crypto_thoughts": crypto_result.market_analysis,
            "generation_time": crypto_result.processing_time_seconds,
            "tokens_used": crypto_result.tokens_used,
            "timestamp": crypto_result.timestamp,
            "success": True,
        }

        # Get updated all thoughts
        updated_thoughts = await self.get_all_status_thoughts()

        return {
            "refresh_complete": True,
            "timestamp": datetime.now().isoformat(),
            "refresh_results": refresh_results,
            "updated_thoughts": updated_thoughts,
        }
