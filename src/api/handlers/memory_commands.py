"""Memory and mood related command handlers.

These commands provide explicit access to memory management,
mood tracking, and relationship features.
"""

import json
import os

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.models.memory import Memory
from core.services.database import AsyncSessionLocal
from core.services.memory_service import MemoryService
from core.services.mood_service import MoodService

router = Router()

# Load admin IDs
ADMIN_IDS = set(
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
)


@router.message(Command("mood"))
async def cmd_mood(message: types.Message):
    """Show bot's current mood and emotional state."""
    async with AsyncSessionLocal() as session:
        mood_service = MoodService(session)
        mood_summary = await mood_service.get_mood_summary()

        # Get user relationship
        rel_service = MoodService(session)
        relationship = await rel_service.get_user_relationship(message.from_user.id)

        # Format mood display
        text = f"""<b>{mood_summary["mood_emoji"]} Lilith's Current Mood</b>

<b>Feeling:</b> {mood_summary["primary_mood"]} ({mood_summary["mood_intensity"]})
<b>Energy Level:</b> {mood_summary["energy_level"]} ({mood_summary["energy_value"]})
<b>Confidence:</b> {mood_summary["confidence"]} ({mood_summary["confidence_value"]})
<b>Social Engagement:</b> {mood_summary["social_engagement"]}

<b>VAD Emotional State:</b>
• Valence (Positivity): {mood_summary["vad_scores"]["valence"]}
• Arousal (Energy): {mood_summary["vad_scores"]["arousal"]}
• Dominance (Confidence): {mood_summary["vad_scores"]["dominance"]}

<b>Reason:</b> <i>{mood_summary["reason"]}</i>

<b>Interactions Today:</b> {mood_summary["interaction_count"]}
<b>Last Updated:</b> {mood_summary["last_updated"]}"""

        # Add relationship info if not anonymous
        if relationship.total_interactions > 0:
            text += f"""

<b>Our Relationship 💕</b>
<b>Type:</b> {relationship.relationship_type.capitalize()}
<b>Trust Level:</b> {relationship.trust_score:.1%}
<b>Friendship:</b> {relationship.friendship_level:.1%}
<b>How I Feel:</b> {relationship.bot_feeling.replace("_", " ").capitalize()}
<b>Interactions:</b> {relationship.total_interactions} total, {relationship.positive_interactions} positive"""

        await message.reply(text, parse_mode="HTML")


@router.message(Command("memories"))
async def cmd_memories(message: types.Message):
    """Show memories - admin only or user's own memories summary."""
    is_admin = message.from_user.id in ADMIN_IDS

    async with AsyncSessionLocal() as session:
        memory_service = MemoryService(session)
        mood_service = MoodService(session)

        # Get relationship for context
        relationship = await mood_service.get_user_relationship(message.from_user.id)

        if is_admin:
            # Admin gets full system overview
            memories = await memory_service.search_memories(
                user_id=None,  # Search all memories
                limit=20,
                min_importance=100,
            )

            # Get counts by category
            from sqlalchemy import func, select

            from core.models.memory import Category

            category_counts = await session.execute(
                select(Category.name, func.count(Category.name))
                .join(Category.memories)
                .group_by(Category.name)
                .order_by(func.count(Category.name).desc())
                .limit(10)
            )

            text = f"""<b>🧠 Memory System Overview</b>

<b>Total Memories:</b> {len(memories)} shown
<b>Our Relationship:</b> {relationship.bot_feeling.replace("_", " ").title()} ({relationship.friendship_level:.1%} friendship)

<b>Recent Important Memories:</b>"""

            for memory in memories[:5]:
                categories = (
                    ", ".join([c.name for c in memory.categories])
                    if memory.categories
                    else "uncategorized"
                )
                text += f"\n• <i>{memory.simple_content[:100]}...</i>"
                text += f"\n  <b>Importance:</b> {memory.importance} | <b>Categories:</b> {categories}"

                if memory.emotion_label:
                    text += f" | <b>Emotion:</b> {memory.emotion_label}"
                text += "\n"

            if category_counts.rowcount > 0:
                text += "\n<b>Top Categories:</b>"
                for cat_name, count in category_counts.all():
                    text += f"\n• {cat_name}: {count} memories"

            # Add management keyboard for admin
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📊 View Stats", callback_data="memory_stats"
                        ),
                        InlineKeyboardButton(
                            text="🔍 Search", callback_data="memory_search_prompt"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="💾 Create Memory",
                            callback_data="memory_create_prompt",
                        ),
                        InlineKeyboardButton(
                            text="🔗 View Links", callback_data="memory_links"
                        ),
                    ],
                ]
            )

            await message.reply(text, parse_mode="HTML", reply_markup=keyboard)

        else:
            # Regular user gets their memories summary
            memories = await memory_service.search_memories(
                user_id=message.from_user.id, limit=10, min_importance=50
            )

            if not memories:
                await message.reply(
                    "<b>💭 Your Memories</b>\n\n"
                    "I don't have any memories stored about you yet! "
                    "Share something important about yourself and I'll remember it. ^-^\n\n"
                    "<i>You can ask me to memorize things with:</i>\n"
                    "<code>memorize [information]</code>",
                    parse_mode="HTML",
                )
                return

            text = f"""<b>💭 Your Memories</b>

<b>Total memories:</b> {len(memories)}
<b>Our friendship:</b> {relationship.friendship_level:.1%}"""

            for memory in memories[:5]:
                categories = (
                    ", ".join([c.name.split(".")[-1] for c in memory.categories])
                    if memory.categories
                    else "general"
                )
                text += f"\n• <i>{memory.simple_content[:80]}...</i>"
                text += f"\n  <b>Category:</b> {categories}"

                if memory.emotion_label:
                    text += f" | <b>Feeling:</b> {memory.emotion_label}"
                text += "\n"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔍 Search Memories",
                            callback_data="user_memory_search",
                        ),
                        InlineKeyboardButton(
                            text="💾 Tell me to Remember",
                            callback_data="user_memorize_help",
                        ),
                    ]
                ]
            )

            await message.reply(text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("memorize"))
async def cmd_memorize(message: types.Message):
    """Explicitly memorize something."""
    # Extract content after /memorize
    content = message.text[len("/memorize") :].strip()

    if not content:
        await message.reply(
            "<b>💾 Memorize</b>\n\n"
            "Tell me what to memorize! Example:\n"
            "<code>/memorize I love Python programming and my favorite color is blue</code>\n\n"
            "I'll analyze the content and store it as a memory with appropriate categories and importance.",
            parse_mode="HTML",
        )
        return

    async with AsyncSessionLocal() as session:
        from core.services.llm_service import get_llm_service

        llm_service = get_llm_service()
        memory_service = MemoryService(session)
        mood_service = MoodService(session)

        # Analyze content with LLM
        analysis_prompt = f"""Analyze this content for memory storage:
"{content}"

Extract and return JSON with:
{{
  "simple_content": "Brief summary focusing on key facts",
  "categories": ["category1", "category2"],
  "importance": score (0-9999),
  "emotion_valence": -1.0 to 1.0,
  "emotion_arousal": -1.0 to 1.0,
  "emotion_dominance": -1.0 to 1.0,
  "emotion_label": "emotion_name",
  "keywords": ["key1", "key2"],
  "tags": ["tag1", "tag2"]
}}

Available categories: social.person, knowledge.tech_domain, interest.preference, episode.event, meta.learning, etc."""

        try:
            analysis = await llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            import re

            json_match = re.search(
                r"\{.*\}", analysis.choices[0].message.content, re.DOTALL
            )
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis_data = {
                    "simple_content": content[:200],
                    "categories": ["social.person"],
                    "importance": 500,
                    "emotion_valence": 0.0,
                    "emotion_arousal": 0.0,
                    "emotion_dominance": 0.0,
                    "emotion_label": "neutral",
                    "keywords": [],
                    "tags": [],
                }

            # Create the memory
            memory = await memory_service.create_memory(
                simple_content=analysis_data.get("simple_content", content[:200]),
                full_content=content,
                importance=analysis_data.get("importance", 500),
                created_by=message.from_user.id,
                category_ids=None,  # Will be handled by service
                emotion_valence=analysis_data.get("emotion_valence"),
                emotion_arousal=analysis_data.get("emotion_arousal"),
                emotion_dominance=analysis_data.get("emotion_dominance"),
                emotion_label=analysis_data.get("emotion_label"),
                keywords=analysis_data.get("keywords"),
                tags=analysis_data.get("tags"),
            )

            # Update mood based on memory creation
            await mood_service.update_mood(
                valence_change=0.1,
                arousal_change=0.05,
                confidence_change=0.02,
                reason=f"Created new memory: {memory.simple_content[:50]}...",
                user_id=message.from_user.id,
                memory_id=memory.id,
            )

            # Update relationship
            await mood_service.update_relationship(
                message.from_user.id,
                trust_change=0.05,
                friendship_change=0.03,
                familiarity_change=0.1,
                is_positive=True,
                interaction_type="memorize",
            )

            categories = (
                ", ".join([c.name for c in memory.categories])
                if memory.categories
                else "general"
            )

            await message.reply(
                f"✅ <b>Memory Created!</b>\n\n"
                f"<i>{memory.simple_content}</i>\n\n"
                f"<b>Details:</b>\n"
                f"• ID: {memory.id}\n"
                f"• Importance: {memory.importance}\n"
                f"• Categories: {categories}\n"
                f"• Emotion: {memory.emotion_label or 'neutral'}\n\n"
                f"I'll remember this! 💕",
                parse_mode="HTML",
            )

        except Exception as e:
            await message.reply(
                f"❌ <b>Failed to create memory</b>\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try again or rephrase your content.",
                parse_mode="HTML",
            )


@router.message(Command("relate"))
async def cmd_relate(message: types.Message):
    """Create relationships between memories."""
    # Extract IDs after /relate
    parts = message.text[len("/relate") :].strip().split()

    if len(parts) < 2:
        await message.reply(
            "<b>🔗 Relate Memories</b>\n\n"
            "Connect two memories with a relationship. Example:\n"
            "<code>/relate 123 456 related</code>\n\n"
            "Or just provide two IDs:\n"
            "<code>/relate 123 456</code>\n\n"
            "Available link types: related, causes, contradicts, elaborates, precedes, follows",
            parse_mode="HTML",
        )
        return

    try:
        memory_id_1 = int(parts[0])
        memory_id_2 = int(parts[1])
        link_type = parts[2] if len(parts) > 2 else "related"
    except ValueError:
        await message.reply(
            "❌ Invalid memory IDs. Please use numbers.", parse_mode="HTML"
        )
        return

    async with AsyncSessionLocal() as session:
        memory_service = MemoryService(session)

        # Verify memories exist
        mem1 = await session.get(Memory, memory_id_1)
        mem2 = await session.get(Memory, memory_id_2)

        if not mem1 or not mem2:
            missing = []
            if not mem1:
                missing.append(memory_id_1)
            if not mem2:
                missing.append(memory_id_2)
            await message.reply(
                f"❌ Memory not found: {', '.join(map(str, missing))}",
                parse_mode="HTML",
            )
            return

        # Check permission (admin or memory owner)
        is_admin = message.from_user.id in ADMIN_IDS
        if not is_admin and (
            mem1.created_by != message.from_user.id
            or mem2.created_by != message.from_user.id
        ):
            await message.reply(
                "❌ You can only relate your own memories.", parse_mode="HTML"
            )
            return

        # Create the link
        link = await memory_service.create_memory_link(
            from_memory_id=memory_id_1,
            to_memory_id=memory_id_2,
            link_type=link_type,
            context=f"Manually linked by user {message.from_user.id}",
            strength=1.0,
            auto_generated=False,
        )

        await message.reply(
            f"✅ <b>Memories Linked!</b>\n\n"
            f"<b>Link ID:</b> {link.id}\n"
            f"<b>Memory {memory_id_1}</b> → <b>Memory {memory_id_2}</b>\n"
            f"<b>Type:</b> {link_type}\n"
            f"<b>Context:</b> {link.context}\n\n"
            f"💕 The memories are now connected!",
            parse_mode="HTML",
        )


# Callback handlers for inline keyboards
@router.callback_query(lambda c: c.data.startswith("memory_"))
async def memory_callback(callback: types.CallbackQuery):
    """Handle memory-related callback queries."""
    action = callback.data.split("_")[1]

    if action == "stats":
        await callback.answer("📊 Memory stats coming soon!")
    elif action == "search_prompt":
        await callback.answer(
            "🔍 Use /memories to see memories, then tell me what to search for!"
        )
    elif action == "create_prompt":
        await callback.answer("💾 Use /memorize [content] to create a memory!")
    elif action == "links":
        await callback.answer("🔗 Memory links view coming soon!")
    elif action == "user_memory_search":
        await callback.answer("🔍 Tell me what you want to remember!")
    elif action == "user_memorize_help":
        await callback.answer(
            "💾 Use /memorize [content] to make me remember something!"
        )

    await callback.message.edit_reply_markup(reply_markup=None)
