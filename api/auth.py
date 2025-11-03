"""Authentication API endpoints for webapp admin access.

This module provides HTTP endpoints for token-based authentication
and admin session management for the Telegram webapp.
"""

import logging
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.token_service import TokenService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])


class AuthRequest(BaseModel):
    """Authentication request model."""

    token: str = Field(..., description="Admin authentication token")


class AuthResponse(BaseModel):
    """Authentication response model."""

    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Success or error message")
    admin_id: Optional[int] = Field(None, description="Admin user ID if successful")
    token_info: Optional[Dict] = Field(None, description="Token information")


class TokenCreateRequest(BaseModel):
    """Token creation request model."""

    name: str = Field(..., description="Token name for identification")
    description: Optional[str] = Field(None, description="Token description")
    expires_hours: int = Field(default=24, description="Token expiration in hours")


class TokenCreateResponse(BaseModel):
    """Token creation response model."""

    success: bool = Field(..., description="Whether token creation was successful")
    token: Optional[str] = Field(None, description="Generated token")
    token_info: Optional[Dict] = Field(None, description="Token information")
    message: str = Field(..., description="Success or error message")


def create_auth_router(token_service: TokenService) -> APIRouter:
    """Create and configure the authentication router with dependencies."""

    @router.post("/validate", response_model=AuthResponse)
    async def validate_token(
        auth_request: AuthRequest, request: Request
    ) -> JSONResponse:
        """
        Validate an admin authentication token.

        This endpoint validates tokens presented by the webapp and returns
        admin information if the token is valid.
        """
        try:
            # Extract token from request
            token = auth_request.token

            if not token:
                raise HTTPException(status_code=400, detail="Token is required")

            # Validate token
            admin_token = await token_service.validate_token(token)

            if not admin_token:
                logger.warning(
                    f"Failed token validation attempt from {request.client.host}"
                )
                return JSONResponse(
                    content=AuthResponse(
                        success=False,
                        message="Invalid or expired token",
                        admin_id=None,
                        token_info=None,
                    ).dict(),
                    status_code=401,
                )

            # Token is valid - return success with admin info
            logger.info(
                f"Successful token validation for admin {admin_token.created_by}"
            )

            return JSONResponse(
                content=AuthResponse(
                    success=True,
                    message="Authentication successful",
                    admin_id=admin_token.created_by,
                    token_info={
                        "name": admin_token.name,
                        "prefix": admin_token.token_prefix,
                        "created_at": admin_token.created_at.isoformat(),
                        "expires_at": admin_token.expires_at.isoformat(),
                        "last_used_at": admin_token.last_used_at.isoformat()
                        if admin_token.last_used_at
                        else None,
                    },
                ).dict()
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during token validation: {e}", exc_info=True)
            return JSONResponse(
                content=AuthResponse(
                    success=False,
                    message="Authentication service error",
                    admin_id=None,
                    token_info=None,
                ).dict(),
                status_code=500,
            )

    @router.post("/check", response_model=Dict)
    async def check_authentication(request: Request) -> JSONResponse:
        """
        Check if a token in the Authorization header is valid.

        This endpoint provides a simple check for middleware and other
        components to validate tokens without requiring a full login flow.
        """
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content={
                        "valid": False,
                        "message": "Missing or invalid Authorization header",
                    },
                    status_code=401,
                )

            token = auth_header[7:]  # Remove "Bearer " prefix

            if token == "anonymous":
                # Allow anonymous access for public features
                return JSONResponse(
                    content={
                        "valid": True,
                        "anonymous": True,
                        "message": "Anonymous access granted",
                    }
                )

            # Validate admin token
            admin_token = await token_service.validate_token(token)

            if not admin_token:
                return JSONResponse(
                    content={"valid": False, "message": "Invalid or expired token"},
                    status_code=401,
                )

            # Token is valid
            return JSONResponse(
                content={
                    "valid": True,
                    "anonymous": False,
                    "admin_id": admin_token.created_by,
                    "token_name": admin_token.name,
                    "message": "Token is valid",
                }
            )

        except Exception as e:
            logger.error(f"Error during authentication check: {e}", exc_info=True)
            return JSONResponse(
                content={"valid": False, "message": "Authentication check failed"},
                status_code=500,
            )

    @router.get("/status", response_model=Dict)
    async def auth_status(request: Request) -> JSONResponse:
        """
        Get authentication status without requiring a token.

        This endpoint returns information about the authentication service
        status and requirements for the webapp.
        """
        try:
            return JSONResponse(
                content={
                    "status": "operational",
                    "auth_required": True,
                    "supports_anonymous": True,
                    "token_length": 43,  # URL-safe token length
                    "token_format": "URL-safe base64 encoded string",
                    "version": "1.0.0",
                }
            )

        except Exception as e:
            logger.error(f"Error getting auth status: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Authentication status unavailable",
                },
                status_code=500,
            )

    return router


def get_auth_router(token_service: TokenService) -> APIRouter:
    """Get the configured authentication router."""
    return create_auth_router(token_service)
