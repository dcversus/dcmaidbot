"""Domik tool for dcmaidbot integration with webapp sandbox.

This tool provides dcmaidbot with the ability to read and write files
in the webapp sandbox, enabling p2p realtime game creation capabilities.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from src.core.services.domik_service import DomikService
from src.core.services.event_service import EventService
from src.core.services.token_service import TokenService

logger = logging.getLogger(__name__)


class DomikTool:
    """Tool for dcmaidbot to interact with the webapp sandbox."""

    def __init__(
        self,
        token_service: TokenService,
        domik_service: DomikService,
        event_service: EventService,
        admin_id: int,
    ):
        """Initialize Domik tool with required services."""
        self.token_service = token_service
        self.domik_service = domik_service
        self.event_service = event_service
        self.admin_id = admin_id

    async def get_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read a file from the webapp sandbox.

        Args:
            file_path: Path to the file to read

        Returns:
            Dictionary with file content and metadata
        """
        try:
            logger.info(
                f"🏠 Domik: Reading file '{file_path}' for admin {self.admin_id}"
            )

            result = await self.domik_service.read_file(file_path, self.admin_id)

            if result["success"]:
                # Emit event for file read
                await self.event_service.create_event(
                    event_id=f"domik_read_{file_path.replace('/', '_')}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_file_read",
                    data={
                        "file_path": file_path,
                        "file_size": result.get("size", 0),
                        "tool": "domik_tool",
                    },
                )

                logger.info(f"✅ Domik: Successfully read file '{file_path}'")
                return {
                    "success": True,
                    "content": result["content"],
                    "size": result.get("size", 0),
                    "path": result.get("path", file_path),
                    "message": f"File '{file_path}' read successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to read file '{file_path}': {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to read file '{file_path}'",
                }

        except Exception as e:
            logger.error(
                f"💥 Domik: Error reading file '{file_path}': {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Error reading file '{file_path}'",
            }

    async def edit_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file in the webapp sandbox.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file

        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(
                f"🏠 Domik: Writing file '{file_path}' for admin {self.admin_id}"
            )

            # Validate JSON content if it's a JSON file
            if file_path.endswith(".json"):
                validation_result = await self.domik_service.validate_json_content(
                    content
                )
                if not validation_result["valid"]:
                    logger.warning(
                        f"⚠️ Domik: JSON validation failed for '{file_path}': {validation_result.get('error')}"
                    )
                    return {
                        "success": False,
                        "error": f"JSON validation failed: {validation_result.get('error')}",
                        "message": f"File '{file_path}' contains invalid JSON",
                    }

            result = await self.domik_service.write_file(
                file_path, content, self.admin_id
            )

            if result["success"]:
                # Emit event for file write
                await self.event_service.create_event(
                    event_id=f"domik_write_{file_path.replace('/', '_')}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_file_write",
                    data={
                        "file_path": file_path,
                        "content_size": result.get("size", 0),
                        "tool": "domik_tool",
                    },
                )

                logger.info(
                    f"✅ Domik: Successfully wrote file '{file_path}' ({result.get('size', 0)} bytes)"
                )
                return {
                    "success": True,
                    "size": result.get("size", 0),
                    "path": result.get("path", file_path),
                    "message": f"File '{file_path}' written successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to write file '{file_path}': {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to write file '{file_path}'",
                }

        except Exception as e:
            logger.error(
                f"💥 Domik: Error writing file '{file_path}': {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Error writing file '{file_path}'",
            }

    async def list_directory(self, dir_path: str = "") -> Dict[str, Any]:
        """
        List files and directories in the sandbox.

        Args:
            dir_path: Directory path to list (empty for root)

        Returns:
            Dictionary with directory contents
        """
        try:
            logger.info(
                f"🏠 Domik: Listing directory '{dir_path}' for admin {self.admin_id}"
            )

            result = await self.domik_service.list_directory(dir_path, self.admin_id)

            if result["success"]:
                # Emit event for directory listing
                await self.event_service.create_event(
                    event_id=f"domik_list_{dir_path.replace('/', '_')}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_directory_list",
                    data={
                        "directory_path": dir_path,
                        "item_count": result.get("count", 0),
                        "tool": "domik_tool",
                    },
                )

                logger.info(
                    f"✅ Domik: Successfully listed directory '{dir_path}' ({result.get('count', 0)} items)"
                )
                return {
                    "success": True,
                    "items": result.get("items", []),
                    "path": result.get("path", dir_path),
                    "count": result.get("count", 0),
                    "message": f"Directory '{dir_path}' listed successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to list directory '{dir_path}': {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to list directory '{dir_path}'",
                }

        except Exception as e:
            logger.error(
                f"💥 Domik: Error listing directory '{dir_path}': {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Error listing directory '{dir_path}'",
            }

    async def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Create a new directory in the sandbox.

        Args:
            dir_path: Path of the directory to create

        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(
                f"🏠 Domik: Creating directory '{dir_path}' for admin {self.admin_id}"
            )

            result = await self.domik_service.create_directory(dir_path, self.admin_id)

            if result["success"]:
                # Emit event for directory creation
                await self.event_service.create_event(
                    event_id=f"domik_mkdir_{dir_path.replace('/', '_')}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_directory_create",
                    data={"directory_path": dir_path, "tool": "domik_tool"},
                )

                logger.info(f"✅ Domik: Successfully created directory '{dir_path}'")
                return {
                    "success": True,
                    "path": result.get("path", dir_path),
                    "message": f"Directory '{dir_path}' created successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to create directory '{dir_path}': {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to create directory '{dir_path}'",
                }

        except Exception as e:
            logger.error(
                f"💥 Domik: Error creating directory '{dir_path}': {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Error creating directory '{dir_path}'",
            }

    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file or directory from the sandbox.

        Args:
            file_path: Path to the file or directory to delete

        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(f"🏠 Domik: Deleting '{file_path}' for admin {self.admin_id}")

            result = await self.domik_service.delete_file_or_directory(
                file_path, self.admin_id
            )

            if result["success"]:
                # Emit event for file deletion
                await self.event_service.create_event(
                    event_id=f"domik_delete_{file_path.replace('/', '_')}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_file_delete",
                    data={
                        "file_path": file_path,
                        "item_type": result.get("type", "unknown"),
                        "tool": "domik_tool",
                    },
                )

                logger.info(f"✅ Domik: Successfully deleted '{file_path}'")
                return {
                    "success": True,
                    "path": result.get("path", file_path),
                    "type": result.get("type", "unknown"),
                    "message": f"'{file_path}' deleted successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to delete '{file_path}': {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to delete '{file_path}'",
                }

        except Exception as e:
            logger.error(f"💥 Domik: Error deleting '{file_path}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Error deleting '{file_path}'",
            }

    async def get_game_templates(self) -> Dict[str, Any]:
        """
        Get available game templates.

        Returns:
            Dictionary with available game templates
        """
        try:
            logger.info(f"🏠 Domik: Getting game templates for admin {self.admin_id}")

            result = await self.domik_service.get_game_templates()

            if result["success"]:
                # Emit event for template access
                await self.event_service.create_event(
                    event_id=f"domik_templates_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_templates_access",
                    data={
                        "template_count": len(result.get("templates", {})),
                        "tool": "domik_tool",
                    },
                )

                logger.info(
                    f"✅ Domik: Successfully retrieved {len(result.get('templates', {}))} game templates"
                )
                return {
                    "success": True,
                    "templates": result.get("templates", {}),
                    "message": "Game templates retrieved successfully",
                }
            else:
                logger.error(
                    f"❌ Domik: Failed to get game templates: {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": "Failed to get game templates",
                }

        except Exception as e:
            logger.error(f"💥 Domik: Error getting game templates: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting game templates",
            }

    async def create_game_from_template(
        self,
        template_name: str,
        game_path: str,
        customizations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new game from a template.

        Args:
            template_name: Name of the template to use
            game_path: Path where to create the game file
            customizations: Optional customizations to apply to the template

        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(
                f"🏠 Domik: Creating game from template '{template_name}' at '{game_path}' for admin {self.admin_id}"
            )

            # Get templates
            templates_result = await self.get_game_templates()
            if not templates_result["success"]:
                return templates_result

            templates = templates_result["templates"]
            if template_name not in templates:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                    "message": f"Available templates: {list(templates.keys())}",
                }

            # Get template
            template = templates[template_name]["template"]

            # Apply customizations if provided
            if customizations:
                template.update(customizations)

            # Convert to JSON
            game_content = json.dumps(template, indent=2)

            # Write game file
            result = await self.edit_file(game_path, game_content)

            if result["success"]:
                # Emit event for game creation
                await self.event_service.create_event(
                    event_id=f"domik_create_game_{template_name}_{int(time.time())}",
                    user_id=self.admin_id,
                    event_type="domik_game_create",
                    data={
                        "template_name": template_name,
                        "game_path": game_path,
                        "game_size": result.get("size", 0),
                        "tool": "domik_tool",
                    },
                )

                logger.info(
                    f"✅ Domik: Successfully created game from template '{template_name}' at '{game_path}'"
                )
                result["message"] = (
                    f"Game created from template '{template_name}' at '{game_path}'"
                )

            return result

        except Exception as e:
            logger.error(
                f"💥 Domik: Error creating game from template '{template_name}': {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Error creating game from template '{template_name}'",
            }

    async def get_webapp_events(
        self, unread_only: bool = True, limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get events from the webapp for processing.

        Args:
            unread_only: Whether to get only unread events
            limit: Maximum number of events to retrieve

        Returns:
            Dictionary with events data
        """
        try:
            logger.info(
                f"🏠 Domik: Getting webapp events for admin {self.admin_id} (unread_only={unread_only}, limit={limit})"
            )

            if unread_only:
                events = await self.event_service.get_unread_events(
                    limit=limit, event_types=["webapp"]
                )
            else:
                events = await self.event_service.get_events_for_user(
                    user_id=self.admin_id, event_type="webapp", limit=limit
                )

            # Convert events to a more readable format
            event_list = []
            for event in events:
                event_data = {
                    "id": event.event_id,
                    "type": event.event_type,
                    "data": event.data,
                    "created_at": event.created_at.isoformat(),
                    "status": event.status,
                }
                event_list.append(event_data)

            logger.info(f"✅ Domik: Retrieved {len(event_list)} webapp events")
            return {
                "success": True,
                "events": event_list,
                "count": len(event_list),
                "unread_only": unread_only,
                "message": f"Retrieved {len(event_list)} webapp events",
            }

        except Exception as e:
            logger.error(f"💥 Domik: Error getting webapp events: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting webapp events",
            }

    async def mark_events_read(self, event_ids: List[str]) -> Dict[str, Any]:
        """
        Mark webapp events as read (processed).

        Args:
            event_ids: List of event IDs to mark as read

        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(
                f"🏠 Domik: Marking {len(event_ids)} events as read for admin {self.admin_id}"
            )

            count = await self.event_service.mark_events_as_read(event_ids)

            # Emit event for batch processing
            await self.event_service.create_event(
                event_id=f"domik_mark_read_{int(time.time())}",
                user_id=self.admin_id,
                event_type="domik_events_processed",
                data={
                    "processed_count": count,
                    "requested_count": len(event_ids),
                    "tool": "domik_tool",
                },
            )

            logger.info(f"✅ Domik: Successfully marked {count} events as read")
            return {
                "success": True,
                "processed_count": count,
                "requested_count": len(event_ids),
                "message": f"Marked {count} events as read",
            }

        except Exception as e:
            logger.error(f"💥 Domik: Error marking events as read: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Error marking events as read",
            }

    async def get_sandbox_status(self) -> Dict[str, Any]:
        """
        Get status information about the sandbox.

        Returns:
            Dictionary with sandbox status
        """
        try:
            logger.info(f"🏠 Domik: Getting sandbox status for admin {self.admin_id}")

            # List root directory to get overview
            root_list = await self.list_directory("")

            # Calculate total size
            total_size = 0
            file_count = 0
            directory_count = 0

            if root_list["success"]:
                for item in root_list["items"]:
                    if item["type"] == "file":
                        file_count += 1
                        total_size += item.get("size", 0)
                    elif item["type"] == "directory":
                        directory_count += 1

            status = {
                "success": True,
                "admin_id": self.admin_id,
                "total_files": file_count,
                "total_directories": directory_count,
                "total_size": total_size,
                "sandbox_path": str(self.domik_service.sandbox_base_path),
                "max_file_size": self.domik_service.max_file_size,
                "max_directory_size": self.domik_service.max_directory_size,
                "message": f"Sandbox contains {file_count} files and {directory_count} directories ({total_size} bytes)",
            }

            logger.info(
                f"✅ Domik: Sandbox status - {file_count} files, {directory_count} directories, {total_size} bytes"
            )
            return status

        except Exception as e:
            logger.error(f"💥 Domik: Error getting sandbox status: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting sandbox status",
            }
