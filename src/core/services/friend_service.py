"""
Friend Service Implementation
============================

Friend system management service for social features.
Implements PRP-019 Friends System functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from core.models.friend import Friendship
from core.services.database import get_async_session

logger = logging.getLogger(__name__)


class FriendService:
    """Friend system management service."""

    def __init__(self):
        """Initialize friend service."""
        self.pending_requests = {}  # Temporary storage for pending requests

    async def add_friend(self, user_id: int, friend_id: int) -> Dict[str, Any]:
        """Send a friend request to another user.

        Args:
            user_id: User sending the request
            friend_id: User receiving the request

        Returns:
            Result of the friend request
        """
        if user_id == friend_id:
            return {
                "success": False,
                "error": "Cannot add yourself as a friend",
                "user_id": user_id,
                "friend_id": friend_id,
            }

        # Check if already friends
        existing = await self._check_friendship(user_id, friend_id)
        if existing:
            return {
                "success": False,
                "error": "Already friends with this user",
                "user_id": user_id,
                "friend_id": friend_id,
            }

        # Check for existing pending request
        request_key = f"{user_id}-{friend_id}"
        if request_key in self.pending_requests:
            return {
                "success": False,
                "error": "Friend request already sent",
                "user_id": user_id,
                "friend_id": friend_id,
            }

        # Create pending request
        self.pending_requests[request_key] = {
            "from_user": user_id,
            "to_user": friend_id,
            "created_at": datetime.utcnow(),
            "status": "pending",
        }

        logger.info(f"Friend request from {user_id} to {friend_id} created")

        return {
            "success": True,
            "message": "Friend request sent",
            "user_id": user_id,
            "friend_id": friend_id,
            "request_id": request_key,
        }

    async def accept_friend_request(
        self, user_id: int, request_id: str
    ) -> Dict[str, Any]:
        """Accept a friend request.

        Args:
            user_id: User accepting the request
            request_id: Friend request identifier

        Returns:
            Result of accepting the request
        """
        if request_id not in self.pending_requests:
            return {
                "success": False,
                "error": "Friend request not found",
                "request_id": request_id,
            }

        request = self.pending_requests[request_id]

        # Verify user is the recipient
        if request["to_user"] != user_id:
            return {
                "success": False,
                "error": "Cannot accept friend request for another user",
                "request_id": request_id,
            }

        try:
            # Create friendship in database
            async with get_async_session() as session:
                friendship = Friendship(
                    user_id=request["from_user"],
                    friend_id=request["to_user"],
                    status="active",
                    created_at=datetime.utcnow(),
                )
                session.add(friendship)
                await session.commit()

            # Remove pending request
            del self.pending_requests[request_id]

            logger.info(
                f"Friendship created between {request['from_user']} and {request['to_user']}"
            )

            return {
                "success": True,
                "message": "Friend request accepted",
                "friend_id": request["from_user"],
                "friendship_id": friendship.id,
            }

        except Exception as e:
            logger.error(f"Failed to accept friend request {request_id}: {e}")
            return {
                "success": False,
                "error": "Failed to create friendship",
                "request_id": request_id,
            }

    async def list_friends(self, user_id: int) -> List[Dict[str, Any]]:
        """List all friends for a user.

        Args:
            user_id: User ID

        Returns:
            List of friends
        """
        try:
            async with get_async_session() as session:
                # Query friendships where user is either user_id or friend_id
                friendships = await session.execute(
                    """
                    SELECT DISTINCT
                        CASE
                            WHEN user_id = :uid THEN friend_id
                            ELSE user_id
                        END as friend_id,
                        created_at,
                        status
                    FROM friendships
                    WHERE (user_id = :uid OR friend_id = :uid)
                    AND status = 'active'
                    ORDER BY created_at DESC
                    """,
                    {"uid": user_id},
                )

                friends = []
                for row in friendships:
                    friends.append(
                        {
                            "friend_id": row[0],
                            "friendship_date": row[1].isoformat(),
                            "status": row[2],
                        }
                    )

                return friends

        except Exception as e:
            logger.error(f"Failed to list friends for user {user_id}: {e}")
            return []

    async def remove_friend(self, user_id: int, friend_id: int) -> Dict[str, Any]:
        """Remove a friend.

        Args:
            user_id: User removing the friend
            friend_id: Friend to remove

        Returns:
            Result of removing friend
        """
        try:
            async with get_async_session() as session:
                # Find and delete friendship
                await session.execute(
                    """
                    DELETE FROM friendships
                    WHERE (
                        (user_id = :uid AND friend_id = :fid) OR
                        (user_id = :fid AND friend_id = :uid)
                    ) AND status = 'active'
                    """,
                    {"uid": user_id, "fid": friend_id},
                )
                await session.commit()

                logger.info(f"Friendship removed between {user_id} and {friend_id}")

                return {
                    "success": True,
                    "message": "Friend removed successfully",
                    "user_id": user_id,
                    "friend_id": friend_id,
                }

        except Exception as e:
            logger.error(f"Failed to remove friend {friend_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": "Failed to remove friend",
                "user_id": user_id,
                "friend_id": friend_id,
            }

    async def get_pending_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """Get pending friend requests for a user.

        Args:
            user_id: User ID

        Returns:
            List of pending requests
        """
        requests = []
        for request_id, request in self.pending_requests.items():
            if request["to_user"] == user_id and request["status"] == "pending":
                requests.append(
                    {
                        "request_id": request_id,
                        "from_user": request["from_user"],
                        "created_at": request["created_at"].isoformat(),
                    }
                )

        return requests

    async def _check_friendship(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are already friends.

        Args:
            user_id: First user ID
            friend_id: Second user ID

        Returns:
            True if users are friends
        """
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    """
                    SELECT 1 FROM friendships
                    WHERE (
                        (user_id = :uid AND friend_id = :fid) OR
                        (user_id = :fid AND friend_id = :uid)
                    ) AND status = 'active'
                    LIMIT 1
                    """,
                    {"uid": user_id, "fid": friend_id},
                )
                return result.fetchone() is not None

        except Exception as e:
            logger.error(
                f"Failed to check friendship between {user_id} and {friend_id}: {e}"
            )
            return False

    async def get_friends_count(self, user_id: int) -> int:
        """Get the number of friends for a user.

        Args:
            user_id: User ID

        Returns:
            Number of friends
        """
        friends = await self.list_friends(user_id)
        return len(friends)

    async def are_friends(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are friends.

        Args:
            user_id: First user ID
            friend_id: Second user ID

        Returns:
            True if users are friends
        """
        return await self._check_friendship(user_id, friend_id)

    async def health_check(self) -> Dict[str, Any]:
        """Check friend service health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "pending_requests": len(self.pending_requests),
            "service_version": "1.0.0",
        }


# Singleton instance
_friend_service = None


def get_friend_service() -> FriendService:
    """Get or create friend service singleton."""
    global _friend_service
    if _friend_service is None:
        _friend_service = FriendService()
    return _friend_service
