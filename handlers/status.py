"""
Status endpoint handlers for HTTP monitoring.

Provides /version and /health endpoints for:
- Human-readable status page
- Kubernetes liveness/readiness probes
- Deployment verification
"""

import html

from aiohttp import web

from services.status_service import StatusService

# Initialize status service with database engine
try:
    from database import engine

    status_service = StatusService(db_engine=engine)
except ImportError:
    # Fallback if database module not available
    status_service = StatusService()


async def version_handler(request: web.Request) -> web.Response:
    """GET /version - Return version and status information as HTML.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: HTML page with complete status information
    """
    status = await status_service.get_full_status()
    html_content = render_status_html(status)

    return web.Response(text=html_content, content_type="text/html", charset="utf-8")


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


async def api_version_handler(request: web.Request) -> web.Response:
    """GET /api/version - Lightweight version info API for landing page.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: JSON response with version information
    """
    status = await status_service.get_full_status()
    version_info = status["version_info"]
    system_info = status["system_info"]

    # Extract relevant data for landing page
    uptime_seconds = system_info["uptime_seconds"]
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_display = f"{hours}h {minutes}m"

    redis_status = "offline"
    if status["redis"]["connected"]:
        redis_status = status["redis"]["status"]

    db_status = "offline"
    if status["database"]["connected"]:
        db_status = status["database"]["status"]

    data = {
        "version": version_info["version"],
        "commit": version_info["git_commit"][:7],
        "uptime": uptime_display,
        "redis": redis_status,
        "postgresql": db_status,
        "bot": "online",
        "image_tag": version_info["image_tag"],
        "build_time": version_info["build_time"],
    }

    return web.json_response(data, status=200)


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
