"""
Landing page handler for Lilith's Room.

Serves the interactive chibi anime landing page at /.
"""

import os

from aiohttp import web


async def landing_handler(request: web.Request) -> web.Response:
    """GET / - Return the main landing page.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: HTML landing page
    """
    # Get the path to static/index.html
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(current_dir, "static", "index.html")

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return web.Response(
            text=html_content, content_type="text/html", charset="utf-8"
        )

    except FileNotFoundError:
        return web.Response(
            text="Landing page not found", status=404, content_type="text/plain"
        )
