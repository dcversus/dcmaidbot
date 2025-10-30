"""Shared pytest fixtures for all tests.

IMPORTANT: We use PostgreSQL for ALL tests (unit, E2E, integration).
NO SQLite in tests - we test with the same database as production.
"""

import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from database import Base
from models.memory import Category


# Use actual PostgreSQL from environment (same as production)
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://dcmaidbot:password@localhost:5432/dcmaidbot_test"
)

# Convert to async URL if needed
if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine (function-scoped to match async event loop)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(test_engine):
    """Create async test database session (function-scoped).

    Each test gets a fresh session. After the test completes,
    any uncommitted changes are rolled back for test isolation.
    """
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        # Rollback any uncommitted changes after test
        await session.rollback()


@pytest.fixture
async def test_categories(async_session):
    """Create test categories for memory tests."""
    categories = [
        Category(
            name="person",
            domain="social",
            full_path="social.person",
            description="Individual profiles",
            icon="👤",
            importance_range_min=100,
            importance_range_max=10000,
        ),
        Category(
            name="tech_domain",
            domain="knowledge",
            full_path="knowledge.tech_domain",
            description="Programming languages",
            icon="💻",
            importance_range_min=1000,
            importance_range_max=5000,
        ),
        Category(
            name="project",
            domain="knowledge",
            full_path="knowledge.project",
            description="Software projects",
            icon="📦",
            importance_range_min=1000,
            importance_range_max=8000,
        ),
    ]

    for cat in categories:
        async_session.add(cat)
    await async_session.commit()

    # Refresh to get IDs
    for cat in categories:
        await async_session.refresh(cat)

    return categories


@pytest.fixture(autouse=True)
async def cleanup_test_data(async_session):
    """Cleanup test data after each test.

    This fixture runs automatically for every test.
    Deletes all data from tables except categories to ensure clean state.
    Silently ignores tables that don't exist yet.

    Note: Using DELETE instead of TRUNCATE to avoid permission issues.
    """
    yield

    # Cleanup after test - ignore missing tables
    # Use DELETE instead of TRUNCATE (requires fewer privileges)
    tables = [
        "memory_links",  # Delete links first due to foreign keys
        "memories",
        "users",
        "messages",
        "facts",
        "stats",
        "lessons",
    ]

    for table in tables:
        try:
            await async_session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            # Table doesn't exist yet, that's fine
            pass

    await async_session.commit()
