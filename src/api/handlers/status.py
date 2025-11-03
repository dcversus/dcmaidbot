"""
Status endpoint handlers for HTTP monitoring.

Provides /version, /health, and /statusm endpoints for:
- Human-readable status page
- Kubernetes liveness/readiness probes
- Deployment verification
- Comprehensive status with all thoughts and opinions
"""

import html
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from aiohttp import web

from core.services.status_service import StatusService

logger = logging.getLogger(__name__)

# Initialize status service with database engine
try:
    from core.services.database import engine

    status_service = StatusService(db_engine=engine)
except ImportError:
    # Fallback if database module not available
    status_service = StatusService()


async def status_handler(request: web.Request) -> web.Response:
    """GET /status - Universal status endpoint returning latest synced status.

    Supports both public and authenticated responses:
    - Public: Basic status information
    - Authenticated (API key): Full admin data including LLM context and interactions

    Args:
        request: aiohttp request object

    Returns:
        web.Response: JSON response with status data
    """
    # Check for API key authentication
    api_key = None
    if "X-API-Key" in request.headers:
        api_key = request.headers["X-API-Key"]
    elif "api_key" in request.query:
        api_key = request.query["api_key"]

    try:
        # Get basic status
        basic_status = await status_service.get_full_status()

        # Check if valid API key provided
        is_authenticated = False
        key_info = {}
        if api_key:
            is_authenticated, key_info = await validate_api_key(api_key, "status:read")

        if is_authenticated:
            # Return full admin status (previously /statusm)
            admin_status = await get_admin_status(basic_status, request, key_info)
            return web.json_response(admin_status, status=200)
        else:
            # Return public status (previous /version API response)
            public_status = get_public_status(basic_status)
            return web.json_response(public_status, status=200)

    except Exception as e:
        logger.error(f"Failed to get status: {e}")

        error_response = {
            "error": "Failed to retrieve status",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return web.json_response(error_response, status=500)


async def get_admin_status(
    basic_status: dict, request: web.Request, key_info: dict
) -> dict:
    """
    Get comprehensive admin status including LLM context and interactions.

    Args:
        basic_status: Basic system status
        request: HTTP request for pagination parameters
        key_info: API key information for access control

    Returns:
        dict: Comprehensive admin status data
    """
    try:
        # Get stored thoughts from background service
        thoughts_data = await get_stored_thoughts()

        # Get pagination parameters
        page = int(request.query.get("page", 1))
        per_page = min(int(request.query.get("per_page", 50)), 100)  # Max 100 per page

        # Get admin LLM context
        admin_llm_context = await get_admin_llm_context()

        # Get admin interactions with pagination
        admin_interactions = await get_admin_interactions(page, per_page)

        # Get crypto data from database
        crypto_data = await get_crypto_data_from_db()

        # Combine all data
        admin_status = {
            # Basic system info
            "versiontxt": basic_status["version_info"]["versiontxt"],
            "version": basic_status["version_info"]["version"],
            "commit": basic_status["version_info"]["git_commit"],
            "uptime": basic_status["system_info"]["uptime_seconds"],
            "start_time": basic_status["system_info"]["start_time"],
            # Enhanced thoughts data
            "version_thoughts": thoughts_data.get(
                "version_thoughts",
                {
                    "available": False,
                    "lilith_opinion": "Not generated yet",
                    "generation_time": None,
                    "tokens_used": 0,
                    "last_updated": None,
                },
            ),
            "self_check_thoughts": thoughts_data.get(
                "self_check_thoughts",
                {
                    "available": False,
                    "lilith_honest_opinion": "Not generated yet",
                    "total_time": None,
                    "tokens_used": 0,
                    "last_updated": None,
                },
            ),
            "crypto_thoughts": thoughts_data.get(
                "crypto_thoughts",
                {
                    "available": False,
                    "market_analysis": "Not generated yet",
                    "generation_time": None,
                    "tokens_used": 0,
                    "last_updated": None,
                },
            ),
            # Admin-specific data
            "admin_llm_context": admin_llm_context,
            "admin_interactions": admin_interactions,
            "crypto_database_data": crypto_data,
            "api_key_info": {
                "key_id": key_info.get("key_hash", "")[:16] if key_info else None,
                "description": key_info.get("description", "") if key_info else None,
                "permissions": key_info.get("permissions", []) if key_info else [],
                "last_used_at": key_info.get("last_used_at") if key_info else None,
                "usage_count": key_info.get("usage_count", 0) if key_info else 0,
            },
            # Timing information
            "self_check_time_sec": thoughts_data.get("self_check_thoughts", {}).get(
                "total_time"
            ),
            "crypto_thoughts_secs": thoughts_data.get("crypto_thoughts", {}).get(
                "generation_time"
            ),
            "crypto_thoughts_time": thoughts_data.get("crypto_thoughts", {}).get(
                "last_updated"
            ),
            "crypto_thoughts_tokens": thoughts_data.get("crypto_thoughts", {}).get(
                "tokens_used", 0
            ),
            # Token usage tracking
            "tokens_total": (
                thoughts_data.get("version_thoughts", {}).get("tokens_used", 0)
                + thoughts_data.get("self_check_thoughts", {}).get("tokens_used", 0)
                + thoughts_data.get("crypto_thoughts", {}).get("tokens_used", 0)
            ),
            "tokens_uptime": (
                thoughts_data.get("version_thoughts", {}).get("tokens_used", 0)
                + thoughts_data.get("self_check_thoughts", {}).get("tokens_used", 0)
                + thoughts_data.get("crypto_thoughts", {}).get("tokens_used", 0)
            )
            / basic_status["system_info"]["uptime_seconds"]
            if basic_status["system_info"]["uptime_seconds"] > 0
            else 0,
            # System components
            "redis": {
                "status": "operational"
                if basic_status["redis"]["connected"]
                else "offline",
                "response_time": 0.1 if basic_status["redis"]["connected"] else None,
            },
            "postgresql": {
                "status": "operational"
                if basic_status["database"]["connected"]
                else "offline",
                "connections": 5 if basic_status["database"]["connected"] else 0,
            },
            "telegram": {
                "status": "operational",
                "last_update": basic_status["system_info"]["current_time_utc"],
            },
            "bot": {
                "status": "operational",
                "commands_processed": 100,  # Placeholder
            },
            # Infrastructure info
            "image_tag": basic_status["version_info"]["image_tag"],
            "build_time": basic_status["version_info"]["build_time"],
            # Nudge tracking
            "last_nudge_fact": None,
            "last_nudge_read": None,
            "timestamp": basic_status["system_info"]["current_time_utc"],
        }

        return admin_status

    except Exception as e:
        logger.error(f"Failed to get admin status: {e}")
        raise


def get_public_status(basic_status: dict) -> dict:
    """
    Get public status information (previous /version endpoint data).

    Args:
        basic_status: Basic system status

    Returns:
        dict: Public status data
    """
    # Extract relevant data for public consumption (previous api_version_handler logic)
    uptime_seconds = basic_status["system_info"]["uptime_seconds"]
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_display = f"{hours}h {minutes}m"

    redis_status = "offline"
    if basic_status["redis"]["connected"]:
        redis_status = basic_status["redis"]["status"]

    db_status = "offline"
    if basic_status["database"]["connected"]:
        db_status = basic_status["database"]["status"]

    return {
        "version": basic_status["version_info"]["version"],
        "commit": basic_status["version_info"]["git_commit"][:7],
        "uptime": uptime_display,
        "redis": redis_status,
        "postgresql": db_status,
        "bot": "online",
        "image_tag": basic_status["version_info"]["image_tag"],
        "build_time": basic_status["version_info"]["build_time"],
        "timestamp": basic_status["system_info"]["current_time_utc"],
    }


async def validate_api_key(
    api_key: str, required_permission: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate API key for admin access.

    Args:
        api_key: API key string to validate
        required_permission: Specific permission required

    Returns:
        Tuple[bool, Dict]: (is_valid, key_info)
    """
    try:
        # Import API key service
        from core.services.api_key_service import api_key_service

        # Validate the key
        is_valid, key_info = api_key_service.validate_api_key(
            api_key, required_permission
        )

        return is_valid, key_info

    except Exception as e:
        logger.error(f"API key validation error: {e}")
        return False, {"error": str(e)}


async def get_admin_llm_context() -> dict:
    """
    Get admin LLM context data.

    Returns:
        dict: Admin LLM context information
    """
    try:
        # TODO: Implement admin LLM context retrieval
        # This should include recent LLM interactions, context data, etc.

        return {
            "current_context": "No active context",
            "recent_prompts": [],
            "token_usage_today": 0,
            "last_llm_interaction": None,
            "context_size": 0,
            "active_sessions": 0,
        }

    except Exception as e:
        logger.error(f"Failed to get admin LLM context: {e}")
        return {"error": str(e)}


async def get_admin_interactions(page: int = 1, per_page: int = 50) -> dict:
    """
    Get admin interactions with pagination.

    Args:
        page: Page number (1-based)
        per_page: Items per page (max 100)

    Returns:
        dict: Paginated admin interactions data
    """
    try:
        # TODO: Implement database query for admin interactions
        # This should include logs, messages, user interactions, etc.

        # Mock data for structure demonstration
        total_interactions = 0
        interactions = []
        total_pages = 0

        return {
            "interactions": interactions,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_interactions,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "filters": {
                "date_from": None,
                "date_to": None,
                "user_id": None,
                "interaction_type": None,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get admin interactions: {e}")
        return {"interactions": [], "pagination": {"error": str(e)}, "filters": {}}


async def health_handler(request: web.Request) -> web.Response:
    """GET /health - Health check endpoint for Kubernetes probes.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: JSON response with health status
    """
    is_healthy, health_details = await status_service.get_health_status()

    if is_healthy:
        return web.json_response(health_details, status=200)
    else:
        return web.json_response(health_details, status=503)


async def version_html_handler(request: web.Request) -> web.Response:
    """GET /version - HTML version status page (backward compatibility).

    Args:
        request: aiohttp request object

    Returns:
        web.Response: HTML page with complete status information
    """
    status = await status_service.get_full_status()
    html_content = render_status_html(status)

    return web.Response(text=html_content, content_type="text/html", charset="utf-8")


async def api_version_handler(request: web.Request) -> web.Response:
    """GET /api/version - JSON version status for API consumption.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: JSON with complete status information including crypto thoughts
    """
    status = await status_service.get_full_status()

    # Return complete status information as JSON (including crypto thoughts)
    return web.json_response(status)


def render_status_html(status: dict) -> str:
    """Render status as cute HTML page with dcmaidbot personality.

    Args:
        status: Complete status dictionary from StatusService

    Returns:
        str: HTML page content
    """
    version_info = status["version_info"]
    system_info = status["system_info"]
    database = status["database"]
    redis = status["redis"]

    # Escape all dynamic content to prevent XSS
    version = html.escape(version_info["version"])
    git_commit = html.escape(version_info["git_commit"][:7])
    image_tag = html.escape(version_info["image_tag"])
    build_time = html.escape(version_info["build_time"])
    environment = html.escape(system_info["environment"])
    pod_name = html.escape(system_info["pod_name"])
    python_version = html.escape(system_info["python_version"])
    current_time_utc = html.escape(system_info["current_time_utc"])
    changelog = html.escape(version_info["changelog"])
    db_message = html.escape(database.get("message", "Unknown"))
    redis_message = html.escape(redis.get("message", "Unknown"))

    # Format uptime nicely
    uptime_seconds = system_info["uptime_seconds"]
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_display = f"{hours}h {minutes}m"

    # Status emoji
    db_emoji = (
        "⏳"
        if database.get("status") == "not_implemented"
        else ("✅" if database["connected"] else "❌")
    )
    redis_emoji = (
        "⏳"
        if redis.get("status") == "not_implemented"
        else ("✅" if redis["connected"] else "❌")
    )

    # Status CSS classes
    db_status_class = (
        "status-pending"
        if database.get("status") == "not_implemented"
        else ("status-ok" if database["connected"] else "status-error")
    )
    redis_status_class = (
        "status-pending"
        if redis.get("status") == "not_implemented"
        else ("status-ok" if redis["connected"] else "status-error")
    )

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dcmaidbot Status - v{version_info["version"]}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Courier New', Consolas, Monaco, monospace;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #00ff00;
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            color: #ff69b4;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(255, 105, 180, 0.5);
        }}

        .subtitle {{
            text-align: center;
            color: #87ceeb;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .section {{
            background: rgba(42, 42, 42, 0.8);
            border: 2px solid #00ff00;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 255, 0, 0.1);
            backdrop-filter: blur(10px);
        }}

        .section h2 {{
            color: #ff69b4;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 2px solid #ff69b4;
            padding-bottom: 10px;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #333;
        }}

        .info-row:last-child {{
            border-bottom: none;
        }}

        .label {{
            color: #87ceeb;
            font-weight: bold;
        }}

        .value {{
            color: #00ff00;
            font-family: monospace;
        }}

        .status-ok {{
            color: #00ff00;
        }}

        .status-pending {{
            color: #ffa500;
        }}

        .status-error {{
            color: #ff0000;
        }}

        pre {{
            background: #000;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
        }}

        .badge {{
            display: inline-block;
            background: #ff69b4;
            color: #000;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #ff69b4;
            font-size: 1.2em;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .card {{
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 20px;
        }}

        .card-title {{
            color: #87ceeb;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        code {{
            background: rgba(0, 255, 0, 0.1);
            color: #00ff00;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8em;
            }}

            .section {{
                padding: 15px;
            }}

            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💕 dcmaidbot Status</h1>
        <div class="subtitle">
            Nya~ I'm running and healthy! 🎀<br>
            Version <span class="badge">{version}</span>
        </div>

        <!-- Deployment Information -->
        <div class="section">
            <h2>📦 Deployment Information</h2>
            <div class="info-row">
                <span class="label">Version:</span>
                <span class="value">{version}</span>
            </div>
            <div class="info-row">
                <span class="label">Git Commit:</span>
                <span class="value"><code>{git_commit}</code></span>
            </div>
            <div class="info-row">
                <span class="label">Image Tag:</span>
                <span class="value">{image_tag}</span>
            </div>
            <div class="info-row">
                <span class="label">Build Time:</span>
                <span class="value">{build_time}</span>
            </div>
            <div class="info-row">
                <span class="label">Environment:</span>
                <span class="value">{environment}</span>
            </div>
            <div class="info-row">
                <span class="label">Pod Name:</span>
                <span class="value">{pod_name}</span>
            </div>
        </div>

        <!-- System Information -->
        <div class="section">
            <h2>⏰ System Information</h2>
            <div class="info-row">
                <span class="label">Current Time (UTC):</span>
                <span class="value">{current_time_utc}</span>
            </div>
            <div class="info-row">
                <span class="label">Uptime:</span>
                <span class="value status-ok">{uptime_display}</span>
            </div>
            <div class="info-row">
                <span class="label">Python Version:</span>
                <span class="value">{python_version}</span>
            </div>
        </div>

        <!-- Service Status Grid -->
        <div class="grid">
            <div class="card">
                <div class="card-title">{db_emoji} Database (PostgreSQL)</div>
                <div class="info-row">
                    <span class="label">Status:</span>
                    <span class="value {db_status_class}">
                        {db_message}
                    </span>
                </div>
            </div>

            <div class="card">
                <div class="card-title">{redis_emoji} Cache (Redis)</div>
                <div class="info-row">
                    <span class="label">Status:</span>
                    <span class="value {redis_status_class}">
                        {redis_message}
                    </span>
                </div>
            </div>
        </div>

        <!-- Recent Changelog -->
        <div class="section">
            <h2>📜 Recent Changelog</h2>
            <pre>{changelog}</pre>
        </div>

        <div class="footer">
            Nya~ Made with 💕 by dcmaidbot<br>
            <small style="color: #87ceeb;">Myaw myaw! 🐱</small>
        </div>
    </div>
</body>
</html>
"""
    return html_content


async def get_stored_thoughts() -> Dict[str, Any]:
    """
    Retrieve stored thoughts from Redis storage.
    This function gets the last stored thoughts from Redis storage.

    Returns:
        Dict: Stored thoughts data with timing information
    """
    try:
        # Import here to avoid circular imports
        from core.services.thoughts_background_service import (
            thoughts_background_service,
        )

        # Get stored thoughts from Redis (async method)
        return await thoughts_background_service.get_stored_thoughts()

    except Exception as e:
        logger.error(f"Failed to get stored thoughts: {e}")
        return {
            "version_thoughts": {"error": str(e)},
            "self_check_thoughts": {"error": str(e)},
            "crypto_thoughts": {"error": str(e)},
        }


async def get_crypto_data_from_db() -> Dict[str, Any]:
    """
    Retrieve crypto data from Redis storage.

    Returns:
        Dict: Crypto database data
    """
    try:
        # Import here to avoid circular imports
        from core.services.thoughts_background_service import (
            thoughts_background_service,
        )

        # Get stored crypto data from background service (async method)
        crypto_data = await thoughts_background_service.get_stored_crypto_data(limit=20)

        return {
            "records": crypto_data,
            "total_records": len(crypto_data),
            "last_updated": crypto_data[0]["timestamp"] if crypto_data else None,
            "database_status": "operational",
        }

    except Exception as e:
        logger.error(f"Failed to get crypto data from Redis: {e}")
        return {
            "records": [],
            "total_records": 0,
            "last_updated": None,
            "database_status": "error",
            "error": str(e),
        }
