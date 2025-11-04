"""Unified command registry for all entry points (Telegram, HTTP /call, Discord)."""

from typing import Any, Dict, List, Optional

from src.core.services.auth_service import AuthService


class CommandRegistry:
    """Unified command registry for all entry points."""

    _commands: Dict[str, Dict[str, Any]] = {
        # User commands
        "/start": {
            "description": "Start using the bot",
            "admin_only": False,
            "category": "general",
        },
        "/help": {
            "description": "Show available commands",
            "admin_only": False,
            "category": "general",
        },
        "/ping": {
            "description": "Check if bot is responding",
            "admin_only": False,
            "category": "general",
        },
        "/joke": {
            "description": "Get a random joke",
            "admin_only": False,
            "category": "fun",
        },
        "/remember": {
            "description": "Save something to memory",
            "admin_only": False,
            "category": "memory",
        },
        "/forget": {
            "description": "Remove from memory",
            "admin_only": False,
            "category": "memory",
        },
        "/search": {
            "description": "Search the web",
            "admin_only": False,
            "category": "tools",
        },
        "/status": {
            "description": "Check bot status",
            "admin_only": False,
            "category": "system",
        },
        # Admin commands
        "/view_lessons": {
            "description": "View all lesson instructions",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
        },
        "/add_lesson": {
            "description": "Add a new lesson",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
            "usage": "/add_lesson <text>",
        },
        "/edit_lesson": {
            "description": "Edit existing lesson",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
            "usage": "/edit_lesson <id> <text>",
        },
        "/remove_lesson": {
            "description": "Delete a lesson",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
            "usage": "/remove_lesson <id>",
        },
        "/admin": {
            "description": "Admin panel",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
        },
        "/broadcast": {
            "description": "Send message to all users",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
        },
        "/stats": {
            "description": "View usage statistics",
            "admin_only": True,
            "category": "admin",
            "icon": "🔧",
        },
    }

    @classmethod
    def get_all_commands(cls) -> Dict[str, Dict[str, Any]]:
        """Get all registered commands."""
        return cls._commands.copy()

    @classmethod
    def get_user_commands(cls) -> List[Dict[str, Any]]:
        """Get regular user commands."""
        return [
            {"command": cmd, **info}
            for cmd, info in cls._commands.items()
            if not info["admin_only"]
        ]

    @classmethod
    def get_admin_commands(cls) -> List[Dict[str, Any]]:
        """Get admin-only commands with icons."""
        return [
            {"command": cmd, **info}
            for cmd, info in cls._commands.items()
            if info["admin_only"]
        ]

    @classmethod
    def get_commands_for_user(cls, user_id: int) -> List[Dict[str, Any]]:
        """Get list of commands available to user based on role."""
        commands = cls.get_user_commands()

        auth_service = AuthService()
        if auth_service.is_admin(user_id):
            # Add admin commands with icons
            admin_commands = cls.get_admin_commands()
            commands.extend(admin_commands)

        return commands

    @classmethod
    def get_help_text(cls, user_id: int) -> str:
        """Generate help text based on user role."""
        commands = cls.get_commands_for_user(user_id)

        # Group by category
        categories = {}
        for cmd in commands:
            cat = cmd["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cmd)

        help_text = "🌟 *Available Commands*\n\n"

        # Category order
        cat_order = ["general", "fun", "memory", "tools", "system", "admin"]

        for cat in cat_order:
            if cat in categories:
                if cat == "admin":
                    help_text += "🔧 *Admin Commands*\n"
                else:
                    help_text += f"• *{cat.title()}*\n"

                for cmd in categories[cat]:
                    line = f"  {cmd['command']} - {cmd['description']}"
                    if "usage" in cmd:
                        line += f"\n    Usage: `{cmd['usage']}`"
                    help_text += line + "\n"
                help_text += "\n"

        help_text += (
            "💡 *Tip*: I can also help you with web search and memory management!"
        )

        return help_text

    @classmethod
    def register_command(cls, command: str, info: Dict[str, Any]) -> None:
        """Register a new command."""
        cls._commands[command] = info

    @classmethod
    def unregister_command(cls, command: str) -> None:
        """Unregister a command."""
        if command in cls._commands:
            del cls._commands[command]

    @classmethod
    def is_command_registered(cls, command: str) -> bool:
        """Check if a command is registered."""
        return command in cls._commands

    @classmethod
    def get_command_info(cls, command: str) -> Optional[Dict[str, Any]]:
        """Get information about a command."""
        return cls._commands.get(command)


# Singleton instance
_command_registry = CommandRegistry()


def get_command_registry() -> CommandRegistry:
    """Get the command registry instance."""
    return _command_registry
