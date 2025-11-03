"""
Discord Bot Manager
==================

Main Discord bot class with enhanced functionality, slash commands,
and integration with the dcmaidbot system.
"""

import logging
from typing import Optional

import discord

from config.discord_config import get_discord_config
from services.discord_service import DiscordService

logger = logging.getLogger(__name__)


class DiscordBotManager:
    """Manages Discord bot lifecycle and integration."""

    def __init__(self):
        self.config = get_discord_config()
        self.discord_service: Optional[DiscordService] = None
        self.bot: Optional[discord.Client] = None
        self._running = False

    async def initialize(self) -> bool:
        """Initialize Discord bot and services."""
        try:
            # Initialize Discord service
            self.discord_service = DiscordService()
            if not self.discord_service.initialize():
                logger.error("Failed to initialize Discord service")
                return False

            self.bot = self.discord_service.bot

            # Setup command handlers
            await self._setup_commands()

            logger.info("Discord bot manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Discord bot manager: {e}")
            return False

    async def start(self) -> bool:
        """Start the Discord bot."""
        if not self.discord_service:
            logger.error("Discord service not initialized")
            return False

        try:
            self._running = True
            success = await self.discord_service.start()

            if success:
                logger.info("Discord bot started successfully")
                # Send startup notification to admins
                await self._notify_admins("🎉 DC MaidBot is now online on Discord!")

            return success

        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            self._running = False
            return False

    async def stop(self):
        """Stop the Discord bot."""
        if not self._running:
            return

        try:
            self._running = False
            if self.discord_service:
                await self.discord_service.stop()
            logger.info("Discord bot stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping Discord bot: {e}")

    async def _setup_commands(self):
        """Setup Discord slash commands."""
        if not self.bot or not self.config.enable_slash_commands:
            return

        # Basic ping command for testing
        @self.bot.tree.command(name="ping", description="Check bot latency")
        async def ping(interaction: discord.Interaction):
            """Simple ping command to test bot responsiveness."""
            latency = round(self.bot.latency * 1000)  # Convert to milliseconds
            await interaction.response.send_message(
                f"🏓 Pong! Latency: {latency}ms", ephemeral=True
            )

        # Help command
        @self.bot.tree.command(name="help", description="Show available commands")
        async def help_command(interaction: discord.Interaction):
            """Show help information."""
            embed = discord.Embed(
                title="🤖 DC MaidBot Help",
                description="Welcome to DC MaidBot! Here are the available commands:",
                color=self.config.embed_color,
            )

            embed.add_field(
                name="🏠 House Exploration",
                value="`/explore` - Explore the virtual house\n`/rooms` - List available rooms",
                inline=False,
            )

            embed.add_field(
                name="🎵 Music",
                value="`/play` - Play music\n`/pause` - Pause playback\n`/stop` - Stop music",
                inline=False,
            )

            embed.add_field(
                name="🎮 Games",
                value="`/games` - List available games\n`/play_game` - Play a game",
                inline=False,
            )

            embed.add_field(
                name="ℹ️ Other",
                value="`/ping` - Check bot latency\n`/status` - Bot status",
                inline=False,
            )

            embed.set_footer(
                text="Use / before each command. More features coming soon!"
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        # Status command
        @self.bot.tree.command(name="status", description="Check bot status")
        async def status(interaction: discord.Interaction):
            """Show bot status information."""
            if interaction.user.id not in self.config.admin_ids:
                await interaction.response.send_message(
                    "❌ This command is only available to administrators.",
                    ephemeral=True,
                )
                return

            guild_count = len(self.bot.guilds)
            user_count = sum(guild.member_count for guild in self.bot.guilds)

            embed = discord.Embed(title="📊 Bot Status", color=self.config.embed_color)

            embed.add_field(
                name="Connected",
                value="✅ Online"
                if self.discord_service.is_connected
                else "❌ Offline",
            )
            embed.add_field(name="Guilds", value=str(guild_count))
            embed.add_field(name="Total Users", value=str(user_count))
            embed.add_field(name="Uptime", value="🔄 Active")
            embed.add_field(name="Admins", value=str(len(self.config.admin_ids)))
            embed.add_field(
                name="Commands",
                value="✅ Enabled"
                if self.config.enable_slash_commands
                else "❌ Disabled",
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        logger.info("Discord slash commands setup completed")

    async def _notify_admins(self, message: str):
        """Send notification to all Discord admin users."""
        if not self.discord_service:
            return

        for admin_id in self.config.admin_ids:
            try:
                result = await self.discord_service.send_message(admin_id, message)
                if result.get("status") != "success":
                    logger.warning(f"Failed to notify admin {admin_id}: {result}")
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")

    @property
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        return self._running and (
            self.discord_service.is_connected if self.discord_service else False
        )
