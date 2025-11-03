"""API routes setup."""

from aiohttp import web

from .handlers import (
    call_handler,
    event_handler,
    health_handler,
    landing_handler,
    nudge_handler,
    version_handler,
)


def setup_routes(app: web.Application) -> None:
    """Setup all API routes."""
    # API routes
    app.router.add_post("/call", call_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/api/version", version_handler)
    app.router.add_post("/nudge", nudge_handler)
    app.router.add_post("/event", event_handler)

    # Landing page
    app.router.add_get("/", landing_handler)
    app.router.add_static("/static", "static", name="static")

    # CORS
    app.router.add_options("/{path:.*}", lambda r: web.Response(status=200))
