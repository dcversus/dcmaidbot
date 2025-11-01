"""Shared markdown rendering utility for all platforms.

This utility provides consistent markdown formatting across Telegram,
Discord, and other messaging platforms with proper visual hierarchy
using emojis, bold text, and structured formatting.
"""

import re
from enum import Enum
from typing import Dict, List


class Platform(Enum):
    """Supported messaging platforms."""

    TELEGRAM = "telegram"
    DISCORD = "discord"
    GENERIC = "generic"


class MarkdownRenderer:
    """Universal markdown renderer with platform-specific optimizations."""

    # Platform-specific formatting patterns
    PLATFORM_PATTERNS = {
        Platform.TELEGRAM: {
            "bold": "*",
            "italic": "_",
            "code": "`",
            "code_block": "```",
            "strike": "~",
        },
        Platform.DISCORD: {
            "bold": "**",
            "italic": "*",
            "code": "`",
            "code_block": "```",
            "strike": "~~",
        },
        Platform.GENERIC: {
            "bold": "*",
            "italic": "_",
            "code": "`",
            "code_block": "```",
            "strike": "~",
        },
    }

    # Visual hierarchy emojis for different levels
    HIERARCHY_EMOJIS = [
        "🎯",  # Target/Goal
        "🚀",  # Rocket/Launch
        "⭐",  # Star/Important
        "✨",  # Sparkles/New
        "🎨",  # Art/Design
        "🔧",  # Wrench/Technical
        "📋",  # Clipboard/List
        "🎪",  # Tent/Event
        "🎭",  # Masks/Performance
        "🎪",  # Tent/Fun
    ]

    # Status emojis
    STATUS_EMOJIS = {
        "success": ["✅", "🎉", "🚀", "⭐", "🏆"],
        "warning": ["⚠️", "🔥", "💥", "⚡"],
        "error": ["❌", "🚫", "💔", "👻"],
        "info": ["ℹ️", "💡", "📢", "🔔"],
        "new": ["🆕", "✨", "🎉", "🌟"],
        "improved": ["⬆️", "📈", "🚀", "💪"],
        "fixed": ["🔧", "🛠️", "✅", "🎯"],
        "added": ["➕", "🆕", "📝", "🎁"],
        "removed": ["➖", "🗑️", "❌", "🚫"],
    }

    # Section type patterns with emojis
    SECTION_PATTERNS = {
        "title": ["🎯", "🚀", "⭐", "🎨"],
        "feature": ["✨", "🆕", "🎁", "🌟"],
        "improvement": ["⬆️", "📈", "💪", "🚀"],
        "fix": ["🔧", "🛠️", "✅", "🎯"],
        "breaking": ["⚠️", "🚨", "💥", "🔥"],
        "security": ["🔒", "🛡️", "🔐", "🚨"],
        "docs": ["📚", "📖", "📝", "📋"],
        "test": ["🧪", "✅", "🔬", "📊"],
        "performance": ["⚡", "🚀", "📈", "💨"],
        "ui": ["🎨", "✨", "🖼️", "🎪"],
        "api": ["🔌", "⚙️", "🔧", "📡"],
    }

    def __init__(self, platform: Platform = Platform.TELEGRAM):
        """Initialize renderer for specific platform."""
        self.platform = platform
        self.patterns = self.PLATFORM_PATTERNS[platform]
        self.emoji_counter = 0

    def get_next_emoji(self, emoji_list: List[str]) -> str:
        """Get next emoji from list with rotation."""
        emoji = emoji_list[self.emoji_counter % len(emoji_list)]
        self.emoji_counter += 1
        return emoji

    def render_heading(
        self, text: str, level: int = 1, section_type: str = "title"
    ) -> str:
        """Render a heading with appropriate emoji and formatting."""
        # Get appropriate emoji for section type and level
        base_emojis = self.SECTION_PATTERNS.get(section_type, self.HIERARCHY_EMOJIS)
        emoji = self.get_next_emoji(base_emojis)

        # Create hierarchical numbering
        if level == 1:
            numbering = ""
        elif level == 2:
            numbering = "1."
        elif level == 3:
            numbering = "1.1."
        else:
            numbering = f"1.{'.' * (level - 1)}"

        bold = self.patterns["bold"]
        return f"{emoji} {numbering} {bold}{text}{bold}"

    def render_list_item(self, text: str, level: int = 0, status: str = None) -> str:
        """Render a list item with proper indentation and optional status."""
        # Determine bullet style based on level
        if level == 0:
            bullet = "•"
        elif level == 1:
            bullet = "◦"
        elif level == 2:
            bullet = "◊"
        else:
            bullet = "▪"

        # Add status emoji if provided
        status_emoji = ""
        if status:
            status_emojis = self.STATUS_EMOJIS.get(status, [])
            if status_emojis:
                status_emoji = f"{self.get_next_emoji(status_emojis)} "

        indent = "  " * level
        return f"{indent}{bullet} {status_emoji}{text}"

    def render_code_block(self, code: str, language: str = "") -> str:
        """Render a code block with syntax highlighting hint."""
        return f"{self.patterns['code_block']}{language}\n{code}\n{self.patterns['code_block']}"

    def render_inline_code(self, text: str) -> str:
        """Render inline code."""
        return f"{self.patterns['code']}{text}{self.patterns['code']}"

    def render_bold(self, text: str) -> str:
        """Render bold text."""
        return f"{self.patterns['bold']}{text}{self.patterns['bold']}"

    def render_italic(self, text: str) -> str:
        """Render italic text."""
        return f"{self.patterns['italic']}{text}{self.patterns['italic']}"

    def render_strike(self, text: str) -> str:
        """Render strikethrough text."""
        return f"{self.patterns['strike']}{text}{self.patterns['strike']}"

    def format_version_info(self, version: str, title: str = None) -> str:
        """Format version information with visual appeal."""
        version_emoji = self.get_next_emoji(["🏷️", "📦", "🔖", "🎯"])
        if title:
            return f"{version_emoji} *{title}* v{version}"
        return f"{version_emoji} v{version}"

    def format_status_line(self, text: str, status: str = "info") -> str:
        """Format a status line with appropriate emoji."""
        status_emojis = self.STATUS_EMOJIS.get(status, ["ℹ️"])
        emoji = self.get_next_emoji(status_emojis)
        return f"{emoji} {text}"

    def format_separator(self) -> str:
        """Format a visual separator."""
        return "───── ⚡ ─────"

    def format_highlight_box(self, text: str, highlight_type: str = "info") -> str:
        """Format highlighted text in a box."""
        highlight_emojis = {
            "info": ["💡", "ℹ️", "📢"],
            "warning": ["⚠️", "🔥", "💥"],
            "success": ["✅", "🎉", "🚀"],
            "error": ["❌", "🚫", "💔"],
        }

        emojis = highlight_emojis.get(highlight_type, ["💡"])
        emoji = self.get_next_emoji(emojis)

        return f"""
{emoji} {highlight_type.upper()}
{text}
{emoji}
        """.strip()

    def render_changelog_entry(
        self, version: str, sections: Dict[str, List[str]]
    ) -> str:
        """Render a complete changelog entry with all sections."""
        output = []

        # Version header
        output.append(self.format_version_info(version, "Release"))
        output.append("")

        # Process each section
        section_order = [
            "added",
            "improved",
            "fixed",
            "removed",
            "security",
            "breaking",
        ]

        for section_type in section_order:
            if section_type in sections and sections[section_type]:
                # Section header
                section_title = section_type.title()
                output.append(self.render_heading(section_title, 2, section_type))
                output.append("")

                # Section items
                for item in sections[section_type]:
                    output.append(self.render_list_item(item, status=section_type))
                output.append("")

        return "\n".join(output).strip()

    def parse_and_render_markdown(self, markdown_text: str) -> str:
        """Parse existing markdown and render it with platform-specific formatting."""
        lines = markdown_text.split("\n")
        rendered_lines = []

        for line in lines:
            line = line.rstrip()

            # Headers (# ## ### etc.)
            header_match = re.match(r"^(#{1,6})\s+(.+)", line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                rendered_lines.append(self.render_heading(text, level))
                continue

            # List items (- * 1. 1.1. etc.)
            list_match = re.match(r"^(\s*)[-*+•]\s+(.+)", line)
            if list_match:
                indent = len(list_match.group(1)) // 2
                text = list_match.group(2)
                rendered_lines.append(self.render_list_item(text, indent))
                continue

            # Numbered list items
            numbered_match = re.match(r"^(\s*)(\d+(?:\.\d+)*)\.\s+(.+)", line)
            if numbered_match:
                indent = len(numbered_match.group(1)) // 2
                numbered_match.group(2)
                text = numbered_match.group(3)
                # Convert numbered to hierarchical emoji bullets
                rendered_lines.append(self.render_list_item(text, indent))
                continue

            # Code blocks
            if line.strip().startswith("```"):
                rendered_lines.append(line)  # Keep code blocks as-is
                continue

            # Regular text - apply basic formatting
            if line.strip():
                # Convert **bold** to platform-specific
                line = re.sub(
                    r"\*\*(.+?)\*\*", lambda m: self.render_bold(m.group(1)), line
                )
                # Convert *italic* to platform-specific (avoid conflicts with bold)
                line = re.sub(
                    r"(?<!\*)\*([^*]+)\*(?!\*)",
                    lambda m: self.render_italic(m.group(1)),
                    line,
                )
                # Convert `code` to platform-specific
                line = re.sub(
                    r"`([^`]+)`", lambda m: self.render_inline_code(m.group(1)), line
                )

            rendered_lines.append(line)

        return "\n".join(rendered_lines)


# Convenience functions for common use cases
def render_for_telegram(markdown_text: str) -> str:
    """Render markdown for Telegram platform."""
    renderer = MarkdownRenderer(Platform.TELEGRAM)
    return renderer.parse_and_render_markdown(markdown_text)


def render_for_discord(markdown_text: str) -> str:
    """Render markdown for Discord platform."""
    renderer = MarkdownRenderer(Platform.DISCORD)
    return renderer.parse_and_render_markdown(markdown_text)


def render_generic(markdown_text: str) -> str:
    """Render markdown for generic platform."""
    renderer = MarkdownRenderer(Platform.GENERIC)
    return renderer.parse_and_render_markdown(markdown_text)


def create_changelog(
    version: str, sections: Dict[str, List[str]], platform: Platform = Platform.TELEGRAM
) -> str:
    """Create a formatted changelog for the specified platform."""
    renderer = MarkdownRenderer(platform)
    return renderer.render_changelog_entry(version, sections)


# Example usage and templates
CHANGELOG_TEMPLATES = {
    "feature_update": {
        "added": [
            "New feature that enhances user experience",
            "Additional functionality for better workflow",
        ],
        "improved": [
            "Performance improvements for faster response times",
            "Enhanced UI/UX for better accessibility",
        ],
        "fixed": [
            "Critical bug fixes for stability",
            "Edge case handling improvements",
        ],
    },
    "security_update": {
        "security": [
            "Enhanced security measures for user protection",
            "Fixed potential vulnerabilities",
        ],
        "fixed": ["Security-related bug fixes"],
    },
    "performance_update": {
        "improved": [
            "Major performance optimizations",
            "Reduced memory usage",
            "Faster API response times",
        ],
        "fixed": ["Performance bottlenecks resolved"],
    },
}
