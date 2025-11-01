"""
E2E Production Validation Script

Tests all user stories with real Telegram API calls.
Run after each production deployment to verify functionality.

Usage:
    python tests/e2e_production.py

    Or via GitHub Actions:
    gh workflow run e2e-production.yml

Requirements:
    - BOT_TOKEN: Production bot token
    - TEST_ADMIN_ID: Admin user ID for testing
    - PRODUCTION_URL: https://dcmaidbot.theedgestory.org
"""

import asyncio
import os
import sys
from datetime import datetime

import httpx
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

# Test configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
TEST_ADMIN_ID = int(os.getenv("TEST_ADMIN_ID", "0"))
PRODUCTION_URL = os.getenv("PRODUCTION_URL", "https://dcmaidbot.theedgestory.org")

# Test results
test_results: list[dict] = []


class Colors:
    """Terminal colors for output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def log_test(name: str, status: str, details: str = ""):
    """Log test result."""
    timestamp = datetime.now().isoformat()
    result = {
        "name": name,
        "status": status,
        "details": details,
        "timestamp": timestamp,
    }
    test_results.append(result)

    if status == "PASS":
        color = Colors.GREEN
        icon = "✅"
    elif status == "FAIL":
        color = Colors.RED
        icon = "❌"
    else:
        color = Colors.YELLOW
        icon = "⏭️"

    print(f"{color}{icon} {name}: {status}{Colors.RESET}")
    if details:
        print(f"   {details}")


async def test_health_endpoint():
    """Test /health endpoint returns healthy status."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTION_URL}/health", timeout=10.0)

            if response.status_code != 200:
                log_test(
                    "Health Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
                return False

            data = response.json()
            if data.get("status") != "healthy":
                log_test(
                    "Health Endpoint",
                    "FAIL",
                    f"Status not healthy: {data}",
                )
                return False

            # Check all services
            checks = data.get("checks", {})
            if checks.get("bot") != "ok":
                log_test("Health Endpoint", "FAIL", "Bot status not ok")
                return False

            if checks.get("database") != "ok":
                log_test("Health Endpoint", "FAIL", "Database status not ok")
                return False

            log_test(
                "Health Endpoint",
                "PASS",
                f"All services healthy: {checks}",
            )
            return True

    except Exception as e:
        log_test("Health Endpoint", "FAIL", f"Exception: {e}")
        return False


async def test_landing_page():
    """Test landing page loads and /api/version endpoint works."""
    try:
        async with httpx.AsyncClient() as client:
            # Test landing page HTML loads
            response = await client.get(f"{PRODUCTION_URL}/", timeout=10.0)

            if response.status_code != 200:
                log_test(
                    "Landing Page",
                    "FAIL",
                    f"HTTP {response.status_code}",
                )
                return False

            html = response.text

            # Check for key elements
            if "Lilith" not in html or "DCMaidBot" not in html:
                log_test("Landing Page", "FAIL", "Missing bot name")
                return False

            # Test /api/version endpoint (used by landing page JS)
            api_response = await client.get(
                f"{PRODUCTION_URL}/api/version", timeout=10.0
            )

            if api_response.status_code != 200:
                log_test(
                    "Landing Page",
                    "FAIL",
                    f"/api/version returned HTTP {api_response.status_code}",
                )
                return False

            version_data = api_response.json()

            # Check version from API matches version.txt
            with open("version.txt") as f:
                expected_version = f.read().strip()

            if version_data.get("version") != expected_version:
                log_test(
                    "Landing Page",
                    "FAIL",
                    f"/api/version returned {version_data.get('version')}, "
                    f"expected {expected_version}",
                )
                return False

            log_test(
                "Landing Page",
                "PASS",
                f"HTML loads, /api/version returns v{expected_version}",
            )
            return True

    except Exception as e:
        log_test("Landing Page", "FAIL", f"Exception: {e}")
        return False


async def test_bot_me():
    """Test bot.get_me() returns correct bot info."""
    try:
        if not BOT_TOKEN:
            log_test("Bot Info", "SKIP", "No BOT_TOKEN provided")
            return False

        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        await bot.session.close()

        if not me.username:
            log_test("Bot Info", "FAIL", "No username returned")
            return False

        log_test(
            "Bot Info",
            "PASS",
            f"@{me.username} (ID: {me.id})",
        )
        return True

    except Exception as e:
        log_test("Bot Info", "FAIL", f"Exception: {e}")
        return False


async def test_send_message_to_admin():
    """Test sending a message to admin (simulates bot outgoing message)."""
    try:
        if not BOT_TOKEN or not TEST_ADMIN_ID:
            log_test(
                "Send Message",
                "SKIP",
                "BOT_TOKEN or TEST_ADMIN_ID not provided",
            )
            return False

        bot = Bot(token=BOT_TOKEN)

        test_message = (
            f"🧪 E2E Test: Bot can send messages (UTC: {datetime.utcnow().isoformat()})"
        )

        msg = await bot.send_message(
            chat_id=TEST_ADMIN_ID,
            text=test_message,
        )
        await bot.session.close()

        if not msg.message_id:
            log_test("Send Message", "FAIL", "No message_id returned")
            return False

        log_test(
            "Send Message",
            "PASS",
            f"Message sent to admin (msg_id: {msg.message_id})",
        )
        return True

    except Exception as e:
        log_test("Send Message", "FAIL", f"Exception: {e}")
        return False


async def test_bot_commands():
    """Test bot commands are configured."""
    try:
        if not BOT_TOKEN:
            log_test("Bot Commands", "SKIP", "No BOT_TOKEN provided")
            return False

        bot = Bot(token=BOT_TOKEN)
        commands = await bot.get_my_commands()
        await bot.session.close()

        if not commands:
            log_test("Bot Commands", "FAIL", "No commands configured")
            return False

        command_list = [f"/{cmd.command}" for cmd in commands]
        log_test(
            "Bot Commands",
            "PASS",
            f"Commands configured: {', '.join(command_list)}",
        )
        return True

    except Exception as e:
        log_test("Bot Commands", "FAIL", f"Exception: {e}")
        return False


async def test_database_connection():
    """Test database is accessible via bot check."""
    # This is implicit in health check, but we can verify via logs
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTION_URL}/health", timeout=10.0)
            data = response.json()

            checks = data.get("checks", {})
            if checks.get("database") == "ok":
                log_test("Database Connection", "PASS", "Database accessible")
                return True
            else:
                log_test(
                    "Database Connection",
                    "FAIL",
                    f"Database status: {checks.get('database')}",
                )
                return False

    except Exception as e:
        log_test("Database Connection", "FAIL", f"Exception: {e}")
        return False


async def test_redis_connection():
    """Test Redis is accessible via bot check."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTION_URL}/health", timeout=10.0)
            data = response.json()

            checks = data.get("checks", {})
            redis_status = checks.get("redis", "unknown")

            if redis_status == "ok":
                log_test("Redis Connection", "PASS", "Redis accessible")
                return True
            elif redis_status == "unavailable":
                log_test(
                    "Redis Connection",
                    "PASS",
                    "Redis not configured (bot works without it)",
                )
                return True
            else:
                log_test("Redis Connection", "FAIL", f"Redis status: {redis_status}")
                return False

    except Exception as e:
        log_test("Redis Connection", "FAIL", f"Exception: {e}")
        return False


async def test_webhook_configured():
    """Test webhook is configured correctly."""
    try:
        if not BOT_TOKEN:
            log_test("Webhook Config", "SKIP", "No BOT_TOKEN provided")
            return False

        bot = Bot(token=BOT_TOKEN)
        webhook_info = await bot.get_webhook_info()
        await bot.session.close()

        if not webhook_info.url:
            log_test("Webhook Config", "FAIL", "No webhook URL configured")
            return False

        expected_webhook = f"{PRODUCTION_URL}/webhook"
        if webhook_info.url != expected_webhook:
            log_test(
                "Webhook Config",
                "FAIL",
                f"Webhook URL mismatch: {webhook_info.url} != {expected_webhook}",
            )
            return False

        log_test(
            "Webhook Config",
            "PASS",
            f"Webhook: {webhook_info.url}",
        )
        return True

    except Exception as e:
        log_test("Webhook Config", "FAIL", f"Exception: {e}")
        return False


def print_summary():
    """Print test summary."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")

    print(f"Total Tests:  {total}")
    print(f"{Colors.GREEN}Passed:       {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed:       {failed}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped:      {skipped}{Colors.RESET}")

    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ E2E VALIDATION FAILED{Colors.RESET}\n")
        print("Failed tests:")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  - {r['name']}: {r['details']}")
        return False
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ E2E VALIDATION PASSED{Colors.RESET}\n")
        return True


async def main():
    """Run all E2E tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(
        f"{Colors.BOLD}{Colors.BLUE}DCMaidBot E2E Production Validation{Colors.RESET}"
    )
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

    print(f"Production URL: {PRODUCTION_URL}")
    print(f"Test Admin ID:  {TEST_ADMIN_ID if TEST_ADMIN_ID else 'Not configured'}")
    print(f"Bot Token:      {'✅ Provided' if BOT_TOKEN else '❌ Missing'}\n")

    # Run all tests
    await test_health_endpoint()
    await test_landing_page()
    await test_bot_me()
    await test_bot_commands()
    await test_webhook_configured()
    await test_database_connection()
    await test_redis_connection()
    await test_send_message_to_admin()

    # Print summary and exit
    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
