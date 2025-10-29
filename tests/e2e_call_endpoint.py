"""
E2E Testing via /call Endpoint

Tests bot functionality by calling the /call endpoint directly,
bypassing Telegram entirely. This allows testing all bot logic
without needing Telegram API credentials or user interaction.

Usage:
    python tests/e2e_call_endpoint.py

Requirements:
    - PRODUCTION_URL: Bot URL (default: https://dcmaidbot.theedgestory.org)
    - NUDGE_SECRET: Authentication token
    - TEST_USER_ID: User ID for testing (default: 122657093)
"""

import asyncio
import os
import sys
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

# Test configuration
PRODUCTION_URL = os.getenv("PRODUCTION_URL", "https://dcmaidbot.theedgestory.org")
NUDGE_SECRET = os.getenv("NUDGE_SECRET")
TEST_USER_ID = int(os.getenv("TEST_USER_ID", "122657093"))

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


async def call_bot(command: str = None, message: str = None) -> dict:
    """Call the /call endpoint.

    Args:
        command: Optional command (e.g., "/start")
        message: Optional natural language message

    Returns:
        dict: Response JSON from /call endpoint
    """
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {NUDGE_SECRET}",
            "Content-Type": "application/json",
        }

        payload = {"user_id": TEST_USER_ID}
        if command:
            payload["command"] = command
        if message:
            payload["message"] = message

        response = await client.post(
            f"{PRODUCTION_URL}/call",
            json=payload,
            headers=headers,
            timeout=30.0,
        )

        return response.json(), response.status_code


async def test_start_command():
    """Test /start command."""
    try:
        data, status = await call_bot(command="/start")

        if status != 200:
            log_test("US-001: /start command", "FAIL", f"HTTP {status}: {data}")
            return False

        if not data.get("success"):
            log_test("US-001: /start command", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if "Welcome" in response or "Lilit" in response:
            log_test(
                "US-001: /start command",
                "PASS",
                f"Response: {response[:100]}...",
            )
            return True
        else:
            log_test(
                "US-001: /start command",
                "FAIL",
                "Response missing welcome message",
            )
            return False

    except Exception as e:
        log_test("US-001: /start command", "FAIL", f"Exception: {e}")
        return False


async def test_help_command():
    """Test /help command."""
    try:
        data, status = await call_bot(command="/help")

        if status != 200:
            log_test("US-002: /help command", "FAIL", f"HTTP {status}")
            return False

        if not data.get("success"):
            log_test("US-002: /help command", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if "Command List" in response or "help" in response.lower():
            log_test("US-002: /help command", "PASS", "Help text returned")
            return True
        else:
            log_test("US-002: /help command", "FAIL", "Invalid help response")
            return False

    except Exception as e:
        log_test("US-002: /help command", "FAIL", f"Exception: {e}")
        return False


async def test_status_command():
    """Test /status command."""
    try:
        data, status = await call_bot(command="/status")

        if status != 200:
            log_test("US-003: /status command", "FAIL", f"HTTP {status}")
            return False

        if not data.get("success"):
            log_test("US-003: /status command", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if "Status" in response or "Version" in response:
            log_test("US-003: /status command", "PASS", "Status returned")
            return True
        else:
            log_test("US-003: /status command", "FAIL", "Invalid status response")
            return False

    except Exception as e:
        log_test("US-003: /status command", "FAIL", f"Exception: {e}")
        return False


async def test_joke_command():
    """Test /joke command (LLM integration)."""
    try:
        data, status = await call_bot(command="/joke")

        if status != 200:
            log_test("US-004: /joke command", "FAIL", f"HTTP {status}")
            return False

        if not data.get("success"):
            log_test("US-004: /joke command", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if len(response) > 10:  # Joke should have some content
            log_test(
                "US-004: /joke command",
                "PASS",
                "Joke generated (LLM working)",
            )
            return True
        else:
            log_test("US-004: /joke command", "FAIL", "No joke returned")
            return False

    except Exception as e:
        log_test("US-004: /joke command", "FAIL", f"Exception: {e}")
        return False


async def test_love_command():
    """Test /love command."""
    try:
        data, status = await call_bot(command="/love")

        if status != 200:
            log_test("US-005: /love command", "FAIL", f"HTTP {status}")
            return False

        if not data.get("success"):
            log_test("US-005: /love command", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if "LOVE" in response or "love" in response.lower():
            log_test("US-005: /love command", "PASS", "Love message sent")
            return True
        else:
            log_test("US-005: /love command", "FAIL", "Invalid love response")
            return False

    except Exception as e:
        log_test("US-005: /love command", "FAIL", f"Exception: {e}")
        return False


async def test_waifu_personality():
    """Test waifu personality with natural message (LLM)."""
    try:
        data, status = await call_bot(message="Hello! How are you today?")

        if status != 200:
            log_test("US-006: Waifu personality", "FAIL", f"HTTP {status}")
            return False

        if not data.get("success"):
            log_test("US-006: Waifu personality", "FAIL", f"API error: {data}")
            return False

        response = data.get("response", "")
        if len(response) > 10:  # Should have a response
            log_test(
                "US-006: Waifu personality",
                "PASS",
                f"LLM response: {response[:100]}...",
            )
            return True
        else:
            log_test("US-006: Waifu personality", "FAIL", "No LLM response")
            return False

    except Exception as e:
        log_test("US-006: Waifu personality", "FAIL", f"Exception: {e}")
        return False


async def test_authentication():
    """Test /call authentication."""
    try:
        async with httpx.AsyncClient() as client:
            # Test without auth header
            response = await client.post(
                f"{PRODUCTION_URL}/call",
                json={"user_id": TEST_USER_ID, "command": "/start"},
                timeout=10.0,
            )

            if response.status_code == 401:
                log_test(
                    "Authentication",
                    "PASS",
                    "Correctly rejects unauthenticated requests",
                )
                return True
            else:
                log_test(
                    "Authentication",
                    "FAIL",
                    f"Expected 401, got {response.status_code}",
                )
                return False

    except Exception as e:
        log_test("Authentication", "FAIL", f"Exception: {e}")
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
    """Run all E2E tests via /call endpoint."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}DCMaidBot /call Endpoint E2E Tests{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

    # Check configuration
    if not NUDGE_SECRET:
        print(f"{Colors.RED}ERROR: NUDGE_SECRET not configured{Colors.RESET}")
        print("Set in .env file or environment variables")
        sys.exit(1)

    print(f"Production URL: {PRODUCTION_URL}")
    print(f"Test User ID:   {TEST_USER_ID}")
    print(f"Secret:         {'✅ Provided' if NUDGE_SECRET else '❌ Missing'}\n")

    print(f"{Colors.BOLD}Running Tests:{Colors.RESET}\n")

    # Run tests
    await test_authentication()
    await test_start_command()
    await test_help_command()
    await test_status_command()
    await test_love_command()
    await test_joke_command()
    await test_waifu_personality()

    # Print summary and exit
    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
