"""
E2E Testing with Pyrogram User Client

Uses Pyrogram (MTProto) to simulate a real user sending messages to the bot.
This allows testing actual bot responses without "chat not found" errors.

Setup:
1. Get API credentials from https://my.telegram.org/apps
2. Set environment variables:
   - TELEGRAM_API_ID: Your API ID
   - TELEGRAM_API_HASH: Your API hash
   - TELEGRAM_USER_PHONE: Your phone number (for first login)
3. First run will prompt for login code sent via SMS
4. Session saved to tests/userbot.session (keep secure!)

Usage:
    export TELEGRAM_API_ID=12345
    export TELEGRAM_API_HASH="your_hash_here"
    export TELEGRAM_USER_PHONE="+1234567890"
    python tests/e2e_with_userbot.py
"""

import asyncio
import os
import sys
from datetime import datetime

from pyrogram import Client

# Test configuration
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_USER_PHONE = os.getenv("TELEGRAM_USER_PHONE", "")
PRODUCTION_BOT_USERNAME = os.getenv("BOT_USERNAME", "dcmaidbot")
TEST_BOT_USERNAME = os.getenv("TEST_BOT_USERNAME", "dcnotabot")

# Use test bot for testing
BOT_USERNAME = TEST_BOT_USERNAME

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


async def test_bot_start_command(app: Client):
    """Test /start command and verify bot responds."""
    try:
        # Send /start command
        sent_msg = await app.send_message(BOT_USERNAME, "/start")
        print("   Sent /start, waiting for response...")

        # Wait for bot response
        await asyncio.sleep(3)

        # Get message history to check for response
        async for message in app.get_chat_history(BOT_USERNAME, limit=5):
            if message.date > sent_msg.date and message.from_user.is_bot:
                response_text = message.text[:100] if message.text else "(no text)"
                log_test(
                    "US-001: /start command",
                    "PASS",
                    f"Bot responded: {response_text}",
                )
                return True

        log_test("US-001: /start command", "FAIL", "No response from bot")
        return False

    except Exception as e:
        log_test("US-001: /start command", "FAIL", f"Exception: {e}")
        return False


async def test_bot_help_command(app: Client):
    """Test /help command."""
    try:
        sent_msg = await app.send_message(BOT_USERNAME, "/help")
        print("   Sent /help, waiting for response...")
        await asyncio.sleep(3)

        async for message in app.get_chat_history(BOT_USERNAME, limit=5):
            if message.date > sent_msg.date and message.from_user.is_bot:
                log_test(
                    "US-002: /help command",
                    "PASS",
                    "Bot responded with help text",
                )
                return True

        log_test("US-002: /help command", "FAIL", "No response from bot")
        return False

    except Exception as e:
        log_test("US-002: /help command", "FAIL", f"Exception: {e}")
        return False


async def test_bot_status_command(app: Client):
    """Test /status command."""
    try:
        sent_msg = await app.send_message(BOT_USERNAME, "/status")
        print("   Sent /status, waiting for response...")
        await asyncio.sleep(3)

        async for message in app.get_chat_history(BOT_USERNAME, limit=5):
            if message.date > sent_msg.date and message.from_user.is_bot:
                log_test(
                    "US-003: /status command",
                    "PASS",
                    "Bot responded with status info",
                )
                return True

        log_test("US-003: /status command", "FAIL", "No response from bot")
        return False

    except Exception as e:
        log_test("US-003: /status command", "FAIL", f"Exception: {e}")
        return False


async def test_bot_waifu_personality(app: Client):
    """Test waifu personality with natural message."""
    try:
        sent_msg = await app.send_message(BOT_USERNAME, "Hello! How are you today? 💕")
        print("   Sent natural message, waiting for waifu response...")
        await asyncio.sleep(5)  # LLM responses take longer

        async for message in app.get_chat_history(BOT_USERNAME, limit=5):
            if message.date > sent_msg.date and message.from_user.is_bot:
                response_text = message.text[:100] if message.text else "(no text)"
                log_test(
                    "US-006: Waifu personality",
                    "PASS",
                    f"Bot responded: {response_text}",
                )
                return True

        log_test("US-006: Waifu personality", "FAIL", "No response from bot")
        return False

    except Exception as e:
        log_test("US-006: Waifu personality", "FAIL", f"Exception: {e}")
        return False


async def test_bot_joke_command(app: Client):
    """Test /joke command with LLM."""
    try:
        sent_msg = await app.send_message(BOT_USERNAME, "/joke")
        print("   Sent /joke, waiting for LLM-generated joke...")
        await asyncio.sleep(5)  # LLM responses take longer

        async for message in app.get_chat_history(BOT_USERNAME, limit=5):
            if message.date > sent_msg.date and message.from_user.is_bot:
                log_test(
                    "US-004: /joke command",
                    "PASS",
                    "Bot told a joke",
                )
                return True

        log_test("US-004: /joke command", "FAIL", "No response from bot")
        return False

    except Exception as e:
        log_test("US-004: /joke command", "FAIL", f"Exception: {e}")
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
    """Run all E2E tests with Pyrogram user client."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    title = "DCMaidBot E2E Testing with User Client"
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

    # Check credentials
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error_msg = "ERROR: Missing TELEGRAM_API_ID or TELEGRAM_API_HASH"
        print(f"{Colors.RED}{error_msg}{Colors.RESET}")
        print("Get credentials from https://my.telegram.org/apps")
        sys.exit(1)

    print(f"Bot Username:   @{BOT_USERNAME}")
    print(f"API ID:         {TELEGRAM_API_ID}")
    print("Session File:   tests/userbot.session\n")

    # Create Pyrogram client
    session_file = "tests/userbot"  # Will create userbot.session
    app = Client(
        session_file,
        api_id=int(TELEGRAM_API_ID),
        api_hash=TELEGRAM_API_HASH,
        phone_number=TELEGRAM_USER_PHONE,
    )

    async with app:
        print(f"{Colors.GREEN}✅ Logged in to Telegram as user{Colors.RESET}\n")
        print(f"{Colors.BOLD}Running User Story Tests:{Colors.RESET}\n")

        # Run tests
        await test_bot_start_command(app)
        await test_bot_help_command(app)
        await test_bot_status_command(app)
        await test_bot_joke_command(app)
        await test_bot_waifu_personality(app)

    # Print summary and exit
    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
