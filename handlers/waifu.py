from aiogram import Router, types
from aiogram.filters import Command

router = Router()


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
    """Handle regular messages with waifu personality."""
    text = message.text.lower() if message.text else ""

    # Check for admin mentions or special triggers
    if "master" in text or "admin" in text or "creator" in text:
        await message.reply(
            "💕 Oh! You mentioned my beloved creators! I love them so much! 💖"
        )
        return

    # Simple response for other messages
    responses = [
        "Nya! That's interesting! 💕",
        "Kawai! Tell me more! 🐱",
        "Myaw! I love chatting with you! 💖",
        "That's so cool! Nya! ✨",
    ]

    # For now, respond to all messages from admins
    import random

    await message.reply(random.choice(responses))


# Protector functionality (to be implemented)
# Will kick enemies when detected
