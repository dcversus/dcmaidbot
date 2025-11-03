"""
Friends Handler
===============

Handler for friend system commands and social features.
Implements PRP-019 Friends System functionality.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.friend_service import get_friend_service

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.startswith("/add_friend"))
async def handle_add_friend(message: Message, state: FSMContext):
    """Handle add friend command."""
    try:
        # Parse friend ID from command
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply(
                "👥 **Add Friend**\n\n"
                "Usage: `/add_friend <user_id>`\n\n"
                "Example: `/add_friend 123456789`\n\n"
                "Note: You need the Telegram user ID of the person you want to add."
            )
            return

        try:
            friend_id = int(command_parts[1])
        except ValueError:
            await message.reply("⚠️ **Invalid User ID. Please use a numeric user ID.**")
            return

        user_id = message.from_user.id

        # Get friend service
        friend_service = get_friend_service()

        # Send friend request
        result = await friend_service.add_friend(user_id, friend_id)

        if result['success']:
            response = "✅ **Friend Request Sent!**\n\n"
            response += f"👤 **To:** User ID `{friend_id}`\n"
            response += f"🆔 **Request ID:** `{result['request_id']}`\n\n"
            response += "The other user will need to accept your friend request."
        else:
            response = "❌ **Request Failed**\n\n"
            response += f"Error: {result.get('error', 'Unknown error')}"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error adding friend: {e}")
        await message.reply(
            "❌ **Add Failed**\n\n"
            "Failed to send friend request. Please try again later."
        )


@router.message(F.text.startswith("/friends"))
async def handle_friends_list(message: Message, state: FSMContext):
    """Handle friends list command."""
    try:
        user_id = message.from_user.id

        # Get friend service
        friend_service = get_friend_service()

        # Get friends list
        friends = await friend_service.list_friends(user_id)

        if not friends:
            await message.reply(
                "👥 **Friends List**\n\n"
                "You don't have any friends yet.\n\n"
                "Add friends with `/add_friend <user_id>`"
            )
            return

        # Format friends list
        response = f"👥 **Your Friends** ({len(friends)} total)\n\n"

        for i, friend in enumerate(friends, 1):
            friend_id = friend['friend_id']
            friendship_date = friend['friendship_date'].split('T')[0]  # Just show date
            response += f"{i}. 👤 User ID: `{friend_id}`\n"
            response += f"   📅 Friends since: {friendship_date}\n\n"

        # Add additional info
        response += "💡 **Tip:** Use `/pending_requests` to see friend requests awaiting your response."

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error listing friends: {e}")
        await message.reply(
            "❌ **List Failed**\n\n"
            "Failed to retrieve friends list. Please try again later."
        )


@router.message(F.text.startswith("/pending_requests"))
async def handle_pending_requests(message: Message, state: FSMContext):
    """Handle pending friend requests command."""
    try:
        user_id = message.from_user.id

        # Get friend service
        friend_service = get_friend_service()

        # Get pending requests
        requests = await friend_service.get_pending_requests(user_id)

        if not requests:
            await message.reply(
                "📥 **Pending Requests**\n\n"
                "You have no pending friend requests."
            )
            return

        # Format pending requests
        response = f"📥 **Pending Friend Requests** ({len(requests)} total)\n\n"

        for i, req in enumerate(requests, 1):
            from_user = req['from_user']
            created_date = req['created_at'].split('T')[0]
            response += f"{i}. 👤 From: User ID `{from_user}`\n"
            response += f"   📅 Date: {created_date}\n"
            response += f"   🆔 Request ID: `{req['request_id']}`\n\n"

        response += "💡 **Tip:** To accept a request, use: `/accept_request <request_id>`"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        await message.reply(
            "❌ **Requests Failed**\n\n"
            "Failed to retrieve pending requests. Please try again later."
        )


@router.message(F.text.startswith("/accept_request"))
async def handle_accept_request(message: Message, state: FSMContext):
    """Handle accept friend request command."""
    try:
        # Parse request ID from command
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply(
                "✅ **Accept Request**\n\n"
                "Usage: `/accept_request <request_id>`\n\n"
                "Example: `/accept_request 12345-67890`\n\n"
                "Get request IDs from `/pending_requests`"
            )
            return

        request_id = command_parts[1]
        user_id = message.from_user.id

        # Get friend service
        friend_service = get_friend_service()

        # Accept request
        result = await friend_service.accept_friend_request(user_id, request_id)

        if result['success']:
            response = "✅ **Friend Request Accepted!**\n\n"
            response += f"👤 **New Friend:** User ID `{result['friend_id']}`\n"
            response += f"🆔 **Friendship ID:** `{result.get('friendship_id', 'N/A')}`\n\n"
            response += "You are now friends! View your full friends list with `/friends`"
        else:
            response = "❌ **Accept Failed**\n\n"
            response += f"Error: {result.get('error', 'Unknown error')}"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error accepting friend request: {e}")
        await message.reply(
            "❌ **Accept Failed**\n\n"
            "Failed to accept friend request. Please try again later."
        )


@router.message(F.text.startswith("/remove_friend"))
async def handle_remove_friend(message: Message, state: FSMContext):
    """Handle remove friend command."""
    try:
        # Parse friend ID from command
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply(
                "👋 **Remove Friend**\n\n"
                "Usage: `/remove_friend <user_id>`\n\n"
                "Example: `/remove_friend 123456789`\n\n"
                "⚠️ This action cannot be undone!"
            )
            return

        try:
            friend_id = int(command_parts[1])
        except ValueError:
            await message.reply("⚠️ **Invalid User ID. Please use a numeric user ID.**")
            return

        user_id = message.from_user.id

        # Get friend service
        friend_service = get_friend_service()

        # Remove friend
        result = await friend_service.remove_friend(user_id, friend_id)

        if result['success']:
            response = "👋 **Friend Removed**\n\n"
            response += f"👤 **Removed:** User ID `{friend_id}`\n\n"
            response += "The friendship has been ended. You can add them as a friend again if you wish."
        else:
            response = "❌ **Remove Failed**\n\n"
            response += f"Error: {result.get('error', 'Unknown error')}"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error removing friend: {e}")
        await message.reply(
            "❌ **Remove Failed**\n\n"
            "Failed to remove friend. Please try again later."
        )
