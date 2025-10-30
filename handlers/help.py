"""Role-aware /help command handler.

Shows different help content for admins vs non-admins.
Admins see all commands including admin-only tools,
while non-admins see only public commands.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.auth_service import AuthService

router = Router()
auth_service = AuthService()


@router.message(Command("help"))
async def cmd_help_role_aware(message: Message) -> None:
    """Show available commands with role-aware content.

    Admins see all commands including lesson management and admin tools.
    Non-admins see only public commands.
    """
    if not message.from_user:
        return

    is_admin = auth_service.is_admin(message.from_user.id)

    if is_admin:
        help_text = """<b>📚 DCMaid Help - Admin Mode</b>

<b>🔧 Admin Commands (Lessons):</b>
/view_lessons - View all lesson instructions
/add_lesson &lt;text&gt; - Add a new lesson
/edit_lesson &lt;id&gt; &lt;text&gt; - Edit existing lesson
/remove_lesson &lt;id&gt; - Delete a lesson
/reorder_lesson &lt;id&gt; &lt;order&gt; - Change lesson order

<b>🤖 Admin Commands (System):</b>
/status - Bot status, version, and uptime

<b>💬 Public Commands:</b>
/start - Welcome message
/help - This help message
/joke - Tell a random joke
/love - Show love for admins

<b>✨ Agentic Tools (Available to You!):</b>
I can help you manage lessons through natural conversation! Just ask me to:
• "Save this as a lesson: ..."
• "Show me all my lessons"
• "Edit lesson #3 to say..."
• "Delete lesson #5"

I also have access to:
• <b>Memory management</b> - Create, search, and retrieve memories
• <b>Web search</b> - Search the web via DuckDuckGo
• <b>Lesson tools</b> - Full lesson CRUD through conversation

<i>Nya~ I'm here to help you manage everything! 💕</i>"""
    else:
        help_text = """<b>📚 DCMaid Help</b>

<b>💬 Available Commands:</b>
/start - Welcome message and introduction
/help - This help message
/joke - Tell you a random joke
/status - Check bot status

<b>✨ About Me:</b>
I'm your kawaii AI maid! 💕 I can chat with you, remember our conversations,
and help you with various tasks!

Just talk to me naturally and I'll do my best to help!

I can:
• Have natural conversations
• Remember important things you tell me
• Search the web for information
• Tell jokes and spread positivity

<i>Nya~ Let's chat! 🎀</i>"""

    await message.reply(help_text, parse_mode="HTML")
