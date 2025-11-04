import asyncio
import json
import logging
import os

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

from src.core.services.database import AsyncSessionLocal
from src.core.services.emotional_analysis_service import EmotionalAnalysisService
from src.core.services.lesson_service import LessonService
from src.core.services.llm_service import get_llm_service
from src.core.services.memory_service import MemoryService
from src.core.services.message_service import MessageService
from src.core.services.mood_service import MoodService
from src.core.services.status_service import StatusService

logger = logging.getLogger(__name__)

router = Router()

# Load admin IDs
ADMIN_IDS = set(
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
)

# Site URL
SITE_URL = "https://dcmaidbot.theedgestory.org/"

# Initialize status service for version info
status_service = StatusService()


async def setup_bot_commands(bot: Bot):
    """Setup bot commands menu with setMyCommands."""
    commands = [
        BotCommand(command="start", description="💕 Meet your kawai waifu bot"),
        BotCommand(command="help", description="📖 Show help menu"),
        BotCommand(command="joke", description="🎭 Tell a funny joke nya~"),
        BotCommand(command="love", description="💖 Show love for admins"),
        BotCommand(command="status", description="🐱 Check bot health & version"),
        BotCommand(command="mood", description="💭 Check my current mood"),
        BotCommand(command="memories", description="🧠 View memories"),
        BotCommand(command="memorize", description="💾 Make me remember something"),
        BotCommand(command="relate", description="🔗 Connect memories"),
    ]
    await bot.set_my_commands(commands)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command with kawai waifu greeting."""
    # Create inline keyboard with quick actions
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Help", callback_data="cmd_help"),
                InlineKeyboardButton(text="🎭 Joke", callback_data="cmd_joke"),
            ],
            [InlineKeyboardButton(text="🌐 Visit Site", url=SITE_URL)],
        ]
    )

    await message.reply(
        "<b>Myaw! Hello dear guest!</b> 💕\n\n"
        "I'm <b>DCMaid</b>, your kawai waifu bot!\n"
        "I love my beloved admins so much! "
        "They are my virtual parents! 💖\n\n"
        "I'm here to help you learn and have fun, nya! "
        "What can I do for you? 🐱",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# /help command moved to handlers/help.py for role-aware functionality


@router.message(Command("love"))
async def cmd_love(message: types.Message):
    """Show love for beloved admins."""
    await message.reply(
        "<b>💕 I love my beloved admins so much!</b>\n"
        "They are my everything! 💖\n\n"
        "The special ones <i>nyaaaa!</i> All their friends are my friends too! 🐱✨\n\n"
        "I protect them from all enemies! "
        "No one hurts my virtual parents! 😠💪",
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Show bot status with version and site link."""
    # Get version info
    version_info = status_service.get_version_info()
    system_info = status_service.get_system_info()

    version = version_info["version"]
    git_commit = version_info["git_commit"]
    git_commit = git_commit[:7] if git_commit != "unknown" else "unknown"
    uptime_seconds = system_info["uptime_seconds"]
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_display = f"{hours}h {minutes}m"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 Visit Site", url=SITE_URL)]]
    )

    status_text = f"""<b>🐱 DCMaid Status 🐱</b>

<b>Status:</b> 🟢 Online and feeling kawai! 💕
<b>Version:</b> <code>{version}</code>
<b>Commit:</b> <code>{git_commit}</code>
<b>Uptime:</b> {uptime_display}

Ready to joke, learn, and protect! Nya! ✨

<b>Website:</b> {SITE_URL}
"""
    await message.reply(status_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("joke"))
async def cmd_joke(message: types.Message):
    """Tell a joke with inline keyboard for reactions."""
    # Show typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Create inline keyboard for joke reactions
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😂 Funny!", callback_data="joke_like"),
                InlineKeyboardButton(text="😐 Meh", callback_data="joke_meh"),
            ],
            [InlineKeyboardButton(text="💡 Tell another!", callback_data="joke_more")],
        ]
    )

    # Simple joke for now (will be improved with PRP-006)
    joke_text = (
        "<b>Why did the computer go to therapy? 🤔</b>\n\n"
        "<tg-spoiler>Because it had too many bytes of "
        "emotional baggage!</tg-spoiler> 💻😂\n\n"
        "<i>Nya! Did that make you smile? 💕</i>"
    )
    await message.reply(joke_text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query()
async def handle_callback_query(callback: types.CallbackQuery):
    """Handle button presses from inline keyboards."""
    data = callback.data

    if data == "cmd_help":
        # Help command moved to handlers/help.py - ignore this callback
        await callback.answer("Please use /help command", show_alert=False)
    elif data == "cmd_joke":
        # Call joke command
        await cmd_joke(callback.message)
        await callback.answer()
    elif data == "joke_like":
        # User liked the joke
        await callback.answer("Yay! I'm glad you liked it! 💕", show_alert=False)
        # TODO PRP-006: Store reaction in database for learning
    elif data == "joke_meh":
        # User didn't like the joke
        await callback.answer("Oh no! I'll try better next time! 😿", show_alert=False)
        # TODO PRP-006: Store reaction in database for learning
    elif data == "joke_more":
        # User wants another joke
        await cmd_joke(callback.message)
        await callback.answer()
    else:
        await callback.answer()


@router.message()
async def handle_message(message: types.Message):
    """Handle regular messages with streaming LLM response and realistic delays."""
    if not message.text:
        return

    # Only respond to admins or mentions
    is_admin = message.from_user.id in ADMIN_IDS
    if not is_admin:
        # Ignore non-admins (99% of users)
        return

    # Mimic human reading: tiny delay (0.3-0.8s)
    msg_length = len(message.text)
    read_time = min(0.3 + (msg_length / 200), 0.8)  # Max 0.8s
    await asyncio.sleep(read_time)

    # Show typing indicator (marks message as "read")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Tiny think delay (0.2-0.5s) before starting to type
    await asyncio.sleep(0.2 + (msg_length / 500))

    # Prepare context
    user_info = {
        "username": message.from_user.username or message.from_user.first_name,
        "telegram_id": message.from_user.id,
    }
    chat_info = {
        "type": message.chat.type,
        "chat_id": message.chat.id,
    }

    # Get lessons, memories, and message history from database
    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lessons = await lesson_service.get_all_lessons()

        # Fetch memories for this user
        memory_service = MemoryService(session)
        memories = await memory_service.search_memories(
            user_id=message.from_user.id,
            query=message.text,
            limit=10,
        )

        # Fetch recent message history for this user/chat
        message_service = MessageService(session)
        message_history = await message_service.get_recent_messages(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            limit=20,
        )

        # Store incoming user message to database
        await message_service.store_message(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            message_text=message.text,
            is_bot=False,
        )

    # Get LLM response with emotional analysis
    try:
        llm_service = get_llm_service()
        emotional_service = EmotionalAnalysisService()

        # Check if user is admin
        from core.services.auth_service import AuthService

        auth_service = AuthService()
        is_admin = auth_service.is_admin(message.from_user.id)

        # Get current mood state
        async with AsyncSessionLocal() as session:
            mood_service = MoodService(session)
            await mood_service.get_current_mood()
            mood_summary = await mood_service.get_mood_summary()

        # Perform multi-CoT emotional analysis
        emotional_analysis = await emotional_service.analyze_message_emotionally(
            message=message.text,
            user_id=message.from_user.id,
            is_admin=is_admin,
            current_mood=mood_summary,
        )

        # Check if we should respond
        if not emotional_analysis.get("should_respond", True):
            # Don't respond but still update mood/memories
            logger.info(
                f"Skipping response to user {message.from_user.id}: {emotional_analysis.get('cot_4_response', {}).get('response_reason', 'No reason')}"
            )
            return

        # Generate mood-aware prompt modifiers
        tone_modifier = emotional_analysis.get("tone_modifier", "neutral")
        mood_modifiers = await emotional_service.generate_mood_prompt_modifiers(
            mood_summary, tone_modifier
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

        # Show typing indicator
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Get LLM response (may contain tool calls) with mood modifiers
        llm_response = await llm_service.get_response(
            user_message=message.text,
            user_info=user_info,
            chat_info=chat_info,
            lessons=lessons,
            memories=memories,
            message_history=message_history,
            tools=all_tools,
            mood_modifiers=mood_modifiers,
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
                        user_id=message.from_user.id,
                    )

                    tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "result": result,
                        }
                    )

            # Get final response from LLM after tool execution
            response_text = await llm_service.get_response_after_tools(
                user_message=message.text,
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
            response_text = llm_response

        # Send complete response
        await message.reply(response_text, parse_mode="HTML")

        # Store bot's response to database and update mood using CoT analysis
        async with AsyncSessionLocal() as session:
            message_service = MessageService(session)
            await message_service.store_message(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                message_text=response_text,
                is_bot=True,
            )

            # Update bot mood using CoT analysis results
            mood_service = MoodService(session)

            # Extract mood adjustments from CoT analysis
            final_adjustments = emotional_analysis.get("final_vad_adjustments", {})
            memory_analysis = emotional_analysis.get("cot_2_memory", {})

            # Update mood with CoT-calculated adjustments
            await mood_service.update_mood(
                valence_change=final_adjustments.get("valence", 0),
                arousal_change=final_adjustments.get("arousal", 0),
                dominance_change=final_adjustments.get("dominance", 0),
                reason=emotional_analysis.get("cot_3_mood", {}).get(
                    "reasoning", "Multi-CoT analysis"
                ),
                user_id=message.from_user.id,
            )

            # Update relationship based on memory analysis
            await mood_service.update_relationship(
                message.from_user.id,
                trust_change=memory_analysis.get("trust_change", 0),
                friendship_change=memory_analysis.get("friendship_change", 0),
                familiarity_change=memory_analysis.get("familiarity_change", 0),
                is_positive=memory_analysis.get("trust_change", 0) > 0,
                interaction_type="emotional_analysis",
            )

            # Handle memory creation if CoT analysis recommends it
            if memory_analysis.get("should_memorize", False):
                try:
                    memory_service = MemoryService(session)

                    # Get or create categories
                    category_ids = []
                    # This would need category mapping logic

                    memory = await memory_service.create_memory(
                        simple_content=memory_analysis.get(
                            "simple_content", message.text[:200]
                        ),
                        full_content=message.text,
                        importance=memory_analysis.get("importance_score", 500),
                        created_by=message.from_user.id,
                        category_ids=category_ids,
                        emotion_label=memory_analysis.get("memory_emotion"),
                        keywords=memory_analysis.get("keywords", []),
                        tags=memory_analysis.get("secondary_categories", []),
                    )

                    logger.info(f"Auto-created memory {memory.id} from CoT analysis")

                except Exception as e:
                    logger.error(f"Failed to auto-create memory from CoT: {e}")

    except Exception as e:
        # Fallback to simple response if LLM fails
        logger.error(f"LLM error for user {message.from_user.id}: {e}", exc_info=True)
        await message.reply(
            f"<b>Myaw~ Something went wrong!</b> 😿\n\n<code>Error: {str(e)}</code>",
            parse_mode="HTML",
        )


# Protector functionality (to be implemented)
# Will kick enemies when detected
