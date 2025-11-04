"""Application factory for DCMAIDBot API."""

from aiohttp import web

from .routes import setup_routes


def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()

    # Setup routes
    setup_routes(app)

    # Note: AnalyticsMiddleware is for aiogram (Telegram bot), not aiohttp web server
    # It should only be used in the bot setup, not the web API

    return app
