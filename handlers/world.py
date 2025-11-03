"""
World Handler
=============

Handler for world generation and exploration commands.
Implements PRP-016 Animal Crossing World functionality.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.world_service import get_world_service

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.startswith("/generate_world"))
async def handle_generate_world(message: Message, state: FSMContext):
    """Handle world generation command."""
    try:
        # Parse world size from command
        command_parts = message.text.split()
        width = 10
        height = 10

        if len(command_parts) >= 3:
            try:
                width = int(command_parts[1])
                height = int(command_parts[2])
                # Limit size to prevent huge messages
                width = min(max(width, 5), 20)
                height = min(max(height, 5), 20)
            except ValueError:
                await message.reply(
                    "⚠️ **Invalid Size**\n\n"
                    "Usage: `/generate_world [width] [height]`\n\n"
                    "Example: `/generate_world 10 10`\n"
                    "Valid range: 5-20 for both dimensions."
                )
                return

        await message.reply(f"🌍 **Generating World** {width}x{height}...")

        # Generate world
        world_service = get_world_service()
        world_data = world_service.generate_world(width, height)

        # Render world as emoji
        world_render = world_service.render_world(world_data)

        # Prepare response
        response = "🌍 **Virtual World Generated!**\n\n"
        response += f"📏 **Size:** {world_data['width']}x{world_data['height']}\n"
        response += f"🆔 **World ID:** `{world_data['id']}`\n"
        response += f"🎯 **Spawn Point:** ({world_data['spawn_point'][0]}, {world_data['spawn_point'][1]})\n\n"
        response += "**Map Legend:**\n"
        response += "🌿 Grass | 💧 Water | 🏖️ Sand | 🪨 Stone\n"
        response += "🌳 Tree | 🌻 Flower | 🏠 House\n\n"

        # Add world map
        response += "🗺️ **World Map:**\n"
        response += "```\n" + world_render + "\n```"

        # Add features summary
        features = world_data.get('features', {})
        if features:
            response += "\n📊 **Terrain Distribution:**\n"
            for terrain_type, count in features.items():
                response += f"• {terrain_type}: {count} tiles\n"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error generating world: {e}")
        await message.reply(
            "❌ **Generation Failed**\n\n"
            "Failed to generate world. Please try again later."
        )


@router.message(F.text.startswith("/world_info"))
async def handle_world_info(message: Message, state: FSMContext):
    """Handle world info command."""
    try:
        # Parse world ID from command
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply(
                "ℹ️ **World Info**\n\n"
                "Usage: `/world_info <world_id> [x] [y]`\n\n"
                "Examples:\n"
                "• `/world_info world_1234` - Show world summary\n"
                "• `/world_info world_1234 5 5` - Show tile info at (5,5)"
            )
            return

        world_id = command_parts[1]
        x = y = None

        if len(command_parts) >= 4:
            try:
                x = int(command_parts[2])
                y = int(command_parts[3])
            except ValueError:
                await message.reply("⚠️ **Invalid coordinates. Use integer values.**")
                return

        # Get world service
        world_service = get_world_service()
        world_data = world_service.get_world(world_id)

        if not world_data:
            await message.reply(
                f"❌ **World Not Found**\n\n"
                f"World ID `{world_id}` does not exist.\n\n"
                "Generate a new world with `/generate_world`"
            )
            return

        if x is not None and y is not None:
            # Get tile info
            tile_info = world_service.get_tile_info(world_id, x, y)

            if 'error' in tile_info:
                await message.reply(f"❌ **Error:** {tile_info['error']}")
                return

            response = "📍 **Tile Information**\n\n"
            response += f"🌍 **World:** `{world_id}`\n"
            response += f"📍 **Coordinates:** ({x}, {y})\n"
            response += f"🎨 **Terrain:** {tile_info['terrain_type']}\n"
            response += f"😀 **Emoji:** {tile_info['emoji']}\n"
            response += f"🚶 **Walkable:** {'Yes' if tile_info['walkable'] else 'No'}\n"
            response += f"🎨 **Color:** {tile_info['color']}"
        else:
            # Show world summary
            response = "🌍 **World Information**\n\n"
            response += f"🆔 **World ID:** `{world_data['id']}`\n"
            response += f"📏 **Size:** {world_data['width']}x{world_data['height']}\n"
            response += f"🎯 **Spawn Point:** ({world_data['spawn_point'][0]}, {world_data['spawn_point'][1]})\n"
            response += f"📅 **Created:** {world_data['created_at']}\n\n"

            features = world_data.get('features', {})
            if features:
                response += "📊 **Terrain Distribution:**\n"
                for terrain_type, count in features.items():
                    percentage = (count / (world_data['width'] * world_data['height'])) * 100
                    response += f"• {terrain_type}: {count} tiles ({percentage:.1f}%)\n"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error getting world info: {e}")
        await message.reply(
            "❌ **Info Failed**\n\n"
            "Failed to retrieve world information."
        )
