"""Seed default categories for PRP-005 Memory System.

Predefined categories:
- person: Information about people (friends, family, etc.)
- event: Significant events or moments
- emotion: Emotional experiences (panic attacks, joy, etc.)
- interest: Hobbies, likes, preferences
- fact: General factual information
- skill: Abilities or skills
- goal: Future goals or aspirations
- problem: Issues or challenges
- location: Places and locations
- custom: User-defined categories
"""

import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models.memory import Category


DEFAULT_CATEGORIES = [
    {
        "name": "person",
        "description": "Information about people (friends, family, etc.)",
        "icon": "👤",
    },
    {
        "name": "event",
        "description": "Significant events or moments",
        "icon": "📅",
    },
    {
        "name": "emotion",
        "description": "Emotional experiences (panic attacks, joy, etc.)",
        "icon": "💕",
    },
    {
        "name": "interest",
        "description": "Hobbies, likes, preferences",
        "icon": "⭐",
    },
    {
        "name": "fact",
        "description": "General factual information",
        "icon": "📚",
    },
    {
        "name": "skill",
        "description": "Abilities or skills",
        "icon": "🎯",
    },
    {
        "name": "goal",
        "description": "Future goals or aspirations",
        "icon": "🎯",
    },
    {
        "name": "problem",
        "description": "Issues or challenges",
        "icon": "⚠️",
    },
    {
        "name": "location",
        "description": "Places and locations",
        "icon": "📍",
    },
    {
        "name": "custom",
        "description": "User-defined categories",
        "icon": "✨",
    },
]


async def seed_categories():
    """Seed default categories into database."""

    # Create async engine
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_async_engine(database_url, echo=True)

    # Create session
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as session:
        # Check if categories already exist
        result = await session.execute(select(Category))
        existing_categories = result.scalars().all()

        if existing_categories:
            print(f"✅ Categories already seeded ({len(existing_categories)} found)")
            return

        # Create default categories
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(**cat_data)
            session.add(category)
            print(f"➕ Adding category: {cat_data['name']} {cat_data['icon']}")

        await session.commit()
        print(f"\n✅ Successfully seeded {len(DEFAULT_CATEGORIES)} categories!")


if __name__ == "__main__":
    print("🌱 Seeding default categories for PRP-005 Memory System...")
    asyncio.run(seed_categories())
