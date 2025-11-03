#!/usr/bin/env python3
"""
Discord Integration Example
==========================

Demonstrates Discord service usage for cross-platform dcmaidbot integration.
This example shows how to use the Discord service for sending rich content,
creating embeds, and handling user interactions.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.messenger_service import (
    Embed,
    EmbedField,
    InlineButton,
    MessageType,
    MessengerFactory,
    RichContent,
)


async def example_discord_rich_content():
    """Example of creating and sending rich Discord content."""
    print("🎨 Creating Discord rich content example...")

    # Create Discord service
    MessengerFactory.create_messenger("discord")

    # Create an embed with Discord-specific formatting
    status_embed = Embed(
        title="🏠 Virtual House Status",
        description="Welcome to your virtual house! All systems are operational.",
        color=0x00FF00,  # Green color for success
        fields=[
            EmbedField(name="Living Room", value="✅ Clean and cozy", inline=True),
            EmbedField(name="Kitchen", value="✅ Ready for cooking", inline=True),
            EmbedField(name="Bedroom", value="✅ Peaceful resting area", inline=True),
            EmbedField(
                name="Garden", value="🌻 Flowers blooming beautifully", inline=False
            ),
        ],
    )

    # Create interactive buttons
    buttons = [
        InlineButton(text="🏠 Explore House", callback_data="explore_house"),
        InlineButton(text="🎵 Play Music", callback_data="play_music"),
        InlineButton(text="📋 View Inventory", callback_data="view_inventory"),
        InlineButton(text="❓ Get Help", callback_data="get_help"),
    ]

    # Create rich content with embed and buttons
    rich_content = RichContent(
        content="Hello! **Welcome to DC MaidBot** on Discord! 🎉\n\n"
        "I'm here to help you explore the virtual house, play music, "
        "and much more. Choose an action below to get started!",
        message_type=MessageType.EMBED,
        embeds=[status_embed],
        buttons=buttons,
    )

    print("✅ Created rich content:")
    print(f"   Message type: {rich_content.message_type}")
    print(f"   Content length: {len(rich_content.content)} characters")
    print(f"   Embeds: {len(rich_content.embeds)}")
    print(f"   Buttons: {len(rich_content.buttons)}")

    return rich_content


async def example_discord_features():
    """Example of Discord-specific features."""
    print("\n🔧 Demonstrating Discord-specific features...")

    discord_service = MessengerFactory.create_messenger("discord")

    # Example 1: Markdown parsing for Discord
    markdown_content = """
# House Exploration Guide

## Available Rooms

Here are the rooms you can explore:

- **Living Room** - Comfortable space for relaxation
- **Kitchen** - Well-equipped for cooking
- **Garden** - Beautiful outdoor space
- **Library** - Quiet reading area

## Quick Actions

[Start Tour](start_tour)
[Check Status](check_status)
[Get Help](get_help)

Enjoy your virtual house experience! 🏡
    """

    parsed_content = discord_service.parse_markdown_to_platform(markdown_content)
    print("✅ Markdown parsed for Discord:")
    print(f"   Original length: {len(markdown_content)}")
    print(f"   Parsed length: {len(parsed_content.content)}")
    print(f"   Extracted embeds: {len(parsed_content.embeds or [])}")
    print(f"   Extracted buttons: {len(parsed_content.buttons or [])}")

    # Example 2: Welcome buttons
    user_id = 123456789
    welcome_buttons = discord_service.create_welcome_buttons(user_id)
    print(f"✅ Created welcome buttons for user {user_id}:")
    for button in welcome_buttons:
        print(f"   - {button['text']} (callback: {button['callback_data']})")


async def example_cross_platform_compatibility():
    """Example of cross-platform compatibility."""
    print("\n🌐 Demonstrating cross-platform compatibility...")

    # Create services for both platforms
    telegram_service = MessengerFactory.create_messenger("telegram")
    discord_service = MessengerFactory.create_messenger("discord")

    # Same content, different platforms
    test_message = (
        "Hello from **DC MaidBot**! This message works on both Telegram and Discord. 🎉"
    )

    # Parse for each platform
    telegram_content = telegram_service.parse_markdown_to_platform(test_message)
    discord_content = discord_service.parse_markdown_to_platform(test_message)

    print("✅ Cross-platform content parsing:")
    print(f"   Telegram parse mode: {telegram_content.parse_mode}")
    print(f"   Discord parse mode: {discord_content.parse_mode}")
    print(
        f"   Content preserved: {'✅' if telegram_content.content == discord_content.content else '❌'}"
    )


async def simulate_discord_interaction():
    """Simulate Discord interaction (without sending actual messages)."""
    print("\n💬 Simulating Discord interaction...")

    discord_service = MessengerFactory.create_messenger("discord")

    # Create sample rich content
    rich_content = await example_discord_rich_content()

    # Simulate sending to a user (this will return error since no token is configured)
    user_id = 123456789
    result = await discord_service.send_message(user_id, rich_content)

    print("✅ Message simulation result:")
    print(f"   Status: {result['status']}")
    print(f"   Platform: {result['platform']}")
    print(f"   User ID: {result['user_id']}")

    if result["status"] == "error":
        print(f"   Error: {result['error']}")
        print("   (This is expected - no Discord bot token configured)")
    else:
        print(f"   Message ID: {result.get('message_id', 'N/A')}")
        print(f"   Channel ID: {result.get('channel_id', 'N/A')}")


async def main():
    """Run all Discord integration examples."""
    print("🤖 DC MaidBot Discord Integration Example")
    print("=" * 50)

    # Run examples
    await example_discord_rich_content()
    await example_discord_features()
    await example_cross_platform_compatibility()
    await simulate_discord_interaction()

    print("\n" + "=" * 50)
    print("✅ Discord integration examples completed!")
    print("\n💡 To use Discord integration with a real bot:")
    print("   1. Set DISCORD_BOT_TOKEN environment variable")
    print("   2. Configure DISCORD_ADMIN_IDS for admin notifications")
    print("   3. Set optional Discord configuration variables")
    print("   4. The service will automatically connect and respond to commands")


if __name__ == "__main__":
    # Set minimal environment for demonstration
    if not os.getenv("ADMIN_IDS"):
        os.environ["ADMIN_IDS"] = "123456789"

    asyncio.run(main())
