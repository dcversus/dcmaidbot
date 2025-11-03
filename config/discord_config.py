"""
Discord Configuration Management
===============================

Handles Discord-specific configuration, environment variables,
and validation for bot deployment.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DiscordConfig:
    """Discord bot configuration settings."""

    # Required configuration
    bot_token: str
    admin_ids: List[int]

    # Optional configuration
    guild_id: Optional[int] = None
    premium_intents: bool = False
    log_level: str = "INFO"
    max_message_length: int = 2000
    embed_color: int = 0x3498DB  # Discord blue
    command_prefix: str = "!"

    # Bot behavior settings
    activity_type: str = "playing"
    activity_name: str = "Virtual House Exploration"
    status: str = "online"  # online, idle, dnd, invisible

    # Interaction settings
    component_timeout: int = 180  # 3 minutes
    delete_after: Optional[int] = None  # Auto-delete messages after N seconds

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_messages: int = 5
    rate_limit_window: int = 60  # seconds

    # Feature flags
    enable_slash_commands: bool = True
    enable_context_menus: bool = True
    enable_modals: bool = True
    enable_threads: bool = True


class DiscordConfigManager:
    """Manages Discord configuration from environment variables."""

    @staticmethod
    def load_config() -> DiscordConfig:
        """Load Discord configuration from environment variables."""

        # Required configuration
        bot_token = os.getenv("DISCORD_BOT_TOKEN")
        if not bot_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")

        # Parse admin IDs
        admin_ids = DiscordConfigManager._parse_admin_ids()
        if not admin_ids:
            raise ValueError("At least one admin ID must be configured")

        # Optional configuration with defaults
        guild_id = DiscordConfigManager._parse_int_env("DISCORD_GUILD_ID")
        premium_intents = (
            os.getenv("DISCORD_PREMIUM_INTENTS", "false").lower() == "true"
        )
        log_level = os.getenv("DISCORD_LOG_LEVEL", "INFO").upper()
        max_message_length = DiscordConfigManager._parse_int_env(
            "DISCORD_MAX_MESSAGE_LENGTH", 2000
        )
        embed_color = DiscordConfigManager._parse_color_env(
            "DISCORD_EMBED_COLOR", 0x3498DB
        )
        command_prefix = os.getenv("DISCORD_COMMAND_PREFIX", "!")

        # Bot behavior
        activity_type = os.getenv("DISCORD_ACTIVITY_TYPE", "playing").lower()
        activity_name = os.getenv("DISCORD_ACTIVITY_NAME", "Virtual House Exploration")
        status = os.getenv("DISCORD_STATUS", "online").lower()

        # Interaction settings
        component_timeout = DiscordConfigManager._parse_int_env(
            "DISCORD_COMPONENT_TIMEOUT", 180
        )
        delete_after = DiscordConfigManager._parse_int_env("DISCORD_DELETE_AFTER")

        # Rate limiting
        rate_limit_enabled = (
            os.getenv("DISCORD_RATE_LIMIT_ENABLED", "true").lower() == "true"
        )
        rate_limit_messages = DiscordConfigManager._parse_int_env(
            "DISCORD_RATE_LIMIT_MESSAGES", 5
        )
        rate_limit_window = DiscordConfigManager._parse_int_env(
            "DISCORD_RATE_LIMIT_WINDOW", 60
        )

        # Feature flags
        enable_slash_commands = (
            os.getenv("DISCORD_ENABLE_SLASH_COMMANDS", "true").lower() == "true"
        )
        enable_context_menus = (
            os.getenv("DISCORD_ENABLE_CONTEXT_MENUS", "true").lower() == "true"
        )
        enable_modals = os.getenv("DISCORD_ENABLE_MODALS", "true").lower() == "true"
        enable_threads = os.getenv("DISCORD_ENABLE_THREADS", "true").lower() == "true"

        config = DiscordConfig(
            bot_token=bot_token,
            admin_ids=admin_ids,
            guild_id=guild_id,
            premium_intents=premium_intents,
            log_level=log_level,
            max_message_length=max_message_length,
            embed_color=embed_color,
            command_prefix=command_prefix,
            activity_type=activity_type,
            activity_name=activity_name,
            status=status,
            component_timeout=component_timeout,
            delete_after=delete_after,
            rate_limit_enabled=rate_limit_enabled,
            rate_limit_messages=rate_limit_messages,
            rate_limit_window=rate_limit_window,
            enable_slash_commands=enable_slash_commands,
            enable_context_menus=enable_context_menus,
            enable_modals=enable_modals,
            enable_threads=enable_threads,
        )

        # Validate configuration
        DiscordConfigManager._validate_config(config)

        logger.info(f"Discord configuration loaded for {len(admin_ids)} admin(s)")
        return config

    @staticmethod
    def _parse_admin_ids() -> List[int]:
        """Parse admin IDs from environment variables."""
        admin_ids = []

        # Try Discord-specific admin IDs first
        discord_admins = os.getenv("DISCORD_ADMIN_IDS", "")
        if discord_admins:
            admin_ids.extend(DiscordConfigManager._parse_int_list(discord_admins))

        # Fallback to general admin IDs
        if not admin_ids:
            general_admins = os.getenv("ADMIN_IDS", "")
            if general_admins:
                admin_ids.extend(DiscordConfigManager._parse_int_list(general_admins))

        return admin_ids

    @staticmethod
    def _parse_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
        """Parse integer from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default

    @staticmethod
    def _parse_int_list(value: str) -> List[int]:
        """Parse comma-separated list of integers."""
        result = []
        for item in value.split(","):
            item = item.strip()
            if item:
                try:
                    result.append(int(item))
                except ValueError:
                    logger.warning(f"Invalid integer in list: {item}")
        return result

    @staticmethod
    def _parse_color_env(key: str, default: int) -> int:
        """Parse color from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default

        try:
            # Support hex format (0xRRGGBB) and decimal
            if value.startswith("0x"):
                return int(value, 16)
            else:
                return int(value)
        except ValueError:
            logger.warning(f"Invalid color value for {key}: {value}, using default")
            return default

    @staticmethod
    def _validate_config(config: DiscordConfig):
        """Validate Discord configuration."""

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level not in valid_log_levels:
            raise ValueError(
                f"Invalid log level: {config.log_level}. Valid levels: {valid_log_levels}"
            )

        # Validate activity type
        valid_activities = ["playing", "listening", "watching", "competing"]
        if config.activity_type not in valid_activities:
            raise ValueError(
                f"Invalid activity type: {config.activity_type}. Valid types: {valid_activities}"
            )

        # Validate status
        valid_statuses = ["online", "idle", "dnd", "invisible"]
        if config.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {config.status}. Valid statuses: {valid_statuses}"
            )

        # Validate command prefix
        if not config.command_prefix or len(config.command_prefix) > 5:
            raise ValueError("Command prefix must be 1-5 characters long")

        # Validate message length
        if config.max_message_length < 1 or config.max_message_length > 2000:
            raise ValueError("Max message length must be between 1 and 2000")

        # Validate component timeout
        if config.component_timeout < 1 or config.component_timeout > 3600:
            raise ValueError("Component timeout must be between 1 and 3600 seconds")

        # Validate rate limiting
        if config.rate_limit_enabled:
            if config.rate_limit_messages < 1 or config.rate_limit_messages > 100:
                raise ValueError("Rate limit messages must be between 1 and 100")
            if config.rate_limit_window < 1 or config.rate_limit_window > 3600:
                raise ValueError("Rate limit window must be between 1 and 3600 seconds")

    @staticmethod
    def get_config_dict() -> Dict[str, Any]:
        """Get Discord configuration as dictionary (for logging/debugging)."""
        try:
            config = DiscordConfigManager.load_config()
            return {
                "admin_count": len(config.admin_ids),
                "guild_id": config.guild_id,
                "premium_intents": config.premium_intents,
                "log_level": config.log_level,
                "max_message_length": config.max_message_length,
                "embed_color": hex(config.embed_color),
                "command_prefix": config.command_prefix,
                "activity_type": config.activity_type,
                "activity_name": config.activity_name,
                "status": config.status,
                "component_timeout": config.component_timeout,
                "delete_after": config.delete_after,
                "rate_limit_enabled": config.rate_limit_enabled,
                "enable_slash_commands": config.enable_slash_commands,
                "enable_context_menus": config.enable_context_menus,
                "enable_modals": config.enable_modals,
                "enable_threads": config.enable_threads,
            }
        except Exception as e:
            return {"error": str(e)}


# Global configuration instance
_discord_config: Optional[DiscordConfig] = None


def get_discord_config() -> DiscordConfig:
    """Get Discord configuration (singleton pattern)."""
    global _discord_config
    if _discord_config is None:
        _discord_config = DiscordConfigManager.load_config()
    return _discord_config


def reload_discord_config() -> DiscordConfig:
    """Reload Discord configuration from environment."""
    global _discord_config
    _discord_config = DiscordConfigManager.load_config()
    return _discord_config
