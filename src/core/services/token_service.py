"""Token authentication service for admin webapp access.

This service provides secure token generation, validation, and management
for admin-only access to the Telegram webapp mini-game creator.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.admin_token import AdminToken

logger = logging.getLogger(__name__)


class TokenService:
    """Service for managing admin authentication tokens."""

    def __init__(self, session: AsyncSession):
        """Initialize token service with database session."""
        self.session = session

    async def create_token(
        self,
        name: str,
        created_by: int,
        description: Optional[str] = None,
        expires_hours: int = 24,
    ) -> tuple[AdminToken, str]:
        """Create a new admin token and return both the object and raw token."""
        # Generate the actual token
        raw_token = AdminToken.generate_token()
        token_hash = AdminToken.hash_token(raw_token)
        token_prefix = raw_token[:8]
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        admin_token = AdminToken(
            name=name,
            token_hash=token_hash,
            token_prefix=token_prefix,
            created_by=created_by,
            expires_at=expires_at,
            description=description,
        )

        self.session.add(admin_token)
        await self.session.commit()
        await self.session.refresh(admin_token)

        logger.info(
            f"Created admin token: {name} (prefix: {token_prefix}) for admin: {created_by}"
        )
        return admin_token, raw_token

    async def validate_token(self, raw_token: str) -> Optional[AdminToken]:
        """Validate a token and return the associated admin token if valid."""
        try:
            token_hash = AdminToken.hash_token(raw_token)

            result = await self.session.execute(
                select(AdminToken).where(
                    AdminToken.token_hash == token_hash,
                    AdminToken.is_active,
                )
            )
            admin_token = result.scalar_one_or_none()

            if not admin_token:
                logger.warning(f"Invalid token attempted: {raw_token[:8]}...")
                return None

            if admin_token.is_expired:
                logger.warning(f"Expired token attempted: {admin_token.token_prefix}")
                return None

            # Update last used timestamp
            admin_token.last_used_at = datetime.utcnow()
            await self.session.commit()

            logger.info(f"Token validated successfully: {admin_token.token_prefix}")
            return admin_token

        except Exception as e:
            logger.error(f"Error validating token: {e}", exc_info=True)
            return None

    async def revoke_token(self, token_id: int) -> bool:
        """Revoke an admin token by setting it as inactive."""
        try:
            result = await self.session.execute(
                select(AdminToken).where(AdminToken.id == token_id)
            )
            admin_token = result.scalar_one_or_none()

            if not admin_token:
                return False

            admin_token.is_active = False
            await self.session.commit()

            logger.info(f"Token revoked: {admin_token.token_prefix}")
            return True

        except Exception as e:
            logger.error(f"Error revoking token: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def get_tokens_for_admin(self, admin_id: int) -> list[AdminToken]:
        """Get all tokens created by a specific admin."""
        result = await self.session.execute(
            select(AdminToken)
            .where(AdminToken.created_by == admin_id)
            .order_by(AdminToken.created_at.desc())
        )
        return result.scalars().all()

    async def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens older than 7 days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            from sqlalchemy import delete

            result = await self.session.execute(
                delete(AdminToken).where(
                    AdminToken.expires_at < cutoff_date,
                    not AdminToken.is_active,
                )
            )

            await self.session.commit()
            return result.rowcount

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}", exc_info=True)
            await self.session.rollback()
            return 0

    async def extend_token(self, token_id: int, hours: int = 24) -> bool:
        """Extend the expiration time of a token."""
        try:
            result = await self.session.execute(
                select(AdminToken).where(AdminToken.id == token_id)
            )
            admin_token = result.scalar_one_or_none()

            if not admin_token or not admin_token.is_active:
                return False

            admin_token.expires_at = datetime.utcnow() + timedelta(hours=hours)
            await self.session.commit()

            logger.info(f"Token extended: {admin_token.token_prefix}")
            return True

        except Exception as e:
            logger.error(f"Error extending token: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def get_admin_id_from_token(self, raw_token: str) -> Optional[int]:
        """Get admin_id from a validated token."""
        try:
            admin_token = await self.validate_token(raw_token)
            if admin_token:
                return admin_token.admin_id
            return None
        except Exception as e:
            logger.error(f"Error getting admin_id from token: {e}", exc_info=True)
            return None
