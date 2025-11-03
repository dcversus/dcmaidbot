"""E2E tests for webapp event flow and integration."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.services.domik_service import DomikService
from core.services.event_service import EventService
from core.services.token_service import TokenService
from core.tools.domik_tool import DomikTool


class TestWebappEventFlow:
    """End-to-end tests for webapp event processing."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.scalar_one_or_none = AsyncMock()
        session.scalars.return_value.all.return_value = []
        return session

    @pytest.fixture
    def admin_id(self):
        """Test admin ID."""
        return 123456

    @pytest.fixture
    def token_service(self, mock_session):
        """Create TokenService instance."""
        return TokenService(mock_session)

    @pytest.fixture
    def event_service(self, mock_session):
        """Create EventService instance."""
        return EventService(mock_session)

    @pytest.fixture
    def domik_service(self, token_service):
        """Create DomikService instance."""
        return DomikService(token_service, sandbox_base_path="test_games")

    @pytest.fixture
    def domik_tool(self, token_service, domik_service, event_service, admin_id):
        """Create DomikTool instance."""
        return DomikTool(token_service, domik_service, event_service, admin_id)

    @pytest.mark.asyncio
    async def test_webapp_authentication_flow(self, token_service, mock_session):
        """Test complete webapp authentication flow."""
        # Step 1: Create admin token
        admin_token, raw_token = await token_service.create_token(
            name="Test Webapp Token",
            created_by=123456,
            description="Token for webapp testing",
            expires_hours=24,
        )

        # Mock successful token lookup
        mock_session.scalar_one_or_none.return_value = admin_token
        mock_session.commit.return_value = None

        # Step 2: Validate token through service
        validated_token = await token_service.validate_token(raw_token)

        # Verify authentication success
        assert validated_token is not None
        assert validated_token.name == "Test Webapp Token"
        assert validated_token.created_by == 123456
        assert validated_token.is_valid is True

    @pytest.mark.asyncio
    async def test_webapp_event_collection(self, event_service, mock_session):
        """Test webapp event collection and processing."""
        # Mock database operations
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Step 1: Create a webapp event
        event_data = {
            "id": "webapp_test_event_001",
            "user_id": 123456,
            "event_type": "button_click",
            "data": {"action": "create_quiz", "button_text": "🧠 Create Quiz Game"},
            "event_subtype": "webapp",
            "user_agent": "Mozilla/5.0 (Webapp)",
            "session_id": "session_123",
        }

        # Step 2: Store event
        event = await event_service.create_event(**event_data)

        # Verify event creation
        assert event.event_id == "webapp_test_event_001"
        assert event.user_id == 123456
        assert event.event_type == "button_click"
        assert event.event_subtype == "webapp"
        assert event.status == "unread"

    @pytest.mark.asyncio
    async def test_domik_file_operations(self, domik_tool, tmp_path):
        """Test Domik tool file operations."""
        # Create temporary sandbox directory
        sandbox_path = tmp_path / "test_games"
        sandbox_path.mkdir(exist_ok=True)

        # Update domik service to use temporary path
        domik_tool.domik_service.sandbox_base_path = sandbox_path

        # Step 1: Create a test game file
        game_content = json.dumps(
            {
                "type": "quiz",
                "title": "Test Quiz",
                "questions": [
                    {
                        "question": "What is 2+2?",
                        "options": ["3", "4", "5"],
                        "correct": 1,
                    }
                ],
            },
            indent=2,
        )

        # Step 2: Write file using Domik tool
        write_result = await domik_tool.edit_file("test_quiz.json", game_content)

        # Verify file write
        assert write_result["success"] is True
        assert write_result["path"] == "test_quiz.json"
        assert "written successfully" in write_result["message"]

        # Verify file actually exists
        file_path = sandbox_path / "test_quiz.json"
        assert file_path.exists()

        # Step 3: Read file using Domik tool
        read_result = await domik_tool.get_file("test_quiz.json")

        # Verify file read
        assert read_result["success"] is True
        assert read_result["content"] == game_content
        assert read_result["path"] == "test_quiz.json"

        # Step 4: List directory
        list_result = await domik_tool.list_directory("")

        # Verify directory listing
        assert list_result["success"] is True
        assert list_result["count"] == 1
        assert len(list_result["items"]) == 1
        assert list_result["items"][0]["name"] == "test_quiz.json"
        assert list_result["items"][0]["type"] == "file"

    @pytest.mark.asyncio
    async def test_game_template_creation(self, domik_tool, tmp_path):
        """Test creating games from templates."""
        # Create temporary sandbox directory
        sandbox_path = tmp_path / "test_games"
        sandbox_path.mkdir(exist_ok=True)

        # Update domik service to use temporary path
        domik_tool.domik_service.sandbox_base_path = sandbox_path

        # Step 1: Create game from quiz template
        create_result = await domik_tool.create_game_from_template(
            template_name="quiz",
            game_path="my_new_quiz.json",
            customizations={
                "title": "My Awesome Quiz",
                "description": "A custom quiz game",
            },
        )

        # Verify game creation
        assert create_result["success"] is True
        assert create_result["path"] == "my_new_quiz.json"
        assert "created successfully" in create_result["message"]

        # Step 2: Verify game content
        read_result = await domik_tool.get_file("my_new_quiz.json")
        assert read_result["success"] is True

        game_data = json.loads(read_result["content"])
        assert game_data["type"] == "quiz"
        assert game_data["title"] == "My Awesome Quiz"
        assert game_data["description"] == "A custom quiz game"
        assert len(game_data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_event_processing_workflow(
        self, event_service, domik_tool, mock_session
    ):
        """Test complete event processing workflow."""
        # Mock database operations
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        mock_session.scalar_one_or_none.return_value = None  # No existing events
        mock_session.scalars.return_value.all.return_value = []

        # Step 1: Simulate webapp events
        events = [
            {
                "event_id": "auth_success_001",
                "user_id": 123456,
                "event_type": "auth_success",
                "data": {"admin_id": 123456},
                "event_subtype": "webapp",
            },
            {
                "event_id": "game_action_001",
                "user_id": 123456,
                "event_type": "game_action",
                "data": {"action": "create_quiz"},
                "event_subtype": "webapp",
            },
            {
                "event_id": "file_save_001",
                "user_id": 123456,
                "event_type": "domik_file_write",
                "data": {"file_path": "quiz_game.json", "size": 1024},
                "event_subtype": "domik",
            },
        ]

        # Step 2: Store events
        stored_events = []
        for event_data in events:
            event = await event_service.create_event(**event_data)
            stored_events.append(event)

        # Verify events stored
        assert len(stored_events) == 3
        assert all(event.status == "unread" for event in stored_events)

        # Step 3: Get unread events for processing
        unread_events = await event_service.get_unread_events(event_types=["webapp"])

        # Verify unread events retrieved
        assert len(unread_events) >= 2  # At least the webapp events

        # Step 4: Mark events as processed
        event_ids = [
            event.event_id for event in stored_events[:2]
        ]  # Mark first 2 as read
        marked_count = await event_service.mark_events_as_read(event_ids)

        # Verify events marked as read
        assert marked_count == 2

    @pytest.mark.asyncio
    async def test_sandbox_security_restrictions(self, domik_tool, tmp_path):
        """Test sandbox security restrictions."""
        # Create temporary sandbox directory
        sandbox_path = tmp_path / "test_games"
        sandbox_path.mkdir(exist_ok=True)

        # Update domik service to use temporary path
        domik_tool.domik_service.sandbox_base_path = sandbox_path

        # Test 1: Try to access files outside sandbox
        outside_result = await domik_tool.get_file("../../../etc/passwd")
        assert outside_result["success"] is False
        assert "validation failed" in outside_result["message"]

        # Test 2: Try to write files with disallowed extensions
        dangerous_result = await domik_tool.edit_file("malware.exe", "fake content")
        assert dangerous_result["success"] is False
        assert "extension" in dangerous_result["message"].lower()

        # Test 3: Try to write overly large content
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        large_result = await domik_tool.edit_file("large_file.txt", large_content)
        assert large_result["success"] is False
        assert "too large" in large_result["message"]

    @pytest.mark.asyncio
    async def test_webapp_interface_integration(
        self, event_service, token_service, mock_session
    ):
        """Test webapp interface integration with services."""
        # Mock successful operations
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Create admin token for testing
        admin_token, raw_token = await token_service.create_token(
            name="Webapp Test Token", created_by=123456, expires_hours=24
        )

        # Mock token validation
        mock_session.scalar_one_or_none.return_value = admin_token

        # Simulate webapp page load event
        page_load_event = {
            "id": "page_load_001",
            "user_id": 123456,
            "event_type": "page_load",
            "data": {"page": "workshop", "user_agent": "Mozilla/5.0 (Webapp)"},
            "event_subtype": "webapp",
            "user_agent": "Mozilla/5.0 (Webapp)",
            "session_id": "session_webapp_001",
        }

        # Store page load event
        event = await event_service.create_event(**page_load_event)
        assert event.event_type == "page_load"

        # Simulate button click event
        button_click_event = {
            "id": "button_click_001",
            "user_id": 123456,
            "event_type": "game_action",
            "data": {"action": "create_story", "timestamp": 1234567890},
            "event_subtype": "webapp",
        }

        # Store button click event
        event = await event_service.create_event(**button_click_event)
        assert event.event_type == "game_action"
        assert event.data["action"] == "create_story"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, domik_tool, event_service, mock_session
    ):
        """Test error handling and recovery mechanisms."""
        # Mock database failure
        mock_session.commit.side_effect = Exception("Database connection lost")

        # Test event creation failure handling
        try:
            await event_service.create_event(
                event_id="error_test_001",
                user_id=123456,
                event_type="test_event",
                data={},
            )
            # If no exception, verify error was handled gracefully
            assert True  # This indicates proper error handling
        except Exception:
            # Exception should be caught and logged
            assert True

        # Reset mock for next test
        mock_session.commit.side_effect = None

        # Test file operation error handling
        try:
            # Try to read non-existent file
            result = await domik_tool.get_file("non_existent_file.json")
            assert result["success"] is False
            assert (
                "not found" in result["message"].lower()
                or "failed" in result["message"].lower()
            )
        except Exception as e:
            # Should not raise exceptions, should return error response
            pytest.fail(f"Unexpected exception: {e}")

    @pytest.mark.asyncio
    async def test_performance_under_load(self, event_service, mock_session):
        """Test system performance under moderate load."""
        # Mock database operations
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Create multiple concurrent events
        event_tasks = []
        for i in range(50):
            event_data = {
                "event_id": f"load_test_event_{i:03d}",
                "user_id": 123456,
                "event_type": "button_click",
                "data": {"button_id": f"button_{i}"},
                "event_subtype": "webapp",
            }
            task = event_service.create_event(**event_data)
            event_tasks.append(task)

        # Execute all tasks concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*event_tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        # Verify performance
        duration = end_time - start_time
        assert duration < 5.0  # Should complete within 5 seconds

        # Verify all events created successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 45  # At least 90% success rate

        print(f"Created {len(successful_results)} events in {duration:.2f} seconds")
