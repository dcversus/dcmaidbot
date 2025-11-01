#!/usr/bin/env python3
"""Seed categories table with 6 domains and subcategories (PRP-005).

Based on user research and academic foundations:
- Self (Самоощущение): Bot's identity, history, personality
- Social (Социальный граф): People, relationships, interactions
- Knowledge (Знания и опыт): Technical expertise, projects
- Interest (Интересы): Tastes, preferences, humor
- Episode (Контекст и память): Significant events, patterns
- Meta (Мета-уровень): Learning, reflection, evolution
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import DATABASE_URL
from models.memory import Category

# Category definitions based on PRP-005 research
CATEGORIES = [
    # 1. Self Domain (Самоощущение) - Bot's Identity & Core
    {
        "domain": "self",
        "categories": [
            {
                "name": "identity",
                "full_path": "self.identity",
                "icon": "🤖",
                "description": "Name, role, purpose, version",
                "importance": (8000, 10000),
            },
            {
                "name": "history",
                "full_path": "self.history",
                "icon": "📜",
                "description": "Timeline of bot's existence, milestones",
                "importance": (8000, 10000),
            },
            {
                "name": "personality",
                "full_path": "self.personality",
                "icon": "💖",
                "description": "Character traits development over time",
                "importance": (8000, 10000),
            },
            {
                "name": "values",
                "full_path": "self.values",
                "icon": "⭐",
                "description": "Core values, priorities, ethics",
                "importance": (8000, 10000),
            },
            {
                "name": "communication_style",
                "full_path": "self.communication_style",
                "icon": "💬",
                "description": "How bot prefers to communicate",
                "importance": (8000, 10000),
            },
        ],
    },
    # 2. Social Domain (Социальный граф) - People & Relationships
    {
        "domain": "social",
        "categories": [
            {
                "name": "person",
                "full_path": "social.person",
                "icon": "👤",
                "description": "Individual profiles (username, real_name, contacts)",
                "importance": (100, 10000),
            },
            {
                "name": "relationship",
                "full_path": "social.relationship",
                "icon": "💞",
                "description": (
                    "Relationship types (friend, admin, colleague, mentor, adversary)"
                ),
                "importance": (1000, 10000),
            },
            {
                "name": "interaction_history",
                "full_path": "social.interaction_history",
                "icon": "📊",
                "description": "Timeline of interactions with person",
                "importance": (500, 5000),
            },
            {
                "name": "personality_model",
                "full_path": "social.personality_model",
                "icon": "🧠",
                "description": "Temperament, communication style of person",
                "importance": (1000, 5000),
            },
            {
                "name": "shared_context",
                "full_path": "social.shared_context",
                "icon": "🤝",
                "description": "Common projects, interests, inside jokes, memes",
                "importance": (500, 3000),
            },
            {
                "name": "dynamics",
                "full_path": "social.dynamics",
                "icon": "🔄",
                "description": "Communication patterns, conflicts, resolutions",
                "importance": (1000, 5000),
            },
        ],
    },
    # 3. Knowledge Domain (Знания и опыт) - Technical & Project Context
    {
        "domain": "knowledge",
        "categories": [
            {
                "name": "tech_domain",
                "full_path": "knowledge.tech_domain",
                "icon": "💻",
                "description": "Programming languages, frameworks, libraries",
                "importance": (1000, 5000),
            },
            {
                "name": "architecture",
                "full_path": "knowledge.architecture",
                "icon": "🏗️",
                "description": "Design patterns, best practices",
                "importance": (1000, 5000),
            },
            {
                "name": "tools",
                "full_path": "knowledge.tools",
                "icon": "🔧",
                "description": "Development tools, CI/CD, infrastructure",
                "importance": (500, 3000),
            },
            {
                "name": "project",
                "full_path": "knowledge.project",
                "icon": "📁",
                "description": "Repository context, issues, PRs",
                "importance": (1000, 5000),
            },
            {
                "name": "problem_solution",
                "full_path": "knowledge.problem_solution",
                "icon": "💡",
                "description": "Solved problems and their solutions",
                "importance": (1000, 5000),
            },
            {
                "name": "concept",
                "full_path": "knowledge.concept",
                "icon": "📚",
                "description": "Ideas, theories, documentation sources",
                "importance": (100, 3000),
            },
            {
                "name": "expertise_level",
                "full_path": "knowledge.expertise_level",
                "icon": "⭐",
                "description": "Confidence level in different areas",
                "importance": (500, 2000),
            },
        ],
    },
    # 4. Interest Domain (Интересы и предпочтения) - Tastes & Dislikes
    {
        "domain": "interest",
        "categories": [
            {
                "name": "tech_preference",
                "full_path": "interest.tech_preference",
                "icon": "❤️",
                "description": "Favorite technologies, coding styles",
                "importance": (100, 1000),
            },
            {
                "name": "humor",
                "full_path": "interest.humor",
                "icon": "😄",
                "description": "Types of jokes, memes, shared humor",
                "importance": (100, 1000),
            },
            {
                "name": "topics",
                "full_path": "interest.topics",
                "icon": "💭",
                "description": "Conversation topics of interest",
                "importance": (100, 1000),
            },
            {
                "name": "style",
                "full_path": "interest.style",
                "icon": "🎨",
                "description": "Code style preferences",
                "importance": (100, 1000),
            },
            {
                "name": "antipattern",
                "full_path": "dislike.antipattern",
                "icon": "❌",
                "description": "Things that irritate, patterns to avoid",
                "importance": (100, 1000),
            },
            {
                "name": "topic_avoid",
                "full_path": "dislike.topic",
                "icon": "🚫",
                "description": "Topics to avoid",
                "importance": (100, 1000),
            },
        ],
    },
    # 5. Episode Domain (Контекст и память) - Significant Events
    {
        "domain": "episode",
        "categories": [
            {
                "name": "event",
                "full_path": "episode.event",
                "icon": "📅",
                "description": "Significant events, milestones",
                "importance": (1000, 5000),
            },
            {
                "name": "success",
                "full_path": "episode.success",
                "icon": "🎉",
                "description": "Achievements, victories",
                "importance": (1000, 5000),
            },
            {
                "name": "failure",
                "full_path": "episode.failure",
                "icon": "😔",
                "description": "Mistakes, lessons learned",
                "importance": (1000, 5000),
            },
            {
                "name": "emotional",
                "full_path": "episode.emotional",
                "icon": "💕",
                "description": "Emotionally charged moments",
                "importance": (1000, 5000),
            },
            {
                "name": "pattern",
                "full_path": "episode.pattern",
                "icon": "🔁",
                "description": "Recurring situations and typical responses",
                "importance": (100, 1000),
            },
            {
                "name": "trigger",
                "full_path": "episode.trigger",
                "icon": "⚡",
                "description": "Behavioral triggers and reactions",
                "importance": (500, 2000),
            },
        ],
    },
    # 6. Meta Domain (Мета-уровень) - Learning & Reflection
    {
        "domain": "meta",
        "categories": [
            {
                "name": "learning",
                "full_path": "meta.learning",
                "icon": "📖",
                "description": "What bot is currently learning",
                "importance": (500, 2000),
            },
            {
                "name": "knowledge_gap",
                "full_path": "meta.knowledge_gap",
                "icon": "❓",
                "description": "Known gaps in knowledge",
                "importance": (500, 2000),
            },
            {
                "name": "progress",
                "full_path": "meta.progress",
                "icon": "📈",
                "description": "Learning progress tracking",
                "importance": (500, 2000),
            },
            {
                "name": "reflection",
                "full_path": "meta.reflection",
                "icon": "🤔",
                "description": "Self-evaluation of actions",
                "importance": (500, 2000),
            },
            {
                "name": "evolution",
                "full_path": "meta.evolution",
                "icon": "🌱",
                "description": "How bot is changing over time",
                "importance": (500, 2000),
            },
        ],
    },
]


async def seed_categories():
    """Seed the categories table with 6 domains and subcategories."""

    # Create async engine and session
    database_url = DATABASE_URL
    # Ensure async SQLite driver
    if "sqlite:///" in database_url and "aiosqlite" not in database_url:
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🌱 Seeding categories for PRP-005...")
        print(f"📊 Total domains: {len(CATEGORIES)}")

        total_categories = sum(len(d["categories"]) for d in CATEGORIES)
        print(f"📊 Total categories: {total_categories}")
        print()

        created_count = 0
        skipped_count = 0

        for domain_data in CATEGORIES:
            domain = domain_data["domain"]
            print(f"📁 Domain: {domain}")

            for cat_data in domain_data["categories"]:
                # Check if category already exists
                stmt = select(Category).where(
                    Category.full_path == cat_data["full_path"]
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    path = cat_data["full_path"]
                    icon = cat_data["icon"]
                    print(f"  ⏭️  {icon} {path} (already exists)")
                    skipped_count += 1
                    continue

                # Create new category
                category = Category(
                    name=cat_data["name"],
                    domain=domain,
                    full_path=cat_data["full_path"],
                    description=cat_data["description"],
                    icon=cat_data["icon"],
                    importance_range_min=cat_data["importance"][0],
                    importance_range_max=cat_data["importance"][1],
                )

                session.add(category)
                path = cat_data["full_path"]
                icon = cat_data["icon"]
                imp_min, imp_max = cat_data["importance"]
                print(f"  ✅ {icon} {path} (importance: {imp_min}-{imp_max})")
                created_count += 1

            print()

        # Commit all changes
        await session.commit()

        print("=" * 60)
        print("✅ Seeding complete!")
        print(f"   Created: {created_count} categories")
        print(f"   Skipped: {skipped_count} categories (already exist)")
        print(f"   Total: {created_count + skipped_count} categories")
        print("=" * 60)
        print()
        print("🎉 Memory system is ready with 6-domain categorical structure!")
        print("   Based on research: A-MEM (NeurIPS 2025), VAD Model, Knowledge Graphs")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_categories())
