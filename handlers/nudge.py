"""
Nudge endpoint handler for agent-to-user communication.

Provides POST /nudge endpoint that:
1. Validates authentication via NUDGE_SECRET
2. Validates request payload
3. Sends message directly or via LLM pipeline to Telegram users
4. Returns response or error
"""

import os

from aiohttp import web

from services.nudge_service import NudgeService

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

    Authentication:
        Requires Authorization: Bearer <NUDGE_SECRET> header

    Request Body (JSON):
        {
            "message": "Rich **markdown** [message](url)",  // Required: Markdown
            "type": "direct",                                // Required: "direct"|"llm"
            "user_id": 123456789                            // Optional: specific user
        }

    Returns:
        200: Success - message sent to user(s)
        400: Bad Request - invalid payload
        401: Unauthorized - missing or invalid auth token
        500: Internal Server Error - failed to send message
    """
    # 1. Validate authentication
    auth_header = request.headers.get("Authorization", "")
    expected_token = os.getenv("NUDGE_SECRET")

    if not expected_token:
        return web.json_response(
            {"status": "error", "error": "NUDGE_SECRET not configured on server"},
            status=500,
        )

    if not auth_header.startswith("Bearer "):
        return web.json_response(
            {
                "status": "error",
                "error": (
                    "Invalid authorization header format. Expected: Bearer <token>"
                ),
            },
            status=401,
        )

    provided_token = auth_header.split(" ", 1)[1]
    if provided_token != expected_token:
        return web.json_response(
            {"status": "error", "error": "Invalid authorization token"}, status=401
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
