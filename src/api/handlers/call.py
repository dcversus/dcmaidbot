"""
/call endpoint - Direct bot logic testing without Telegram

Allows E2E testing of bot functionality by calling handlers directly
without going through Telegram's webhook/polling system.

Authentication: Supports multiple methods:
- API Key (X-API-Key header or api_key query param)
- Admin ID (X-Admin-ID header or admin_id query param)
- NUDGE_SECRET (Authorization: Bearer <NUDGE_SECRET> - for backward compatibility)
"""

import json
import os
from typing import Optional

from aiohttp import web

from src.core.middleware.auth import get_unified_auth
from src.core.services.database import AsyncSessionLocal
from src.core.services.emotional_analysis_service import EmotionalAnalysisService
from src.core.services.lesson_service import LessonService
from src.core.services.llm_service import get_llm_service
from src.core.services.memory_service import MemoryService
from src.core.services.message_service import MessageService
from src.core.services.mood_service import MoodService


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

    Authentication (supports multiple methods):
    1. API Key: X-API-Key header or api_key query parameter (user-specific)
    2. Admin ID: X-Admin-ID header or admin_id query parameter (admin-specific)
    3. NUDGE_SECRET: Authorization: Bearer <NUDGE_SECRET> (master key)
    """
    # Check unified authentication
    unified_auth = get_unified_auth()
    nudge_secret = os.getenv("NUDGE_SECRET")

    # Extract headers and query params
    headers = dict(request.headers)
    query_params = dict(request.rel_url.query)

    # Authenticate request
    is_auth, auth_user_id, auth_method = await unified_auth.authenticate_request(
        headers=headers,
        query_params=query_params,
        allow_nudge_secret=True,
        nudge_secret=nudge_secret,
    )

    if not is_auth:
        return web.json_response(
            {
                "error": "Invalid or missing authentication",
                "message": "Provide API key, admin ID, or NUDGE_SECRET",
            },
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

    # If is_admin not provided, infer using authentication
    if is_admin is None:
        # If authenticated with admin_id or API key, check if that user is admin
        if auth_user_id and auth_method in ["admin_id", "api_key"]:
            is_admin = (
                auth_user_id == user_id
            )  # The authenticated user must match the request user
        else:
            # NUDGE_SECRET (master key) auth - check if user_id is in ADMIN_IDS
            from src.core.services.auth_service import AuthService

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

    # /help command - use unified command registry
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
            llm_service_instance = get_llm_service()
            joke = await llm_service_instance.get_response(prompt, user_info, chat_info)
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

    # /mood command
    elif command == "/mood":
        try:
            async with AsyncSessionLocal() as session:
                mood_service = MoodService(session)
                mood_summary = await mood_service.get_mood_summary()

                # Get relationship info for this user
                relationship = await mood_service.get_user_relationship(user_id)

                # Admin protection check
                admin_ids = [
                    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
                ]
                is_admin_user = user_id in admin_ids

                return (
                    f"<b>💭 My Current Mood</b>\n\n"
                    f"{mood_summary['mood_emoji']} <b>{mood_summary['primary_mood']}</b> "
                    f"(Intensity: {mood_summary['mood_intensity']})\n\n"
                    f"<b>VAD Scores:</b>\n"
                    f"• Valence (Positivity): {mood_summary['vad_scores']['valence']}\n"
                    f"• Arousal (Energy): {mood_summary['vad_scores']['arousal']}\n"
                    f"• Dominance (Control): {mood_summary['vad_scores']['dominance']}\n\n"
                    f"<b>Stats:</b>\n"
                    f"• Energy: {mood_summary['energy_level']} ({mood_summary['energy_value']})\n"
                    f"• Confidence: {mood_summary['confidence']} ({mood_summary['confidence_value']})\n"
                    f"• Social: {mood_summary['social_engagement']}\n"
                    f"• Interactions: {mood_summary['interaction_count']}\n\n"
                    f"<b>Reason:</b> {mood_summary['reason']}\n\n"
                    f"<b>Our Relationship:</b> {relationship.bot_feeling} "
                    f"(Trust: {relationship.trust_score:.1%}, "
                    f"Friendship: {relationship.friendship_level:.1%})\n\n"
                    f"<i>Last updated: {mood_summary['last_updated']}</i>"
                )
        except Exception as e:
            return f"😅 Oops! I couldn't check my mood right now. Error: {e}"

    # /memories command
    elif command == "/memories":
        # Check if user is admin
        admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        if user_id not in admin_ids:
            return (
                "🔒 <b>Access Denied</b>\n\n"
                "Sorry, only administrators can view and manage memories. "
                "This is to protect everyone's privacy!\n\n"
                "<i>If you're an admin, make sure your Telegram ID is in ADMIN_IDS</i>"
            )

        try:
            async with AsyncSessionLocal() as session:
                memory_service = MemoryService(session)

                # Parse command arguments
                parts = command.split()
                action = parts[1] if len(parts) > 1 else "list"

                if action == "search" and len(parts) > 2:
                    # Search memories
                    query = " ".join(parts[2:])
                    memories = await memory_service.search_memories(
                        user_id=None,  # Admin can search all
                        query=query,
                        limit=10,
                    )

                    if not memories:
                        return f"🔍 <b>No memories found</b>\n\nNo memories match: <code>{query}</code>"

                    result = f"🔍 <b>Memories matching: {query}</b>\n\n"
                    for i, memory in enumerate(memories[:5], 1):
                        # Get categories from the memory object
                        categories = getattr(memory, "categories", [])
                        category_names = (
                            [cat.name for cat in categories] if categories else []
                        )

                        result += (
                            f"{i}. <b>ID:</b> {memory.id}\n"
                            f"   <b>Content:</b> {memory.simple_content or memory.full_content[:100]}...\n"
                            f"   <b>Categories:</b> {', '.join(category_names)}\n"
                            f"   <b>Importance:</b> {memory.importance}/100\n"
                            f"   <b>Emotion:</b> {memory.emotion_label or 'neutral'}\n"
                            f"   <b>Created:</b> {memory.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                        )
                    return result

                else:
                    # List recent memories (search with empty query to get all)
                    memories = await memory_service.search_memories(
                        user_id=None,  # Admin can see all
                        query="",
                        limit=10,
                    )

                    if not memories:
                        return "📝 <b>No memories stored yet</b>\n\nI haven't stored any important memories yet!"

                    result = (
                        "📝 <b>Recent Memories</b> (showing up to 10 most recent)\n\n"
                    )
                    for i, memory in enumerate(memories[:10], 1):
                        # Get categories from the memory object
                        categories = getattr(memory, "categories", [])
                        category_names = (
                            [cat.name for cat in categories] if categories else []
                        )

                        result += (
                            f"{i}. <b>ID:</b> {memory.id}\n"
                            f"   <b>Content:</b> {memory.simple_content or memory.full_content[:100]}...\n"
                            f"   <b>Categories:</b> {', '.join(category_names)}\n"
                            f"   <b>Importance:</b> {memory.importance}/100\n"
                            f"   <b>Emotion:</b> {memory.emotion_label or 'neutral'}\n"
                            f"   <b>By User:</b> {memory.created_by}\n\n"
                        )

                    result += (
                        "<b>Memory Commands:</b>\n"
                        "• /memories - List recent memories\n"
                        "• /memories search &lt;query&gt; - Search memories\n"
                        '• Natural: "Show me memories about..."\n\n'
                        f"<i>Showing {len(memories)} recent memories</i>"
                    )
                    return result

        except Exception as e:
            return f"😅 Oops! I couldn't access memories right now. Error: {e}"

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
        # Keep session open for potential tool execution
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
            from src.core.tools.api_key_tools import API_KEY_TOOLS
            from src.core.tools.lesson_tools import LESSON_TOOLS
            from src.core.tools.memory_tools import MEMORY_TOOLS
            from src.core.tools.openai_search_tools import OPENAI_SEARCH_TOOLS
            from src.core.tools.tool_executor import ToolExecutor
            from src.core.tools.web_search_tools import WEB_SEARCH_TOOLS

            # Choose search provider based on environment
            search_provider = os.getenv("SEARCH_PROVIDER", "openai").lower()
            if search_provider == "openai":
                search_tools = OPENAI_SEARCH_TOOLS
            else:
                search_tools = WEB_SEARCH_TOOLS

            # Build tools list (admins get lesson and API key tools, non-admins don't)
            all_tools = MEMORY_TOOLS + search_tools
            if is_admin:
                all_tools = all_tools + LESSON_TOOLS + API_KEY_TOOLS

            # Use LLM with waifu personality + context + tools
            user_info = {"id": user_id, "username": "test_user", "telegram_id": user_id}
            chat_info = {"id": user_id, "type": "private", "chat_id": user_id}
            llm_service_instance = get_llm_service()
            llm_response = await llm_service_instance.get_response(
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
                # Execute tools using the same session
                tool_executor = ToolExecutor(session)
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
                response = await llm_service_instance.get_response_after_tools(
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

            # Auto-create memories for important information
            emotional_service = EmotionalAnalysisService()
            memory_service = MemoryService(session)

            # Analyze the conversation for memory creation opportunities
            analysis = await emotional_service.analyze_message_emotionally(
                message=message, user_id=user_id, is_admin=is_admin
            )

            # Create memory if analysis indicates it should be stored
            if analysis.get("should_create_memory", False):
                # Create memory with emotional context
                memory_data = {
                    "full_content": message,
                    "simple_content": analysis.get("memory_summary", ""),
                    "categories": analysis.get("categories", []),
                    "importance": analysis.get("importance", 100),
                    "created_by": user_id,
                    # Add VAD emotion values
                    "emotion_valence": analysis.get("vad", {}).get("valence", 0.0),
                    "emotion_arousal": analysis.get("vad", {}).get("arousal", 0.0),
                    "emotion_dominance": analysis.get("vad", {}).get("dominance", 0.0),
                    "emotion_label": analysis.get("emotion_label", "neutral"),
                }

                try:
                    created_memory = await memory_service.create_memory(
                        full_content=memory_data["full_content"],
                        simple_content=memory_data.get("simple_content"),
                        categories=memory_data.get("categories", []),
                        created_by=memory_data["created_by"],
                        importance=memory_data["importance"],
                        emotion_valence=memory_data["emotion_valence"],
                        emotion_arousal=memory_data["emotion_arousal"],
                        emotion_dominance=memory_data["emotion_dominance"],
                        emotion_label=memory_data["emotion_label"],
                    )

                    # If memory was created successfully, prepend feedback to response
                    if created_memory and analysis.get("memory_feedback", ""):
                        response = f"{analysis['memory_feedback']}\n\n{response}"
                except Exception as e:
                    # Log error but don't fail the response
                    print(f"Error creating auto-memory: {e}")

            # Update mood and relationship based on interaction
            mood_service = MoodService(session)

            # Analyze message sentiment for mood update
            message_lower = message.lower()
            sentiment_analysis = analysis if "analysis" in locals() else {}

            # Determine sentiment-based mood changes
            valence_change = 0.0
            arousal_change = 0.0

            # Positive indicators
            positive_words = [
                "love",
                "amazing",
                "great",
                "awesome",
                "thank",
                "thanks",
                "wonderful",
                "fantastic",
                "perfect",
                "best",
                "good",
                "happy",
                "excited",
            ]
            # Negative indicators
            negative_words = [
                "hate",
                "terrible",
                "awful",
                "bad",
                "worst",
                "stupid",
                "useless",
                "angry",
                "sad",
                "frustrated",
                "annoyed",
                "disappointed",
            ]

            # Count positive/negative words
            pos_count = sum(1 for word in positive_words if word in message_lower)
            neg_count = sum(1 for word in negative_words if word in message_lower)

            # Calculate mood changes (smaller for non-admins to protect from mood swings)
            if user_id not in [
                int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
            ]:
                # Non-admin users have smaller impact on mood
                valence_change = (pos_count * 0.02) - (neg_count * 0.03)
                arousal_change = 0.01 if pos_count > 0 or neg_count > 0 else 0.0
            else:
                # Admins can affect mood more (but still limited)
                valence_change = (pos_count * 0.05) - (neg_count * 0.08)
                arousal_change = 0.02 if pos_count > 0 or neg_count > 0 else 0.0

            # Update mood if there's a change
            if abs(valence_change) > 0.01 or abs(arousal_change) > 0.01:
                mood_reason = (
                    f"User message: {message[:50]}..." if len(message) > 50 else message
                )
                await mood_service.update_mood(
                    valence_change=valence_change,
                    arousal_change=arousal_change,
                    reason=mood_reason,
                    user_id=user_id,
                )

            # Update relationship
            is_positive_interaction = pos_count > neg_count
            trust_change = 0.01 if is_positive_interaction else -0.005
            friendship_change = 0.02 if is_positive_interaction else -0.01
            familiarity_change = 0.01  # Always increase familiarity with interaction

            await mood_service.update_relationship(
                user_id=user_id,
                trust_change=trust_change,
                friendship_change=friendship_change,
                familiarity_change=familiarity_change,
                is_positive=is_positive_interaction,
                interaction_type="chat",
            )

        return response
    except Exception as e:
        return f"😅 Oops! I had trouble processing that. Error: {e}"
