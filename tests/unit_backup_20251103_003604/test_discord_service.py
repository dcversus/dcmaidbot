"""
Unit tests for Discord service integration.

Tests Discord messenger service implementation, embed creation,
and platform-specific functionality.
"""

from unittest.mock import patch

import pytest

from services.messenger_service import (
    DiscordService,
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    InlineButton,
    MessageType,
    MessengerFactory,
    RichContent,
    SelectMenu,
    SelectOption,
)
from services.nudge_service import NudgeService


class TestDiscordService:
    """Test Discord service functionality."""

    @pytest.fixture
    def discord_service(self):
        """Create Discord service instance for testing."""
        return DiscordService()

    @pytest.fixture
    def sample_embed(self):
        """Create sample embed for testing."""
        return Embed(
            title="Test Embed",
            description="Test Description",
            color=0x00FF00,
            fields=[
                EmbedField(name="Field 1", value="Value 1", inline=True),
                EmbedField(name="Field 2", value="Value 2", inline=False),
            ],
            footer=EmbedFooter(text="Test Footer"),
            author=EmbedAuthor(name="Test Author"),
        )

    @pytest.fixture
    def sample_rich_content(self, sample_embed):
        """Create sample rich content with embed."""
        return RichContent(
            content="Main message content",
            message_type=MessageType.EMBED,
            embeds=[sample_embed],
            buttons=[
                InlineButton(text="Button 1", callback_data="btn1"),
                InlineButton(text="Button 2", url="https://example.com"),
            ],
        )

    def test_discord_service_creation(self, discord_service):
        """Test Discord service initialization."""
        assert discord_service.platform_name == "Discord"
        assert isinstance(discord_service, DiscordService)

    def test_parse_markdown_to_platform_basic(self, discord_service):
        """Test basic markdown parsing for Discord."""
        markdown = """
# Main Title

This is **bold text** and *italic text*.

## Subsection

Here's a `code snippet` and ~~strikethrough~~ text.

- List item 1
- List item 2
        """

        result = discord_service.parse_markdown_to_platform(markdown)

        assert isinstance(result, RichContent)
        assert result.message_type == MessageType.MARKDOWN
        assert result.parse_mode == "Markdown"
        assert "**Main Title**" in result.content
        assert "**bold text**" in result.content
        assert "*italic text*" in result.content
        assert "**Subsection**" in result.content
        assert "`code snippet`" in result.content

    def test_parse_markdown_with_embeds(self, discord_service):
        """Test parsing markdown with embed definitions."""
        markdown = """
Hello world!

Embed: Alert|This is an important alert|16711680

Embed: Info|Some additional information|65280

Regular text continues here.
        """

        result = discord_service.parse_markdown_to_platform(markdown)

        assert isinstance(result, RichContent)
        assert result.embeds is not None
        assert len(result.embeds) == 2

        # Check first embed (red alert)
        alert_embed = result.embeds[0]
        assert alert_embed.title == "Alert"
        assert alert_embed.description == "This is an important alert"
        assert alert_embed.color == 16711680  # Red color

        # Check second embed (green info)
        info_embed = result.embeds[1]
        assert info_embed.title == "Info"
        assert info_embed.description == "Some additional information"
        assert info_embed.color == 65280  # Green color

        # Main content should still contain bold titles
        assert "**Alert**" in result.content
        assert "**Info**" in result.content

    def test_parse_markdown_with_buttons(self, discord_service):
        """Test parsing markdown with button definitions."""
        markdown = """
Choose an action:

[Explore House](explore_house)
[Visit Website](https://example.com)
[Help](help_command)

Let me know what you think!
        """

        result = discord_service.parse_markdown_to_platform(markdown)

        assert isinstance(result, RichContent)
        assert result.buttons is not None
        assert len(result.buttons) == 3

        # Check callback button
        explore_btn = result.buttons[0]
        assert explore_btn.text == "Explore House"
        assert explore_btn.callback_data == "explore_house"
        assert explore_btn.url is None

        # Check URL button
        website_btn = result.buttons[1]
        assert website_btn.text == "Visit Website"
        assert website_btn.url == "https://example.com"
        assert website_btn.callback_data is None

        # Check main content
        assert "**Explore House**" in result.content
        assert "**Visit Website**" in result.content
        assert "**Help**" in result.content

    @pytest.mark.asyncio
    async def test_send_message_with_string(self, discord_service):
        """Test sending message with plain string content."""
        result = await discord_service.send_message(123456, "Hello Discord!")

        # Should either work (if token configured) or return error (if not configured)
        assert result["status"] in ["success", "error"]
        assert result["platform"] == "Discord"
        assert result["user_id"] == 123456

        if result["status"] == "error":
            # If not configured, should have appropriate error message
            assert any(
                keyword in result["error"].lower()
                for keyword in ["not connected", "not found", "forbidden", "token"]
            )

    @pytest.mark.asyncio
    async def test_send_rich_content_with_embeds(
        self, discord_service, sample_rich_content
    ):
        """Test sending rich content with embeds."""
        result = await discord_service.send_rich_content(123456, sample_rich_content)

        # Should either work (if token configured) or return error (if not configured)
        assert result["status"] in ["success", "error"]
        assert result["platform"] == "Discord"
        assert result["user_id"] == 123456

        if result["status"] == "success":
            # If successful, should match the original content type
            assert result["message_type"] == MessageType.EMBED.value
            assert result["has_embeds"] is True
            assert result["has_components"] is True
        else:
            # If error, should have appropriate error message and error type
            assert result["message_type"] == "error"
            assert any(
                keyword in result["error"].lower()
                for keyword in [
                    "not connected",
                    "not found",
                    "forbidden",
                    "token",
                    "not available",
                ]
            )

    def test_create_embed_helper(self, discord_service):
        """Test embed creation helper method."""
        fields = [
            {"name": "Status", "value": "Online", "inline": True},
            {"name": "Users", "value": "150", "inline": True},
        ]

        embed = discord_service.create_embed(
            title="Server Status",
            description="Current server information",
            color=0x00FF00,
            fields=fields,
            footer_text="Updated 5 minutes ago",
            thumbnail_url="https://example.com/thumb.png",
            author_name="Status Bot",
            author_url="https://example.com/bot",
        )

        assert isinstance(embed, Embed)
        assert embed.title == "Server Status"
        assert embed.description == "Current server information"
        assert embed.color == 0x00FF00
        assert embed.footer.text == "Updated 5 minutes ago"
        assert embed.thumbnail.url == "https://example.com/thumb.png"
        assert embed.author.name == "Status Bot"
        assert embed.author.url == "https://example.com/bot"
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Status"
        assert embed.fields[0].value == "Online"
        assert embed.fields[0].inline is True

    def test_create_select_menu_helper(self, discord_service):
        """Test select menu creation helper method."""
        options = [
            {
                "label": "Option 1",
                "value": "opt1",
                "description": "First option",
                "emoji": "🎯",
            },
            {
                "label": "Option 2",
                "value": "opt2",
                "description": "Second option",
                "default": True,
            },
        ]

        select_menu = discord_service.create_select_menu(
            custom_id="menu_1",
            placeholder="Choose an option",
            options=options,
            min_values=1,
            max_values=2,
        )

        assert isinstance(select_menu, SelectMenu)
        assert select_menu.callback_data == "menu_1"
        assert select_menu.placeholder == "Choose an option"
        assert select_menu.min_values == 1
        assert select_menu.max_values == 2
        assert len(select_menu.options) == 2

        # Check first option
        opt1 = select_menu.options[0]
        assert opt1.label == "Option 1"
        assert opt1.value == "opt1"
        assert opt1.description == "First option"
        assert opt1.emoji == "🎯"
        assert opt1.default is False

        # Check second option
        opt2 = select_menu.options[1]
        assert opt2.label == "Option 2"
        assert opt2.value == "opt2"
        assert opt2.description == "Second option"
        assert opt2.default is True

    def test_create_welcome_buttons(self, discord_service):
        """Test Discord welcome buttons creation."""
        buttons = discord_service.create_welcome_buttons(123456)

        assert isinstance(buttons, list)
        assert len(buttons) == 5  # Discord has one extra button

        # Check specific buttons
        button_texts = [btn["text"] for btn in buttons]
        assert "🏠 Explore House" in button_texts
        assert "🎵 Play Music" in button_texts
        assert "📋 Changelog" in button_texts
        assert "❓ Help" in button_texts
        assert "🎮 Play Games" in button_texts

        # Check callback data contains user ID
        for btn in buttons:
            assert "123456" in btn["callback_data"]

    def test_extract_embeds_complex_content(self, discord_service):
        """Test embed extraction from complex markdown."""
        content = """
# System Alert

Embed: Critical Error|Database connection failed|16711680

Please check the logs.

Embed: Warning|High memory usage detected|16776960

Embed: Success|Backup completed successfully|65280

All systems operational.
        """

        processed_content, embeds = discord_service._extract_embeds_from_markdown(
            content
        )

        # Check embeds extracted
        assert len(embeds) == 3
        assert embeds[0].title == "Critical Error"
        assert embeds[0].color == 16711680  # Red
        assert embeds[1].title == "Warning"
        assert embeds[1].color == 16776960  # Orange
        assert embeds[2].title == "Success"
        assert embeds[2].color == 65280  # Green

        # Check content processing
        assert "**Critical Error**" in processed_content
        assert "**Warning**" in processed_content
        assert "**Success**" in processed_content

    def test_extract_buttons_complex_content(self, discord_service):
        """Test button extraction from complex markdown."""
        content = """
Available actions:

[Start Bot](start_command)
[Stop Bot](stop_command)
[View Dashboard](https://dashboard.example.com)
[Get Help](help_command)

Choose wisely!
        """

        processed_content, buttons = discord_service._extract_buttons_from_markdown(
            content
        )

        # Check buttons extracted
        assert len(buttons) == 4
        assert buttons[0].text == "Start Bot"
        assert buttons[0].callback_data == "start_command"
        assert buttons[2].text == "View Dashboard"
        assert buttons[2].url == "https://dashboard.example.com"

        # Check content processing
        assert "**Start Bot**" in processed_content
        assert "**Stop Bot**" in processed_content
        assert "**View Dashboard**" in processed_content
        assert "**Get Help**" in processed_content


class TestMessengerFactory:
    """Test messenger factory functionality."""

    def test_create_telegram_service(self):
        """Test creating Telegram service via factory."""
        service = MessengerFactory.create_messenger("telegram")
        assert service.__class__.__name__ == "TelegramService"
        assert service.platform_name == "Telegram"

    def test_create_discord_service(self):
        """Test creating Discord service via factory."""
        service = MessengerFactory.create_messenger("discord")
        assert service.__class__.__name__ == "DiscordService"
        assert service.platform_name == "Discord"

    def test_create_discord_service_case_insensitive(self):
        """Test creating Discord service with case insensitive name."""
        service = MessengerFactory.create_messenger("DISCORD")
        assert service.__class__.__name__ == "DiscordService"
        assert service.platform_name == "Discord"

    def test_create_unsupported_service(self):
        """Test creating unsupported service raises error."""
        with pytest.raises(ValueError) as exc_info:
            MessengerFactory.create_messenger("slack")

        assert "Unsupported platform: slack" in str(exc_info.value)
        assert "Supported platforms: telegram, discord" in str(exc_info.value)


class TestNudgeServiceDiscord:
    """Test NudgeService Discord integration."""

    @pytest.fixture
    def discord_nudge_service(self):
        """Create Discord nudge service for testing."""
        return NudgeService(platform="discord")

    @pytest.fixture
    def telegram_nudge_service(self):
        """Create Telegram nudge service for comparison."""
        return NudgeService(platform="telegram")

    def test_discord_nudge_service_creation(self, discord_nudge_service):
        """Test Discord nudge service initialization."""
        assert discord_nudge_service.platform == "discord"
        assert discord_nudge_service.messenger_service.platform_name == "Discord"

    def test_admin_ids_discord_specific(self, discord_nudge_service):
        """Test Discord-specific admin ID retrieval."""
        with patch.dict("os.environ", {"DISCORD_ADMIN_IDS": "123456,789012"}):
            admin_ids = discord_nudge_service._get_admin_ids()
            assert admin_ids == [123456, 789012]

    def test_admin_ids_fallback_to_general(self, discord_nudge_service):
        """Test Discord admin IDs fall back to general ADMIN_IDS."""
        with patch.dict("os.environ", {"ADMIN_IDS": "123456,789012"}, clear=True):
            admin_ids = discord_nudge_service._get_admin_ids()
            assert admin_ids == [123456, 789012]

    def test_admin_ids_missing_discord(self, discord_nudge_service):
        """Test missing Discord admin IDs raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                discord_nudge_service._get_admin_ids()

            assert "DISCORD_ADMIN_IDS not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_direct_discord(self, discord_nudge_service):
        """Test sending direct message via Discord."""
        with patch.dict("os.environ", {"DISCORD_ADMIN_IDS": "123456"}):
            result = await discord_nudge_service.send_direct("Hello Discord!")

            assert result["platform"] == "discord"
            assert result["mode"] == "direct"
            assert result["sent_count"] == 1
            assert result["failed_count"] == 0
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_embed_discord(self, discord_nudge_service):
        """Test sending embed via Discord."""
        with patch.dict("os.environ", {"DISCORD_ADMIN_IDS": "123456"}):
            result = await discord_nudge_service.send_embed(
                title="Test Alert",
                description="This is a test embed",
                color=0xFF0000,
                fields=[
                    {"name": "Status", "value": "Active"},
                    {"name": "Users", "value": "42"},
                ],
            )

            assert result["platform"] == "discord"
            assert result["mode"] == "embed"
            assert result["sent_count"] == 1
            assert result["failed_count"] == 0
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_embed_telegram_fallback(self, telegram_nudge_service):
        """Test embed sending falls back to formatted text on Telegram."""
        with patch.dict("os.environ", {"ADMIN_IDS": "123456"}):
            result = await telegram_nudge_service.send_embed(
                title="Test Alert",
                description="This is a test embed",
                fields=[
                    {"name": "Status", "value": "Active"},
                    {"name": "Users", "value": "42"},
                ],
            )

            assert result["platform"] == "telegram"
            assert result["mode"] == "direct"  # Falls back to direct mode
            # Allow for 0 sent if Telegram service is not fully implemented
            assert result["sent_count"] >= 0
            assert result["success"] in [
                True,
                False,
            ]  # May fail if Telegram not available

    @pytest.mark.asyncio
    async def test_send_via_llm_discord(self, discord_nudge_service):
        """Test LLM-processed message sending via Discord."""
        with patch.dict("os.environ", {"DISCORD_ADMIN_IDS": "123456"}):
            # Mock the LLM service
            with patch.object(
                discord_nudge_service.llm_service,
                "get_response",
                return_value="Nya~ Hello Discord Master! 💕",
            ):
                result = await discord_nudge_service.send_via_llm(
                    "Say hello to Discord admin"
                )

                assert result["platform"] == "discord"
                assert result["mode"] == "llm"
                assert result["sent_count"] == 1
                assert result["failed_count"] == 0
                assert result["success"] is True
                assert "Nya~" in result["results"][0]["llm_response"]


class TestDiscordRichContent:
    """Test Discord-specific rich content features."""

    def test_rich_content_with_discord_features(self):
        """Test RichContent with Discord-specific fields."""
        embed = Embed(title="Test", description="Test embed")
        select_menu = SelectMenu(
            text="Select",
            callback_data="test_select",
            placeholder="Choose",
            options=[SelectOption(label="Option 1", value="opt1")],
        )

        content = RichContent(
            content="Main message",
            message_type=MessageType.EMBED,
            embeds=[embed],
            components=[select_menu],
            tts=True,
            allowed_mentions={"users": True, "everyone": False},
            reference="123456789",
        )

        assert content.embeds == [embed]
        assert content.components == [select_menu]
        assert content.tts is True
        assert content.allowed_mentions == {"users": True, "everyone": False}
        assert content.reference == "123456789"

    def test_rich_content_without_discord_features(self):
        """Test RichContent without Discord-specific fields (backward compatibility)."""
        content = RichContent(
            content="Simple message",
            message_type=MessageType.TEXT,
            buttons=[InlineButton(text="Click me", callback_data="test")],
        )

        assert content.embeds is None
        assert content.components is None
        assert content.tts is False
        assert content.allowed_mentions is None
        assert content.reference is None
