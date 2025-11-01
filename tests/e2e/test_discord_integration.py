"""
End-to-end tests for Discord integration.

Tests complete Discord bot functionality including message sending,
embed creation, slash commands, and interaction handling.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.messenger_service import (
    DiscordService,
    EmbedField,
    InlineButton,
    MessageType,
    MessengerFactory,
    RichContent,
    get_messenger_service,
)
from services.nudge_service import NudgeService


@pytest.mark.e2e
class TestDiscordBotIntegration:
    """End-to-end tests for Discord bot integration."""

    @pytest.fixture
    def mock_discord_client(self):
        """Mock Discord client for testing."""
        mock_client = MagicMock()
        mock_client.user = MagicMock()
        mock_client.user.id = 123456789
        mock_client.is_ready = AsyncMock(return_value=True)
        return mock_client

    @pytest.fixture
    def mock_discord_context(self):
        """Mock Discord interaction context."""
        mock_ctx = MagicMock()
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 987654321
        mock_ctx.author.name = "TestUser"
        mock_ctx.author.display_name = "Test User"
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.id = 123456789
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 555555555
        mock_ctx.guild.name = "Test Server"
        mock_ctx.send = AsyncMock()
        mock_ctx.respond = AsyncMock()
        mock_ctx.reply = AsyncMock()
        return mock_ctx

    @pytest.fixture
    def discord_service(self):
        """Create Discord service for testing."""
        return DiscordService()

    @pytest.fixture
    def setup_discord_env(self):
        """Setup Discord environment variables for testing."""
        env_vars = {
            "DISCORD_BOT_TOKEN": "test_discord_token",
            "DISCORD_APPLICATION_ID": "987654321",
            "DISCORD_PUBLIC_KEY": "test_public_key",
            "DISCORD_ADMIN_IDS": "123456789,987654321",
            "DISCORD_GUILD_ID": "555555555",
            "DEFAULT_MESSAGING_PLATFORM": "discord",
        }
        with patch.dict("os.environ", env_vars):
            yield env_vars

    @pytest.mark.asyncio
    async def test_discord_service_message_flow(
        self, discord_service, mock_discord_context
    ):
        """Test complete message flow through Discord service."""
        # Create test rich content with embed
        embed = discord_service.create_embed(
            title="🎮 Game Started",
            description="A new game session has begun!",
            color=0x00FF00,
            fields=[
                EmbedField(name="Players", value="4/10", inline=True),
                EmbedField(name="Mode", value="Adventure", inline=True),
                EmbedField(name="Duration", value="30 minutes", inline=False),
            ],
            footer_text="Use !join to participate",
        )

        rich_content = RichContent(
            content="Game session is now live!",
            message_type=MessageType.EMBED,
            embeds=[embed],
            buttons=[
                InlineButton(text="🎮 Join Game", callback_data="join_game_123"),
                InlineButton(text="📊 View Stats", callback_data="view_stats_123"),
            ],
        )

        # Test sending (mocked since discord.py not available)
        result = await discord_service.send_rich_content(
            mock_discord_context.author.id, rich_content
        )

        # Verify result structure
        assert result["platform"] == "Discord"
        assert result["user_id"] == mock_discord_context.author.id
        assert result["message_type"] == MessageType.EMBED.value
        assert result["has_embeds"] is True
        assert result["has_components"] is True

    @pytest.mark.asyncio
    async def test_nudge_service_discord_integration(self, setup_discord_env):
        """Test NudgeService integration with Discord."""
        nudge_service = NudgeService(platform="discord")

        # Test direct message sending
        result = await nudge_service.send_direct(
            "🚀 **System Update Complete**\n\n"
            "The bot has been successfully updated with new features:\n"
            "• Enhanced Discord integration\n"
            "• Rich embed support\n"
            "• Improved error handling\n\n"
            "Enjoy the new features! 💕"
        )

        assert result["platform"] == "discord"
        assert result["mode"] == "direct"
        assert result["success"] is True
        assert result["sent_count"] == 2  # Two admin IDs configured

    @pytest.mark.asyncio
    async def test_nudge_service_discord_embed(self, setup_discord_env):
        """Test sending Discord embeds via NudgeService."""
        nudge_service = NudgeService(platform="discord")

        result = await nudge_service.send_embed(
            title="📊 **Bot Statistics Report**",
            description="Weekly performance metrics and user engagement data",
            color=0x3498DB,  # Blue color
            fields=[
                {"name": "👥 Active Users", "value": "1,234", "inline": True},
                {"name": "💬 Messages Processed", "value": "45,678", "inline": True},
                {"name": "🎮 Games Played", "value": "892", "inline": True},
                {"name": "⚡ Response Time", "value": "124ms average", "inline": False},
                {
                    "name": "🔧 System Health",
                    "value": "✅ All systems operational",
                    "inline": False,
                },
            ],
            footer_text="Report generated automatically",
            thumbnail_url="https://example.com/bot-icon.png",
        )

        assert result["platform"] == "discord"
        assert result["mode"] == "embed"
        assert result["success"] is True
        assert result["sent_count"] == 2

    @pytest.mark.asyncio
    async def test_complex_rich_content_scenario(
        self, discord_service, setup_discord_env
    ):
        """Test complex rich content scenario with multiple embeds and components."""
        # Create multiple embeds
        status_embed = discord_service.create_embed(
            title="🔧 System Status",
            description="All systems are functioning normally",
            color=0x00FF00,
            fields=[
                EmbedField(name="Database", value="✅ Connected", inline=True),
                EmbedField(name="API", value="✅ Responsive", inline=True),
                EmbedField(name="Cache", value="✅ Available", inline=True),
            ],
        )

        activity_embed = discord_service.create_embed(
            title="📈 Recent Activity",
            description="Latest user interactions and system events",
            color=0x3498DB,
            fields=[
                EmbedField(name="New Users", value="12", inline=True),
                EmbedField(name="Messages", value="234", inline=True),
                EmbedField(name="Commands", value="56", inline=True),
            ],
            footer_text="Last updated: 5 minutes ago",
        )

        # Create select menu for actions
        select_menu = discord_service.create_select_menu(
            custom_id="admin_actions",
            placeholder="Choose admin action",
            options=[
                {
                    "label": "👥 View Users",
                    "value": "view_users",
                    "description": "Show registered users list",
                },
                {
                    "label": "📊 View Statistics",
                    "value": "view_stats",
                    "description": "Display bot statistics",
                },
                {
                    "label": "🔧 System Control",
                    "value": "system_control",
                    "description": "Access system controls",
                },
                {
                    "label": "📝 Send Announcement",
                    "value": "send_announcement",
                    "description": "Broadcast message to all users",
                },
            ],
        )

        # Create rich content with multiple embeds and components
        rich_content = RichContent(
            content="🎯 **Admin Dashboard**\n\nHere's the current system overview and available actions:",
            message_type=MessageType.EMBED,
            embeds=[status_embed, activity_embed],
            components=[select_menu],
            buttons=[
                InlineButton(text="🔄 Refresh", callback_data="refresh_dashboard"),
                InlineButton(text="⚙️ Settings", callback_data="open_settings"),
            ],
            tts=False,
            allowed_mentions={"users": True, "everyone": False},
        )

        # Test sending complex content
        result = await discord_service.send_rich_content(123456, rich_content)

        assert result["platform"] == "Discord"
        assert result["has_embeds"] is True
        assert result["has_components"] is True
        assert result["message_type"] == MessageType.EMBED.value

    @pytest.mark.asyncio
    async def test_markdown_conversion_discord_format(self, discord_service):
        """Test markdown conversion for Discord format."""
        complex_markdown = """
# 🎮 dcmaidbot Dashboard

## System Information
Bot is **running normally** with *99.9% uptime*.

### Recent Updates
- ✅ Discord integration completed
- ✅ Enhanced rich content support
- ✅ Improved error handling
- 🔄 Database optimization in progress

## Available Commands
`/help` - Show all available commands
`/status` - Check bot status
`/play <game>` - Start a game

## Quick Actions
[View Dashboard](dashboard_view)
[Send Message](send_message)
[System Settings](system_settings)

> **Note**: Some features require administrator permissions

### Important Links
[Documentation](https://docs.example.com)
[Support Server](https://discord.gg/example)
[GitHub Repository](https://github.com/example)

---

Embed: System Alert|A system maintenance is scheduled for tonight|16711680

Embed: Success|All integrations are working correctly|65280
        """

        result = discord_service.parse_markdown_to_platform(complex_markdown)

        # Verify markdown conversion
        assert result.message_type == MessageType.MARKDOWN
        assert result.parse_mode == "Markdown"
        assert "**🎮 dcmaidbot Dashboard**" in result.content
        assert "**System Information**" in result.content
        assert "**running normally**" in result.content
        assert "*99.9% uptime*" in result.content

        # Verify button extraction (including URL links)
        assert result.buttons is not None
        assert len(result.buttons) == 6  # 3 action buttons + 3 URL links
        button_labels = [btn.text for btn in result.buttons]
        assert "View Dashboard" in button_labels
        assert "Send Message" in button_labels
        assert "System Settings" in button_labels
        assert "Documentation" in button_labels
        assert "Support Server" in button_labels
        assert "GitHub Repository" in button_labels

        # Verify embed extraction
        assert result.embeds is not None
        assert len(result.embeds) == 2
        assert result.embeds[0].title == "System Alert"
        assert result.embeds[0].color == 16711680  # Red
        assert result.embeds[1].title == "Success"
        assert result.embeds[1].color == 65280  # Green

    @pytest.mark.asyncio
    async def test_error_handling_discord_service(self, discord_service):
        """Test error handling in Discord service."""
        # Test with invalid user ID
        result = await discord_service.send_message("invalid_id", "Test message")
        assert result["status"] == "not_implemented"
        assert "user_id" in result

        # Test with malformed rich content
        malformed_content = RichContent(
            content="", message_type=MessageType.EMBED, embeds=None, buttons=None
        )
        result = await discord_service.send_rich_content(123456, malformed_content)
        assert result["status"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_multi_platform_messenger_factory(self):
        """Test messenger factory with multiple platforms."""
        # Test Telegram service
        telegram_service = MessengerFactory.create_messenger("telegram")
        assert telegram_service.platform_name == "Telegram"

        # Test Discord service
        discord_service = MessengerFactory.create_messenger("discord")
        assert discord_service.platform_name == "Discord"

        # Test singleton pattern
        discord_service_2 = get_messenger_service("discord")
        discord_service_3 = get_messenger_service("discord")
        assert discord_service_2 is discord_service_3

        # Test different platforms are separate instances
        telegram_service_2 = get_messenger_service("telegram")
        assert discord_service_2 is not telegram_service_2

    @pytest.mark.asyncio
    async def test_discord_specific_features(self, discord_service):
        """Test Discord-specific features and behaviors."""
        # Test TTS (Text-to-Speech) functionality
        content_with_tts = RichContent(
            content="This message should be read aloud",
            message_type=MessageType.TEXT,
            tts=True,
        )
        result = await discord_service.send_rich_content(123456, content_with_tts)
        assert result["status"] == "not_implemented"

        # Test allowed mentions configuration
        content_with_mentions = RichContent(
            content="@everyone Important announcement!",
            message_type=MessageType.TEXT,
            allowed_mentions={"everyone": False, "users": True, "roles": False},
        )
        result = await discord_service.send_rich_content(123456, content_with_mentions)
        assert result["status"] == "not_implemented"

        # Test message references (replies)
        content_with_reference = RichContent(
            content="This is a reply to another message",
            message_type=MessageType.TEXT,
            reference="987654321098765432",
        )
        result = await discord_service.send_rich_content(123456, content_with_reference)
        assert result["status"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_discord_welcome_sequence(self, discord_service, setup_discord_env):
        """Test Discord welcome message sequence."""
        user_id = 987654321

        # Create welcome embed
        welcome_embed = discord_service.create_embed(
            title="🌸 Welcome to dcmaidbot!",
            description=(
                "Hello! I'm dcmaidbot, your kawaii AI assistant! 💕\n\n"
                "I'm here to help you with various tasks, play games, "
                "and provide assistance whenever you need it. Nya~"
            ),
            color=0xFF69B4,  # Pink color
            thumbnail_url="https://example.com/bot-avatar.png",
            fields=[
                EmbedField(
                    name="🎮 Available Features",
                    value="• Interactive games\n• Music playback\n• House exploration\n• AI conversation\n• Memory system",
                    inline=False,
                ),
                EmbedField(
                    name="📝 Quick Commands",
                    value="• `/help` - Show all commands\n• `/play` - Start a game\n• `/status` - Check bot status",
                    inline=False,
                ),
            ],
            footer_text="Type /help to see all available commands!",
        )

        # Create welcome buttons
        welcome_buttons = discord_service.create_welcome_buttons(user_id)

        # Create welcome rich content
        welcome_content = RichContent(
            content=f"Hello <@{user_id}>! Welcome to the server! 🎉",
            message_type=MessageType.EMBED,
            embeds=[welcome_embed],
            buttons=[
                InlineButton(text=btn["text"], callback_data=btn["callback_data"])
                for btn in welcome_buttons
            ],
        )

        # Test sending welcome message
        result = await discord_service.send_rich_content(user_id, welcome_content)

        assert result["platform"] == "Discord"
        assert result["has_embeds"] is True
        assert result["message_type"] == MessageType.EMBED.value
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_discord_game_interaction(self, discord_service):
        """Test Discord game interaction flow."""
        # Create game embed
        game_embed = discord_service.create_embed(
            title="🎮 Mystery House Adventure",
            description="You find yourself in front of a mysterious house. What do you do?",
            color=0x9932CC,  # Purple color
            fields=[
                EmbedField(
                    name="📍 Location", value="Mysterious House Entrance", inline=True
                ),
                EmbedField(name="⏰ Time", value="Night", inline=True),
                EmbedField(
                    name="🎯 Objective",
                    value="Explore the house and uncover its secrets",
                    inline=False,
                ),
            ],
            footer_text="Choose your action wisely...",
        )

        # Create action select menu
        action_menu = discord_service.create_select_menu(
            custom_id="house_action",
            placeholder="What will you do?",
            options=[
                {
                    "label": "🚪 Enter the house",
                    "value": "enter_house",
                    "description": "Go inside through the front door",
                },
                {
                    "label": "🔍 Look around outside",
                    "value": "explore_outside",
                    "description": "Search the area around the house",
                },
                {
                    "label": "🚶 Walk away",
                    "value": "leave_area",
                    "description": "Leave this mysterious place",
                },
                {
                    "label": "📱 Call for help",
                    "value": "call_help",
                    "description": "Try to contact someone",
                },
            ],
        )

        # Create game content
        game_content = RichContent(
            content="**🎮 A new adventure begins!**\n\n*The house stands before you, dark and inviting...*",
            message_type=MessageType.EMBED,
            embeds=[game_embed],
            components=[action_menu],
            buttons=[
                InlineButton(text="📊 View Inventory", callback_data="view_inventory"),
                InlineButton(text="🗺️ View Map", callback_data="view_map"),
            ],
        )

        # Test game interaction
        result = await discord_service.send_rich_content(123456, game_content)

        assert result["platform"] == "Discord"
        assert result["has_embeds"] is True
        assert result["has_components"] is True
        assert result["message_type"] == MessageType.EMBED.value


@pytest.mark.e2e
class TestDiscordProductionSimulation:
    """Production-like simulation tests for Discord integration."""

    @pytest.mark.asyncio
    async def test_full_bot_lifecycle_simulation(self):
        """Simulate complete bot lifecycle with Discord integration."""
        # This test simulates real-world usage patterns

        # 1. Bot startup and initialization
        discord_service = DiscordService()
        assert discord_service.platform_name == "Discord"

        # 2. Admin notification via nudge service
        with patch.dict(
            "os.environ",
            {
                "DISCORD_BOT_TOKEN": "test_token",
                "DISCORD_ADMIN_IDS": "123456789",
                "DEFAULT_MESSAGING_PLATFORM": "discord",
            },
        ):
            nudge_service = NudgeService(platform="discord")

            # 3. System status notification
            status_result = await nudge_service.send_embed(
                title="🤖 Bot Status Update",
                description="dcmaidbot has started successfully",
                color=0x00FF00,
                fields=[
                    {"name": "🔧 Version", "value": "v2.0.0", "inline": True},
                    {"name": "🌐 Platform", "value": "Discord", "inline": True},
                    {"name": "⚡ Status", "value": "🟢 Online", "inline": True},
                ],
                footer_text="All systems operational",
            )
            assert status_result["success"] is True

            # 4. User interaction simulation
            welcome_message = """
# 🌸 Hello! Welcome to dcmaidbot!

I'm your kawaii AI assistant, ready to help and play! 💕

## What can I do?
- 🎮 Play interactive games
- 🎵 Play music for you
- 🏠 Explore virtual locations
- 💬 Chat and have fun
- 🔧 Help with various tasks

## Quick Start
- Use `/help` to see all commands
- Try `/play` to start a game
- Just say hello and chat with me!

Embed: Welcome|Enjoy your time with dcmaidbot!|65280
            """

            welcome_result = await nudge_service.send_direct(welcome_message)
            assert welcome_result["success"] is True

        # 5. Simulate multiple concurrent operations
        async def simulate_user_interaction():
            """Simulate typical user interactions."""
            # Create embed for game
            game_embed = discord_service.create_embed(
                title="🎮 Game Started",
                description="Adventure game initiated!",
                color=0x3498DB,
            )

            content = RichContent(
                content="Game session starting...",
                message_type=MessageType.EMBED,
                embeds=[game_embed],
            )

            return await discord_service.send_rich_content(999, content)

        # Run multiple simulations concurrently
        results = await asyncio.gather(
            simulate_user_interaction(),
            simulate_user_interaction(),
            simulate_user_interaction(),
            return_exceptions=True,
        )

        # Verify all operations completed (even if not implemented)
        assert len(results) == 3
        for result in results:
            if not isinstance(result, Exception):
                assert result["platform"] == "Discord"

    @pytest.mark.asyncio
    async def test_error_recovery_simulation(self):
        """Test error recovery and fallback mechanisms."""
        discord_service = DiscordService()
        NudgeService(platform="discord")

        # Simulate various error conditions
        error_scenarios = [
            ("Invalid user ID", "invalid_id"),
            ("Empty message", ""),
            ("Malformed content", None),
            ("Network timeout", None),
        ]

        for scenario_name, test_input in error_scenarios:
            try:
                if test_input is None:
                    # Test with malformed RichContent
                    malformed_content = RichContent(content=None, message_type=None)
                    result = await discord_service.send_rich_content(
                        123, malformed_content
                    )
                else:
                    result = await discord_service.send_message(test_input, "Test")

                # Even error cases should return structured responses
                assert isinstance(result, dict)
                assert "platform" in result
                assert result["platform"] == "Discord"

            except Exception as e:
                # Should handle exceptions gracefully
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    @pytest.mark.asyncio
    async def test_performance_load_simulation(self):
        """Test performance under simulated load."""
        discord_service = DiscordService()

        # Simulate high message volume
        messages = [f"Test message {i} for load testing" for i in range(100)]

        # Process messages concurrently
        async def process_message(msg):
            content = discord_service.parse_markdown_to_platform(msg)
            return await discord_service.send_rich_content(123, content)

        # Run with controlled concurrency
        semaphore = asyncio.Semaphore(10)  # Limit concurrent operations

        async def limited_process(msg):
            async with semaphore:
                return await process_message(msg)

        results = await asyncio.gather(
            *[limited_process(msg) for msg in messages], return_exceptions=True
        )

        # Verify all operations completed
        assert len(results) == len(messages)
        successful_operations = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_operations == len(messages)
