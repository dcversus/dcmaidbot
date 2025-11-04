"""
Nudge endpoint handler for agent-to-user communication.

Provides POST /nudge endpoint that:
1. Validates authentication (API key, admin ID, or NUDGE_SECRET)
2. Validates request payload
3. Sends message directly or via LLM pipeline to Telegram users
4. Returns response or error

Authentication (supports multiple methods):
1. API Key: X-API-Key header or api_key query parameter
2. Admin ID: X-Admin-ID header or admin_id query parameter
3. NUDGE_SECRET: Authorization: Bearer <NUDGE_SECRET> (legacy)
"""

import os

from aiohttp import web

from src.core.middleware.auth import get_unified_auth
from src.core.services.nudge_service import NudgeService

# Lazy-loaded service instance (created on first use)
_nudge_service = None


def get_nudge_service() -> NudgeService:
    """Get or create NudgeService instance (lazy loading)."""
    global _nudge_service
    if _nudge_service is None:
        _nudge_service = NudgeService()
    return _nudge_service


async def nudge_handler(request: web.Request) -> web.Response:
    """POST /nudge - Send messages to admins via Telegram.

    Authentication (supports multiple methods):
    1. API Key: X-API-Key header or api_key query parameter (user-specific)
    2. Admin ID: X-Admin-ID header or admin_id query parameter (admin-specific)
    3. NUDGE_SECRET: Authorization: Bearer <NUDGE_SECRET> (master key)

    Request Body (JSON):
        {
            "message": "Rich **markdown** [message](url)",  // Required: Markdown
            "type": "direct",                                // Required: "direct"|"llm"
            "user_id": 123456789                            // Optional: specific user
        }

    Returns:
        200: Success - message sent to user(s)
        400: Bad Request - invalid payload
        401: Unauthorized - missing or invalid auth
        500: Internal Server Error - failed to send message
    """
    # 1. Validate unified authentication
    unified_auth = get_unified_auth()
    nudge_secret = os.getenv("NUDGE_SECRET")

    # Extract headers and query params
    headers = dict(request.headers)
    query_params = dict(request.rel_url.query)

    # Authenticate request
    is_auth, user_id, auth_method = await unified_auth.authenticate_request(
        headers=headers,
        query_params=query_params,
        allow_nudge_secret=True,
        nudge_secret=nudge_secret,
    )

    if not is_auth:
        return web.json_response(
            {
                "status": "error",
                "error": "Invalid or missing authentication",
                "message": "Provide API key, admin ID, or NUDGE_SECRET",
            },
            status=401,
        )

    # 2. Parse and validate request body
    try:
        data = await request.json()
    except Exception as e:
        return web.json_response(
            {"status": "error", "error": f"Invalid JSON: {e}"}, status=400
        )

    message = data.get("message")
    msg_type = data.get("type")
    user_id = data.get("user_id")

    # Validate required fields
    if not message or not isinstance(message, str):
        return web.json_response(
            {
                "status": "error",
                "error": "Missing or invalid field: message (must be string)",
            },
            status=400,
        )

    if not msg_type or msg_type not in ["direct", "llm"]:
        return web.json_response(
            {
                "status": "error",
                "error": ("Missing or invalid field: type (must be 'direct' or 'llm')"),
            },
            status=400,
        )

    # Validate optional user_id
    if user_id is not None and not isinstance(user_id, int):
        return web.json_response(
            {
                "status": "error",
                "error": "Invalid field: user_id (must be integer if provided)",
            },
            status=400,
        )

    # 3. Send message via appropriate mode
    try:
        service = get_nudge_service()
        if msg_type == "direct":
            result = await service.send_direct(
                message=message,
                user_id=user_id,
            )
        else:  # msg_type == "llm"
            result = await service.send_via_llm(
                message=message,
                user_id=user_id,
            )

        return web.json_response(
            {
                "status": "success",
                "message": f"Message sent via {msg_type} mode",
                "result": result,
            },
            status=200,
        )

    except Exception as e:
        return web.json_response(
            {
                "status": "error",
                "error": f"Failed to send message: {str(e)}",
            },
            status=500,
        )
