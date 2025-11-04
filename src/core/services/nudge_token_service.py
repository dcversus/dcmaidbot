"""Nudge token service for dynamic nudge token management.

This service provides business logic for creating, managing, and validating
nudge tokens for agent-to-user communication via the /nudge endpoint.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.nudge_token import NudgeToken

logger = logging.getLogger(__name__)


class NudgeTokenService:
    """Service for managing nudge tokens."""

    def __init__(self, session: AsyncSession):
        """Initialize nudge token service with database session."""
        self.session = session

    async def create_nudge_token(
        self,
        name: str,
        created_by: int,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> tuple[NudgeToken, str]:
        """Create a new nudge token and return both the object and the raw token."""
        # Generate the actual token
        raw_token = NudgeToken.generate_token()
        token_hash = NudgeToken.hash_token(raw_token)
        token_prefix = raw_token[:8]

        nudge_token = NudgeToken(
            name=name,
            token_hash=token_hash,
            token_prefix=token_prefix,
            description=description,
            expires_at=expires_at,
            created_by=created_by,
        )

        self.session.add(nudge_token)
        await self.session.commit()
        await self.session.refresh(nudge_token)

        logger.info(f"Created nudge token: {name} (prefix: {token_prefix})")
        return nudge_token, raw_token

    async def validate_nudge_token(self, token: str) -> Optional[NudgeToken]:
        """Validate a nudge token and return the token object if valid."""
        token_hash = NudgeToken.hash_token(token)

        result = await self.session.execute(
            select(NudgeToken).where(
                and_(
                    NudgeToken.token_hash == token_hash,
                    NudgeToken.is_active,
                )
            )
        )
        nudge_token = result.scalar_one_or_none()

        if not nudge_token:
            logger.warning("Invalid or inactive nudge token used")
            return None

        # Check if expired
        if nudge_token.is_expired():
            logger.warning(f"Expired nudge token used: {nudge_token.name}")
            return None

        # Update usage statistics
        await self.update_token_usage(nudge_token.id)

        return nudge_token

    async def update_token_usage(self, token_id: int) -> None:
        """Update token usage statistics."""
        try:
            await self.session.execute(
                update(NudgeToken)
                .where(NudgeToken.id == token_id)
                .values(
                    usage_count=NudgeToken.usage_count + 1,
                    last_used_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error updating nudge token usage: {e}", exc_info=True)

    async def get_nudge_tokens_by_creator(self, created_by: int) -> list[NudgeToken]:
        """Get all nudge tokens created by a specific user."""
        result = await self.session.execute(
            select(NudgeToken)
            .where(NudgeToken.created_by == created_by)
            .order_by(NudgeToken.created_at.desc())
        )
        return result.scalars().all()

    async def deactivate_nudge_token(self, token_id: int) -> bool:
        """Deactivate a nudge token."""
        try:
            result = await self.session.execute(
                update(NudgeToken)
                .where(NudgeToken.id == token_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            await self.session.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error deactivating nudge token: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def get_nudge_token_by_id(self, token_id: int) -> Optional[NudgeToken]:
        """Get a nudge token by its database ID."""
        result = await self.session.execute(
            select(NudgeToken).where(NudgeToken.id == token_id)
        )
        return result.scalar_one_or_none()

    async def get_nudge_token_by_name(
        self, name: str, created_by: int
    ) -> Optional[NudgeToken]:
        """Get a nudge token by name and creator."""
        result = await self.session.execute(
            select(NudgeToken).where(
                and_(NudgeToken.name == name, NudgeToken.created_by == created_by)
            )
        )
        return result.scalar_one_or_none()

    async def delete_old_tokens(self, days: int = 90) -> int:
        """Delete nudge tokens older than specified days."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await self.session.execute(
                delete(NudgeToken).where(NudgeToken.created_at < cutoff_date)
            )

            await self.session.commit()
            return result.rowcount

        except Exception as e:
            logger.error(f"Error deleting old nudge tokens: {e}", exc_info=True)
            await self.session.rollback()
            return 0

    async def get_active_tokens_count(self, created_by: Optional[int] = None) -> int:
        """Get count of active nudge tokens."""
        query = select(NudgeToken).where(NudgeToken.is_active)

        if created_by:
            query = query.where(NudgeToken.created_by == created_by)

        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def get_token_statistics(
        self, created_by: Optional[int] = None
    ) -> dict[str, Any]:
        """Get statistics about nudge tokens."""
        try:
            base_query = select(NudgeToken)
            if created_by:
                base_query = base_query.where(NudgeToken.created_by == created_by)

            result = await self.session.execute(base_query)
            tokens = result.scalars().all()

            stats = {
                "total_tokens": len(tokens),
                "active_tokens": len([t for t in tokens if t.is_active]),
                "inactive_tokens": len([t for t in tokens if not t.is_active]),
                "expired_tokens": len([t for t in tokens if t.is_expired()]),
                "total_usage": sum(t.usage_count for t in tokens),
                "tokens_with_usage": len([t for t in tokens if t.usage_count > 0]),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting nudge token statistics: {e}", exc_info=True)
            return {}
