"""Application factory for DCMAIDBot API."""

from aiohttp import web

from .routes import setup_routes


def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()

    # Setup routes
    setup_routes(app)

    # Setup middleware
    from src.api.middleware.analytics import analytics_middleware

    app.middlewares.append(analytics_middleware)

    return app
