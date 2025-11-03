"""Files API endpoints for Domik sandbox operations.

This module provides HTTP endpoints for safe file operations within
the sandboxed game creation environment.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.domik_service import DomikService
from services.token_service import TokenService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/files", tags=["files"])


class FileReadRequest(BaseModel):
    """File read request model."""

    path: str = Field(..., description="File path to read")


class FileWriteRequest(BaseModel):
    """File write request model."""

    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="File content to write")


class DirectoryListRequest(BaseModel):
    """Directory list request model."""

    path: str = Field(default="", description="Directory path to list")


class DirectoryCreateRequest(BaseModel):
    """Directory create request model."""

    path: str = Field(..., description="Directory path to create")


class FileDeleteRequest(BaseModel):
    """File/directory delete request model."""

    path: str = Field(..., description="File or directory path to delete")


class FileOperationResponse(BaseModel):
    """File operation response model."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Success or error message")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation result data")


def create_files_router(
    token_service: TokenService, domik_service: DomikService
) -> APIRouter:
    """Create and configure the files router with dependencies."""

    async def validate_request(request: Request) -> int:
        """Validate request and return admin ID."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Missing or invalid Authorization header"
            )

        token = auth_header[7:]
        admin_token = await token_service.validate_token(token)

        if not admin_token:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

        return admin_token.created_by

    @router.post("/read", response_model=FileOperationResponse)
    async def read_file(
        request: FileReadRequest, http_request: Request
    ) -> JSONResponse:
        """Read a file from the sandbox."""
        try:
            admin_id = await validate_request(http_request)
            result = await domik_service.read_file(request.path, admin_id)

            return JSONResponse(
                content=FileOperationResponse(
                    success=result["success"],
                    message=result.get("message", "Operation completed"),
                    data=result if result["success"] else None,
                ).dict(),
                status_code=200 if result["success"] else 400,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in read_file endpoint: {e}", exc_info=True)
            return JSONResponse(
                content=FileOperationResponse(
                    success=False, message="Internal server error"
                ).dict(),
                status_code=500,
            )

    @router.post("/write", response_model=FileOperationResponse)
    async def write_file(
        request: FileWriteRequest, http_request: Request
    ) -> JSONResponse:
        """Write content to a file in the sandbox."""
        try:
            admin_id = await validate_request(http_request)
            result = await domik_service.write_file(
                request.path, request.content, admin_id
            )

            return JSONResponse(
                content=FileOperationResponse(
                    success=result["success"],
                    message=result.get("message", "Operation completed"),
                    data=result if result["success"] else None,
                ).dict(),
                status_code=200 if result["success"] else 400,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in write_file endpoint: {e}", exc_info=True)
            return JSONResponse(
                content=FileOperationResponse(
                    success=False, message="Internal server error"
                ).dict(),
                status_code=500,
            )

    @router.post("/list", response_model=FileOperationResponse)
    async def list_directory(
        request: DirectoryListRequest, http_request: Request
    ) -> JSONResponse:
        """List files and directories in the sandbox."""
        try:
            admin_id = await validate_request(http_request)
            result = await domik_service.list_directory(request.path, admin_id)

            return JSONResponse(
                content=FileOperationResponse(
                    success=result["success"],
                    message=result.get("message", "Operation completed"),
                    data=result if result["success"] else None,
                ).dict(),
                status_code=200 if result["success"] else 400,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in list_directory endpoint: {e}", exc_info=True)
            return JSONResponse(
                content=FileOperationResponse(
                    success=False, message="Internal server error"
                ).dict(),
                status_code=500,
            )

    @router.post("/create-directory", response_model=FileOperationResponse)
    async def create_directory(
        request: DirectoryCreateRequest, http_request: Request
    ) -> JSONResponse:
        """Create a new directory in the sandbox."""
        try:
            admin_id = await validate_request(http_request)
            result = await domik_service.create_directory(request.path, admin_id)

            return JSONResponse(
                content=FileOperationResponse(
                    success=result["success"],
                    message=result.get("message", "Operation completed"),
                    data=result if result["success"] else None,
                ).dict(),
                status_code=200 if result["success"] else 400,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create_directory endpoint: {e}", exc_info=True)
            return JSONResponse(
                content=FileOperationResponse(
                    success=False, message="Internal server error"
                ).dict(),
                status_code=500,
            )

    @router.post("/delete", response_model=FileOperationResponse)
    async def delete_file_or_directory(
        request: FileDeleteRequest, http_request: Request
    ) -> JSONResponse:
        """Delete a file or directory from the sandbox."""
        try:
            admin_id = await validate_request(http_request)
            result = await domik_service.delete_file_or_directory(
                request.path, admin_id
            )

            return JSONResponse(
                content=FileOperationResponse(
                    success=result["success"],
                    message=result.get("message", "Operation completed"),
                    data=result if result["success"] else None,
                ).dict(),
                status_code=200 if result["success"] else 400,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error in delete_file_or_directory endpoint: {e}", exc_info=True
            )
            return JSONResponse(
                content=FileOperationResponse(
                    success=False, message="Internal server error"
                ).dict(),
                status_code=500,
            )

    @router.get("/templates", response_model=Dict[str, Any])
    async def get_game_templates(http_request: Request) -> JSONResponse:
        """Get available game templates."""
        try:
            await validate_request(http_request)  # Validate authentication
            result = await domik_service.get_game_templates()

            return JSONResponse(content=result, status_code=200)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_game_templates endpoint: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "success": False,
                    "message": "Internal server error",
                    "templates": {},
                },
                status_code=500,
            )

    @router.post("/validate-json", response_model=Dict[str, Any])
    async def validate_json_content(
        request: FileWriteRequest, http_request: Request
    ) -> JSONResponse:
        """Validate JSON content for game files."""
        try:
            await validate_request(http_request)  # Validate authentication
            result = await domik_service.validate_json_content(request.content)

            return JSONResponse(content=result, status_code=200)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in validate_json_content endpoint: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "valid": False,
                    "error": "Validation service error",
                    "message": "Failed to validate JSON content",
                },
                status_code=500,
            )

    @router.get("/info", response_model=Dict[str, Any])
    async def get_sandbox_info(http_request: Request) -> JSONResponse:
        """Get information about the sandbox environment."""
        try:
            await validate_request(http_request)  # Validate authentication

            return JSONResponse(
                content={
                    "success": True,
                    "sandbox_path": str(domik_service.sandbox_base_path),
                    "allowed_extensions": list(domik_service.allowed_extensions),
                    "max_file_size": domik_service.max_file_size,
                    "max_directory_size": domik_service.max_directory_size,
                    "features": {
                        "read_files": True,
                        "write_files": True,
                        "list_directories": True,
                        "create_directories": True,
                        "delete_files": True,
                        "validate_json": True,
                        "game_templates": True,
                    },
                    "message": "Sandbox information retrieved successfully",
                },
                status_code=200,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_sandbox_info endpoint: {e}", exc_info=True)
            return JSONResponse(
                content={"success": False, "message": "Failed to get sandbox info"},
                status_code=500,
            )

    return router


def get_files_router(
    token_service: TokenService, domik_service: DomikService
) -> APIRouter:
    """Get the configured files router."""
    return create_files_router(token_service, domik_service)
