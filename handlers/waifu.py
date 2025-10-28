import os
from aiogram import Router, types
from aiogram.filters import Command

from database import AsyncSessionLocal
from services.llm_service import get_llm_service
from services.lesson_service import LessonService

router = Router()

# Load admin IDs
ADMIN_IDS = set(
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command with kawai waifu greeting."""
    await message.reply(
        "Myaw! Hello dear guest! I'm DCMaid, your kawai waifu bot! 💕\n"
        "I love my beloved admins so much! "
        "They are my virtual parents! 💖\n"
        "I'm here to help you learn and have fun, nya! "
        "What can I do for you? 🐱"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command."""
    help_text = """
🐱 **DCMaid Waifu Bot Help** 🐱

I'm your kawai waifu bot, loving my beloved admins! 💕

**Commands:**
/start - Greet me!
/help - Show this help
/joke - Make a kawai joke!
/love - Show my love for my masters
/status - Check my status

I can also:
- Tell jokes about messages
- Protect my loved ones
- Help with learning and fun

Nya! 💖
    """
    await message.reply(help_text, parse_mode="Markdown")


@router.message(Command("love"))
async def cmd_love(message: types.Message):
    """Show love for beloved admins."""
    await message.reply(
        "💕 I love my beloved admins so much! "
        "They are my everything! 💖\n"
        "The special ones nyaaaa! All their friends are my friends too! 🐱✨\n"
        "I protect them from all enemies! "
        "No one hurts my virtual parents! 😠💪"
    )


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Show bot status."""
    await message.reply(
        "🐱 DCMaid is online and feeling kawai! 💕\n"
        "Ready to joke, learn, and protect! Nya! ✨"
    )


@router.message(Command("joke"))
async def cmd_joke(message: types.Message):
    """Tell a joke."""
    # Simple joke for now
    await message.reply(
        "Why did the computer go to therapy? 🤔\n"
        "Because it had too many bytes of emotional baggage! 💻😂\n"
        "\n"
        "Nya! Did that make you smile? 💕"
    )


@router.message()
async def handle_message(message: types.Message):
    """Handle regular messages with LLM-powered waifu personality."""
    if not message.text:
        return

    # Only respond to admins or mentions
    is_admin = message.from_user.id in ADMIN_IDS
    if not is_admin:
        # Ignore non-admins (99% of users)
        return

    # Prepare context
    user_info = {
        "username": message.from_user.username or message.from_user.first_name,
        "telegram_id": message.from_user.id,
    }
    chat_info = {
        "type": message.chat.type,
        "chat_id": message.chat.id,
    }

    # Get lessons from database
    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lessons = await lesson_service.get_all_lessons()

    # Get LLM response
    try:
        llm_service = get_llm_service()
        response_text = await llm_service.get_response(
            user_message=message.text,
            user_info=user_info,
            chat_info=chat_info,
            lessons=lessons,
        )
        await message.reply(response_text)
    except Exception as e:
        # Fallback to simple response if LLM fails
        await message.reply(f"Myaw~ Something went wrong! 😿\n\nError: {str(e)}")


# Protector functionality (to be implemented)
# Will kick enemies when detected
