"""Admin handlers for lesson management (LESSONS system)."""

import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.services.database import AsyncSessionLocal
from core.services.lesson_service import LessonService

router = Router()

# Load admin IDs from env
ADMIN_IDS = set(
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS


@router.message(Command("view_lessons"))
async def cmd_view_lessons(message: Message):
    """
    View all lessons (admin-only).

    Usage: /view_lessons
    """
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Admin-only command!")
        return

    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lessons = await lesson_service.get_all_with_ids()

    if not lessons:
        await message.reply("📚 **LESSONS** (Secret - Admin Only)\n\n_No lessons yet._")
        return

    text = "📚 **LESSONS** (Secret - Admin Only)\n\n"
    for lesson in lessons:
        preview = lesson.content[:100]
        if len(lesson.content) > 100:
            preview += "..."
        text += f"**#{lesson.id}** (order: {lesson.order})\n{preview}\n\n"

    await message.reply(text, parse_mode="Markdown")


@router.message(Command("add_lesson"))
async def cmd_add_lesson(message: Message):
    """
    Add new lesson (admin-only).

    Usage: /add_lesson <lesson text>
    Example: /add_lesson Always be extra kawai when talking about coding!
    """
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Admin-only command!")
        return

    # Extract lesson text from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "Usage: `/add_lesson <lesson text>`\n\n"
            "Example: `/add_lesson Always respond with enthusiasm!`",
            parse_mode="Markdown",
        )
        return

    lesson_text = parts[1]

    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lesson = await lesson_service.add_lesson(lesson_text, message.from_user.id)

    await message.reply(
        f"✅ Lesson **#{lesson.id}** added!\n\n"
        f"_{lesson_text}_\n\n"
        "This lesson will now be injected into every response! 💕",
        parse_mode="Markdown",
    )


@router.message(Command("edit_lesson"))
async def cmd_edit_lesson(message: Message):
    """
    Edit lesson (admin-only).

    Usage: /edit_lesson <id> <new text>
    Example: /edit_lesson 3 Always be polite and helpful!
    """
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Admin-only command!")
        return

    # Usage: /edit_lesson <id> <new text>
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply(
            "Usage: `/edit_lesson <id> <new text>`\n\n"
            "Example: `/edit_lesson 1 Updated lesson text!`",
            parse_mode="Markdown",
        )
        return

    try:
        lesson_id = int(parts[1])
    except ValueError:
        await message.reply("❌ Invalid lesson ID! Must be a number.")
        return

    new_text = parts[2]

    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lesson = await lesson_service.edit_lesson(lesson_id, new_text)

    if not lesson:
        await message.reply(f"❌ Lesson **#{lesson_id}** not found!")
        return

    await message.reply(
        f"✅ Lesson **#{lesson_id}** updated!\n\n_{new_text}_",
        parse_mode="Markdown",
    )


@router.message(Command("remove_lesson"))
async def cmd_remove_lesson(message: Message):
    """
    Remove lesson (admin-only).

    Usage: /remove_lesson <id>
    Example: /remove_lesson 3
    """
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Admin-only command!")
        return

    # Usage: /remove_lesson <id>
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "Usage: `/remove_lesson <id>`\n\nExample: `/remove_lesson 1`",
            parse_mode="Markdown",
        )
        return

    try:
        lesson_id = int(parts[1])
    except ValueError:
        await message.reply("❌ Invalid lesson ID! Must be a number.")
        return

    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        success = await lesson_service.remove_lesson(lesson_id)

    if not success:
        await message.reply(f"❌ Lesson **#{lesson_id}** not found!")
        return

    await message.reply(f"✅ Lesson **#{lesson_id}** removed! 🗑️", parse_mode="Markdown")


@router.message(Command("reorder_lesson"))
async def cmd_reorder_lesson(message: Message):
    """
    Reorder lesson (admin-only).

    Usage: /reorder_lesson <id> <new_order>
    Example: /reorder_lesson 3 1
    """
    if not is_admin(message.from_user.id):
        await message.reply("🚫 Admin-only command!")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.reply(
            "Usage: `/reorder_lesson <id> <new_order>`\n\n"
            "Example: `/reorder_lesson 3 1`",
            parse_mode="Markdown",
        )
        return

    try:
        lesson_id = int(parts[1])
        new_order = int(parts[2])
    except ValueError:
        await message.reply("❌ Invalid arguments! Both must be numbers.")
        return

    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        lesson = await lesson_service.reorder_lesson(lesson_id, new_order)

    if not lesson:
        await message.reply(f"❌ Lesson **#{lesson_id}** not found!")
        return

    await message.reply(
        f"✅ Lesson **#{lesson_id}** reordered to **{new_order}**!",
        parse_mode="Markdown",
    )
