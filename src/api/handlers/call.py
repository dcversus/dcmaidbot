"""
/call endpoint - Direct bot logic testing without Telegram

Allows E2E testing of bot functionality by calling handlers directly
without going through Telegram's webhook/polling system.

Authentication: Uses same NUDGE_SECRET as /nudge endpoint
"""

import json
import os
from typing import Optional

from aiohttp import web

from core.services.auth_service import AuthService
from core.services.database import AsyncSessionLocal
from core.services.lesson_service import LessonService
from core.services.llm_service import llm_service
from core.services.memory_service import MemoryService
from core.services.message_service import MessageService


async def call_handler(request: web.Request) -> web.Response:
    """POST /call - Invoke bot logic directly without Telegram.

    Request body:
    {
        "user_id": 123456789,
        "message": "Hello bot!",
        "command": "/start",  # Optional, if it's a command
        "is_admin": true  # Optional, default: check ADMIN_IDS env
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
    is_admin = data.get("is_admin")

    if not user_id:
        return web.json_response(
            {"error": "Missing required field: user_id"},
            status=400,
        )

    # If is_admin not provided, infer using AuthService
    if is_admin is None:
        auth_service = AuthService()
        is_admin = auth_service.is_admin(user_id)

    # Process command or message
    response_text: Optional[str] = None
    command_handled: Optional[str] = None

    try:
        # Handle commands
        if command:
            response_text = await handle_command(command, user_id, is_admin)
            command_handled = command
        # Handle natural language messages
        elif message:
            response_text = await handle_message(message, user_id, is_admin)
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


async def handle_command(command: str, user_id: int, is_admin: bool) -> str:
    """Handle bot commands directly.

    Args:
        command: Command string (e.g., "/start", "/help")
        user_id: Telegram user ID
        is_admin: Whether user is admin (affects /help content)

    Returns:
        str: Bot's response text
    """
    # /start command
    if command == "/start":
        return (
            "💕 <b>Nya~ Welcome, dear friend!</b>\n\n"
            "I'm <b>Lilith</b>, your kawaii maid bot! I'm here to chat, "
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

    # /help command - role-aware
    elif command == "/help":
        if is_admin:
            return (
                "<b>📚 DCMaid Help - Admin Mode</b>\n\n"
                "<b>🔧 Admin Commands (Lessons):</b>\n"
                "/view_lessons - View all lesson instructions\n"
                "/add_lesson &lt;text&gt; - Add a new lesson\n"
                "/edit_lesson &lt;id&gt; &lt;text&gt; - Edit existing lesson\n"
                "/remove_lesson &lt;id&gt; - Delete a lesson\n"
                "/reorder_lesson &lt;id&gt; &lt;order&gt; - Change lesson order\n\n"
                "<b>🤖 Admin Commands (System):</b>\n"
                "/status - Bot status, version, and uptime\n\n"
                "<b>💬 Public Commands:</b>\n"
                "/start - Welcome message\n"
                "/help - This help message\n"
                "/joke - Tell a random joke\n"
                "/love - Show love for admins\n\n"
                "<b>✨ Agentic Tools (Available to You!):</b>\n"
                "I can help you manage lessons through natural conversation! "
                "Just ask me to:\n"
                '• "Save this as a lesson: ..."\n'
                '• "Show me all my lessons"\n'
                '• "Edit lesson #3 to say..."\n'
                '• "Delete lesson #5"\n\n'
                "I also have access to:\n"
                "• <b>Memory management</b> - Create, search, and retrieve memories\n"
                "• <b>Web search</b> - Search the web via DuckDuckGo\n"
                "• <b>Lesson tools</b> - Full lesson CRUD through conversation\n\n"
                "<i>Nya~ I'm here to help you manage everything! 💕</i>"
            )
        else:
            return (
                "<b>📚 DCMaid Help</b>\n\n"
                "<b>💬 Available Commands:</b>\n"
                "/start - Welcome message and introduction\n"
                "/help - This help message\n"
                "/joke - Tell you a random joke\n"
                "/status - Check bot status\n\n"
                "<b>✨ About Me:</b>\n"
                "I'm your kawaii AI maid! 💕 I can chat with you, "
                "remember our conversations, and help you with various tasks!\n\n"
                "Just talk to me naturally and I'll do my best to help!\n\n"
                "I can:\n"
                "• Have natural conversations\n"
                "• Remember important things you tell me\n"
                "• Search the web for information\n"
                "• Tell jokes and spread positivity\n\n"
                "<i>Nya~ Let's chat! 🎀</i>"
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


async def handle_message(message: str, user_id: int, is_admin: bool) -> str:
    """Handle natural language messages using LLM with memories and history.

    Args:
        message: User's message text
        user_id: Telegram user ID
        is_admin: Whether user is admin (affects tool availability)

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

        # Import tools for agentic behavior
        from core.tools.lesson_tools import LESSON_TOOLS
        from core.tools.memory_tools import MEMORY_TOOLS
        from core.tools.tool_executor import ToolExecutor
        from core.tools.web_search_tools import WEB_SEARCH_TOOLS

        # Build tools list (admins get lesson tools, non-admins don't)
        all_tools = MEMORY_TOOLS + WEB_SEARCH_TOOLS
        if is_admin:
            all_tools = all_tools + LESSON_TOOLS

        # Use LLM with waifu personality + context + tools
        user_info = {"id": user_id, "username": "test_user", "telegram_id": user_id}
        chat_info = {"id": user_id, "type": "private", "chat_id": user_id}
        llm_response = await llm_service.get_response(
            message,
            user_info,
            chat_info,
            lessons,
            memories=memories,
            message_history=message_history,
            tools=all_tools,
        )

        # Check if LLM wants to use tools
        if hasattr(llm_response, "tool_calls") and llm_response.tool_calls:
            # Execute each tool call
            async with AsyncSessionLocal() as tool_session:
                tool_executor = ToolExecutor(tool_session)
                tool_results = []

                for tool_call in llm_response.tool_calls:
                    # Parse tool arguments
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    # Execute tool
                    result = await tool_executor.execute(
                        tool_name=tool_call.function.name,
                        arguments=arguments,
                        user_id=user_id,
                    )

                    tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "result": result,
                        }
                    )

            # Get final response from LLM after tool execution
            response = await llm_service.get_response_after_tools(
                user_message=message,
                user_info=user_info,
                chat_info=chat_info,
                lessons=lessons,
                memories=memories,
                message_history=message_history,
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in llm_response.tool_calls
                ],
                tool_results=tool_results,
            )
        else:
            # No tools needed, just use the text response
            response = llm_response

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
