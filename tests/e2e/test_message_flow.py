"""E2E test for message storage and retrieval (PRP-003)."""

import pytest
from sqlalchemy import select
from models.user import User
from models.message import Message

# async_session fixture provided by tests/conftest.py (PostgreSQL)


@pytest.fixture
async def session(async_session):
    """Alias async_session as session for compatibility with existing tests."""
    return async_session


@pytest.mark.asyncio
async def test_message_storage_and_retrieval_flow(session):
    """
    E2E test: Full message flow from storage to retrieval.

    This test simulates:
    1. Creating users
    2. Storing multiple messages from different users
    3. Retrieving messages by chat_id (linear history)
    4. Retrieving messages by user_id
    5. Retrieving recent messages (for RAG context)
    """
    # Step 1: Create users
    user1 = User(telegram_id=111111111, username="alice", first_name="Alice")
    user2 = User(telegram_id=222222222, username="bob", first_name="Bob")
    session.add(user1)
    session.add(user2)
    await session.commit()

    # Step 2: Store multiple messages in a chat
    chat_id = -1001234567890
    messages_data = [
        (user1, "Hello everyone!", "en"),
        (user2, "Hi Alice!", "en"),
        (user1, "How are you doing?", "en"),
        (user2, "Great! Working on dcmaidbot", "en"),
        (user1, "Звучит здорово!", "ru"),  # Russian message
    ]

    for i, (user, text, language) in enumerate(messages_data):
        message = Message(
            user_id=user.id,
            chat_id=chat_id,
            message_id=1000 + i,
            text=text,
            message_type="text",
            language=language,
        )
        session.add(message)

    await session.commit()

    # Step 3: Retrieve all messages from chat (linear history)
    # Order by message_id for guaranteed order
    stmt = (
        select(Message).where(Message.chat_id == chat_id).order_by(Message.message_id)
    )
    result = await session.execute(stmt)
    chat_messages = result.scalars().all()

    assert len(chat_messages) == 5
    assert chat_messages[0].text == "Hello everyone!"
    assert chat_messages[1].text == "Hi Alice!"
    assert chat_messages[4].text == "Звучит здорово!"
    assert chat_messages[4].language == "ru"

    # Step 4: Retrieve messages by specific user
    stmt = (
        select(Message).where(Message.user_id == user1.id).order_by(Message.message_id)
    )
    result = await session.execute(stmt)
    alice_messages = result.scalars().all()

    assert len(alice_messages) == 3
    assert alice_messages[0].text == "Hello everyone!"
    assert alice_messages[2].text == "Звучит здорово!"

    # Step 5: Retrieve recent messages (last 3, for RAG context)
    stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.message_id.desc())
        .limit(3)
    )
    result = await session.execute(stmt)
    recent_messages = result.scalars().all()

    assert len(recent_messages) == 3
    # Most recent first due to desc()
    assert recent_messages[0].text == "Звучит здорово!"
    assert recent_messages[1].text == "Great! Working on dcmaidbot"
    assert recent_messages[2].text == "How are you doing?"

    # Step 6: Search for Russian messages
    stmt = select(Message).where(Message.language == "ru")
    result = await session.execute(stmt)
    russian_messages = result.scalars().all()

    assert len(russian_messages) == 1
    assert russian_messages[0].text == "Звучит здорово!"


@pytest.mark.asyncio
async def test_multi_chat_message_isolation(session):
    """Test that messages from different chats are properly isolated."""
    # Create user
    user = User(telegram_id=333333333, username="charlie")
    session.add(user)
    await session.commit()

    # Create messages in different chats
    chat1_id = -1001111111111
    chat2_id = -1002222222222

    msg1 = Message(
        user_id=user.id,
        chat_id=chat1_id,
        message_id=1,
        text="Message in chat 1",
    )
    msg2 = Message(
        user_id=user.id,
        chat_id=chat2_id,
        message_id=2,
        text="Message in chat 2",
    )
    session.add(msg1)
    session.add(msg2)
    await session.commit()

    # Retrieve messages from chat1 only
    stmt = select(Message).where(Message.chat_id == chat1_id)
    result = await session.execute(stmt)
    chat1_messages = result.scalars().all()

    assert len(chat1_messages) == 1
    assert chat1_messages[0].text == "Message in chat 1"

    # Retrieve messages from chat2 only
    stmt = select(Message).where(Message.chat_id == chat2_id)
    result = await session.execute(stmt)
    chat2_messages = result.scalars().all()

    assert len(chat2_messages) == 1
    assert chat2_messages[0].text == "Message in chat 2"
