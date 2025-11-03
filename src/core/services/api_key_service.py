"""
API Key Service for dcmaidbot

Manages API key generation, validation, and access control for admin endpoints.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class APIKeyService:
    """
    Service for managing API keys for admin access to dcmaidbot endpoints.

    Features:
    - Secure API key generation using cryptographic random values
    - Key validation and access control
    - Key usage tracking and rate limiting
    - Key expiration and revocation
    - Admin key management
    """

    def __init__(self):
        """Initialize API key service."""
        # In-memory storage (replace with database in production)
        self.api_keys = {}
        self.key_usage = {}

        # Key configuration
        self.key_length = 32
        self.default_expiration_days = 365
        self.rate_limit_per_hour = 1000

        # Prefix for dcmaidbot API keys
        self.key_prefix = "dcb_"

    def generate_api_key(
        self,
        user_id: int,
        description: str = "",
        expires_in_days: Optional[int] = None,
        permissions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new API key for admin access.

        Args:
            user_id: Telegram user ID requesting the key
            description: Optional description for the key
            expires_in_days: Custom expiration period (default: 365 days)
            permissions: List of permissions for this key

        Returns:
            Dict: Generated API key information
        """
        try:
            # Generate secure random key
            key_suffix = secrets.token_urlsafe(24)
            api_key = f"{self.key_prefix}{key_suffix}"

            # Hash the key for storage (never store the actual key)
            key_hash = self._hash_key(api_key)

            # Set expiration
            if expires_in_days is None:
                expires_in_days = self.default_expiration_days

            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

            # Set default permissions
            if permissions is None:
                permissions = ["status:read", "interactions:read", "context:read"]

            # Store key information
            key_info = {
                "key_hash": key_hash,
                "user_id": user_id,
                "description": description,
                "permissions": permissions,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_used_at": None,
                "usage_count": 0,
                "is_active": True,
            }

            self.api_keys[key_hash] = key_info

            logger.info(f"Generated API key for user {user_id}: {description}")

            return {
                "api_key": api_key,  # Return actual key only once
                "key_id": key_hash[:16],  # Short identifier
                "description": description,
                "permissions": permissions,
                "expires_at": expires_at.isoformat(),
                "created_at": key_info["created_at"],
                "prefix": self.key_prefix,
            }

        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise

    def validate_api_key(
        self, api_key: str, required_permission: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate an API key and check permissions.

        Args:
            api_key: API key to validate
            required_permission: Specific permission required for access

        Returns:
            Tuple[bool, Dict]: (is_valid, key_info)
        """
        try:
            if not api_key or not api_key.startswith(self.key_prefix):
                return False, {"error": "Invalid key format"}

            # Hash the provided key
            key_hash = self._hash_key(api_key)

            # Check if key exists
            if key_hash not in self.api_keys:
                return False, {"error": "Key not found"}

            key_info = self.api_keys[key_hash]

            # Check if key is active
            if not key_info.get("is_active", True):
                return False, {"error": "Key is deactivated"}

            # Check expiration
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                return False, {"error": "Key has expired"}

            # Check permissions
            if required_permission:
                permissions = key_info.get("permissions", [])
                if required_permission not in permissions:
                    return False, {
                        "error": f"Permission '{required_permission}' not granted"
                    }

            # Check rate limiting
            if not self._check_rate_limit(key_hash):
                return False, {"error": "Rate limit exceeded"}

            # Update usage tracking
            self._update_usage(key_hash)

            logger.info(
                f"API key validated successfully: {key_info.get('description', 'Unknown')}"
            )
            return True, key_info

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False, {"error": "Validation error"}

    def revoke_api_key(self, key_id: str, user_id: int) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: Key identifier (hash or prefix)
            user_id: User ID requesting revocation

        Returns:
            bool: True if key was revoked
        """
        try:
            # Find the key
            key_hash = None
            for hash_val, key_info in self.api_keys.items():
                if hash_val.startswith(key_id) or key_info.get("user_id") == user_id:
                    key_hash = hash_val
                    break

            if not key_hash:
                return False

            # Deactivate the key
            self.api_keys[key_hash]["is_active"] = False
            self.api_keys[key_hash]["revoked_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            logger.info(f"API key revoked: {key_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    def list_user_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all API keys for a user.

        Args:
            user_id: User ID

        Returns:
            List[Dict]: List of user's API keys (without actual keys)
        """
        try:
            user_keys = []
            for key_info in self.api_keys.values():
                if key_info.get("user_id") == user_id:
                    # Return key info without the actual key
                    safe_key_info = {
                        "key_id": key_info["key_hash"][:16],
                        "description": key_info["description"],
                        "permissions": key_info["permissions"],
                        "created_at": key_info["created_at"],
                        "expires_at": key_info["expires_at"],
                        "last_used_at": key_info["last_used_at"],
                        "usage_count": key_info["usage_count"],
                        "is_active": key_info["is_active"],
                        "revoked_at": key_info.get("revoked_at"),
                    }
                    user_keys.append(safe_key_info)

            return user_keys

        except Exception as e:
            logger.error(f"Failed to list user keys: {e}")
            return []

    def get_key_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get API key usage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dict: Usage statistics
        """
        try:
            user_keys = self.list_user_keys(user_id)

            total_usage = sum(key["usage_count"] for key in user_keys)
            active_keys = sum(1 for key in user_keys if key["is_active"])
            expired_keys = 0

            for key in user_keys:
                expires_at = datetime.fromisoformat(key["expires_at"])
                if datetime.now(timezone.utc) > expires_at:
                    expired_keys += 1

            return {
                "total_keys": len(user_keys),
                "active_keys": active_keys,
                "expired_keys": expired_keys,
                "total_usage": total_usage,
                "last_used": max(
                    (key["last_used_at"] for key in user_keys if key["last_used_at"]),
                    default=None,
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get key stats: {e}")
            return {}

    def _hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _check_rate_limit(self, key_hash: str) -> bool:
        """Check if key is within rate limits."""
        try:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)

            # Get usage for this key
            usage = self.key_usage.get(key_hash, [])

            # Filter usage from last hour
            recent_usage = [timestamp for timestamp in usage if timestamp > hour_ago]

            # Check rate limit
            if len(recent_usage) >= self.rate_limit_per_hour:
                return False

            # Update usage list
            self.key_usage[key_hash] = recent_usage
            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    def _update_usage(self, key_hash: str) -> None:
        """Update key usage information."""
        try:
            now = datetime.now(timezone.utc)

            # Update usage list
            if key_hash not in self.key_usage:
                self.key_usage[key_hash] = []
            self.key_usage[key_hash].append(now)

            # Update key info
            if key_hash in self.api_keys:
                self.api_keys[key_hash]["last_used_at"] = now.isoformat()
                self.api_keys[key_hash]["usage_count"] += 1

        except Exception as e:
            logger.error(f"Failed to update usage: {e}")

    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired and inactive keys.

        Returns:
            int: Number of keys cleaned up
        """
        try:
            now = datetime.now(timezone.utc)
            cleaned_count = 0

            keys_to_remove = []
            for key_hash, key_info in self.api_keys.items():
                expires_at = datetime.fromisoformat(key_info["expires_at"])

                # Remove expired inactive keys
                if now > expires_at and not key_info.get("is_active", True):
                    keys_to_remove.append(key_hash)

            # Remove keys
            for key_hash in keys_to_remove:
                del self.api_keys[key_hash]
                if key_hash in self.key_usage:
                    del self.key_usage[key_hash]
                cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired API keys")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0


# Global instance for the service
api_key_service = APIKeyService()
