"""Unified command registry for all entry points."""

from .registry import CommandRegistry, get_command_registry

__all__ = ["CommandRegistry", "get_command_registry"]
