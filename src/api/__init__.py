"""API module for DCMAIDBot."""

from aiohttp import web

from .app import create_app
from .routes import setup_routes

__all__ = ["create_app", "setup_routes", "web"]
