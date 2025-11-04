"""
External Tools Handler
======================

Handler for external tool commands like web search.
Implements PRP-009 External Tools functionality.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.api.handlers.admin import is_admin
from src.core.services.tool_service import ToolService

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.startswith("/web_search"))
async def handle_web_search(message: Message, state: FSMContext):
    """Handle web search command."""
    # Extract search query
    query = message.text.replace("/web_search", "").strip()

    if not query:
        await message.reply(
            "🔍 **Web Search**\n\n"
            "Usage: `/web_search <query>`\n\n"
            "Example: `/web_search latest AI developments`"
        )
        return

    try:
        # Check if user is admin (web search requires admin access)
        user_id = message.from_user.id
        is_admin_user = await is_admin(user_id)

        if not is_admin_user:
            await message.reply(
                "⚠️ **Access Denied**\n\nWeb search is only available to administrators."
            )
            return

        # Initialize tool service and perform search
        tool_service = ToolService()

        await message.reply(f"🔍 **Searching for:** `{query}`...")

        # Perform web search
        results = await tool_service.web_search(query, user_id)

        if results and results.get("success"):
            # Format search results
            response_text = f"🔍 **Search Results for:** `{query}`\n\n"

            for i, result in enumerate(results.get("results", [])[:5], 1):
                title = result.get("title", "No title")
                url = result.get("url", "")
                snippet = result.get("snippet", "No description")

                response_text += f"**{i}. {title}**\n"
                response_text += f"🔗 {url}\n"
                response_text += f"📝 {snippet}\n\n"

            if not results.get("results"):
                response_text += "❌ No results found.\n"

            response_text += f"\n⚡ Powered by: {results.get('engine', 'DuckDuckGo')}"

            # Split if message is too long
            if len(response_text) > 4000:
                parts = [
                    response_text[i : i + 4000]
                    for i in range(0, len(response_text), 4000)
                ]
                for part in parts:
                    await message.reply(part)
            else:
                await message.reply(response_text)
        else:
            error_msg = (
                results.get("error", "Unknown error occurred")
                if results
                else "Search service unavailable"
            )
            await message.reply(
                f"❌ **Search Failed**\n\nError: {error_msg}\n\nPlease try again later."
            )

    except Exception as e:
        logger.error(f"Error in web search command: {e}")
        await message.reply(
            "❌ **Search Error**\n\n"
            "An unexpected error occurred while performing the search. "
            "Please try again later."
        )


@router.message(F.text.startswith("/curl"))
async def handle_curl_request(message: Message, state: FSMContext):
    """Handle cURL-like request command."""
    # Extract URL
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.reply(
            "🌐 **cURL Request**\n\n"
            "Usage: `/curl <url>`\n\n"
            "Example: `/curl https://api.github.com`"
        )
        return

    url = command_parts[1]
    user_id = message.from_user.id

    try:
        # Check if user is admin
        is_admin_user = await is_admin(user_id)

        if not is_admin_user:
            await message.reply(
                "⚠️ **Access Denied**\n\n"
                "cURL requests are only available to administrators."
            )
            return

        # Initialize tool service and make request
        tool_service = ToolService()

        await message.reply(f"🌐 **Requesting:** `{url}`...")

        # Make HTTP request
        result = await tool_service.curl_request(url, user_id)

        if result and result.get("success"):
            # Format response
            status_code = result.get("status_code", 0)
            content = result.get("content", "")
            content_type = result.get("content_type", "unknown")

            response_text = "🌐 **cURL Response**\n\n"
            response_text += f"📊 **Status:** {status_code}\n"
            response_text += f"📄 **Content-Type:** {content_type}\n\n"

            # Truncate content if too long
            if len(content) > 3500:
                content = content[:3500] + "... (truncated)"

            response_text += f"📝 **Content:**\n```\n{content}\n```"

            await message.reply(response_text)
        else:
            error_msg = (
                result.get("error", "Unknown error occurred")
                if result
                else "Request failed"
            )
            await message.reply(
                f"❌ **Request Failed**\n\n"
                f"Error: {error_msg}\n\n"
                "Please check the URL and try again."
            )

    except Exception as e:
        logger.error(f"Error in curl command: {e}")
        await message.reply(
            "❌ **Request Error**\n\n"
            "An unexpected error occurred while making the request. "
            "Please try again later."
        )
