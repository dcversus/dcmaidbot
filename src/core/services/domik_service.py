"""Domik service for sandbox file operations.

This service provides safe file operations within a sandboxed environment
for the webapp game creator, allowing dcmaidbot to manage game files
securely.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Tuple

from src.core.services.token_service import TokenService

logger = logging.getLogger(__name__)


class DomikService:
    """Service for managing sandboxed file operations."""

    def __init__(self, token_service: TokenService, sandbox_base_path: str = "games"):
        """Initialize Domik service with token validation and sandbox path."""
        self.token_service = token_service
        self.sandbox_base_path = Path(sandbox_base_path)

        # Create sandbox directory if it doesn't exist
        self.sandbox_base_path.mkdir(exist_ok=True)

        # Define allowed file extensions for security
        self.allowed_extensions = {
            ".json",
            ".txt",
            ".md",
            ".html",
            ".css",
            ".js",
            ".py",
            ".xml",
            ".yaml",
            ".yml",
        }

        # Define maximum file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

        # Define maximum directory size (100MB)
        self.max_directory_size = 100 * 1024 * 1024

    async def validate_file_path(
        self, file_path: str, admin_id: int
    ) -> Tuple[bool, str]:
        """Validate that a file path is safe and within the sandbox."""
        try:
            # Clean the path to prevent directory traversal
            clean_path = Path(file_path).as_posix()
            clean_path = clean_path.replace("..", "").replace("//", "/")

            # Create the full path within the sandbox
            full_path = self.sandbox_base_path / clean_path

            # Ensure the path is within the sandbox
            try:
                full_path.resolve().relative_to(self.sandbox_base_path.resolve())
            except ValueError:
                return False, "Path outside sandbox is not allowed"

            # Check file extension
            if full_path.suffix and full_path.suffix not in self.allowed_extensions:
                return False, f"File extension '{full_path.suffix}' is not allowed"

            return True, str(full_path)

        except Exception as e:
            logger.error(f"Error validating file path '{file_path}': {e}")
            return False, f"Invalid file path: {str(e)}"

    async def read_file(self, file_path: str, admin_id: int) -> Dict[str, Any]:
        """Read a file from the sandbox."""
        try:
            # Validate path
            is_valid, validated_path_or_error = await self.validate_file_path(
                file_path, admin_id
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": validated_path_or_error,
                    "message": "File path validation failed",
                }

            file_path_obj = Path(validated_path_or_error)

            # Check if file exists
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"The file '{file_path}' does not exist",
                }

            # Check if it's a file (not directory)
            if not file_path_obj.is_file():
                return {
                    "success": False,
                    "error": "Not a file",
                    "message": f"The path '{file_path}' is not a file",
                }

            # Check file size
            file_size = file_path_obj.stat().st_size
            if file_size > self.max_file_size:
                return {
                    "success": False,
                    "error": "File too large",
                    "message": f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)",
                }

            # Read file content
            try:
                with open(file_path_obj, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try binary read for non-text files
                with open(file_path_obj, "rb") as f:
                    content = f.read()
                content = f"[Binary file - {len(content)} bytes]"

            logger.info(f"File read successfully: {file_path} (admin: {admin_id})")

            return {
                "success": True,
                "content": content,
                "size": file_size,
                "path": str(file_path_obj.relative_to(self.sandbox_base_path)),
                "message": f"File '{file_path}' read successfully",
            }

        except Exception as e:
            logger.error(f"Error reading file '{file_path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "Read failed",
                "message": f"Failed to read file: {str(e)}",
            }

    async def write_file(
        self, file_path: str, content: str, admin_id: int
    ) -> Dict[str, Any]:
        """Write content to a file in the sandbox."""
        try:
            # Validate path
            is_valid, validated_path_or_error = await self.validate_file_path(
                file_path, admin_id
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": validated_path_or_error,
                    "message": "File path validation failed",
                }

            file_path_obj = Path(validated_path_or_error)

            # Check content size
            content_size = len(content.encode("utf-8"))
            if content_size > self.max_file_size:
                return {
                    "success": False,
                    "error": "Content too large",
                    "message": f"Content size ({content_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)",
                }

            # Check directory size
            directory_size = self._get_directory_size(file_path_obj.parent)
            if directory_size + content_size > self.max_directory_size:
                return {
                    "success": False,
                    "error": "Directory quota exceeded",
                    "message": f"Directory size would exceed maximum allowed size ({self.max_directory_size} bytes)",
                }

            # Create parent directories if they don't exist
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(file_path_obj, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"File written successfully: {file_path} (admin: {admin_id})")

            return {
                "success": True,
                "size": content_size,
                "path": str(file_path_obj.relative_to(self.sandbox_base_path)),
                "message": f"File '{file_path}' written successfully",
            }

        except Exception as e:
            logger.error(f"Error writing file '{file_path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "Write failed",
                "message": f"Failed to write file: {str(e)}",
            }

    async def list_directory(
        self, dir_path: str = "", admin_id: int = None
    ) -> Dict[str, Any]:
        """List files and directories in the sandbox."""
        try:
            # Validate path (empty path means sandbox root)
            if not dir_path:
                target_path = self.sandbox_base_path
            else:
                is_valid, validated_path_or_error = await self.validate_file_path(
                    dir_path, admin_id
                )
                if not is_valid:
                    return {
                        "success": False,
                        "error": validated_path_or_error,
                        "message": "Directory path validation failed",
                    }
                target_path = Path(validated_path_or_error)

            # Check if path exists and is a directory
            if not target_path.exists():
                return {
                    "success": False,
                    "error": "Directory not found",
                    "message": f"The directory '{dir_path}' does not exist",
                }

            if not target_path.is_dir():
                return {
                    "success": False,
                    "error": "Not a directory",
                    "message": f"The path '{dir_path}' is not a directory",
                }

            # List directory contents
            items = []
            try:
                for item in target_path.iterdir():
                    relative_path = item.relative_to(self.sandbox_base_path)

                    if item.is_file():
                        items.append(
                            {
                                "name": item.name,
                                "path": str(relative_path),
                                "type": "file",
                                "size": item.stat().st_size,
                                "extension": item.suffix,
                                "modified": item.stat().st_mtime,
                            }
                        )
                    elif item.is_dir():
                        items.append(
                            {
                                "name": item.name,
                                "path": str(relative_path),
                                "type": "directory",
                                "size": self._get_directory_size(item),
                                "modified": item.stat().st_mtime,
                            }
                        )

                # Sort items: directories first, then files, both alphabetically
                items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "message": f"Permission denied to read directory '{dir_path}'",
                }

            logger.info(
                f"Directory listed successfully: {dir_path} (admin: {admin_id})"
            )

            return {
                "success": True,
                "items": items,
                "path": str(target_path.relative_to(self.sandbox_base_path)),
                "count": len(items),
                "message": f"Directory '{dir_path}' listed successfully",
            }

        except Exception as e:
            logger.error(f"Error listing directory '{dir_path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "List failed",
                "message": f"Failed to list directory: {str(e)}",
            }

    async def create_directory(self, dir_path: str, admin_id: int) -> Dict[str, Any]:
        """Create a new directory in the sandbox."""
        try:
            # Validate path
            is_valid, validated_path_or_error = await self.validate_file_path(
                dir_path, admin_id
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": validated_path_or_error,
                    "message": "Directory path validation failed",
                }

            dir_path_obj = Path(validated_path_or_error)

            # Check if directory already exists
            if dir_path_obj.exists():
                return {
                    "success": False,
                    "error": "Directory exists",
                    "message": f"The directory '{dir_path}' already exists",
                }

            # Create directory
            dir_path_obj.mkdir(parents=True, exist_ok=True)

            logger.info(
                f"Directory created successfully: {dir_path} (admin: {admin_id})"
            )

            return {
                "success": True,
                "path": str(dir_path_obj.relative_to(self.sandbox_base_path)),
                "message": f"Directory '{dir_path}' created successfully",
            }

        except Exception as e:
            logger.error(f"Error creating directory '{dir_path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "Create failed",
                "message": f"Failed to create directory: {str(e)}",
            }

    async def delete_file_or_directory(
        self, path: str, admin_id: int
    ) -> Dict[str, Any]:
        """Delete a file or directory from the sandbox."""
        try:
            # Validate path
            is_valid, validated_path_or_error = await self.validate_file_path(
                path, admin_id
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": validated_path_or_error,
                    "message": "Path validation failed",
                }

            path_obj = Path(validated_path_or_error)

            # Check if path exists
            if not path_obj.exists():
                return {
                    "success": False,
                    "error": "Path not found",
                    "message": f"The path '{path}' does not exist",
                }

            # Delete file or directory
            if path_obj.is_file():
                path_obj.unlink()
                item_type = "file"
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
                item_type = "directory"
            else:
                return {
                    "success": False,
                    "error": "Unknown path type",
                    "message": f"The path '{path}' is neither a file nor a directory",
                }

            logger.info(
                f"{item_type.capitalize()} deleted successfully: {path} (admin: {admin_id})"
            )

            return {
                "success": True,
                "path": str(path_obj.relative_to(self.sandbox_base_path)),
                "type": item_type,
                "message": f"{item_type.capitalize()} '{path}' deleted successfully",
            }

        except Exception as e:
            logger.error(f"Error deleting '{path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "Delete failed",
                "message": f"Failed to delete: {str(e)}",
            }

    async def get_game_templates(self) -> Dict[str, Any]:
        """Get available game templates."""
        templates = {
            "quiz": {
                "name": "Quiz Game",
                "description": "A question-and-answer game with multiple choice questions",
                "template": {
                    "type": "quiz",
                    "title": "My Awesome Quiz",
                    "description": "A fun quiz game!",
                    "questions": [
                        {
                            "question": "What is 2 + 2?",
                            "options": ["3", "4", "5", "6"],
                            "correct": 1,
                            "points": 10,
                        }
                    ],
                    "settings": {
                        "time_limit": 30,
                        "shuffle_questions": False,
                        "show_correct_answers": True,
                    },
                },
            },
            "story": {
                "name": "Story Game",
                "description": "An interactive branching story game",
                "template": {
                    "type": "story",
                    "title": "My Adventure Story",
                    "description": "An interactive story!",
                    "start_scene": "beginning",
                    "scenes": {
                        "beginning": {
                            "text": "You are at the beginning of an adventure...",
                            "choices": [
                                {"text": "Go left", "next_scene": "left_path"},
                                {"text": "Go right", "next_scene": "right_path"},
                            ],
                        }
                    },
                },
            },
            "puzzle": {
                "name": "Puzzle Game",
                "description": "A challenging puzzle game",
                "template": {
                    "type": "puzzle",
                    "title": "My Fun Puzzle",
                    "description": "A challenging puzzle game!",
                    "difficulty": "medium",
                    "puzzle_type": "pattern",
                    "grid_size": [4, 4],
                    "solution": [
                        [1, 2, 3, 4],
                        [5, 6, 7, 8],
                        [9, 10, 11, 12],
                        [13, 14, 15, 0],
                    ],
                },
            },
        }

        return {
            "success": True,
            "templates": templates,
            "message": "Game templates retrieved successfully",
        }

    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of a directory."""
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except (PermissionError, OSError):
            pass
        return total_size

    async def validate_json_content(self, content: str) -> Dict[str, Any]:
        """Validate JSON content for game files."""
        try:
            parsed = json.loads(content)

            # Basic validation for game structure
            if not isinstance(parsed, dict):
                return {"valid": False, "error": "Content must be a JSON object"}

            if "type" not in parsed:
                return {"valid": False, "error": "Game must have a 'type' field"}

            if "title" not in parsed:
                return {"valid": False, "error": "Game must have a 'title' field"}

            return {"valid": True, "parsed": parsed, "message": "JSON content is valid"}

        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON: {str(e)}",
                "message": "JSON content is not valid",
            }
