"""
Abstract Messenger Service
=======================

Provides abstraction layer for different messaging platforms
with rich content rendering capabilities.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Import Telegram Bot types only when needed
try:
    from aiogram import Bot, types

    TELEGRAM_AVAILABLE = True
except ImportError:
    Bot = None
    types = None
    TELEGRAM_AVAILABLE = False


class MessageType(Enum):
    """Supported message types for rich content."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"
    VENUE = "venue"
    AUDIO = "audio"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    STICKER = "sticker"
    # Discord-specific types
    EMBED = "embed"
    SLASH_COMMAND = "slash_command"
    COMPONENT = "component"
    MODAL = "modal"
    SELECT_MENU = "select_menu"


@dataclass
class Button:
    """Base button class for rich content."""

    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None


@dataclass
class InlineButton(Button):
    """Inline keyboard button."""

    pass


@dataclass
class ReplyButton(Button):
    """Reply keyboard button."""

    pass


# Discord-specific component types
@dataclass
class EmbedField:
    """Discord embed field."""

    name: str
    value: str
    inline: bool = False


@dataclass
class EmbedFooter:
    """Discord embed footer."""

    text: str
    icon_url: Optional[str] = None


@dataclass
class EmbedAuthor:
    """Discord embed author."""

    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None


@dataclass
class EmbedThumbnail:
    """Discord embed thumbnail."""

    url: str


@dataclass
class EmbedImage:
    """Discord embed image."""

    url: str


@dataclass
class Embed:
    """Discord embed structure."""

    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None  # Discord color integer
    timestamp: Optional[str] = None
    footer: Optional[EmbedFooter] = None
    image: Optional[EmbedImage] = None
    thumbnail: Optional[EmbedThumbnail] = None
    author: Optional[EmbedAuthor] = None
    fields: Optional[List[EmbedField]] = None


@dataclass
class SelectOption:
    """Discord select menu option."""

    label: str
    value: str
    description: Optional[str] = None
    emoji: Optional[str] = None
    default: bool = False


@dataclass
class SelectMenu(Button):
    """Discord select menu component."""

    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    placeholder: str = ""
    options: Optional[List[SelectOption]] = None
    min_values: int = 1
    max_values: int = 1

    def __post_init__(self):
        if self.options is None:
            self.options = []


@dataclass
class ModalTextInput:
    """Discord modal text input component."""

    custom_id: str
    label: str
    style: str = "short"  # "short" or "paragraph"
    placeholder: Optional[str] = None
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class Modal:
    """Discord modal structure."""

    custom_id: str
    title: str
    components: List[ModalTextInput]


@dataclass
class RichContent:
    """Rich content container with text and interactive elements."""

    content: str
    message_type: MessageType
    buttons: Optional[List[InlineButton]] = None
    reply_buttons: Optional[List[ReplyButton]] = None
    media_url: Optional[str] = None
    media_type: Optional[MessageType] = None
    parse_mode: str = "HTML"
    disable_web_page_preview: bool = False
    disable_notification: bool = False
    # Discord-specific fields
    embeds: Optional[List[Embed]] = None
    components: Optional[List[Union[SelectMenu, Button]]] = None
    modal: Optional[Modal] = None
    tts: bool = False
    allowed_mentions: Optional[Dict[str, Any]] = None
    reference: Optional[str] = None  # Message reference ID for replies


class MessengerService(ABC):
    """Abstract base class for messenger services."""

    def __init__(self):
        self.platform_name = self.__class__.__name__

    @abstractmethod
    async def send_message(
        self, user_id: int, content: Union[str, RichContent], **kwargs
    ) -> Dict[str, Any]:
        """Send message to user."""
        pass

    @abstractmethod
    async def send_rich_content(
        self, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send rich content message to user."""
        pass

    @abstractmethod
    def parse_markdown_to_platform(self, markdown: str) -> RichContent:
        """Parse markdown into platform-specific rich content."""
        pass

    def parse_markdown_to_telegram(self, markdown: str) -> RichContent:
        """Parse markdown into Telegram-compatible rich content (legacy method)."""
        return self.parse_markdown_to_platform(markdown)

    def create_embed(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[List[Union[EmbedField, Dict[str, Any]]]] = None,
        footer_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
        **kwargs,
    ) -> Embed:
        """Create Discord embed from parameters."""
        # Convert field dictionaries to EmbedField objects
        embed_fields = None
        if fields:
            embed_fields = []
            for field in fields:
                if isinstance(field, dict):
                    embed_field = EmbedField(
                        name=field.get("name", ""),
                        value=field.get("value", ""),
                        inline=field.get("inline", False),
                    )
                    embed_fields.append(embed_field)
                else:
                    embed_fields.append(field)

        embed = Embed(
            title=title, description=description, color=color, fields=embed_fields
        )

        if footer_text:
            embed.footer = EmbedFooter(text=footer_text)
        if thumbnail_url:
            embed.thumbnail = EmbedThumbnail(url=thumbnail_url)
        if image_url:
            embed.image = EmbedImage(url=image_url)
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
        """Create Discord select menu from options."""
        select_options = []
        for opt in options:
            select_option = SelectOption(
                label=opt.get("label", ""),
                value=opt.get("value", ""),
                description=opt.get("description"),
                emoji=opt.get("emoji"),
                default=opt.get("default", False),
            )
            select_options.append(select_option)

        return SelectMenu(
            text=placeholder,  # Use placeholder as button text for compatibility
            callback_data=custom_id,
            placeholder=placeholder,
            options=select_options,
            min_values=min_values,
            max_values=max_values,
        )

    def build_inline_keyboard(
        self, buttons: List[Dict[str, str]]
    ) -> Optional[List[List[InlineButton]]]:
        """Build inline keyboard from button definitions."""
        if not buttons:
            return None

        keyboard = []
        row = []

        for button in buttons:
            inline_btn = InlineButton(
                text=button.get("text", ""),
                callback_data=button.get("callback_data"),
                url=button.get("url"),
            )
            row.append(inline_btn)

            if len(row) >= 3:  # Telegram inline keyboard max 3 buttons per row
                keyboard.append(row)
                row = []

        if row:  # Add remaining buttons
            keyboard.append(row)

        return keyboard if keyboard else None

    def create_welcome_buttons(self, user_id: int) -> List[Dict[str, str]]:
        """Create standard welcome buttons for the platform."""
        return [
            {"text": "🏠 Explore House", "callback_data": f"explore_house_{user_id}"},
            {"text": "🎵 Play Music", "callback_data": f"play_music_{user_id}"},
            {"text": "📋 Changelog", "callback_data": f"changelog_{user_id}"},
            {"text": "❓ Help", "callback_data": f"help_{user_id}"},
        ]

    def create_action_buttons(
        self, actions: List[Dict[str, Any]], user_id: int
    ) -> List[Dict[str, str]]:
        """Create action buttons from action definitions."""
        buttons = []

        for action in actions:
            button = {
                "text": action.get("text", "Action"),
                "callback_data": action.get("callback_data", f"action_{user_id}"),
            }

            if action.get("url"):
                button["url"] = action["url"]

            buttons.append(button)

        return buttons


class TelegramService(MessengerService):
    """Telegram-specific messenger service implementation."""

    def __init__(self):
        super().__init__()
        self.platform_name = "Telegram"

    async def send_message(
        self, user_id: int, content: Union[str, RichContent], **kwargs
    ) -> Dict[str, Any]:
        """Send message via Telegram Bot API."""
        if isinstance(content, str):
            # Convert plain text to RichContent
            rich_content = self.parse_markdown_to_telegram(content)
        else:
            rich_content = content

        return await self.send_rich_content(user_id, rich_content, **kwargs)

    async def send_rich_content(
        self, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send rich content message via Telegram."""
        from bot import bot  # Import existing bot instance

        try:
            if rich_content.message_type in [
                MessageType.PHOTO,
                MessageType.VIDEO,
                MessageType.DOCUMENT,
                MessageType.AUDIO,
            ]:
                # Handle media messages
                return await self._send_media_message(
                    bot, user_id, rich_content, **kwargs
                )
            else:
                # Handle text/keyboard messages
                return await self._send_text_message(
                    bot, user_id, rich_content, **kwargs
                )

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to send Telegram message: {str(e)}",
                "user_id": user_id,
                "platform": "Telegram",
            }

    async def _send_text_message(
        self, bot: Any, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send text message with optional inline keyboard."""
        try:
            # Build inline keyboard if present
            reply_markup = None
            if rich_content.buttons:
                reply_markup = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            {
                                "text": btn.text,
                                "callback_data": btn.callback_data,
                                "url": btn.url,
                            }
                            for btn in row
                        ]
                        for row in self._chunk_buttons(rich_content.buttons, 3)
                    ]
                )

            # Send message
            message = await bot.send_message(
                chat_id=user_id,
                text=rich_content.content,
                parse_mode=rich_content.parse_mode,
                disable_web_page_preview=rich_content.disable_web_page_preview,
                disable_notification=rich_content.disable_notification,
                reply_markup=reply_markup,
                **kwargs,
            )

            return {
                "status": "success",
                "message_id": message.message_id,
                "user_id": user_id,
                "platform": "Telegram",
                "content_length": len(rich_content.content),
                "has_buttons": bool(rich_content.buttons),
                "buttons_count": len(rich_content.buttons)
                if rich_content.buttons
                else 0,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to send Telegram text message: {str(e)}",
                "user_id": user_id,
                "platform": "Telegram",
            }

    async def _send_media_message(
        self, bot: Any, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send media message (photo, video, etc.)."""
        try:
            media_kwargs = {
                "chat_id": user_id,
                "caption": rich_content.content,
                "parse_mode": rich_content.parse_mode,
                "disable_notification": rich_content.disable_notification,
            }

            # Add inline keyboard if present
            if rich_content.buttons:
                media_kwargs["reply_markup"] = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            {
                                "text": btn.text,
                                "callback_data": btn.callback_data,
                                "url": btn.url,
                            }
                            for btn in row
                        ]
                        for row in self._chunk_buttons(rich_content.buttons, 2)
                    ]
                )

            # Send based on media type
            if rich_content.message_type == MessageType.PHOTO:
                message = await bot.send_photo(
                    photo=rich_content.media_url, **media_kwargs
                )
            elif rich_content.message_type == MessageType.VIDEO:
                message = await bot.send_video(
                    video=rich_content.media_url, **media_kwargs
                )
            elif rich_content.message_type == MessageType.DOCUMENT:
                message = await bot.send_document(
                    document=rich_content.media_url, **media_kwargs
                )
            elif rich_content.message_type == MessageType.AUDIO:
                message = await bot.send_audio(
                    audio=rich_content.media_url, **media_kwargs
                )
            else:
                # Fallback to text message
                return await self._send_text_message(
                    bot, user_id, rich_content, **kwargs
                )

            return {
                "status": "success",
                "message_id": message.message_id,
                "user_id": user_id,
                "platform": "Telegram",
                "media_type": rich_content.message_type.value,
                "content_length": len(rich_content.content),
                "has_media": bool(rich_content.media_url),
                "has_buttons": bool(rich_content.buttons),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to send Telegram media message: {str(e)}",
                "user_id": user_id,
                "platform": "Telegram",
            }

    def _chunk_buttons(
        self, buttons: List[InlineButton], chunk_size: int
    ) -> List[List[InlineButton]]:
        """Chunk buttons into rows for Telegram."""
        if not buttons:
            return []

        chunks = []
        for i in range(0, len(buttons), chunk_size):
            chunk = buttons[i : i + chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks

    def parse_markdown_to_platform(self, markdown: str) -> RichContent:
        """Parse markdown into Telegram-compatible rich content."""
        # Handle common markdown patterns
        content = markdown

        # Convert headers
        content = self._convert_headers(content)

        # Convert bold/italic/underline
        content = self._convert_formatting(content)

        # Convert links
        content = self._convert_links(content)

        # Convert code blocks
        content = self._convert_code_blocks(content)

        # Convert lists
        content = self._convert_lists(content)

        # Extract buttons from markdown if present
        content, buttons = self._extract_buttons_from_markdown(content)

        return RichContent(
            content=content,
            message_type=MessageType.MARKDOWN,
            buttons=buttons,
            parse_mode="HTML",  # Telegram supports HTML with limited styling
        )

    def _convert_headers(self, content: str) -> str:
        """Convert markdown headers to bold text."""
        import re

        # H1 -> Bold large text
        content = re.sub(r"^# (.+)$", r"<b>\1</b>", content, flags=re.MULTILINE)

        # H2 -> Bold medium text
        content = re.sub(r"^## (.+)$", r"<b>\1</b>", content, flags=re.MULTILINE)

        # H3 -> Bold small text
        content = re.sub(r"^### (.+)$", r"<b>\1</b>", content, flags=re.MULTILINE)

        return content

    def _convert_formatting(self, content: str) -> str:
        """Convert markdown formatting to HTML."""
        # Bold - use proper replacement to avoid double replacement
        content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", content)

        # Italic - avoid replacing inside bold tags
        content = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?!\*)", r"<i>\1</i>", content)

        # Code (inline)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)

        # Strikethrough
        content = re.sub(r"~~(.*?)~~", r"<s>\1</s>", content)

        # Underline (Telegram doesn't support, so remove)
        content = re.sub(r"__(.*?)__", r"\1", content)

        return content

    def _convert_links(self, content: str) -> str:
        """Convert markdown links to HTML."""
        # Regular links: [text](url)
        content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', content)

        return content

    def _convert_code_blocks(self, content: str) -> str:
        """Convert markdown code blocks to HTML."""
        # Code blocks: ```language\ncode\n```
        content = re.sub(
            r"```(\w+)?\n(.*?)\n```",
            lambda m: f"<pre><code>{m.group(2) or ''}</code></pre>",
            content,
            flags=re.DOTALL,
        )

        # Inline code: `code` (skip this since it's handled in _convert_formatting)
        # This prevents double conversion

        return content

    def _convert_lists(self, content: str) -> str:
        """Convert markdown lists to HTML."""
        lines = content.split("\n")
        result = []
        in_list = False
        list_type = None

        for line in lines:
            if line.strip().startswith("- "):
                # Unordered list
                if not in_list:
                    in_list = True
                    list_type = "ul"
                result.append(f"<li>{line.strip()[2:]}</li>")
            elif line.strip().startswith(("* ")):
                # Alternative unordered list
                if not in_list:
                    in_list = True
                    list_type = "ul"
                result.append(f"<li>{line.strip()[2:]}</li>")
            elif re.match(r"^\d+\. ", line.strip()):
                # Ordered list
                if not in_list:
                    in_list = True
                    list_type = "ol"
                space_index = line.strip().find(" ")
                result.append(f"<li>{line.strip()[space_index + 1 :]}</li>")
            elif line.strip() == "" and in_list:
                # End of list
                if list_type == "ul":
                    result.append("</ul>")
                else:
                    result.append("</ol>")
                in_list = False
                list_type = None
            else:
                # Regular line
                result.append(line)

        return "\n".join(result)

    def _extract_buttons_from_markdown(
        self, content: str
    ) -> tuple[str, Optional[List[InlineButton]]]:
        """Extract button definitions from markdown content."""
        import re

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
            return f"<b>{button_text}</b>"  # Keep button text visible

        # Replace button markdown with bold text (buttons will be added to inline keyboard)
        processed_content = re.sub(button_pattern, replace_button, content)

        return processed_content, buttons if buttons else None


class DiscordService(MessengerService):
    """Discord-specific messenger service implementation."""

    def __init__(self):
        super().__init__()
        # Import the actual Discord service implementation
        try:
            from services.discord_service import DiscordService as DiscordServiceImpl

            self._impl = DiscordServiceImpl()
        except ImportError as e:
            logger.warning(f"Discord service implementation not available: {e}")
            self._impl = None
        self.platform_name = "Discord"

    async def send_message(
        self, user_id: int, content: Union[str, RichContent], **kwargs
    ) -> Dict[str, Any]:
        """Send message via Discord Bot API."""
        if self._impl:
            return await self._impl.send_message(user_id, content, **kwargs)

        # Fallback to placeholder if implementation not available
        if isinstance(content, str):
            rich_content = self.parse_markdown_to_platform(content)
        else:
            rich_content = content

        return await self.send_rich_content(user_id, rich_content, **kwargs)

    async def send_rich_content(
        self, user_id: int, rich_content: RichContent, **kwargs
    ) -> Dict[str, Any]:
        """Send rich content message via Discord."""
        if self._impl:
            return await self._impl.send_rich_content(user_id, rich_content, **kwargs)

        # Fallback placeholder response
        return {
            "status": "error",
            "error": "Discord service implementation not available",
            "user_id": user_id,
            "platform": "Discord",
            "message_type": rich_content.message_type.value,
            "has_embeds": bool(rich_content.embeds),
            "has_components": bool(rich_content.components)
            or bool(rich_content.buttons),
        }

    def parse_markdown_to_platform(self, markdown: str) -> RichContent:
        """Parse markdown into Discord-compatible rich content."""
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

    def create_welcome_buttons(self, user_id: int) -> List[Dict[str, str]]:
        """Create standard welcome buttons for Discord."""
        return [
            {"text": "🏠 Explore House", "callback_data": f"explore_house_{user_id}"},
            {"text": "🎵 Play Music", "callback_data": f"play_music_{user_id}"},
            {"text": "📋 Changelog", "callback_data": f"changelog_{user_id}"},
            {"text": "❓ Help", "callback_data": f"help_{user_id}"},
            {"text": "🎮 Play Games", "callback_data": f"play_games_{user_id}"},
        ]


class MessengerFactory:
    """Factory for creating messenger service instances."""

    @staticmethod
    def create_messenger(platform: str = "telegram") -> MessengerService:
        """Create messenger service instance for specified platform."""
        if platform.lower() == "telegram":
            return TelegramService()
        elif platform.lower() == "discord":
            return DiscordService()
        else:
            raise ValueError(
                f"Unsupported platform: {platform}. Supported platforms: telegram, discord"
            )


# Singleton instances for easy access (one per platform)
_messenger_services = {}


def get_messenger_service(platform: str = "telegram") -> MessengerService:
    """Get or create messenger service instance (singleton pattern per platform)."""
    global _messenger_services
    if platform not in _messenger_services:
        _messenger_services[platform] = MessengerFactory.create_messenger(platform)
    return _messenger_services[platform]
