"""
Discord Service Implementation
============================

Complete Discord bot service implementation with unified abstraction layer
for cross-platform dcmaidbot functionality.
"""

import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union

import discord

from core.services.messenger_service import (
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    EmbedThumbnail,
    InlineButton,
    MessageType,
    RichContent,
    SelectMenu,
    SelectOption,
)

logger = logging.getLogger(__name__)


class DiscordBot(discord.Client):
    """Main Discord bot class with enhanced functionality."""

    def __init__(self, intents: Optional[discord.Intents] = None):
        """Initialize Discord bot with proper intents."""
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.members = True

        super().__init__(
            intents=intents,
        )

        self.dcmaidbot_service = None
        self.connected = False

    async def on_ready(self):
        """Called when bot is ready and connected."""
        self.connected = True
        logger.info(f"Discord bot logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        # Set bot activity
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="Virtual House Exploration"
            )
        )

    async def on_connect(self):
        """Called when bot connects to Discord."""
        logger.info("Discord bot connected to gateway")

    async def on_disconnect(self):
        """Called when bot disconnects from Discord."""
        self.connected = False
        logger.warning("Discord bot disconnected from gateway")

    async def on_resumed(self):
        """Called when bot resumes connection."""
        self.connected = True
        logger.info("Discord bot resumed connection")

    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild."""
        logger.info(f"Discord bot joined guild: {guild.name} ({guild.id})")
        # Send welcome message to default channel
        if guild.system_channel:
            try:
                await guild.system_channel.send(
                    embed=discord.Embed(
                        title="🎉 DC MaidBot is here!",
                        description="Hello! I'm DC MaidBot, ready to help you explore virtual houses, play music, and more! Use `/help` to see available commands.",
                        color=discord.Color.blue(),
                    )
                )
            except discord.Forbidden:
                logger.warning(
                    f"Cannot send message in {guild.name} - missing permissions"
                )


class DiscordService:
    """Discord-specific messenger service implementation with full functionality."""

    def __init__(self):
        self.platform_name = "Discord"
        self.bot: Optional[DiscordBot] = None
        self._token: Optional[str] = None
        self._ready_event = asyncio.Event()
        self._connection_task: Optional[asyncio.Task] = None

    def initialize(self) -> bool:
        """Initialize Discord service with token from environment."""
        self._token = os.getenv("DISCORD_BOT_TOKEN")
        if not self._token:
            logger.error("DISCORD_BOT_TOKEN not found in environment variables")
            return False

        # Create bot instance
        self.bot = DiscordBot(intents=self._get_intents())

        # Set up event handlers
        self.bot.add_listener(self._on_ready, "on_ready")
        self.bot.add_listener(self._on_disconnect, "on_disconnect")

        return True

    def _get_intents(self) -> discord.Intents:
        """Get Discord intents based on environment configuration."""
        intents = discord.Intents.default()

        # Check if we have premium intents (requires verification)
        if os.getenv("DISCORD_PREMIUM_INTENTS", "false").lower() == "true":
            intents.message_content = True
            intents.members = True
            intents.presences = True

        intents.guilds = True
        intents.messages = True
        intents.reactions = True

        return intents

    async def start(self) -> bool:
        """Start the Discord bot connection."""
        if not self.bot or not self._token:
            logger.error("Discord service not properly initialized")
            return False

        try:
            # Start connection in background task
            self._connection_task = asyncio.create_task(self.bot.start(self._token))

            # Wait for bot to be ready
            await self._ready_event.wait()

            logger.info("Discord service started successfully")
            return True

        except discord.LoginFailure:
            logger.error("Invalid Discord bot token")
            return False
        except Exception as e:
            logger.error(f"Failed to start Discord service: {e}")
            return False

    async def stop(self):
        """Stop the Discord bot connection."""
        if self.bot:
            await self.bot.close()
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

    async def _on_ready(self):
        """Handle bot ready event."""
        self._ready_event.set()
        await self._register_commands()

    async def _on_disconnect(self):
        """Handle bot disconnect event."""
        self._ready_event.clear()

    async def _register_commands(self):
        """Register slash commands with Discord API."""
        if not self.bot:
            return

        try:
            # Sync commands with Discord
            await self.bot.tree.sync()
            logger.info("Discord slash commands registered successfully")
        except discord.HTTPException as e:
            logger.error(f"Failed to register Discord commands: {e}")

    async def send_message(
        self, user_id: int, content: Union[str, RichContent], **kwargs
    ) -> Dict[str, Any]:
        """Send message via Discord Bot API."""
        if not self.bot or not self.bot.connected:
            return {
                "status": "error",
                "error": "Discord bot not connected",
                "user_id": user_id,
                "platform": "Discord",
                "message_type": "error",
                "has_embeds": False,
                "has_components": False,
            }

        try:
            # Get user object
            user = self.bot.get_user(user_id)
            if not user:
                # Try to fetch user
                try:
                    user = await self.bot.fetch_user(user_id)
                except discord.NotFound:
                    return {
                        "status": "error",
                        "error": f"User {user_id} not found",
                        "user_id": user_id,
                        "platform": "Discord",
                    }

            if isinstance(content, str):
                # Convert plain text to RichContent
                rich_content = self.parse_markdown_to_platform(content)
            else:
                rich_content = content

            return await self.send_rich_content_to_user(user, rich_content, **kwargs)

        except discord.Forbidden:
            return {
                "status": "error",
                "error": f"Cannot send messages to user {user_id} (blocked or DMs disabled)",
                "user_id": user_id,
                "platform": "Discord",
            }
        except Exception as e:
            logger.error(f"Error sending Discord message to {user_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id,
                "platform": "Discord",
            }

    async def send_rich_content_to_user(
        self, user: discord.User, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send rich content message to Discord user."""
        try:
            # Prepare embeds
            embeds = []
            if rich_content.embeds:
                for embed in rich_content.embeds:
                    discord_embed = self._convert_to_discord_embed(embed)
                    embeds.append(discord_embed)

            # Prepare view for components
            view = None
            if rich_content.buttons or rich_content.components:
                view = self._create_view_from_components(
                    rich_content.buttons, rich_content.components
                )

            # Send message
            if embeds:
                message = await user.send(
                    content=rich_content.content,
                    embeds=embeds,
                    view=view,
                    tts=rich_content.tts or False,
                    allowed_mentions=self._parse_allowed_mentions(
                        rich_content.allowed_mentions
                    ),
                )
            else:
                message = await user.send(
                    content=rich_content.content,
                    view=view,
                    tts=rich_content.tts or False,
                    allowed_mentions=self._parse_allowed_mentions(
                        rich_content.allowed_mentions
                    ),
                )

            return {
                "status": "success",
                "message_id": message.id,
                "channel_id": message.channel.id,
                "user_id": user.id,
                "platform": "Discord",
                "message_type": rich_content.message_type.value,
                "has_embeds": bool(embeds),
                "has_components": bool(view),
            }

        except discord.Forbidden:
            return {
                "status": "error",
                "error": f"Cannot send messages to {user.display_name} (blocked or DMs disabled)",
                "user_id": user.id,
                "platform": "Discord",
            }
        except Exception as e:
            logger.error(f"Error sending rich content to Discord user {user.id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user.id,
                "platform": "Discord",
            }

    async def send_rich_content(
        self, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send rich content message via Discord."""
        return await self.send_message(user_id, rich_content, **kwargs)

    def parse_markdown_to_platform(self, markdown: str) -> RichContent:
        """Parse markdown into Discord-compatible rich content."""
        import re

        # Handle common markdown patterns for Discord
        content = markdown

        # Convert headers to Discord's bold format
        content = re.sub(r"^# (.+)$", r"**\1**", content, flags=re.MULTILINE)
        content = re.sub(r"^## (.+)$", r"**\1**", content, flags=re.MULTILINE)
        content = re.sub(r"^### (.+)$", r"**\1**", content, flags=re.MULTILINE)

        # Discord supports markdown natively, so minimal conversion needed
        # Discord supports: **bold**, *italic*, __underline__, ~~strikethrough~~, `code`, ```code blocks```

        # Extract potential embeds from markdown
        content, embeds = self._extract_embeds_from_markdown(content)

        # Extract buttons from markdown if present
        content, buttons = self._extract_buttons_from_markdown(content)

        return RichContent(
            content=content,
            message_type=MessageType.MARKDOWN,
            buttons=buttons,
            embeds=embeds,
            parse_mode="Markdown",  # Discord supports markdown
        )

    def _extract_embeds_from_markdown(
        self, content: str
    ) -> tuple[str, Optional[List[Embed]]]:
        """Extract embed definitions from markdown content."""
        embeds = []

        # Pattern for embeds in markdown: Embed: title|description|color
        embed_pattern = r"Embed:\s*([^|]+)\|([^|]*)\|?(\d+)?"

        def replace_embed(match):
            title = match.group(1).strip()
            description = match.group(2).strip() if match.group(2) else None
            color = int(match.group(3)) if match.group(3) else None

            embed = Embed(title=title, description=description, color=color)
            embeds.append(embed)

            return f"**{title}**"  # Keep title visible in main content

        # Replace embed markdown with bold title (embeds will be added separately)
        processed_content = re.sub(embed_pattern, replace_embed, content)

        return processed_content, embeds if embeds else None

    def _extract_buttons_from_markdown(
        self, content: str
    ) -> tuple[str, Optional[List[InlineButton]]]:
        """Extract button definitions from markdown content."""
        buttons = []

        # Pattern for buttons in markdown: [Button Text](callback_data) or [Button Text](url)
        button_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        def replace_button(match):
            button_text = match.group(1)
            button_target = match.group(2)

            # Determine if it's a callback_data or URL
            if button_target.startswith(("http://", "https://", "www.")):
                button = InlineButton(text=button_text, url=button_target)
            else:
                button = InlineButton(text=button_text, callback_data=button_target)

            buttons.append(button)
            return f"**{button_text}**"  # Keep button text visible

        # Replace button markdown with bold text (buttons will be added to components)
        processed_content = re.sub(button_pattern, replace_button, content)

        return processed_content, buttons if buttons else None

    def _convert_to_discord_embed(self, embed: Embed) -> discord.Embed:
        """Convert unified embed to Discord embed."""
        discord_embed = discord.Embed(
            title=embed.title,
            description=embed.description,
            color=embed.color if embed.color is not None else discord.Color.blue(),
        )

        # Add fields
        if embed.fields:
            for field in embed.fields:
                discord_embed.add_field(
                    name=field.name,
                    value=field.value,
                    inline=field.inline if field.inline is not None else False,
                )

        # Add author
        if embed.author:
            discord_embed.set_author(
                name=embed.author.name,
                url=embed.author.url,
                icon_url=embed.author.icon_url,
            )

        # Add footer
        if embed.footer:
            discord_embed.set_footer(
                text=embed.footer.text,
                icon_url=embed.footer.icon_url,
            )

        # Add image
        if embed.image:
            discord_embed.set_image(url=embed.image.url)

        # Add thumbnail
        if embed.thumbnail:
            discord_embed.set_thumbnail(url=embed.thumbnail.url)

        # Add timestamp
        if embed.timestamp:
            discord_embed.timestamp = embed.timestamp

        return discord_embed

    def _create_view_from_components(
        self,
        buttons: Optional[List[InlineButton]] = None,
        components: Optional[List[Any]] = None,
    ) -> Optional[discord.ui.View]:
        """Create Discord view from buttons and components."""
        if not buttons and not components:
            return None

        view = discord.ui.View(timeout=180)  # 3 minute timeout

        # Add buttons
        if buttons:
            for button in buttons:
                discord_button = discord.ui.Button(
                    label=button.text,
                    style=discord.ButtonStyle.link
                    if button.url
                    else discord.ButtonStyle.primary,
                    url=button.url,
                    custom_id=button.callback_data if not button.url else None,
                )

                if not button.url:
                    discord_button.callback = self._create_button_callback(
                        button.callback_data
                    )

                view.add_item(discord_button)

        # Add other components (select menus, etc.)
        if components:
            for component in components:
                if isinstance(component, SelectMenu):
                    select_menu = discord.ui.Select(
                        placeholder=component.placeholder,
                        custom_id=component.callback_data,
                        min_values=component.min_values or 1,
                        max_values=component.max_values or 1,
                    )

                    for option in component.options:
                        select_menu.add_option(
                            label=option.label,
                            value=option.value,
                            description=option.description,
                            emoji=option.emoji,
                            default=option.default or False,
                        )

                    select_menu.callback = self._create_select_callback(
                        component.callback_data
                    )
                    view.add_item(select_menu)

        return view

    def _create_button_callback(self, callback_data: str):
        """Create button callback function."""

        async def callback(interaction: discord.Interaction):
            try:
                # Handle the button interaction
                await interaction.response.send_message(
                    f"Button clicked: {callback_data}", ephemeral=True
                )

                # Here you would integrate with your existing handlers
                # For now, just acknowledge the interaction

            except Exception as e:
                logger.error(f"Error handling button interaction: {e}")
                await interaction.response.send_message(
                    "An error occurred while handling this interaction.", ephemeral=True
                )

        return callback

    def _create_select_callback(self, callback_data: str):
        """Create select menu callback function."""

        async def callback(interaction: discord.Interaction):
            try:
                values = interaction.data.get("values", [])
                await interaction.response.send_message(
                    f"Selected: {', '.join(values)}", ephemeral=True
                )

                # Here you would integrate with your existing handlers

            except Exception as e:
                logger.error(f"Error handling select interaction: {e}")
                await interaction.response.send_message(
                    "An error occurred while handling this interaction.", ephemeral=True
                )

        return callback

    def _parse_allowed_mentions(
        self, allowed_mentions: Optional[Dict[str, Any]]
    ) -> Optional[discord.AllowedMentions]:
        """Parse allowed mentions from RichContent."""
        if not allowed_mentions:
            return None

        return discord.AllowedMentions(
            users=allowed_mentions.get("users", False),
            everyone=allowed_mentions.get("everyone", False),
            roles=allowed_mentions.get("roles", False),
            replied_user=allowed_mentions.get("replied_user", False),
        )

    def create_welcome_buttons(self, user_id: int) -> List[Dict[str, str]]:
        """Create standard welcome buttons for Discord."""
        return [
            {"text": "🏠 Explore House", "callback_data": f"explore_house_{user_id}"},
            {"text": "🎵 Play Music", "callback_data": f"play_music_{user_id}"},
            {"text": "📋 Changelog", "callback_data": f"changelog_{user_id}"},
            {"text": "❓ Help", "callback_data": f"help_{user_id}"},
            {"text": "🎮 Play Games", "callback_data": f"play_games_{user_id}"},
        ]

    # Helper methods for creating Discord-specific components
    def create_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: int = 0x3498DB,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> Embed:
        """Create Discord embed with common parameters."""
        embed = Embed(title=title, description=description, color=color)

        if fields:
            embed.fields = [
                EmbedField(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False),
                )
                for field in fields
            ]

        if footer_text:
            embed.footer = EmbedFooter(text=footer_text)

        if thumbnail_url:
            embed.thumbnail = EmbedThumbnail(url=thumbnail_url)

        if author_name:
            embed.author = EmbedAuthor(name=author_name, url=author_url)

        return embed

    def create_select_menu(
        self,
        custom_id: str,
        placeholder: str,
        options: List[Dict[str, Any]],
        min_values: int = 1,
        max_values: int = 1,
    ) -> SelectMenu:
        """Create Discord select menu."""
        select_options = []
        for option in options:
            select_options.append(
                SelectOption(
                    label=option["label"],
                    value=option["value"],
                    description=option.get("description"),
                    emoji=option.get("emoji"),
                    default=option.get("default", False),
                )
            )

        return SelectMenu(
            text=placeholder,
            callback_data=custom_id,
            placeholder=placeholder,
            options=select_options,
            min_values=min_values,
            max_values=max_values,
        )

    @property
    def is_connected(self) -> bool:
        """Check if Discord bot is connected."""
        return self.bot is not None and self.bot.connected

    async def get_user(self, user_id: int) -> Optional[discord.User]:
        """Get Discord user by ID."""
        if not self.bot:
            return None

        user = self.bot.get_user(user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                return None

        return user
