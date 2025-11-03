#!/usr/bin/env python3
"""
E2E Tests: PRP-016 Phase 5 - Telegram Integration & Advanced UI Behaviors
======================================================================

Tests the complete Telegram rich content system, advanced UI behaviors,
and integration with the messenger service abstraction.
"""

import os

import pytest

from services.messenger_service import (
    InlineButton,
    MessageType,
    RichContent,
    get_messenger_service,
)
from services.nudge_service import NudgeService


class TestPRP016Phase5TelegramIntegration:
    """Test Phase 5 Telegram integration and advanced UI behaviors"""

    @pytest.fixture
    def messenger_service(self):
        """Get messenger service instance"""
        return get_messenger_service()

    @pytest.fixture
    def nudge_service(self):
        """Get nudge service instance"""
        return NudgeService()

    @pytest.fixture
    def test_config(self):
        """Test configuration from environment"""
        return {
            "vasilisa_id": int(os.getenv("VASILISA_TG_ID", "122657093")),
            "base_url": "https://dcmaidbot.theedgestory.org",
        }

    def test_messenger_service_abstract_interface(self, messenger_service):
        """Test that messenger service provides proper abstraction"""
        # Verify service is instantiated
        assert messenger_service is not None
        assert hasattr(messenger_service, "platform_name")
        assert messenger_service.platform_name == "Telegram"

        # Verify abstract methods are implemented
        assert hasattr(messenger_service, "send_message")
        assert hasattr(messenger_service, "send_rich_content")
        assert hasattr(messenger_service, "parse_markdown_to_telegram")

        # Test helper methods
        assert hasattr(messenger_service, "build_inline_keyboard")
        assert hasattr(messenger_service, "create_welcome_buttons")

    def test_markdown_to_telegram_conversion(self, messenger_service):
        """Test markdown to Telegram rich content conversion"""
        markdown_text = """
# 🎉 Advanced UI Behaviors - v0.1.1

## ✨ What's New

### 🎨 **Advanced UI Behavior Requirements**
- **Hover State Isolation**: Hover only affects specific widget area
- **Modal Color Contrast**: Dark text on transparent backgrounds
- **Widget Background States**: Each widget has pre-generated background

### 📊 **Test Results Summary**
- **Modal Color Contrast**: ✅ **PASSING** (100% dark text achieved)
- **Hover State Isolation**: ✅ Working correctly

[🏠 Explore House](explore_house)
[🎵 Play Music](play_music)
[📋 Changelog](changelog)
        """

        # Convert markdown to rich content
        rich_content = messenger_service.parse_markdown_to_telegram(markdown_text)

        # Verify rich content structure
        assert isinstance(rich_content, RichContent)
        assert rich_content.message_type == MessageType.MARKDOWN
        assert rich_content.parse_mode == "HTML"
        assert len(rich_content.content) > 0

        # Check that headers were converted to bold
        assert "<b>Advanced UI Behaviors</b>" in rich_content.content
        assert "<b>What's New</b>" in rich_content.content

        # Check that buttons were extracted
        assert rich_content.buttons is not None
        assert len(rich_content.buttons) >= 3

        # Verify button structure
        button_texts = [btn.text for btn in rich_content.buttons]
        assert "🏠 Explore House" in button_texts
        assert "🎵 Play Music" in button_texts
        assert "📋 Changelog" in button_texts

        # Verify button callback data
        explore_button = next(
            btn for btn in rich_content.buttons if "Explore" in btn.text
        )
        assert explore_button.callback_data == "explore_house"

    def test_inline_keyboard_construction(self, messenger_service):
        """Test inline keyboard construction from button definitions"""
        button_definitions = [
            {"text": "🏠 Explore House", "callback_data": "explore_house"},
            {"text": "🎵 Play Music", "callback_data": "play_music"},
            {"text": "📋 Changelog", "callback_data": "changelog"},
            {"text": "❓ Help", "callback_data": "help"},
            {"text": "🌐 Website", "url": "https://dcmaidbot.theedgestory.org"},
        ]

        # Build inline keyboard
        keyboard = messenger_service.build_inline_keyboard(button_definitions)

        # Verify keyboard structure
        assert keyboard is not None
        assert len(keyboard) >= 2  # Should have multiple rows

        # Check button distribution (max 3 per row)
        total_buttons = sum(len(row) for row in keyboard)
        assert total_buttons == len(button_definitions)

        # Verify all buttons are properly structured
        for row in keyboard:
            for button in row:
                assert hasattr(button, "text")
                assert hasattr(button, "callback_data")
                assert len(button.text) > 0

    def test_welcome_buttons_creation(self, messenger_service, test_config):
        """Test creation of standard welcome buttons"""
        user_id = test_config["vasilisa_id"]
        welcome_buttons = messenger_service.create_welcome_buttons(user_id)

        # Verify button structure
        assert isinstance(welcome_buttons, list)
        assert len(welcome_buttons) >= 4

        # Check standard buttons
        button_texts = [btn["text"] for btn in welcome_buttons]
        assert "🏠 Explore House" in button_texts
        assert "🎵 Play Music" in button_texts
        assert "📋 Changelog" in button_texts
        assert "❓ Help" in button_texts

        # Verify callback data includes user ID
        for button in welcome_buttons:
            if "callback_data" in button:
                assert str(user_id) in button["callback_data"]

    def test_rich_content_media_handling(self, messenger_service):
        """Test rich content with media attachments"""
        # Create rich content with photo
        photo_content = RichContent(
            content="🏠 **Lilith's Room** - Click to explore!",
            message_type=MessageType.PHOTO,
            media_url="https://example.com/room.jpg",
            buttons=[
                InlineButton(text="🔍 Explore", callback_data="explore_room"),
                InlineButton(text="ℹ️ Info", callback_data="room_info"),
            ],
        )

        # Verify structure
        assert photo_content.message_type == MessageType.PHOTO
        assert photo_content.media_url is not None
        assert photo_content.buttons is not None
        assert len(photo_content.buttons) == 2

    def test_nudge_service_messenger_integration(self, nudge_service):
        """Test that nudge service uses messenger abstraction"""
        # Verify nudge service has messenger service
        assert hasattr(nudge_service, "messenger_service")
        assert nudge_service.messenger_service is not None

        # Verify messenger service is properly configured
        assert hasattr(nudge_service.messenger_service, "platform_name")
        assert nudge_service.messenger_service.platform_name == "Telegram"

    def test_complex_markdown_formatting(self, messenger_service):
        """Test complex markdown formatting conversion"""
        complex_markdown = """
# **Main Title** with *emphasis*

## Lists and Formatting
- **Bold item** with *italic*
- `Code snippet` in line
- [Link to site](https://example.com)

### Code Blocks
```python
def hello_world():
    print("Hello, Telegram!")
```

### Mixed Formatting
**Bold with `code` and *italic* together**

~~Strikethrough text~~

### Buttons
[✅ Accept](accept_action)
[❌ Decline](decline_action)
[🌐 Visit Site](https://dcmaidbot.theedgestory.org)
        """

        # Convert to rich content
        rich_content = messenger_service.parse_markdown_to_telegram(complex_markdown)

        # Verify HTML conversion
        assert "<b>Main Title</b>" in rich_content.content
        assert "<i>emphasis</i>" in rich_content.content
        assert "<code>Code snippet</code>" in rich_content.content
        assert "<pre><code>" in rich_content.content
        assert "<s>Strikethrough text</s>" in rich_content.content

        # Verify link conversion
        assert '<a href="https://example.com">Link to site</a>' in rich_content.content

        # Verify button extraction
        assert rich_content.buttons is not None
        assert len(rich_content.buttons) >= 3

        # Check different button types
        callback_buttons = [btn for btn in rich_content.buttons if btn.callback_data]
        url_buttons = [btn for btn in rich_content.buttons if btn.url]

        assert len(callback_buttons) >= 2
        assert len(url_buttons) >= 1

    def test_empty_and_edge_cases(self, messenger_service):
        """Test edge cases for markdown conversion"""
        # Test empty string
        empty_content = messenger_service.parse_markdown_to_telegram("")
        assert empty_content.content == ""
        assert empty_content.buttons is None

        # Test text without markdown
        plain_text = "Just plain text without any formatting"
        plain_content = messenger_service.parse_markdown_to_telegram(plain_text)
        assert plain_text in plain_content.content
        assert plain_content.buttons is None

        # Test text with only buttons
        buttons_only = "[Button 1](btn1)\n[Button 2](btn2)"
        buttons_content = messenger_service.parse_markdown_to_telegram(buttons_only)
        assert buttons_content.buttons is not None
        assert len(buttons_content.buttons) == 2

    def test_action_button_creation(self, messenger_service):
        """Test creation of action buttons from definitions"""
        actions = [
            {"text": "🏠 Explore", "callback_data": "explore_action"},
            {
                "text": "🎵 Play Music",
                "callback_data": "music_action",
                "url": "https://music.com",
            },
            {"text": "📊 View Stats", "callback_data": "stats_action"},
        ]

        user_id = 123456789
        action_buttons = messenger_service.create_action_buttons(actions, user_id)

        # Verify button creation
        assert len(action_buttons) == len(actions)

        # Check each button structure
        for i, button in enumerate(action_buttons):
            assert button["text"] == actions[i]["text"]
            assert user_id in button["callback_data"]

            # Check URL if present
            if "url" in actions[i]:
                assert button["url"] == actions[i]["url"]

    @pytest.mark.asyncio
    async def test_nudge_pre_release_simulation(self, nudge_service, test_config):
        """Test simulated pre-release nudge message"""
        pre_release_message = """🚨 **PRE-RELEASE WARNING** 🚨

**Release**: Advanced UI Behaviors - v0.1.1
**Target User**: Vasilisa
**Status**: Ready for Review

### 📋 Features Implemented:
- ✅ **Hover State Isolation**: Widget-specific hover effects
- ✅ **Modal Color Contrast**: Dark text on transparent backgrounds (100% achieved)
- ✅ **Rich Content System**: Telegram markdown rendering with buttons
- ✅ **Nudge Integration**: Pre-release and post-release notifications

[🎯 Test Features](test_features)
[📋 View Changelog](view_changelog)
"""

        # Test message parsing (without actual sending)
        rich_content = nudge_service.messenger_service.parse_markdown_to_telegram(
            pre_release_message
        )

        # Verify rich content structure
        assert "PRE-RELEASE WARNING" in rich_content.content
        assert "<b>Release</b>" in rich_content.content
        assert rich_content.buttons is not None
        assert len(rich_content.buttons) >= 2

        # Check button extraction
        button_texts = [btn.text for btn in rich_content.buttons]
        assert "🎯 Test Features" in button_texts
        assert "📋 View Changelog" in button_texts

    @pytest.mark.asyncio
    async def test_nudge_post_release_simulation(self, nudge_service, test_config):
        """Test simulated post-release nudge message"""
        post_release_message = """🎉 **RELEASE DEPLOYED SUCCESSFULLY** 🎉

**Version**: Advanced UI Behaviors - v0.1.1
**Status**: ✅ **PRODUCTION LIVE**

### 📊 **Test Results Summary**
```bash
✅ test_hover_state_isolation_only_widget_area - PASS
✅ test_modal_color_contrast_dark_text_on_transparent_bg - PASS
✅ test_widget_specific_modal_background_states - PASS
✅ test_screenshot_comparison_modal_states - PASS
```

### 🔗 **Quick Links**
[🏠 Live Demo](https://dcmaidbot.theedgestory.org)
[📊 Health Check](https://dcmaidbot.theedgestory.org/health)
[📋 Full Changelog](view_changelog)
"""

        # Test message parsing
        rich_content = nudge_service.messenger_service.parse_markdown_to_telegram(
            post_release_message
        )

        # Verify content structure
        assert "RELEASE DEPLOYED SUCCESSFULLY" in rich_content.content
        assert "<pre><code>" in rich_content.content  # Code block preserved
        assert rich_content.buttons is not None

        # Check URL buttons
        url_buttons = [btn for btn in rich_content.buttons if btn.url]
        assert len(url_buttons) >= 3

        urls = [btn.url for btn in url_buttons]
        assert "https://dcmaidbot.theedgestory.org" in urls

    def test_advanced_ui_behavior_requirements(self, messenger_service):
        """Test specific advanced UI behavior requirements"""
        ui_behavior_message = """
# 🎨 Advanced UI Behaviors Implementation

## ✅ **Hover State Isolation**
- **Requirement**: Hover only affects specific widget area
- **Implementation**: ✅ Working correctly
- **Test**: [Verify Hover Isolation](test_hover)

## 🎭 **Modal Color Contrast**
- **Requirement**: Dark text on transparent backgrounds
- **Implementation**: ✅ 100% dark text achieved
- **Details**: rgba(255, 255, 255, 0.001) - 0.1% white background
- **Test**: [Check Modal Contrast](test_modal)

## 🏗️ **Widget Background States**
- **Requirement**: Each widget has pre-generated background for modal interactions
- **Implementation**: ✅ Unique backgrounds per widget
- **Test**: [Test Widget States](test_widget_states)

## 📸 **Screenshot Comparison**
- **Requirement**: Modal states must show ≥5% visual difference
- **Implementation**: ✅ Hash comparison working
- **Test**: [Compare Screenshots](test_screenshots)

## 🎮 **16-bit Movement Graphics**
- **Requirement**: Pixel-perfect movement animations
- **Implementation**: ✅ Movement vectors detected
- **Test**: [Test Animations](test_animations)
"""

        # Convert and verify structure
        rich_content = messenger_service.parse_markdown_to_telegram(ui_behavior_message)

        # Verify all sections are present
        assert "Hover State Isolation" in rich_content.content
        assert "Modal Color Contrast" in rich_content.content
        assert "Widget Background States" in rich_content.content
        assert "Screenshot Comparison" in rich_content.content
        assert "16-bit Movement Graphics" in rich_content.content

        # Check technical details are preserved
        assert "rgba(255, 255, 255, 0.001)" in rich_content.content
        assert "100% dark text achieved" in rich_content.content
        assert "≥5% visual difference" in rich_content.content

        # Verify test buttons
        assert rich_content.buttons is not None
        assert len(rich_content.buttons) >= 5

    def test_telegram_apps_integration_prep(self, messenger_service):
        """Test preparation for Telegram Apps integration (PRP-018)"""
        apps_message = """
# 🚀 Telegram Apps Integration (PRP-018)

## 📱 **Mini App Features**
- **Touch Interface**: Swipe, tap, long-press gestures
- **Character Interaction**: Real-time waifu responses
- **Rich Content**: Inline keyboards and media galleries
- **Navigation**: Custom components for Telegram app

## 🎮 **Touch Controls**
- **Tap**: Character response
- **Swipe**: Character movement
- **Long-press**: Character falls asleep
- **Double-tap**: Character jumps

## 🔗 **Related Systems**
- [Messenger Service](messenger_info) - Abstract rich content system ✅
- [Rich Content Builder](content_builder) - Telegram markdown rendering ✅
- [Nudge System](nudge_info) - Pre/post-release notifications ✅

## 📋 **Next Steps**
[🎯 Start PRP-018](start_prp018)
[📱 Test Touch Interface](test_touch)
[🎵 Add Audio System](add_audio)
"""

        # Convert and verify integration readiness
        rich_content = messenger_service.parse_markdown_to_telegram(apps_message)

        # Verify PRP-018 content is present
        assert "Telegram Apps Integration" in rich_content.content
        assert "Mini App Features" in rich_content.content
        assert "Touch Controls" in rich_content.content
        assert "Related Systems" in rich_content.content

        # Check that completed systems are marked
        assert "Messenger Service" in rich_content.content
        assert "Rich Content Builder" in rich_content.content
        assert "Nudge System" in rich_content.content

        # Verify action buttons for next steps
        assert rich_content.buttons is not None
        button_texts = [btn.text for btn in rich_content.buttons]
        assert "🎯 Start PRP-018" in button_texts
        assert "📱 Test Touch Interface" in button_texts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
