"""
Unified authentication middleware for dcmaidbot endpoints.

Provides consistent authentication across:
- /call endpoint
- /nudge endpoint
- MCP server
- Any future admin endpoints
"""

import logging
from typing import Optional, Tuple

from src.core.services.api_key_service import get_api_key_service
from src.core.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class UnifiedAuth:
    """Unified authentication system for all admin interfaces."""

    def __init__(self):
        """Initialize unified auth."""
        self.auth_service = AuthService()
        self.api_key_service = get_api_key_service()

    async def authenticate_request(
        self,
        headers: dict,
        query_params: Optional[dict] = None,
        allow_nudge_secret: bool = False,
        nudge_secret: Optional[str] = None,
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Authenticate a request using secure methods only.

        Args:
            headers: Request headers
            query_params: Optional query parameters
            allow_nudge_secret: Whether to allow NUDGE_SECRET (for /nudge endpoint)
            nudge_secret: The expected NUDGE_SECRET value

        Returns:
            Tuple of (is_authenticated, user_id, auth_method)
            auth_method can be: "api_key", "nudge_secret", or None
            NOTE: Admin ID authentication removed for security - anyone could spoof headers
        """
        # Method 1: Check for API key (secure, user-specific with cryptographic validation)
        api_key = self._get_api_key(headers, query_params)
        if api_key:
            is_valid, key_obj = await self.api_key_service.validate_api_key(api_key)
            if is_valid and key_obj:
                logger.debug(f"Authenticated via API key: {key_obj.key_prefix}")
                return True, key_obj.created_by, "api_key"

        # Method 2: Check for NUDGE_SECRET (master API key)
        if allow_nudge_secret and nudge_secret:
            auth_header = headers.get("Authorization", "")
            if auth_header == f"Bearer {nudge_secret}":
                # NUDGE_SECRET is the master API key with system-level access
                # Return True with None user_id for master access
                logger.debug("Authenticated via NUDGE_SECRET (master key)")
                return True, None, "nudge_secret"

        return False, None, None

    def _get_api_key(
        self, headers: dict, query_params: Optional[dict] = None
    ) -> Optional[str]:
        """Extract API key from headers or query params."""
        # Check headers (standard patterns)
        if "X-API-Key" in headers:
            return headers["X-API-Key"]

        if "Authorization" in headers:
            # Support Bearer token format
            auth = headers["Authorization"]
            if auth.startswith("Bearer "):
                return auth[7:]  # Remove "Bearer " prefix

        if "API-Key" in headers:
            return headers["API-Key"]

        # Check query params
        if query_params and "api_key" in query_params:
            return query_params["api_key"]

        return None

    async def check_permissions(
        self,
        user_id: Optional[int],
        auth_method: str,
        required_permission: Optional[str] = None,
    ) -> bool:
        """
        Check if user has specific permissions.

        Args:
            user_id: User ID from authentication
            auth_method: Method used for authentication
            required_permission: Optional specific permission to check

        Returns:
            True if user has required permissions
        """
        # Admin ID authentication has all permissions
        if auth_method == "admin_id" and user_id:
            return self.auth_service.is_admin(user_id)

        # API key permissions could be extended here
        if auth_method == "api_key" and user_id:
            return self.auth_service.is_admin(user_id)

        # NUDGE_SECRET (master key) has all permissions
        if auth_method == "nudge_secret":
            return True  # Master key has full access

        return False


# Singleton instance
_unified_auth = UnifiedAuth()


def get_unified_auth() -> UnifiedAuth:
    """Get the unified auth instance."""
    return _unified_auth
