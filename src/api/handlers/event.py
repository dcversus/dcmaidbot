"""Event collection handler for universal Telegram event processing.

This handler provides the /event endpoint for collecting all Telegram
button events, user interactions, and other UI events.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from aiohttp import web
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.api_key import ApiKey
from src.core.models.event import Event
from src.core.services.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
_rate_limit_store = {}


async def event_handler(request: web.Request) -> web.Response:
    """Handle event collection from external systems.

    Accepts events with API key authentication and stores them
    for processing by dcmaidbot.
    """
    try:
        # Get API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _json_response(
                {"error": "Invalid authorization format. Use: Bearer <api_key>"},
                status=401,
            )

        api_key = auth_header[7:]  # Remove "Bearer " prefix

        # Parse request body
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return _json_response({"error": "Invalid JSON in request body"}, status=400)

        # Validate required fields
        required_fields = ["event_id", "user_id", "event_type"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return _json_response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=400,
            )

        # Validate and process event
        async with AsyncSessionLocal() as session:
            result = await _process_event(session, data, api_key, request)
            return result

    except Exception as e:
        logger.error(f"Unexpected error in event_handler: {e}", exc_info=True)
        return _json_response({"error": "Internal server error"}, status=500)


async def _process_event(
    session: AsyncSession,
    event_data: dict[str, Any],
    api_key: str,
    request: web.Request,
) -> web.Response:
    """Process and store an event after authentication."""
    try:
        # Authenticate API key
        api_key_obj = await _authenticate_api_key(session, api_key)
        if not api_key_obj:
            return _json_response({"error": "Invalid or inactive API key"}, status=401)

        # Check rate limits
        rate_limit_result = await _check_rate_limits(api_key_obj, request.remote)
        if rate_limit_result:
            return rate_limit_result

        # Validate event permissions
        event_type = event_data.get("event_type", "")
        if not api_key_obj.can_submit_event_type(event_type):
            return _json_response(
                {"error": f"API key not authorized to submit event type: {event_type}"},
                status=403,
            )

        # Check for duplicate event_id
        existing_event = await session.execute(
            select(Event).where(Event.event_id == event_data["event_id"])
        )
        if existing_event.scalar_one_or_none():
            return _json_response(
                {"error": "Event with this ID already exists"}, status=409
            )

        # Create and store event
        event = Event(
            event_id=event_data["event_id"],
            user_id=event_data["user_id"],
            chat_id=event_data.get("chat_id"),
            event_type=event_type,
            event_subtype=event_data.get("event_subtype"),
            data=event_data.get("data", {}),
            button_text=event_data.get("button_text"),
            callback_data=event_data.get("callback_data"),
            status="unread",
        )

        session.add(event)
        await session.commit()

        # Update API key usage stats
        api_key_obj.usage_count += 1
        api_key_obj.last_used_at = datetime.utcnow()
        await session.commit()

        logger.info(
            f"Event stored: {event.event_id} (type: {event.event_type}, "
            f"user: {event.user_id}, key: {api_key_obj.name})"
        )

        return _json_response(
            {
                "success": True,
                "event_id": event.event_id,
                "status": "stored",
                "message": "Event successfully stored for processing",
            }
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error processing event: {e}", exc_info=True)
        return _json_response(
            {"error": f"Failed to process event: {str(e)}"}, status=500
        )


async def _authenticate_api_key(
    session: AsyncSession, provided_key: str
) -> Optional[ApiKey]:
    """Authenticate the provided API key."""
    try:
        # Get all active API keys
        result = await session.execute(select(ApiKey).where(ApiKey.is_active))
        api_keys = result.scalars().all()

        # Check each key (hash comparison)
        for api_key_obj in api_keys:
            if api_key_obj.verify_key(provided_key):
                # Check if key is expired
                if api_key_obj.is_expired():
                    logger.warning(f"Expired API key used: {api_key_obj.name}")
                    return None
                return api_key_obj

        return None

    except Exception as e:
        logger.error(f"Error authenticating API key: {e}", exc_info=True)
        return None


async def _check_rate_limits(
    api_key_obj: ApiKey, client_ip: str
) -> Optional[web.Response]:
    """Check rate limits for the API key."""
    try:
        current_time = datetime.utcnow()
        key_id = api_key_obj.id
        ip_key = f"{key_id}:{client_ip}"

        # Initialize rate limit tracking
        if ip_key not in _rate_limit_store:
            _rate_limit_store[ip_key] = {"minute_requests": [], "hour_requests": []}

        tracking = _rate_limit_store[ip_key]

        # Clean old requests
        one_minute_ago = current_time.replace(second=0, microsecond=0).timestamp()
        one_hour_ago = current_time.replace(
            minute=0, second=0, microsecond=0
        ).timestamp()

        tracking["minute_requests"] = [
            req_time
            for req_time in tracking["minute_requests"]
            if req_time > one_minute_ago
        ]
        tracking["hour_requests"] = [
            req_time
            for req_time in tracking["hour_requests"]
            if req_time > one_hour_ago
        ]

        # Check minute limit
        if len(tracking["minute_requests"]) >= api_key_obj.rate_limit_per_minute:
            return _json_response(
                {
                    "error": "Rate limit exceeded",
                    "limit_type": "per_minute",
                    "limit": api_key_obj.rate_limit_per_minute,
                    "retry_after": 60,
                },
                status=429,
            )

        # Check hour limit
        if len(tracking["hour_requests"]) >= api_key_obj.rate_limit_per_hour:
            return _json_response(
                {
                    "error": "Rate limit exceeded",
                    "limit_type": "per_hour",
                    "limit": api_key_obj.rate_limit_per_hour,
                    "retry_after": 3600,
                },
                status=429,
            )

        # Record this request
        current_timestamp = current_time.timestamp()
        tracking["minute_requests"].append(current_timestamp)
        tracking["hour_requests"].append(current_timestamp)

        return None

    except Exception as e:
        logger.error(f"Error checking rate limits: {e}", exc_info=True)
        # Don't block requests on rate limit errors
        return None


def _json_response(data: dict[str, Any], status: int = 200) -> web.Response:
    """Create a JSON response with proper headers."""
    return web.Response(
        text=json.dumps(data),
        status=status,
        content_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


async def options_handler(request: web.Request) -> web.Response:
    """Handle CORS preflight requests."""
    return web.Response(
        status=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )
