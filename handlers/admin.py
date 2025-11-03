"""
Admin Handler
=============

Handler for administrator commands and system status.
Implements PRP-008 Admin Commands functionality.
"""

import logging
import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()

# Get admin IDs from environment
ADMIN_IDS = [
    int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",")
    if id.strip()
]


async def is_admin(user_id: int) -> bool:
    """Check if user is an admin.

    Args:
        user_id: User ID to check

    Returns:
        True if user is admin
    """
    return user_id in ADMIN_IDS


@router.message(F.text.startswith("/admin_status"))
async def handle_admin_status(message: Message, state: FSMContext):
    """Handle admin status command."""
    user_id = message.from_user.id

    if not await is_admin(user_id):
        await message.reply(
            "⚠️ **Access Denied**\n\n"
            "This command is only available to administrators."
        )
        return

    try:
        # Collect status information
        from services.friend_service import get_friend_service
        from services.metrics_service import get_metrics_service
        from services.rag_service import get_rag_service
        from services.world_service import get_world_service

        # Get metrics
        metrics_service = await get_metrics_service()
        metrics = metrics_service.get_metrics_summary()

        # Get service health
        rag_service = await get_rag_service()
        rag_health = await rag_service.health_check()

        world_service = get_world_service()
        world_health = await world_service.health_check()

        friend_service = get_friend_service()
        friend_health = await friend_service.health_check()

        # Format status message
        status_text = "🔧 **System Status**\n\n"

        # Bot information
        status_text += "🤖 **Bot:** Online\n"
        status_text += "👤 **Requester:** Admin\n\n"

        # Metrics
        status_text += "📊 **Metrics:**\n"
        status_text += f"• Uptime: {metrics['uptime_seconds']:.0f}s\n"
        status_text += f"• Messages: {metrics['messages_total']}\n"
        status_text += f"• Commands: {metrics['commands_total']}\n"
        status_text += f"• Errors: {metrics['errors_total']}\n"
        status_text += f"• Active Users (1h): {metrics['active_users_1h']}\n\n"

        # Services
        status_text += "🛠️ **Services:**\n"
        status_text += f"• RAG Service: {rag_health['status']}\n"
        status_text += f"• World Service: {world_health['status']}\n"
        status_text += f"• Friend Service: {friend_health['status']}\n\n"

        # Service details
        status_text += "📋 **Service Details:**\n"

        if rag_health.get('collection_exists'):
            status_text += f"• RAG Documents: {rag_health.get('document_count', 0)}\n"

        status_text += f"• Generated Worlds: {world_health.get('worlds_count', 0)}\n"
        status_text += f"• Pending Friend Requests: {friend_health.get('pending_requests', 0)}\n"

        await message.reply(status_text)

    except Exception as e:
        logger.error(f"Error in admin status command: {e}")
        await message.reply(
            "❌ **Status Error**\n\n"
            "Failed to retrieve system status. Check logs for details."
        )


@router.message(F.text.startswith("/admin_info"))
async def handle_admin_info(message: Message, state: FSMContext):
    """Handle admin info command with system details."""
    user_id = message.from_user.id

    if not await is_admin(user_id):
        await message.reply(
            "⚠️ **Access Denied**\n\n"
            "This command is only available to administrators."
        )
        return

    try:
        # Get system information
        from datetime import datetime

        import psutil

        # System stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        info_text = "ℹ️ **System Information**\n\n"

        # System stats
        info_text += "🖥️ **System:**\n"
        info_text += f"• CPU Usage: {cpu_percent}%\n"
        info_text += f"• Memory Usage: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)\n"
        info_text += f"• Disk Usage: {disk.percent}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)\n\n"

        # Bot info
        info_text += "🤖 **Bot:**\n"
        info_text += f"• Admins: {len(ADMIN_IDS)} configured\n"
        info_text += f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        await message.reply(info_text)

    except Exception as e:
        logger.error(f"Error in admin info command: {e}")
        await message.reply(
            "❌ **Info Error**\n\n"
            "Failed to retrieve system information."
        )
