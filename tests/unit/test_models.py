"""Unit tests for database models (PRP-003)."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models.user import User
from models.message import Message
from models.fact import Fact
from models.stat import Stat
from database import Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, session):
        """Test creating a user."""
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_friend=False,
            language_code="en",
        )
        session.add(user)
        await session.commit()

        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_friend is False
        assert user.language_code == "en"
        assert isinstance(user.created_at, datetime)

    @pytest.mark.asyncio
    async def test_user_defaults(self, session):
        """Test user model defaults."""
        user = User(telegram_id=987654321)
        session.add(user)
        await session.commit()

        assert user.is_friend is False
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_repr(self, session):
        """Test user model representation."""
        user = User(telegram_id=123456789, username="testuser")
        session.add(user)
        await session.commit()

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "123456789" in repr_str


class TestMessageModel:
    """Tests for Message model."""

    @pytest.mark.asyncio
    async def test_create_message(self, session):
        """Test creating a message."""
        # First create a user
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        # Then create a message
        message = Message(
            user_id=user.id,
            chat_id=-1001234567890,
            message_id=100,
            text="Hello, world!",
            message_type="text",
            language="en",
        )
        session.add(message)
        await session.commit()

        assert message.id is not None
        assert message.user_id == user.id
        assert message.chat_id == -1001234567890
        assert message.text == "Hello, world!"
        assert message.message_type == "text"
        assert message.language == "en"
        assert isinstance(message.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_message_defaults(self, session):
        """Test message model defaults."""
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        message = Message(
            user_id=user.id, chat_id=-1001234567890, message_id=100, text="Test"
        )
        session.add(message)
        await session.commit()

        assert message.message_type == "text"
        assert message.timestamp is not None


class TestFactModel:
    """Tests for Fact model."""

    @pytest.mark.asyncio
    async def test_create_fact(self, session):
        """Test creating a fact."""
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        fact = Fact(
            user_id=user.id,
            fact_text="Likes programming in Python",
            source="Chat conversation on 2025-10-26",
        )
        session.add(fact)
        await session.commit()

        assert fact.id is not None
        assert fact.user_id == user.id
        assert fact.fact_text == "Likes programming in Python"
        assert fact.source == "Chat conversation on 2025-10-26"
        assert isinstance(fact.created_at, datetime)

    @pytest.mark.asyncio
    async def test_fact_repr(self, session):
        """Test fact model representation."""
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        fact = Fact(user_id=user.id, fact_text="Loves cats and coding")
        session.add(fact)
        await session.commit()

        repr_str = repr(fact)
        assert str(user.id) in repr_str
        assert "Loves cats" in repr_str


class TestStatModel:
    """Tests for Stat model."""

    @pytest.mark.asyncio
    async def test_create_stat(self, session):
        """Test creating a stat."""
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        stat = Stat(
            user_id=user.id,
            stat_type="message_count",
            value=42.0,
            extra_data='{"chat_id": -1001234567890}',
        )
        session.add(stat)
        await session.commit()

        assert stat.id is not None
        assert stat.user_id == user.id
        assert stat.stat_type == "message_count"
        assert stat.value == 42.0
        assert stat.extra_data == '{"chat_id": -1001234567890}'
        assert isinstance(stat.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_stat_repr(self, session):
        """Test stat model representation."""
        user = User(telegram_id=123456789)
        session.add(user)
        await session.commit()

        stat = Stat(user_id=user.id, stat_type="jokes_told", value=10.0)
        session.add(stat)
        await session.commit()

        repr_str = repr(stat)
        assert "jokes_told" in repr_str
        assert "10.0" in repr_str
