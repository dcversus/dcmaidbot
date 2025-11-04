"""Event service for managing universal event collection system.

This service provides business logic for storing, retrieving,
and processing events collected from Telegram interactions.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.api_key import ApiKey
from src.core.models.event import Event

logger = logging.getLogger(__name__)


class EventService:
    """Service for managing event collection and processing."""

    def __init__(self, session: AsyncSession):
        """Initialize event service with database session."""
        self.session = session

    async def create_event(
        self,
        event_id: str,
        user_id: int,
        event_type: str,
        data: dict[str, Any],
        **kwargs,
    ) -> Event:
        """Create a new event record."""
        # Check for duplicate event_id
        existing = await self.get_event_by_id(event_id)
        if existing:
            raise ValueError(f"Event with ID '{event_id}' already exists")

        event = Event(
            event_id=event_id,
            user_id=user_id,
            chat_id=kwargs.get("chat_id"),
            event_type=event_type,
            event_subtype=kwargs.get("event_subtype"),
            data=data,
            button_text=kwargs.get("button_text"),
            callback_data=kwargs.get("callback_data"),
            status=kwargs.get("status", "unread"),
        )

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)

        logger.info(f"Created event: {event_id} (type: {event_type}, user: {user_id})")
        return event

    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get an event by its ID."""
        result = await self.session.execute(
            select(Event).where(Event.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_event_by_internal_id(self, event_internal_id: int) -> Optional[Event]:
        """Get an event by its internal database ID."""
        result = await self.session.execute(
            select(Event).where(Event.id == event_internal_id)
        )
        return result.scalar_one_or_none()

    async def get_events_for_user(
        self,
        user_id: int,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        """Get events for a specific user."""
        query = select(Event).where(Event.user_id == user_id)

        if status:
            query = query.where(Event.status == status)
        if event_type:
            query = query.where(Event.event_type == event_type)

        query = query.order_by(Event.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_unread_events(
        self, limit: int = 100, event_types: Optional[list[str]] = None
    ) -> list[Event]:
        """Get unread events for processing."""
        query = select(Event).where(Event.status == "unread")

        if event_types:
            query = query.where(Event.event_type.in_(event_types))

        query = query.order_by(Event.created_at.asc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_event_status(
        self, event_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        """Update the status of an event."""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if status == "read" or status == "completed":
                update_data["processed_at"] = datetime.utcnow()
            elif status == "failed" and error_message:
                update_data["error_message"] = error_message
                update_data["processing_attempts"] = Event.processing_attempts + 1

            result = await self.session.execute(
                update(Event).where(Event.event_id == event_id).values(**update_data)
            )

            await self.session.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating event status: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def mark_events_as_read(self, event_ids: list[str]) -> int:
        """Mark multiple events as read."""
        try:
            result = await self.session.execute(
                update(Event)
                .where(Event.event_id.in_(event_ids))
                .where(Event.status == "unread")
                .values(
                    status="read",
                    processed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

            await self.session.commit()
            return result.rowcount

        except Exception as e:
            logger.error(f"Error marking events as read: {e}", exc_info=True)
            await self.session.rollback()
            return 0

    async def delete_old_events(self, days: int = 30) -> int:
        """Delete events older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await self.session.execute(
                delete(Event).where(Event.created_at < cutoff_date)
            )

            await self.session.commit()
            return result.rowcount

        except Exception as e:
            logger.error(f"Error deleting old events: {e}", exc_info=True)
            await self.session.rollback()
            return 0

    async def get_event_statistics(
        self, user_id: Optional[int] = None, days: int = 7
    ) -> dict[str, Any]:
        """Get statistics about events."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            query = select(Event).where(Event.created_at >= cutoff_date)
            if user_id:
                query = query.where(Event.user_id == user_id)

            result = await self.session.execute(query)
            events = result.scalars().all()

            # Calculate statistics
            stats = {
                "total_events": len(events),
                "unread_events": len([e for e in events if e.status == "unread"]),
                "read_events": len([e for e in events if e.status == "read"]),
                "completed_events": len([e for e in events if e.status == "completed"]),
                "failed_events": len([e for e in events if e.status == "failed"]),
                "event_types": {},
                "daily_breakdown": {},
            }

            # Event type breakdown
            for event in events:
                event_type = event.event_type
                if event_type not in stats["event_types"]:
                    stats["event_types"][event_type] = 0
                stats["event_types"][event_type] += 1

                # Daily breakdown
                date_key = event.created_at.strftime("%Y-%m-%d")
                if date_key not in stats["daily_breakdown"]:
                    stats["daily_breakdown"][date_key] = 0
                stats["daily_breakdown"][date_key] += 1

            return stats

        except Exception as e:
            logger.error(f"Error getting event statistics: {e}", exc_info=True)
            return {}

    async def search_events(
        self,
        query: str,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[Event]:
        """Search events by content."""
        try:
            base_query = select(Event)

            # Build conditions
            conditions = []

            if user_id:
                conditions.append(Event.user_id == user_id)
            if event_type:
                conditions.append(Event.event_type == event_type)
            if status:
                conditions.append(Event.status == status)

            # Text search in various fields
            search_conditions = [
                Event.button_text.ilike(f"%{query}%"),
                Event.callback_data.ilike(f"%{query}%"),
                Event.event_subtype.ilike(f"%{query}%"),
            ]

            conditions.append(or_(*search_conditions))

            if conditions:
                base_query = base_query.where(and_(*conditions))

            base_query = base_query.order_by(Event.created_at.desc()).limit(limit)

            result = await self.session.execute(base_query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error searching events: {e}", exc_info=True)
            return []

    async def get_events_by_type_and_status(
        self, event_type: str, status: str, limit: int = 100
    ) -> list[Event]:
        """Get events filtered by type and status."""
        result = await self.session.execute(
            select(Event)
            .where(Event.event_type == event_type)
            .where(Event.status == status)
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


class ApiKeyService:
    """Service for managing API keys for event collection."""

    def __init__(self, session: AsyncSession):
        """Initialize API key service with database session."""
        self.session = session

    async def create_api_key(
        self,
        name: str,
        created_by: int,
        allowed_event_types: Optional[list[str]] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> tuple[ApiKey, str]:
        """Create a new API key and return both the object and the raw key."""
        # Generate the actual key
        raw_key = ApiKey.generate_key()
        key_hash = ApiKey.hash_key(raw_key)
        key_prefix = raw_key[:8]

        api_key = ApiKey(
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            allowed_event_types=",".join(allowed_event_types)
            if allowed_event_types
            else None,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            description=description,
            expires_at=expires_at,
            created_by=created_by,
        )

        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)

        logger.info(f"Created API key: {name} (prefix: {key_prefix})")
        return api_key, raw_key

    async def get_api_keys_by_creator(self, created_by: int) -> list[ApiKey]:
        """Get all API keys created by a specific user."""
        result = await self.session.execute(
            select(ApiKey)
            .where(ApiKey.created_by == created_by)
            .order_by(ApiKey.created_at.desc())
        )
        return result.scalars().all()

    async def deactivate_api_key(self, api_key_id: int) -> bool:
        """Deactivate an API key."""
        try:
            result = await self.session.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            await self.session.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error deactivating API key: {e}", exc_info=True)
            await self.session.rollback()
            return False

    async def get_api_key_by_id(self, api_key_id: int) -> Optional[ApiKey]:
        """Get an API key by its ID."""
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        return result.scalar_one_or_none()
