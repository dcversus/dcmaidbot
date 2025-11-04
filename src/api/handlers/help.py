"""Role-aware /help command handler using unified command registry.

Shows different help content for admins vs non-admins using the
CommandRegistry to ensure consistency across all entry points.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.core.commands.registry import CommandRegistry

router = Router()


@router.message(Command("help"))
async def cmd_help_role_aware(message: Message) -> None:
    """Show available commands with role-aware content.

    Uses the unified CommandRegistry to ensure consistency across
    Telegram, HTTP /call, and Discord entry points.
    """
    if not message.from_user:
        return

    # Get help text from unified command registry
    help_text = CommandRegistry.get_help_text(message.from_user.id)

    await message.reply(help_text, parse_mode="Markdown")
