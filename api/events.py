"""Events API endpoint for collecting webapp events.

This module provides HTTP endpoints for collecting events from the Telegram
webapp and managing event processing for the dcmaidbot integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.event_service import EventService
from services.token_service import TokenService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["events"])


class WebappEvent(BaseModel):
    """Webapp event model for API validation."""

    id: str = Field(..., description="Unique event identifier")
    type: str = Field(
        ..., description="Event type (e.g., 'button_click', 'auth_success')"
    )
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    timestamp: int = Field(..., description="Unix timestamp of the event")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    session_id: Optional[str] = Field(None, description="Session identifier")


class EventResponse(BaseModel):
    """Response model for event endpoints."""

    success: bool = Field(True, description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Success/error message")
    event_id: Optional[str] = Field(None, description="Processed event ID")


def create_events_router(
    token_service: TokenService, event_service: EventService
) -> APIRouter:
    """Create and configure the events router with dependencies."""

    @router.post("/events", response_model=EventResponse)
    async def collect_event(
        event: WebappEvent, request: Request, response: Response
    ) -> JSONResponse:
        """
        Collect an event from the webapp.

        This endpoint receives events from the Telegram webapp and stores them
        for processing by dcmaidbot. Events are authenticated via bearer token.
        """
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid Authorization header"
                )

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate token (allow anonymous events for public interactions)
            admin_token = None
            user_id = None

            if token != "anonymous":
                admin_token = await token_service.validate_token(token)
                if not admin_token:
                    raise HTTPException(
                        status_code=403, detail="Invalid or expired token"
                    )
                user_id = admin_token.created_by
            else:
                # Anonymous user - use default user ID
                user_id = 0

            # Store event using existing EventService
            db_event = await event_service.create_event(
                event_id=event.id,
                user_id=user_id,
                event_type=event.type,
                data=event.data,
                event_subtype="webapp",
                user_agent=event.user_agent,
                session_id=event.session_id,
                # Convert timestamp to datetime
                created_at=datetime.fromtimestamp(event.timestamp / 1000)
                if event.timestamp > 1e10
                else datetime.fromtimestamp(event.timestamp),
            )

            # Log the event
            logger.info(
                f"Collected webapp event: {event.type} (ID: {event.id}, User: {user_id})"
            )

            # Return success response
            return JSONResponse(
                content=EventResponse(
                    success=True,
                    message="Event collected successfully",
                    event_id=db_event.event_id,
                ).dict(),
                status_code=201,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error collecting event {event.id}: {e}", exc_info=True)
            return JSONResponse(
                content=EventResponse(
                    success=False, message=f"Failed to collect event: {str(e)}"
                ).dict(),
                status_code=500,
            )

    @router.get("/events", response_model=Dict[str, Any])
    async def get_events(
        request: Request,
        limit: int = 50,
        unread_only: bool = False,
        event_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        Retrieve events for processing by dcmaidbot.

        This endpoint allows dcmaidbot to read events from the webapp.
        Requires valid admin token for access.
        """
        try:
            # Extract and validate token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid Authorization header"
                )

            token = auth_header[7:]
            admin_token = await token_service.validate_token(token)
            if not admin_token:
                raise HTTPException(status_code=403, detail="Invalid or expired token")

            # Get events based on parameters
            if unread_only:
                events = await event_service.get_unread_events(
                    limit=limit, event_types=[event_type] if event_type else None
                )
            else:
                events = await event_service.get_events_for_user(
                    user_id=admin_token.created_by, event_type=event_type, limit=limit
                )

            # Convert events to dictionary format
            events_data = []
            for event in events:
                events_data.append(
                    {
                        "id": event.event_id,
                        "type": event.event_type,
                        "subtype": event.event_subtype,
                        "data": event.data,
                        "status": event.status,
                        "created_at": event.created_at.isoformat(),
                        "processed_at": event.processed_at.isoformat()
                        if event.processed_at
                        else None,
                        "user_agent": event.user_agent,
                        "session_id": event.session_id,
                    }
                )

            return JSONResponse(
                content={
                    "success": True,
                    "events": events_data,
                    "count": len(events_data),
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving events: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"Failed to retrieve events: {str(e)}",
                },
                status_code=500,
            )

    @router.post("/events/{event_id}/read", response_model=EventResponse)
    async def mark_event_read(event_id: str, request: Request) -> JSONResponse:
        """
        Mark an event as read (processed).

        This endpoint allows dcmaidbot to mark events as processed
        after handling them.
        """
        try:
            # Extract and validate token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid Authorization header"
                )

            token = auth_header[7:]
            admin_token = await token_service.validate_token(token)
            if not admin_token:
                raise HTTPException(status_code=403, detail="Invalid or expired token")

            # Mark event as read
            success = await event_service.update_event_status(event_id, "read")

            if success:
                return JSONResponse(
                    content=EventResponse(
                        success=True,
                        message=f"Event {event_id} marked as read",
                        event_id=event_id,
                    ).dict()
                )
            else:
                return JSONResponse(
                    content=EventResponse(
                        success=False, message=f"Event {event_id} not found"
                    ).dict(),
                    status_code=404,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking event {event_id} as read: {e}", exc_info=True)
            return JSONResponse(
                content=EventResponse(
                    success=False, message=f"Failed to mark event as read: {str(e)}"
                ).dict(),
                status_code=500,
            )

    @router.post("/events/mark-read", response_model=EventResponse)
    async def mark_multiple_events_read(
        request: Request, event_ids: list[str] = []
    ) -> JSONResponse:
        """
        Mark multiple events as read.

        This endpoint allows dcmaidbot to batch mark events as processed.
        """
        try:
            # Extract and validate token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid Authorization header"
                )

            token = auth_header[7:]
            admin_token = await token_service.validate_token(token)
            if not admin_token:
                raise HTTPException(status_code=403, detail="Invalid or expired token")

            # Mark events as read
            count = await event_service.mark_events_as_read(event_ids)

            return JSONResponse(
                content=EventResponse(
                    success=True, message=f"Marked {count} events as read"
                ).dict()
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking events as read: {e}", exc_info=True)
            return JSONResponse(
                content=EventResponse(
                    success=False, message=f"Failed to mark events as read: {str(e)}"
                ).dict(),
                status_code=500,
            )

    @router.get("/events/stats", response_model=Dict[str, Any])
    async def get_event_stats(request: Request, days: int = 7) -> JSONResponse:
        """
        Get statistics about webapp events.

        This endpoint provides analytics for admin monitoring.
        """
        try:
            # Extract and validate token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid Authorization header"
                )

            token = auth_header[7:]
            admin_token = await token_service.validate_token(token)
            if not admin_token:
                raise HTTPException(status_code=403, detail="Invalid or expired token")

            # Get statistics
            stats = await event_service.get_event_statistics(
                user_id=admin_token.created_by, days=days
            )

            return JSONResponse(
                content={"success": True, "stats": stats, "period_days": days}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting event stats: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"Failed to get event stats: {str(e)}",
                },
                status_code=500,
            )

    return router


# Initialize router function for easy import
def get_events_router(
    token_service: TokenService, event_service: EventService
) -> APIRouter:
    """Get the configured events router."""
    return create_events_router(token_service, event_service)
