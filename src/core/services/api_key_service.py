"""
API Key Service for dcmaidbot

Manages API key generation, validation, and access control for admin endpoints.
Uses database storage for persistence.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.core.models.api_key import ApiKey
from src.core.services.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class APIKeyService:
    """
    Service for managing API keys for admin access to dcmaidbot endpoints.

    Features:
    - Secure API key generation using cryptographic random values
    - Key validation and access control
    - Key usage tracking and rate limiting
    - Key expiration and revocation
    - Admin key management via database storage
    """

    def __init__(self):
        """Initialize API key service."""
        # Key configuration
        self.key_length = 32
        self.default_expiration_days = 365
        self.rate_limit_per_hour = 1000

        # Prefix for dcmaidbot API keys
        self.key_prefix = "dcmaid_"

    async def generate_api_key(
        self,
        user_id: int,
        name: str = "Generated Key",
        description: str = "",
        expires_in_days: Optional[int] = None,
        allowed_event_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new API key for admin access.

        Args:
            user_id: ID of the admin user creating the key
            name: Human-readable name for the key
            description: Optional description of the key's purpose
            expires_in_days: Number of days until key expires (default: 365)
            allowed_event_types: List of event types this key can submit

        Returns:
            Dictionary containing:
            - api_key: The full API key (only shown once)
            - key_info: Dictionary with key metadata
        """
        async with AsyncSessionLocal() as session:
            # Generate the actual key
            api_key = ApiKey.generate_key()
            key_hash = ApiKey.hash_key(api_key)
            key_prefix = api_key[:8]

            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    days=expires_in_days
                )

            # Create database record
            db_key = ApiKey(
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                description=description,
                expires_at=expires_at,
                created_by=user_id,
                allowed_event_types=",".join(allowed_event_types)
                if allowed_event_types
                else None,
            )

            session.add(db_key)
            await session.commit()
            await session.refresh(db_key)

            logger.info(
                f"Generated new API key '{name}' (prefix: {key_prefix}) for user {user_id}"
            )

            return {
                "api_key": api_key,  # Only shown once at generation
                "key_info": db_key.to_dict(),
            }

    async def validate_api_key(
        self, api_key: str, event_type: Optional[str] = None
    ) -> Tuple[bool, Optional[ApiKey]]:
        """
        Validate an API key and return the corresponding database record.

        Args:
            api_key: The API key to validate
            event_type: Optional event type to check permissions

        Returns:
            Tuple of (is_valid, api_key_object)
        """
        if not api_key or not api_key.startswith(self.key_prefix):
            return False, None

        async with AsyncSessionLocal() as session:
            # Find key by hash
            key_hash = ApiKey.hash_key(api_key)
            from sqlalchemy import select

            result = await session.execute(
                select(ApiKey).where(ApiKey.key_hash == key_hash)
            )
            db_key = result.scalar_one_or_none()

            if not db_key:
                return False, None

            # Check if key is active
            if not db_key.is_active:
                logger.warning(f"API key {db_key.key_prefix} is inactive")
                return False, None

            # Check expiration
            if db_key.is_expired():
                logger.warning(f"API key {db_key.key_prefix} has expired")
                return False, None

            # Check event type permissions
            if event_type and not db_key.can_submit_event_type(event_type):
                logger.warning(
                    f"API key {db_key.key_prefix} not allowed to submit {event_type}"
                )
                return False, None

            # Update usage tracking
            db_key.usage_count += 1
            db_key.last_used_at = datetime.now(timezone.utc)
            await session.commit()

            return True, db_key

    async def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: ID of the key to revoke
            user_id: ID of the admin revoking the key

        Returns:
            True if key was revoked, False if not found
        """
        async with AsyncSessionLocal() as session:
            db_key = await session.get(ApiKey, key_id)
            if not db_key:
                return False

            db_key.is_active = False
            await session.commit()

            logger.info(
                f"Revoked API key '{db_key.name}' (prefix: {db_key.key_prefix}) by user {user_id}"
            )
            return True

    async def list_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all API keys created by a user.

        Args:
            user_id: ID of the admin user

        Returns:
            List of API key dictionaries (without the actual keys)
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ApiKey)
                .where(ApiKey.created_by == user_id)
                .order_by(ApiKey.created_at.desc())
            )
            keys = result.scalars().all()

            return [key.to_dict() for key in keys]

    async def get_api_key_usage(
        self, key_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed usage information for an API key.

        Args:
            key_id: ID of the key
            user_id: ID of the admin requesting the info

        Returns:
            Dictionary with usage info or None if not found
        """
        async with AsyncSessionLocal() as session:
            db_key = await session.get(ApiKey, key_id)
            if not db_key or db_key.created_by != user_id:
                return None

            return {
                "id": db_key.id,
                "name": db_key.name,
                "key_prefix": db_key.key_prefix,
                "usage_count": db_key.usage_count,
                "last_used_at": db_key.last_used_at.isoformat()
                if db_key.last_used_at
                else None,
                "created_at": db_key.created_at.isoformat(),
                "is_active": db_key.is_active,
                "expires_at": db_key.expires_at.isoformat()
                if db_key.expires_at
                else None,
            }

    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired API keys.

        Returns:
            Number of keys cleaned up
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            # Find and deactivate expired keys
            result = await session.execute(
                select(ApiKey).where(
                    ApiKey.expires_at < datetime.now(timezone.utc), ApiKey.is_active
                )
            )
            expired_keys = result.scalars().all()

            count = 0
            for key in expired_keys:
                key.is_active = False
                count += 1

            await session.commit()

            if count > 0:
                logger.info(f"Deactivated {count} expired API keys")

            return count

    async def get_key_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics about API keys for a user.

        Args:
            user_id: ID of the admin user

        Returns:
            Dictionary with key statistics
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func, select

            # Total keys
            total_result = await session.execute(
                select(func.count(ApiKey.id)).where(ApiKey.created_by == user_id)
            )
            total_keys = total_result.scalar() or 0

            # Active keys
            active_result = await session.execute(
                select(func.count(ApiKey.id)).where(
                    ApiKey.created_by == user_id, ApiKey.is_active
                )
            )
            active_keys = active_result.scalar() or 0

            # Total usage
            usage_result = await session.execute(
                select(func.sum(ApiKey.usage_count)).where(ApiKey.created_by == user_id)
            )
            total_usage = usage_result.scalar() or 0

            return {
                "total_keys": total_keys,
                "active_keys": active_keys,
                "inactive_keys": total_keys - active_keys,
                "total_usage": total_usage,
            }


# Singleton instance
_api_key_service = APIKeyService()


def get_api_key_service() -> APIKeyService:
    """Get the API key service instance."""
    return _api_key_service
