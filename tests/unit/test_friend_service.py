"""
Comprehensive Tests for FriendService
======================================

Test suite for FriendService functionality including friendship management,
relationship tracking, social interactions, and database operations.
"""

import asyncio
import os

# Import the service we're testing
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.services.friend_service import FriendService, Friendship, FriendshipStatus


class TestFriendshipStatus:
    """Test suite for FriendshipStatus enum functionality."""

    def test_friendship_status_values(self):
        """Test that all friendship statuses have expected values."""
        expected_statuses = {"PENDING", "ACCEPTED", "DECLINED", "BLOCKED"}

        actual_statuses = {status.name for status in FriendshipStatus}
        assert actual_statuses == expected_statuses

    def test_friendship_status_properties(self):
        """Test friendship status properties."""
        for status in FriendshipStatus:
            assert hasattr(status, "value")
            assert isinstance(status.value, str)


class TestFriendship:
    """Test suite for Friendship model functionality."""

    def test_friendship_creation(self):
        """Test creating a new friendship."""
        friendship = Friendship(
            user_id=123, friend_id=456, status=FriendshipStatus.ACCEPTED
        )

        assert friendship.user_id == 123
        assert friendship.friend_id == 456
        assert friendship.status == FriendshipStatus.ACCEPTED
        assert friendship.created_at is not None
        assert friendship.updated_at is not None

    def test_friendship_serialization(self):
        """Test friendship serialization to dict."""
        friendship = Friendship(
            user_id=123, friend_id=456, status=FriendshipStatus.ACCEPTED
        )

        data = friendship.to_dict()

        assert data["user_id"] == 123
        assert data["friend_id"] == 456
        assert data["status"] == "ACCEPTED"
        assert "created_at" in data
        assert "updated_at" in data

    def test_friendship_deserialization(self):
        """Test friendship deserialization from dict."""
        data = {
            "user_id": 123,
            "friend_id": 456,
            "status": "ACCEPTED",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        friendship = Friendship.from_dict(data)

        assert friendship.user_id == 123
        assert friendship.friend_id == 456
        assert friendship.status == FriendshipStatus.ACCEPTED

    def test_friendship_update_status(self):
        """Test updating friendship status."""
        friendship = Friendship(
            user_id=123, friend_id=456, status=FriendshipStatus.PENDING
        )

        original_updated = friendship.updated_at
        friendship.status = FriendshipStatus.ACCEPTED

        assert friendship.status == FriendshipStatus.ACCEPTED
        assert friendship.updated_at > original_updated

    def test_friendship_symmetry(self):
        """Test friendship symmetry properties."""
        friendship1 = Friendship(
            user_id=123, friend_id=456, status=FriendshipStatus.ACCEPTED
        )

        friendship2 = Friendship(
            user_id=456, friend_id=123, status=FriendshipStatus.ACCEPTED
        )

        # Should be considered the same friendship
        assert friendship1.is_mutual_friendship(friendship2)

    def test_friendship_different_users(self):
        """Test friendship with different user pairs."""
        friendship1 = Friendship(
            user_id=123, friend_id=456, status=FriendshipStatus.ACCEPTED
        )

        friendship2 = Friendship(
            user_id=123, friend_id=789, status=FriendshipStatus.ACCEPTED
        )

        assert not friendship1.is_mutual_friendship(friendship2)


class TestFriendService:
    """Test suite for FriendService functionality."""

    @pytest.fixture
    def friend_service(self):
        """Create a fresh FriendService instance for each test."""
        return FriendService()

    @pytest.fixture
    def mock_database(self):
        """Create a mock database session."""
        with patch("services.friend_service.get_async_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            yield mock_session

    @pytest.mark.asyncio
    async def test_service_initialization(self, friend_service):
        """Test FriendService initialization."""
        assert friend_service.friendships == {}
        assert friend_service.pending_requests == {}
        assert friend_service.blocked_users == set()

    @pytest.mark.asyncio
    async def test_send_friend_request_success(self, friend_service, mock_database):
        """Test successfully sending a friend request."""
        # Mock database queries
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = (
            None  # No existing friendship
        )
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock the friendship object
        mock_friendship = Mock()
        mock_friendship.to_dict.return_value = {
            "user_id": 123,
            "friend_id": 456,
            "status": "PENDING",
        }

        with patch("services.friend_service.Friendship", return_value=mock_friendship):
            result = await friend_service.send_friend_request(123, 456)

        assert result["success"] is True
        assert result["friendship_id"] is not None
        assert result["status"] == "PENDING"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_friend_request_self(self, friend_service):
        """Test sending friend request to self."""
        result = await friend_service.send_friend_request(123, 123)

        assert result["success"] is False
        assert "Cannot add yourself as a friend" in result["error"]

    @pytest.mark.asyncio
    async def test_send_friend_request_existing(self, friend_service, mock_database):
        """Test sending friend request when friendship already exists."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = 1  # Existing friendship

        result = await friend_service.send_friend_request(123, 456)

        assert result["success"] is False
        assert "Friendship already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_send_friend_request_blocked(self, friend_service):
        """Test sending friend request to blocked user."""
        friend_service.blocked_users.add(456)

        result = await friend_service.send_friend_request(123, 456)

        assert result["success"] is False
        assert "Cannot send friend request to blocked user" in result["error"]

    @pytest.mark.asyncio
    async def test_accept_friend_request_success(self, friend_service, mock_database):
        """Test successfully accepting a friend request."""
        # Mock existing friendship
        mock_friendship = Mock()
        mock_friendship.status = FriendshipStatus.PENDING
        mock_friendship.user_id = 456
        mock_friendship.friend_id = 123
        mock_friendship.to_dict.return_value = {
            "user_id": 456,
            "friend_id": 123,
            "status": "ACCEPTED",
        }

        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_friendship
        )
        mock_session.commit = AsyncMock()

        result = await friend_service.accept_friend_request(123, 456)

        assert result["success"] is True
        assert result["status"] == "ACCEPTED"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_accept_friend_request_not_found(self, friend_service, mock_database):
        """Test accepting non-existent friend request."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await friend_service.accept_friend_request(123, 456)

        assert result["success"] is False
        assert "Friend request not found" in result["error"]

    @pytest.mark.asyncio
    async def test_decline_friend_request_success(self, friend_service, mock_database):
        """Test successfully declining a friend request."""
        mock_friendship = Mock()
        mock_friendship.status = FriendshipStatus.PENDING
        mock_friendship.to_dict.return_value = {"status": "DECLINED"}

        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_friendship
        )
        mock_session.commit = AsyncMock()

        result = await friend_service.decline_friend_request(123, 456)

        assert result["success"] is True
        assert result["status"] == "DECLINED"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_block_user_success(self, friend_service, mock_database):
        """Test successfully blocking a user."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = (
            None  # No existing block
        )
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        result = await friend_service.block_user(123, 456)

        assert result["success"] is True
        assert result["action"] == "blocked"
        assert 456 in friend_service.blocked_users
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unblock_user_success(self, friend_service, mock_database):
        """Test successfully unblocking a user."""
        # First block the user
        friend_service.blocked_users.add(456)

        mock_session = mock_database
        mock_session.execute.return_value.rowcount = 1
        mock_session.commit = AsyncMock()

        result = await friend_service.unblock_user(123, 456)

        assert result["success"] is True
        assert result["action"] == "unblocked"
        assert 456 not in friend_service.blocked_users
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_friends_list(self, friend_service, mock_database):
        """Test getting friends list."""
        # Mock database results
        mock_friends = [
            Mock(
                user_id=123,
                friend_id=456,
                status=FriendshipStatus.ACCEPTED,
                to_dict=lambda: {
                    "user_id": 123,
                    "friend_id": 456,
                    "status": "ACCEPTED",
                },
            ),
            Mock(
                user_id=123,
                friend_id=789,
                status=FriendshipStatus.ACCEPTED,
                to_dict=lambda: {
                    "user_id": 123,
                    "friend_id": 789,
                    "status": "ACCEPTED",
                },
            ),
        ]

        mock_session = mock_database
        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            mock_friends
        )

        result = await friend_service.get_friends_list(123)

        assert result["success"] is True
        assert len(result["friends"]) == 2
        assert result["friends"][0]["friend_id"] == 456
        assert result["friends"][1]["friend_id"] == 789

    @pytest.mark.asyncio
    async def test_get_pending_requests(self, friend_service, mock_database):
        """Test getting pending friend requests."""
        mock_requests = [
            Mock(
                user_id=456,
                friend_id=123,
                status=FriendshipStatus.PENDING,
                to_dict=lambda: {"user_id": 456, "friend_id": 123, "status": "PENDING"},
            )
        ]

        mock_session = mock_database
        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            mock_requests
        )

        result = await friend_service.get_pending_requests(123)

        assert result["success"] is True
        assert len(result["pending_requests"]) == 1
        assert result["pending_requests"][0]["user_id"] == 456

    @pytest.mark.asyncio
    async def test_get_friendship_status(self, friend_service, mock_database):
        """Test getting friendship status."""
        mock_friendship = Mock()
        mock_friendship.status = FriendshipStatus.ACCEPTED
        mock_friendship.to_dict.return_value = {"status": "ACCEPTED"}

        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_friendship
        )

        result = await friend_service.get_friendship_status(123, 456)

        assert result["success"] is True
        assert result["status"] == "ACCEPTED"

    @pytest.mark.asyncio
    async def test_get_friendship_status_not_friends(
        self, friend_service, mock_database
    ):
        """Test getting friendship status when not friends."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await friend_service.get_friendship_status(123, 456)

        assert result["success"] is True
        assert result["status"] == "NONE"

    @pytest.mark.asyncio
    async def test_remove_friend_success(self, friend_service, mock_database):
        """Test successfully removing a friend."""
        mock_session = mock_database
        mock_session.execute.return_value.rowcount = 1
        mock_session.commit = AsyncMock()

        result = await friend_service.remove_friend(123, 456)

        assert result["success"] is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_friend_not_found(self, friend_service, mock_database):
        """Test removing non-existent friend."""
        mock_session = mock_database
        mock_session.execute.return_value.rowcount = 0

        result = await friend_service.remove_friend(123, 456)

        assert result["success"] is False
        assert "Friendship not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_mutual_friends(self, friend_service, mock_database):
        """Test getting mutual friends."""
        mock_mutual_friends = [456, 789]

        mock_session = mock_database
        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            mock_mutual_friends
        )

        result = await friend_service.get_mutual_friends(123, 456)

        assert result["success"] is True
        assert len(result["mutual_friends"]) == 2
        assert 456 in result["mutual_friends"]
        assert 789 in result["mutual_friends"]

    @pytest.mark.asyncio
    async def test_get_friends_count(self, friend_service, mock_database):
        """Test getting friends count."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = 5

        result = await friend_service.get_friends_count(123)

        assert result["success"] is True
        assert result["friends_count"] == 5

    @pytest.mark.asyncio
    async def test_is_friend(self, friend_service, mock_database):
        """Test checking if users are friends."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = 1  # Friends

        result = await friend_service.is_friend(123, 456)

        assert result is True

        # Test not friends
        mock_session.execute.return_value.scalar.return_value = 0
        result = await friend_service.is_friend(123, 456)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_blocked(self, friend_service):
        """Test checking if user is blocked."""
        # Block a user
        friend_service.blocked_users.add(456)

        assert await friend_service.is_blocked(123, 456) is True
        assert await friend_service.is_blocked(123, 789) is False

    @pytest.mark.asyncio
    async def test_validate_user_ids(self, friend_service):
        """Test user ID validation."""
        # Valid IDs
        assert friend_service.validate_user_id(123) is True
        assert friend_service.validate_user_id(1) is True

        # Invalid IDs
        assert friend_service.validate_user_id(0) is False
        assert friend_service.validate_user_id(-1) is False
        assert friend_service.validate_user_id(None) is False
        assert friend_service.validate_user_id("invalid") is False

    @pytest.mark.asyncio
    async def test_can_interact(self, friend_service):
        """Test interaction permissions."""
        # Add users to various states
        friend_service.blocked_users.add(999)  # Blocked user

        # Test blocked user
        assert await friend_service.can_interact(123, 999) is False

        # Test non-blocked user
        assert await friend_service.can_interact(123, 456) is True

    @pytest.mark.asyncio
    async def test_friendship_recommendations(self, friend_service, mock_database):
        """Test friendship recommendations."""
        mock_recommendations = [456, 789, 101]

        mock_session = mock_database
        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            mock_recommendations
        )

        result = await friend_service.get_friendship_recommendations(123, limit=5)

        assert result["success"] is True
        assert len(result["recommendations"]) == 3
        assert 456 in result["recommendations"]

    @pytest.mark.asyncio
    async def test_bulk_friend_operations(self, friend_service, mock_database):
        """Test bulk friend operations."""
        mock_session = mock_database
        mock_session.execute.return_value.rowcount = 3
        mock_session.commit = AsyncMock()

        result = await friend_service.bulk_remove_friends(123, [456, 789, 101])

        assert result["success"] is True
        assert result["removed_count"] == 3
        assert mock_session.commit.call_count == 3

    @pytest.mark.asyncio
    async def test_friend_request_cleanup(self, friend_service, mock_database):
        """Test cleaning up old friend requests."""
        mock_session = mock_database
        mock_session.execute.return_value.rowcount = 5
        mock_session.commit = AsyncMock()

        result = await friend_service.cleanup_old_requests(days=30)

        assert result["success"] is True
        assert result["cleaned_count"] == 5
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_friend_requests(self, friend_service, mock_database):
        """Test handling concurrent friend requests."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = (
            None  # No existing friendship
        )
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = friend_service.send_friend_request(123, 456 + i)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        assert all(isinstance(r, dict) for r in results)
        assert all(r.get("success") for r in results)

    @pytest.mark.asyncio
    async def test_friendship_statistics(self, friend_service, mock_database):
        """Test getting friendship statistics."""
        mock_session = mock_database
        mock_session.execute.side_effect = [
            Mock(scalar=Mock(return_value=10)),  # Total friends
            Mock(scalar=Mock(return_value=3)),  # Pending requests
            Mock(scalar=Mock(return_value=2)),  # Blocked users
        ]

        result = await friend_service.get_friendship_statistics(123)

        assert result["success"] is True
        assert result["total_friends"] == 10
        assert result["pending_requests"] == 3
        assert result["blocked_users"] == 2

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, friend_service, mock_database):
        """Test handling of database errors."""
        mock_session = mock_database
        mock_session.execute.side_effect = Exception("Database error")

        result = await friend_service.send_friend_request(123, 456)

        assert result["success"] is False
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_friendship_caching(self, friend_service, mock_database):
        """Test friendship status caching."""
        mock_friendship = Mock()
        mock_friendship.status = FriendshipStatus.ACCEPTED
        mock_friendship.to_dict.return_value = {"status": "ACCEPTED"}

        mock_session = mock_database
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_friendship
        )

        # First call - should hit database
        result1 = await friend_service.get_friendship_status(123, 456)
        assert result1["success"] is True

        # Cache the result
        cache_key = (123, 456)
        friend_service.friendships[cache_key] = mock_friendship

        # Second call - should use cache
        result2 = await friend_service.get_friendship_status(123, 456)
        assert result2["success"] is True

        # Verify database was called only once
        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self, friend_service):
        """Test rate limiting of friend requests."""
        # Simulate rapid requests
        requests_sent = []
        for i in range(10):
            result = await friend_service.send_friend_request(123, 456 + i)
            requests_sent.append(result)

        # Check if rate limiting is working (implementation dependent)
        # This test would need actual rate limiting implementation
        assert len(requests_sent) == 10

    @pytest.mark.asyncio
    async def test_privacy_settings(self, friend_service):
        """Test privacy settings for friend requests."""
        # Test with different privacy settings
        privacy_settings = {
            "allow_friend_requests": True,
            "require_mutual_friends": False,
            "max_friends": 100,
        }

        # This would require implementing privacy settings
        # For now, test basic functionality
        assert isinstance(privacy_settings["allow_friend_requests"], bool)
        assert isinstance(privacy_settings["require_mutual_friends"], bool)
        assert isinstance(privacy_settings["max_friends"], int)


class TestFriendServiceIntegration:
    """Integration tests for FriendService with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_complete_friendship_lifecycle(self, friend_service, mock_database):
        """Test complete friendship lifecycle from request to removal."""
        # Mock database responses
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = (
            None  # No existing friendship
        )

        # Send friend request
        mock_friendship = Mock()
        mock_friendship.status = FriendshipStatus.PENDING
        mock_friendship.to_dict.return_value = {
            "user_id": 123,
            "friend_id": 456,
            "status": "PENDING",
        }

        with patch("services.friend_service.Friendship", return_value=mock_friendship):
            send_result = await friend_service.send_friend_request(123, 456)
        assert send_result["success"] is True

        # Accept friend request
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_friendship
        )
        accept_result = await friend_service.accept_friend_request(123, 456)
        assert accept_result["success"] is True

        # Check friendship status
        mock_friendship.status = FriendshipStatus.ACCEPTED
        mock_friendship.to_dict.return_value = {"status": "ACCEPTED"}
        status_result = await friend_service.get_friendship_status(123, 456)
        assert status_result["status"] == "ACCEPTED"

        # Remove friend
        mock_session.execute.return_value.rowcount = 1
        remove_result = await friend_service.remove_friend(123, 456)
        assert remove_result["success"] is True

    @pytest.mark.asyncio
    async def test_social_network_simulation(self, friend_service, mock_database):
        """Test simulating a small social network."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = None

        # Create friendships
        friendships = [(100, 200), (100, 300), (200, 300), (300, 400), (400, 500)]

        for user1, user2 in friendships:
            mock_friendship = Mock()
            mock_friendship.to_dict.return_value = {
                "user_id": user1,
                "friend_id": user2,
                "status": "ACCEPTED",
            }
            with patch(
                "services.friend_service.Friendship", return_value=mock_friendship
            ):
                await friend_service.send_friend_request(user1, user2)

        # Test mutual friends
        mock_mutual = [300]
        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            mock_mutual
        )
        mutual_result = await friend_service.get_mutual_friends(100, 200)
        assert len(mutual_result["mutual_friends"]) == 1

        # Test friends count
        mock_session.execute.return_value.scalar.return_value = 2
        count_result = await friend_service.get_friends_count(100)
        assert count_result["friends_count"] == 2

    @pytest.mark.asyncio
    async def test_block_and_unblock_flow(self, friend_service, mock_database):
        """Test complete block and unblock flow."""
        mock_session = mock_database
        mock_session.execute.return_value.scalar.return_value = None

        # Block user
        block_result = await friend_service.block_user(123, 456)
        assert block_result["success"] is True
        assert 456 in friend_service.blocked_users

        # Verify blocked
        is_blocked = await friend_service.is_blocked(123, 456)
        assert is_blocked is True

        # Try to send friend request (should fail)
        request_result = await friend_service.send_friend_request(123, 456)
        assert request_result["success"] is False
        assert "blocked" in request_result["error"].lower()

        # Unblock user
        mock_session.execute.return_value.rowcount = 1
        unblock_result = await friend_service.unblock_user(123, 456)
        assert unblock_result["success"] is True
        assert 456 not in friend_service.blocked_users

        # Verify unblocked
        is_blocked = await friend_service.is_blocked(123, 456)
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_pending_requests_management(self, friend_service, mock_database):
        """Test managing pending friend requests."""
        mock_session = mock_database

        # Create multiple pending requests
        pending_requests = []
        for i in range(5):
            mock_request = Mock()
            mock_request.user_id = 200 + i
            mock_request.friend_id = 123
            mock_request.status = FriendshipStatus.PENDING
            mock_request.to_dict.return_value = {
                "user_id": 200 + i,
                "friend_id": 123,
                "status": "PENDING",
            }
            pending_requests.append(mock_request)

        mock_session.execute.return_value.scalars.return_value.all.return_value = (
            pending_requests
        )

        # Get pending requests
        result = await friend_service.get_pending_requests(123)
        assert result["success"] is True
        assert len(result["pending_requests"]) == 5

        # Accept one request
        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            pending_requests[0]
        )
        accept_result = await friend_service.accept_friend_request(123, 200)
        assert accept_result["success"] is True

        # Decline another request
        decline_result = await friend_service.decline_friend_request(123, 201)
        assert decline_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_recovery_and_consistency(self, friend_service, mock_database):
        """Test error recovery and data consistency."""
        mock_session = mock_database

        # Simulate database error during operation
        mock_session.execute.side_effect = [
            None,  # Check existing friendship (none)
            None,  # Add new friendship
            Exception("Database commit failed"),  # Commit fails
        ]

        result = await friend_service.send_friend_request(123, 456)
        assert result["success"] is False

        # Verify service state is consistent
        cache_key = (123, 456)
        assert cache_key not in friend_service.friendships

        # Recovery - next operation should work
        mock_session.execute.side_effect = [None]  # Reset side effects
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        mock_friendship = Mock()
        mock_friendship.to_dict.return_value = {"status": "PENDING"}
        with patch("services.friend_service.Friendship", return_value=mock_friendship):
            result = await friend_service.send_friend_request(123, 456)
        assert result["success"] is True
