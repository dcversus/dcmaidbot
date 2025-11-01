"""Unit tests for PRP-008 Multi-Chat Processing System."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from services.chat_buffer import BufferedMessage, ChatBuffer, ChatSummary, ChatType
from services.chat_validator import (
    ChatAccessDecision,
    ChatValidationResult,
    ChatValidator,
)
from services.global_chat_manager import ActivityLevel, ChatHealth, GlobalChatManager
from services.memory_implicator import (
    ImportanceLevel,
    MemoryCategory,
    MemoryImplicator,
)
from services.response_flow import (
    ResponseFlow,
    ResponsePriority,
)


class TestChatBuffer:
    """Test the chat buffer service."""

    @pytest.fixture
    def chat_buffer(self):
        """Create a chat buffer instance for testing."""
        return ChatBuffer()

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing."""
        return BufferedMessage(
            id=123,
            user_id=456,
            chat_id=789,
            message_id=123,
            text="Hello world",
            message_type="text",
            language="en",
            timestamp=datetime.utcnow(),
            username="testuser",
            first_name="Test",
            chat_type=ChatType.GROUP,
            is_admin=False,
            is_mention=False,
        )

    @pytest.mark.asyncio
    async def test_add_message(self, chat_buffer, sample_message):
        """Test adding a message to the buffer."""
        should_process = await chat_buffer.add_message(
            user_id=sample_message.user_id,
            chat_id=sample_message.chat_id,
            message_id=sample_message.message_id,
            text=sample_message.text,
            username=sample_message.username,
            first_name=sample_message.first_name,
            chat_type=sample_message.chat_type.value,
        )

        assert should_process is False  # Should not trigger processing yet
        assert sample_message.chat_id in chat_buffer.chats_active
        assert len(chat_buffer.chat_buffers[sample_message.chat_id]) == 1

    @pytest.mark.asyncio
    async def test_buffer_overflow_triggers_processing(self, chat_buffer):
        """Test that buffer overflow triggers processing."""
        chat_id = 789

        # Add messages until buffer overflows
        for i in range(chat_buffer.buffer_size + 1):
            await chat_buffer.add_message(
                user_id=456 + i,
                chat_id=chat_id,
                message_id=1000 + i,
                text=f"Message {i}",
                chat_type="group",
            )

        # Should trigger processing
        assert chat_id in chat_buffer._chat_processing

    @pytest.mark.asyncio
    async def test_chat_summary_update(self, chat_buffer, sample_message):
        """Test that chat summary is updated correctly."""
        await chat_buffer.add_message(
            user_id=sample_message.user_id,
            chat_id=sample_message.chat_id,
            message_id=sample_message.message_id,
            text=sample_message.text,
            username=sample_message.username,
            first_name=sample_message.first_name,
            chat_type=sample_message.chat_type.value,
        )

        summary = chat_buffer.chat_summaries[sample_message.chat_id]
        assert summary.chat_id == sample_message.chat_id
        assert summary.message_count == 1
        assert sample_message.user_id in summary.active_users

    @pytest.mark.asyncio
    async def test_get_global_status(self, chat_buffer):
        """Test getting global status."""
        # Add some messages
        await chat_buffer.add_message(1, 100, 1000, "Test 1", "group")
        await chat_buffer.add_message(2, 101, 1001, "Test 2", "group")

        status = await chat_buffer.get_global_status()

        assert status["total_messages_processed"] == 2
        assert status["active_chats"] == 2
        assert status["average_buffer_size"] == 1.0


class TestMemoryImplicator:
    """Test the memory implicator service."""

    @pytest.fixture
    def memory_implicator(self):
        """Create a memory implicator instance for testing."""
        return MemoryImplicator()

    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing."""
        messages = []
        for i in range(5):
            msg = MagicMock()
            msg.id = 1000 + i
            msg.user_id = 123
            msg.chat_id = 456
            msg.message_id = 2000 + i
            msg.text = f"This is important message {i} with emotion"
            msg.message_type = "text"
            msg.language = "en"
            msg.timestamp = datetime.utcnow()
            msg.first_name = "Test"
            msg.username = "testuser"
            msg.chat_type = "group"
            msg.is_admin = False
            msg.is_mention = i == 2  # Third message has mention
            messages.append(msg)
        return messages

    @pytest.mark.asyncio
    async def test_classify_chat_content(self, memory_implicator, sample_messages):
        """Test chat content classification."""
        with patch.object(
            memory_implicator.llm_service.client.chat.completions, "create"
        ) as mock_create:
            # Mock LLM response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(
                {
                    "primary_topics": ["general", "conversation"],
                    "participant_roles": {"123": "active participant"},
                    "emotional_tone": "positive",
                    "activity_level": "medium",
                    "importance_score": 0.7,
                    "key_entities": ["message", "emotion"],
                    "relationships": [],
                }
            )
            mock_create.return_value = mock_response

            classification = await memory_implicator._classify_chat_content(
                sample_messages
            )

            assert classification.chat_type == "small_group"
            assert classification.emotional_tone == "positive"
            assert classification.importance_score == 0.7

    @pytest.mark.asyncio
    async def test_extract_important_segments(self, memory_implicator, sample_messages):
        """Test extraction of important segments."""
        classification = MagicMock()
        classification.importance_score = 0.7

        segments = await memory_implicator._extract_important_segments(
            sample_messages, classification
        )

        # Should find segments with importance indicators
        assert len(segments) > 0
        assert all("message" in segment for segment in segments)

    @pytest.mark.asyncio
    async def test_generate_memory_tasks(self, memory_implicator, sample_messages):
        """Test generation of memory tasks."""
        segments = [
            {
                "message": msg,
                "text": msg.text,
                "user_id": msg.user_id,
                "timestamp": msg.timestamp,
                "importance_factors": {"has_indicator": True},
            }
            for msg in sample_messages
        ]
        classification = MagicMock()
        classification.primary_topics = ["general"]
        classification.importance_score = 0.7
        classification.emotional_tone = "positive"

        with patch.object(
            memory_implicator.llm_service.client.chat.completions, "create"
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(
                {
                    "tasks": [
                        {
                            "task_type": "create",
                            "content": "Important conversation about emotions",
                            "category": "emotion",
                            "importance": 500,
                            "related_users": [123],
                            "key_entities": ["emotion", "conversation"],
                            "memory_reason": "Important emotional discussion",
                        }
                    ]
                }
            )
            mock_create.return_value = mock_response

            tasks = await memory_implicator._process_segment_batch(
                segments, classification
            )

            assert len(tasks) == 1
            assert tasks[0].task_type == "create"
            assert tasks[0].category == MemoryCategory.EMOTION
            assert tasks[0].importance == ImportanceLevel.MEDIUM


class TestResponseFlow:
    """Test the response flow service."""

    @pytest.fixture
    def response_flow(self):
        """Create a response flow instance for testing."""
        bot = MagicMock()
        return ResponseFlow(bot)

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing."""
        msg = MagicMock()
        msg.from_user.id = 123
        msg.chat.id = 456
        msg.chat.type = "group"
        msg.text = "Hello bot"
        msg.entities = []
        return msg

    @pytest.mark.asyncio
    async def test_admin_immediate_response(self, response_flow, sample_message):
        """Test that admins get immediate responses."""
        with patch.dict("os.environ", {"ADMIN_IDS": "123"}):
            decision = await response_flow.should_respond(sample_message)

            assert decision.should_respond is True
            assert (
                decision.priority == ResponsePriority.MEDIUM
            )  # Personal chat with admin
            assert decision.delay_seconds == 0

    @pytest.mark.asyncio
    async def test_mention_detection(self, response_flow, sample_message):
        """Test mention detection."""
        sample_message.text = "Hello @dcmaidbot"
        sample_message.entities = [MagicMock(type="mention", offset=6, length=9)]

        with patch.dict("os.environ", {"ADMIN_IDS": ""}):
            decision = await response_flow.should_respond(sample_message)

            assert decision.should_respond is True
            assert "mention" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_stranger_delay_calculation(self, response_flow, sample_message):
        """Test delay calculation for strangers."""
        with patch.dict("os.environ", {"ADMIN_IDS": ""}):
            decision = await response_flow.should_respond(sample_message)

            # Should have some delay or be told not to respond
            if decision.should_respond:
                assert decision.delay_seconds >= 5
            else:
                assert decision.delay_seconds == -1 or "Low priority" in decision.reason

    @pytest.mark.asyncio
    async def test_cooldown_enforcement(self, response_flow, sample_message):
        """Test that cooldown is enforced."""
        # Simulate recent response
        response_flow.recent_responses[
            f"{sample_message.from_user.id}:{sample_message.chat.id}"
        ] = datetime.utcnow()

        decision = await response_flow.should_respond(sample_message)

        # Should not respond due to cooldown
        assert decision.should_respond is False
        assert "cooldown" in decision.reason.lower()

    def test_cleanup_old_tracking(self, response_flow):
        """Test cleanup of old tracking data."""
        # Add some old tracking data
        old_time = datetime.utcnow() - timedelta(hours=25)
        response_flow.recent_responses["123:456"] = old_time
        response_flow.last_bot_response[456] = old_time
        response_flow.chat_activity[456] = old_time

        response_flow._cleanup_old_tracking()

        # Should be cleaned up
        assert "123:456" not in response_flow.recent_responses
        assert 456 not in response_flow.last_bot_response
        assert 456 not in response_flow.chat_activity


class TestChatValidator:
    """Test the chat validator service."""

    @pytest.fixture
    def chat_validator(self):
        """Create a chat validator instance for testing."""
        bot = MagicMock()
        return ChatValidator(bot)

    @pytest.mark.asyncio
    async def test_admin_added_chat_allowed(self, chat_validator):
        """Test that chats added by admins are allowed."""
        with patch.dict("os.environ", {"ADMIN_IDS": "123"}):
            result = await chat_validator.validate_chat_access(
                chat_id=456, chat_type="group", added_by=123
            )

            assert result.decision == ChatAccessDecision.ALLOW
            assert result.added_by_admin is True
            assert "admin" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_no_admin_chat_leaves(self, chat_validator):
        """Test that chats without admins are left."""
        with patch.dict("os.environ", {"ADMIN_IDS": "123"}):
            with patch.object(
                chat_validator, "_get_chat_admins", return_value=([], False)
            ):
                result = await chat_validator.validate_chat_access(
                    chat_id=456,
                    chat_type="group",
                    added_by=456,  # Not an admin
                )

                assert result.decision in [
                    ChatAccessDecision.LEAVE_IMMEDIATELY,
                    ChatAccessDecision.LEAVE_WITH_MESSAGE,
                ]
                assert result.admin_present is False

    @pytest.mark.asyncio
    async def test_private_chat_always_allowed(self, chat_validator):
        """Test that private chats are always allowed."""
        result = await chat_validator.validate_chat_access(
            chat_id=456,
            chat_type="private",
            added_by=789,  # Not an admin
        )

        assert result.decision == ChatAccessDecision.ALLOW
        assert "private" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_execute_leave_decision(self, chat_validator):
        """Test execution of leave decision."""
        validation_result = ChatValidationResult(
            decision=ChatAccessDecision.LEAVE_WITH_MESSAGE,
            reason="Test leave",
            admin_ids=[],
            admin_present=False,
            added_by_admin=False,
            chat_type="group",
        )

        with patch.object(
            chat_validator, "_get_goodbye_message", return_value="Goodbye!"
        ):
            with patch.object(chat_validator.bot, "send_message") as mock_send:
                with patch.object(chat_validator.bot, "leave_chat") as mock_leave:
                    success = await chat_validator.execute_leave_decision(
                        456, validation_result
                    )

                    assert success is True
                    mock_send.assert_called_once_with(456, "Goodbye!")
                    mock_leave.assert_called_once_with(456)


class TestGlobalChatManager:
    """Test the global chat manager service."""

    @pytest.fixture
    def global_manager(self):
        """Create a global chat manager instance for testing."""
        return GlobalChatManager()

    @pytest.fixture
    def sample_chat_summary(self):
        """Create a sample chat summary for testing."""
        return ChatSummary(
            chat_id=456,
            chat_title="Test Chat",
            chat_type=ChatType.GROUP,
            message_count=100,
            last_activity=datetime.utcnow(),
            active_users={123, 456},
            admin_present=True,
            buffer_size=50,
            needs_processing=True,
            last_summary="Recent activity about testing",
        )

    def test_update_chat_status(self, global_manager, sample_chat_summary):
        """Test updating chat status."""
        global_manager.update_chat_status(
            sample_chat_summary.chat_id, sample_chat_summary
        )

        status = global_manager.chat_status[sample_chat_summary.chat_id]
        assert status.chat_id == sample_chat_summary.chat_id
        assert status.message_count_total == sample_chat_summary.message_count
        assert status.admin_present == sample_chat_summary.admin_present

    def test_calculate_activity_level(self, global_manager, sample_chat_summary):
        """Test activity level calculation."""
        # Test different buffer sizes
        sample_chat_summary.buffer_size = 150
        level = global_manager._calculate_activity_level(sample_chat_summary)
        assert level == ActivityLevel.VERY_HIGH

        sample_chat_summary.buffer_size = 75
        level = global_manager._calculate_activity_level(sample_chat_summary)
        assert level == ActivityLevel.HIGH

        sample_chat_summary.buffer_size = 25
        level = global_manager._calculate_activity_level(sample_chat_summary)
        assert level == ActivityLevel.MEDIUM

        sample_chat_summary.buffer_size = 5
        level = global_manager._calculate_activity_level(sample_chat_summary)
        assert level == ActivityLevel.LOW

        sample_chat_summary.buffer_size = 0
        level = global_manager._calculate_activity_level(sample_chat_summary)
        assert level == ActivityLevel.INACTIVE

    def test_assess_chat_health(self, global_manager, sample_chat_summary):
        """Test chat health assessment."""
        # Test healthy chat
        sample_chat_summary.buffer_size = 30
        sample_chat_summary.needs_processing = False
        health, issues = global_manager._assess_chat_health(sample_chat_summary)
        assert health == ChatHealth.HEALTHY
        assert len(issues) == 0

        # Test warning chat
        sample_chat_summary.buffer_size = 160
        health, issues = global_manager._assess_chat_health(sample_chat_summary)
        assert health == ChatHealth.WARNING
        assert len(issues) > 0

        # Test critical chat
        sample_chat_summary.buffer_size = 250
        health, issues = global_manager._assess_chat_health(sample_chat_summary)
        assert health == ChatHealth.CRITICAL
        assert "critical" in issues[0].lower()

    def test_assess_system_health(self, global_manager):
        """Test system health assessment."""
        # Test healthy system
        status1 = MagicMock()
        status1.health_status = ChatHealth.HEALTHY
        global_manager.chat_status[1] = status1

        health = global_manager._assess_system_health()
        assert health == ChatHealth.HEALTHY.value

        # Test system with critical issues
        status2 = MagicMock()
        status2.health_status = ChatHealth.CRITICAL
        global_manager.chat_status[2] = status2

        health = global_manager._assess_system_health()
        assert health == ChatHealth.CRITICAL.value

    @pytest.mark.asyncio
    async def test_get_comprehensive_status(self, global_manager):
        """Test getting comprehensive status."""
        # Add some test data
        global_manager.global_stats.total_chats = 5
        global_manager.global_stats.active_chats = 3
        global_manager.performance_metrics["system_errors"] = 2

        status = await global_manager.get_comprehensive_status()

        assert "global_stats" in status
        assert "chat_count" in status
        assert "performance_metrics" in status
        assert status["chat_count"] == 5
        assert status["active_chats_24h"] == 0  # No recent activity in test data

    def test_shutdown(self, global_manager):
        """Test clean shutdown."""
        # Add some background tasks
        task1 = asyncio.create_task(asyncio.sleep(1))
        task2 = asyncio.create_task(asyncio.sleep(1))
        global_manager._background_tasks.add(task1)
        global_manager._background_tasks.add(task2)

        global_manager.shutdown()

        # Tasks should be cancelled
        assert task1.cancelled()
        assert task2.cancelled()


class TestPerformanceBenchmarks:
    """Performance benchmarks for the multi-chat processing system."""

    @pytest.mark.asyncio
    async def test_chat_buffer_performance(self):
        """Test chat buffer performance under load."""
        buffer = ChatBuffer()
        start_time = datetime.utcnow()

        # Add 1000 messages across 10 chats
        for chat_id in range(10):
            for msg_id in range(100):
                await buffer.add_message(
                    user_id=123,
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=f"Message {msg_id} in chat {chat_id}",
                    chat_type="group",
                )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should handle 1000 messages quickly
        assert duration < 5.0  # 5 seconds max
        assert buffer.total_messages_processed == 1000

    @pytest.mark.asyncio
    async def test_memory_implicator_performance(self):
        """Test memory implicator performance."""
        implicator = MemoryImplicator()

        # Create test messages
        messages = []
        for i in range(50):
            msg = MagicMock()
            msg.text = f"Important message {i} with emotional content and decisions"
            msg.user_id = 123 + i % 5
            msg.chat_id = 456
            msg.timestamp = datetime.utcnow()
            msg.first_name = f"User{i % 5}"
            msg.chat_type = "group"
            msg.is_admin = i % 10 == 0
            msg.is_mention = i % 7 == 0
            messages.append(msg)

        start_time = datetime.utcnow()

        # Mock LLM to avoid actual API calls
        with patch.object(
            implicator.llm_service.client.chat.completions, "create"
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps({"tasks": []})
            mock_create.return_value = mock_response

            await implicator.process_messages(messages)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should process 50 messages efficiently
        assert duration < 2.0  # 2 seconds max

    @pytest.mark.asyncio
    async def test_response_flow_performance(self):
        """Test response flow performance."""
        bot = MagicMock()
        flow = ResponseFlow(bot)

        start_time = datetime.utcnow()

        # Process 100 response decisions
        for i in range(100):
            msg = MagicMock()
            msg.from_user.id = 123 + i
            msg.chat.id = 456 + i % 10
            msg.chat.type = "group" if i % 2 else "private"
            msg.text = f"Test message {i}"
            msg.entities = []

            await flow.should_respond(msg)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should handle 100 decisions quickly
        assert duration < 1.0  # 1 second max

    @pytest.mark.asyncio
    async def test_global_manager_performance(self):
        """Test global manager performance."""
        manager = GlobalChatManager()

        # Add many chat statuses
        start_time = datetime.utcnow()

        for i in range(100):
            summary = ChatSummary(
                chat_id=i,
                chat_title=f"Chat {i}",
                chat_type=ChatType.GROUP,
                message_count=100 + i,
                last_activity=datetime.utcnow(),
                active_users={123, 456},
                admin_present=i % 3 == 0,
                buffer_size=50 + i % 50,
                needs_processing=i % 4 == 0,
            )
            await manager.update_chat_status(i, summary)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should handle 100 chat updates efficiently
        assert duration < 1.0  # 1 second max
        assert len(manager.chat_status) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
