"""Shared pytest fixtures for all tests.

Supports both PostgreSQL and SQLite databases.
Includes automatic server management for API tests.
"""

import asyncio
import logging
import os
from typing import AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.models.memory import Category
from src.core.services.database import Base


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_openai: marks tests as requiring OpenAI API key"
    )


# Use PostgreSQL database from environment
# Defaults to dev instance in Kubernetes cluster
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


# ===== Server Management Fixtures =====


@pytest.fixture(scope="session")
def test_server_port() -> int:
    """Get a fixed port for testing to avoid conflicts."""
    return 8765  # Use a different port from main development


@pytest_asyncio.fixture(scope="session")
async def test_server_url(test_server_port: int) -> str:
    """Get the full test server URL."""
    return f"http://localhost:{test_server_port}"


@pytest_asyncio.fixture(scope="session")
async def aiohttp_test_server(test_server_port: int) -> AsyncGenerator[str, None]:
    """Start and stop aiohttp server for testing.

    This fixture provides:
    - Automatic server startup before tests
    - Fixed port allocation to avoid conflicts
    - Graceful cleanup after tests complete
    - Health check to ensure server is ready
    """
    from src.api import create_app

    # Configure test environment
    os.environ["PORT"] = str(test_server_port)
    os.environ["HOST"] = "localhost"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    os.environ["ADMIN_IDS"] = "122657093,196907653"
    os.environ["TEST_MODE"] = "true"

    # Suppress noisy logs during testing
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.server").setLevel(logging.WARNING)

    # Create app and runner
    app = create_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    # Create site
    site = aiohttp.web.TCPSite(runner, "localhost", test_server_port)
    await site.start()

    # Wait for server to be ready and perform health check
    max_wait = 10  # seconds
    for _ in range(max_wait * 10):  # Check every 0.1 seconds
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{test_server_port}/health",
                    timeout=aiohttp.ClientTimeout(total=1),
                ) as resp:
                    if resp.status == 200:
                        break
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await asyncio.sleep(0.1)
    else:
        await runner.cleanup()
        raise pytest.fail(f"Server failed to start on port {test_server_port}")

    yield f"http://localhost:{test_server_port}"

    # Cleanup
    await runner.cleanup()

    # Give the OS time to release the port
    await asyncio.sleep(0.1)


@pytest_asyncio.fixture
async def http_client(
    aiohttp_test_server: str,
) -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Provide HTTP client for testing with base URL configured."""
    async with aiohttp.ClientSession(base_url=aiohttp_test_server) as session:
        yield session


@pytest_asyncio.fixture
async def bot_api_client(http_client: aiohttp.ClientSession):
    """Client specifically for bot API testing.

    Provides a convenient wrapper for the /call endpoint.
    """

    async def call_api(
        message: str, user_id: int, is_admin: bool = False, api_key: str = None
    ):
        """Convenient wrapper for /call endpoint."""
        data = {"message": message, "user_id": user_id, "is_admin": is_admin}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        async with http_client.post("/call", json=data, headers=headers) as resp:
            assert resp.status == 200
            return await resp.json()

    return call_api


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Clean up test database files after test session.

    Automatically removes SQLite test databases after tests complete.
    """
    yield

    # Clean up SQLite test databases
    import glob
    import os

    # Remove test.db and other SQLite files
    for pattern in ["test.db", "test_*.db", "*.sqlite", "*.sqlite3"]:
        for db_file in glob.glob(pattern):
            try:
                os.remove(db_file)
                print(f"Cleaned up test database: {db_file}")
            except OSError:
                pass

    # Remove journal files
    for pattern in ["*.db-journal", "*.sqlite-journal", "*.sqlite3-journal"]:
        for journal_file in glob.glob(pattern):
            try:
                os.remove(journal_file)
            except OSError:
                pass


@pytest.fixture(scope="session")
def admin_id() -> int:
    """Get the first admin ID from ADMIN_IDS environment variable."""
    admin_ids = os.getenv("ADMIN_IDS", "122657093")
    return int(admin_ids.split(",")[0].strip())


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure test environment with sensible defaults."""
    # Suppress noisy logs during testing
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.server").setLevel(logging.WARNING)

    # Set test environment variables
    os.environ.setdefault("TEST_MODE", "true")
    os.environ.setdefault("LOG_LEVEL", "WARNING")

    yield

    # Cleanup if needed


@pytest_asyncio.fixture(autouse=True)
async def test_timeout():
    """Add timeout to prevent hanging tests."""
    try:
        yield
    finally:
        # Force cleanup of any lingering tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
