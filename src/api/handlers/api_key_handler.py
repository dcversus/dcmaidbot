"""
API Key Handler for dcmaidbot

Provides endpoints for generating and managing API keys through bot commands.
"""

import logging
from typing import Any, Dict, Optional

from core.services.api_key_service import api_key_service

logger = logging.getLogger(__name__)


async def generate_api_key_command(
    user_id: int, description: str = "", expires_in_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a new API key for the user.

    Args:
        user_id: Telegram user ID
        description: Optional description for the key
        expires_in_days: Custom expiration period

    Returns:
        Dict: Response with API key or error
    """
    try:
        # Validate user is admin (placeholder check)
        if not await is_admin_user(user_id):
            return {
                "success": False,
                "error": "Unauthorized: Admin access required",
                "message": "Only administrators can generate API keys",
            }

        # Generate API key
        key_result = api_key_service.generate_api_key(
            user_id=user_id,
            description=description or f"API key for user {user_id}",
            expires_in_days=expires_in_days,
        )

        logger.info(f"API key generated for admin user {user_id}")

        return {
            "success": True,
            "message": "🔑 API key generated successfully!",
            "api_key": key_result["api_key"],
            "key_id": key_result["key_id"],
            "description": key_result["description"],
            "permissions": key_result["permissions"],
            "expires_at": key_result["expires_at"],
            "usage_instructions": f"""
📚 **How to use your API key:**

**Method 1 - Header:**
```
curl -H "X-API-Key: {key_result["api_key"]}" https://your-domain.com/status
```

**Method 2 - Query Parameter:**
```
curl "https://your-domain.com/status?api_key={key_result["api_key"]}"
```

**Permissions:** {", ".join(key_result["permissions"])}
**Expires:** {key_result["expires_at"]}

⚠️ **Keep this key secure!** It provides admin access to your bot.
            """.strip(),
            "security_warning": "Save this key securely. It won't be shown again!",
        }

    except Exception as e:
        logger.error(f"Failed to generate API key for user {user_id}: {e}")
        return {
            "success": False,
            "error": "Failed to generate API key",
            "message": f"Sorry, I couldn't generate an API key right now: {str(e)}",
        }


async def list_api_keys_command(user_id: int) -> Dict[str, Any]:
    """
    List all API keys for the user.

    Args:
        user_id: Telegram user ID

    Returns:
        Dict: Response with API keys list or error
    """
    try:
        # Validate user is admin
        if not await is_admin_user(user_id):
            return {
                "success": False,
                "error": "Unauthorized: Admin access required",
                "message": "Only administrators can view API keys",
            }

        # Get user's API keys
        user_keys = api_key_service.list_user_keys(user_id)

        if not user_keys:
            return {
                "success": True,
                "message": "🔑 You don't have any API keys yet.",
                "keys": [],
                "instructions": "Use /generate_api_key to create a new key.",
            }

        # Format keys for display
        formatted_keys = []
        for key in user_keys:
            formatted_keys.append(
                {
                    "key_id": key["key_id"],
                    "description": key["description"],
                    "permissions": key["permissions"],
                    "created_at": key["created_at"],
                    "expires_at": key["expires_at"],
                    "last_used_at": key["last_used_at"],
                    "usage_count": key["usage_count"],
                    "status": "✅ Active" if key["is_active"] else "❌ Inactive",
                }
            )

        return {
            "success": True,
            "message": f"🔑 You have {len(user_keys)} API key(s):",
            "keys": formatted_keys,
            "stats": api_key_service.get_key_stats(user_id),
        }

    except Exception as e:
        logger.error(f"Failed to list API keys for user {user_id}: {e}")
        return {
            "success": False,
            "error": "Failed to list API keys",
            "message": f"Sorry, I couldn't retrieve your API keys: {str(e)}",
        }


async def revoke_api_key_command(user_id: int, key_id: str) -> Dict[str, Any]:
    """
    Revoke an API key.

    Args:
        user_id: Telegram user ID
        key_id: Key identifier to revoke

    Returns:
        Dict: Response with revocation result or error
    """
    try:
        # Validate user is admin
        if not await is_admin_user(user_id):
            return {
                "success": False,
                "error": "Unauthorized: Admin access required",
                "message": "Only administrators can revoke API keys",
            }

        # Revoke the key
        revoked = api_key_service.revoke_api_key(key_id, user_id)

        if revoked:
            return {
                "success": True,
                "message": f"🔑 API key {key_id[:16]}... has been revoked successfully.",
                "confirmation": "The key can no longer be used to access admin endpoints.",
            }
        else:
            return {
                "success": False,
                "error": "Key not found",
                "message": f"Could not find API key {key_id[:16]}... or you don't have permission to revoke it.",
            }

    except Exception as e:
        logger.error(f"Failed to revoke API key {key_id} for user {user_id}: {e}")
        return {
            "success": False,
            "error": "Failed to revoke API key",
            "message": f"Sorry, I couldn't revoke the API key: {str(e)}",
        }


async def api_key_stats_command(user_id: int) -> Dict[str, Any]:
    """
    Show API key usage statistics.

    Args:
        user_id: Telegram user ID

    Returns:
        Dict: Response with usage statistics or error
    """
    try:
        # Validate user is admin
        if not await is_admin_user(user_id):
            return {
                "success": False,
                "error": "Unauthorized: Admin access required",
                "message": "Only administrators can view API key statistics",
            }

        # Get statistics
        stats = api_key_service.get_key_stats(user_id)

        if not stats:
            return {
                "success": True,
                "message": "📊 No API key usage data available.",
                "stats": {},
            }

        return {
            "success": True,
            "message": "📊 Your API key statistics:",
            "stats": stats,
            "details": f"""
📈 **Usage Summary:**
• Total Keys: {stats.get("total_keys", 0)}
• Active Keys: {stats.get("active_keys", 0)}
• Expired Keys: {stats.get("expired_keys", 0)}
• Total Usage: {stats.get("total_usage", 0)} requests
• Last Used: {stats.get("last_used", "Never")}

💡 **Tip:** Use /list_api_keys to see detailed information about each key.
            """.strip(),
        }

    except Exception as e:
        logger.error(f"Failed to get API key stats for user {user_id}: {e}")
        return {
            "success": False,
            "error": "Failed to get statistics",
            "message": f"Sorry, I couldn't retrieve API key statistics: {str(e)}",
        }


async def is_admin_user(user_id: int) -> bool:
    """
    Check if user has admin privileges.

    Args:
        user_id: Telegram user ID

    Returns:
        bool: True if user is admin
    """
    try:
        # TODO: Implement proper admin check
        # This should check against your admin configuration
        # For now, you might check against environment variables or database

        # Example: Check environment variable
        import os

        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        return str(user_id) in admin_ids

    except Exception as e:
        logger.error(f"Admin check error for user {user_id}: {e}")
        return False


# Bot command handlers integration
async def handle_generate_api_key(user_id: int, args: list = None) -> str:
    """Handle /generate_api_key command."""
    description = ""
    expires_in_days = None

    # Parse arguments
    if args:
        if len(args) >= 1:
            description = " ".join(args)
        # TODO: Parse expiration days from args if needed

    result = await generate_api_key_command(user_id, description, expires_in_days)

    if result["success"]:
        return f"""
{result["message"]}

🔑 **Your API Key:**
```
{result["api_key"]}
```

📝 **Description:** {result["description"]}
🔐 **Permissions:** {", ".join(result["permissions"])}
⏰ **Expires:** {result["expires_at"]}

{result["usage_instructions"]}

⚠️ {result["security_warning"]}
        """.strip()
    else:
        return f"❌ {result['message']}"


async def handle_list_api_keys(user_id: int) -> str:
    """Handle /list_api_keys command."""
    result = await list_api_keys_command(user_id)

    if result["success"] and result["keys"]:
        response = f"{result['message']}\n\n"

        for i, key in enumerate(result["keys"], 1):
            response += f"""
🔑 **Key {i}:** `{key["key_id"]}...`
📝 **Description:** {key["description"]}
🔐 **Permissions:** {", ".join(key["permissions"])}
📊 **Usage:** {key["usage_count"]} times
📅 **Created:** {key["created_at"][:10]}
⏰ **Expires:** {key["expires_at"][:10]}
📈 **Status:** {key["status"]}
""".strip()

        # Add stats
        stats = result.get("stats", {})
        response += f"""

📊 **Summary:** {stats.get("total_keys", 0)} total, {stats.get("active_keys", 0)} active, {stats.get("total_usage", 0)} total uses
        """

        return response
    else:
        return result["message"]


async def handle_revoke_api_key(user_id: int, args: list = None) -> str:
    """Handle /revoke_api_key command."""
    if not args or not args[0]:
        return "❌ Please provide a key ID. Usage: `/revoke_api_key <key_id>`"

    key_id = args[0]
    result = await revoke_api_key_command(user_id, key_id)

    return result["message"]


async def handle_api_key_stats(user_id: int) -> str:
    """Handle /api_key_stats command."""
    result = await api_key_stats_command(user_id)

    if result["success"]:
        response = f"{result['message']}\n\n"
        if result.get("details"):
            response += result["details"]
        return response
    else:
        return f"❌ {result['message']}"
