"""
/call endpoint - Direct bot logic testing without Telegram

Allows E2E testing of bot functionality by calling handlers directly
without going through Telegram's webhook/polling system.

Authentication: Uses same NUDGE_SECRET as /nudge endpoint
"""

import os
from typing import Optional

from aiohttp import web

from database import AsyncSessionLocal
from services.llm_service import llm_service
from services.lesson_service import LessonService
from services.memory_service import MemoryService
from services.message_service import MessageService


async def call_handler(request: web.Request) -> web.Response:
    """POST /call - Invoke bot logic directly without Telegram.

    Request body:
    {
        "user_id": 123456789,
        "message": "Hello bot!",
        "command": "/start"  # Optional, if it's a command
    }

    Response:
    {
        "success": true,
        "response": "Bot's response text",
        "command_handled": "/start"  # If a command was processed
    }

    Authentication:
    - Requires Authorization: Bearer <NUDGE_SECRET>
    - Same secret as /nudge endpoint
    """
    # Check authentication
    nudge_secret = os.getenv("NUDGE_SECRET")
    if not nudge_secret:
        return web.json_response(
            {"error": "NUDGE_SECRET not configured on server"},
            status=500,
        )

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return web.json_response(
            {"error": "Missing or invalid Authorization header"},
            status=401,
        )

    token = auth_header.replace("Bearer ", "")
    if token != nudge_secret:
        return web.json_response(
            {"error": "Invalid authentication token"},
            status=401,
        )

    # Parse request
    try:
        data = await request.json()
    except Exception as e:
        return web.json_response(
            {"error": f"Invalid JSON: {e}"},
            status=400,
        )

    user_id = data.get("user_id")
    message = data.get("message", "")
    command = data.get("command")

    if not user_id:
        return web.json_response(
            {"error": "Missing required field: user_id"},
            status=400,
        )

    # Process command or message
    response_text: Optional[str] = None
    command_handled: Optional[str] = None

    try:
        # Handle commands
        if command:
            response_text = await handle_command(command, user_id)
            command_handled = command
        # Handle natural language messages
        elif message:
            response_text = await handle_message(message, user_id)
        else:
            return web.json_response(
                {"error": "Either 'message' or 'command' is required"},
                status=400,
            )

        return web.json_response(
            {
                "success": True,
                "response": response_text,
                "command_handled": command_handled,
            },
            status=200,
        )

    except Exception as e:
        return web.json_response(
            {"error": f"Error processing request: {e}"},
            status=500,
        )


async def handle_command(command: str, user_id: int) -> str:
    """Handle bot commands directly.

    Args:
        command: Command string (e.g., "/start", "/help")
        user_id: Telegram user ID

    Returns:
        str: Bot's response text
    """
    # /start command
    if command == "/start":
        return (
            "💕 <b>Nya~ Welcome, dear friend!</b>\n\n"
            "I'm <b>Lilit</b>, your kawaii maid bot! I'm here to chat, "
            "tell jokes, and spread love! 🎀\n\n"
            "<b>Available commands:</b>\n"
            "• /help - Show all commands\n"
            "• /status - Check bot status\n"
            "• /joke - Tell you a joke\n"
            "• /love - Share some love 💕\n\n"
            "Or just chat with me naturally! I love to talk! 🌸\n\n"
            "<i>Visit my home:</i> "
            '<a href="https://dcmaidbot.theedgestory.org">dcmaidbot.theedgestory.org</a>'
        )

    # /help command
    elif command == "/help":
        return (
            "<b>💕 Lilit's Command List</b>\n\n"
            "<b>General Commands:</b>\n"
            "• /start - Welcome message\n"
            "• /help - This help message\n"
            "• /status - Bot status and uptime\n"
            "• /joke - Random joke from my collection\n"
            "• /love - Spread some love 💕\n\n"
            "<b>Admin Commands:</b>\n"
            "• /view_lessons - View all lessons (admin only)\n\n"
            "<b>Natural Chat:</b>\n"
            "Just send me any message and I'll respond with my "
            "waifu personality! 🎀\n\n"
            "<i>Website:</i> "
            '<a href="https://dcmaidbot.theedgestory.org">dcmaidbot.theedgestory.org</a>'
        )

    # /status command
    elif command == "/status":
        # Get uptime from environment or default
        uptime = os.getenv("UPTIME", "Unknown")
        version = os.getenv("VERSION", "0.3.0")
        commit = os.getenv("GIT_COMMIT", "unknown")[:7]

        return (
            "<b>🤖 Bot Status</b>\n\n"
            f"<b>Version:</b> {version}\n"
            f"<b>Commit:</b> <code>{commit}</code>\n"
            f"<b>Uptime:</b> {uptime}\n"
            f"<b>Status:</b> ✅ Online and healthy\n\n"
            "<i>Visit:</i> "
            '<a href="https://dcmaidbot.theedgestory.org">dcmaidbot.theedgestory.org</a>'
        )

    # /joke command
    elif command == "/joke":
        # Use LLM to generate a joke
        try:
            prompt = (
                "Tell a short, funny joke (2-3 lines). "
                "Use spoiler tags for the punchline."
            )
            user_info = {"id": user_id, "username": "test_user"}
            chat_info = {"id": user_id, "type": "private"}
            joke = await llm_service.get_response(prompt, user_info, chat_info)
            return f"😄 <b>Here's a joke for you!</b>\n\n{joke}"
        except Exception as e:
            return f"😅 Oops! I couldn't think of a joke right now. Error: {e}"

    # /love command
    elif command == "/love":
        return (
            "💕💕💕 <b>LOVE LOVE LOVE!</b> 💕💕💕\n\n"
            "Sending you all my love and affection! "
            "You're amazing and I appreciate you! 🎀✨\n\n"
            "<i>Remember: You're loved! 💖</i>"
        )

    # /view_lessons command (admin only)
    elif command == "/view_lessons":
        # Check if user is admin (simplified check)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

        if user_id not in admin_ids:
            return "❌ This command is only available to admins."

        # Note: Full implementation requires database session
        # For now, return a simplified message
        return (
            "<b>📚 Lessons System</b>\n\n"
            "Lessons are admin-only secret instructions injected "
            "into every LLM call.\n\n"
            "To manage lessons, use the Telegram bot directly:\n"
            "• /view_lessons - View all lessons\n"
            "• /add_lesson - Add a new lesson\n"
            "• /edit_lesson - Edit existing lesson\n"
            "• /remove_lesson - Remove a lesson\n\n"
            "<i>Note: /call endpoint has limited database access. "
            "Use Telegram for full functionality.</i>"
        )

    else:
        return f"❌ Unknown command: {command}"


async def handle_message(message: str, user_id: int) -> str:
    """Handle natural language messages using LLM with memories and history.

    Args:
        message: User's message text
        user_id: Telegram user ID

    Returns:
        str: Bot's response text
    """
    try:
        # Fetch lessons, memories, and message history from database
        async with AsyncSessionLocal() as session:
            lesson_service = LessonService(session)
            lessons = await lesson_service.get_all_lessons()

            # Fetch memories for this user
            memory_service = MemoryService(session)
            memories = await memory_service.search_memories(
                user_id=user_id,
                query=message,
                limit=10,
            )

            # Fetch recent message history for this user
            message_service = MessageService(session)
            message_history = await message_service.get_recent_messages(
                user_id=user_id,
                chat_id=user_id,  # In /call, chat_id = user_id for simplicity
                limit=20,
            )

            # Store incoming user message to database
            await message_service.store_message(
                user_id=user_id,
                chat_id=user_id,
                message_text=message,
                is_bot=False,
            )

        # Use LLM with waifu personality + context
        user_info = {"id": user_id, "username": "test_user", "telegram_id": user_id}
        chat_info = {"id": user_id, "type": "private", "chat_id": user_id}
        response = await llm_service.get_response(
            message,
            user_info,
            chat_info,
            lessons,
            memories=memories,
            message_history=message_history,
        )

        # Store bot's response to database
        async with AsyncSessionLocal() as session:
            message_service = MessageService(session)
            await message_service.store_message(
                user_id=user_id,
                chat_id=user_id,
                message_text=response,
                is_bot=True,
            )

        return response
    except Exception as e:
        return f"😅 Oops! I had trouble processing that. Error: {e}"
