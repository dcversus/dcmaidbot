"""
Nudge endpoint handler for agent-to-user communication.

Provides POST /nudge endpoint that:
1. Validates authentication via NUDGE_SECRET
2. Validates request payload
3. Forwards request to external LLM endpoint
4. Returns response or error
"""

import os
from aiohttp import web

from services.nudge_service import NudgeService

# Global service instance
nudge_service = NudgeService()


async def nudge_handler(request: web.Request) -> web.Response:
    """POST /nudge - Forward agent requests to external LLM endpoint.

    Authentication:
        Requires Authorization: Bearer <NUDGE_SECRET> header

    Request Body (JSON):
        {
            "user_ids": [123456789],  // Required: Admin Telegram user IDs
            "message": "...",          // Required: Human-friendly message
            "pr_url": "...",           // Optional: PR URL
            "prp_file": "...",         // Optional: PRP file path
            "prp_section": "...",      // Optional: Section anchor
            "urgency": "medium"        // Optional: low|medium|high
        }

    Returns:
        200: Success - nudge forwarded to external endpoint
        400: Bad Request - invalid payload
        401: Unauthorized - missing or invalid auth token
        500: Internal Server Error - NUDGE_SECRET not configured
        502: Bad Gateway - failed to forward to external endpoint
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

    user_ids = data.get("user_ids")
    message = data.get("message")

    if not user_ids or not isinstance(user_ids, list):
        return web.json_response(
            {
                "status": "error",
                "error": (
                    "Missing or invalid field: user_ids (must be list of integers)"
                ),
            },
            status=400,
        )

    if not message or not isinstance(message, str):
        return web.json_response(
            {
                "status": "error",
                "error": "Missing or invalid field: message (must be string)",
            },
            status=400,
        )

    # 3. Forward to external endpoint
    try:
        response_data = await nudge_service.forward_nudge(
            user_ids=user_ids,
            message=message,
            pr_url=data.get("pr_url"),
            prp_file=data.get("prp_file"),
            prp_section=data.get("prp_section"),
            urgency=data.get("urgency", "medium"),
        )

        return web.json_response(
            {
                "status": "success",
                "message": "Nudge forwarded to external endpoint",
                "forwarded_to": nudge_service.EXTERNAL_ENDPOINT,
                "user_ids": user_ids,
                "external_response": response_data,
            },
            status=200,
        )

    except Exception as e:
        return web.json_response(
            {"status": "error", "error": f"Failed to forward nudge: {str(e)}"},
            status=502,
        )
