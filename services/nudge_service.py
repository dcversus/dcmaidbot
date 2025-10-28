"""
Nudge Service for agent-to-user communication.

Forwards nudge requests from autonomous agents to external LLM endpoint
which processes the request and sends Telegram messages to admins.
"""

import os
from typing import Any, Optional

import aiohttp


class NudgeService:
    """Service for forwarding nudge requests to external LLM endpoint."""

    EXTERNAL_ENDPOINT = "https://dcmaid.theedgestory.org/nudge"

    async def forward_nudge(
        self,
        user_ids: list[int],
        message: str,
        pr_url: Optional[str] = None,
        prp_file: Optional[str] = None,
        prp_section: Optional[str] = None,
        urgency: str = "medium",
    ) -> dict[str, Any]:
        """Forward nudge request to external LLM endpoint.

        Args:
            user_ids: List of Telegram user IDs to notify (admins)
            message: Human-friendly message describing the request
            pr_url: Optional URL to related pull request
            prp_file: Optional PRP file path (e.g., "PRPs/PRP-014.md")
            prp_section: Optional section anchor (e.g., "#authentication")
            urgency: Urgency level: "low", "medium", or "high"

        Returns:
            dict: Response from external endpoint

        Raises:
            ValueError: If NUDGE_SECRET not configured
            aiohttp.ClientError: If request to external endpoint fails
        """
        nudge_secret = os.getenv("NUDGE_SECRET")
        if not nudge_secret:
            raise ValueError("NUDGE_SECRET not configured in environment")

        # Build payload
        payload: dict[str, Any] = {
            "user_ids": user_ids,
            "message": message,
        }

        if pr_url:
            payload["pr_url"] = pr_url
        if prp_file:
            payload["prp_file"] = prp_file
        if prp_section:
            payload["prp_section"] = prp_section
        if urgency:
            payload["urgency"] = urgency

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {nudge_secret}",
            "Content-Type": "application/json",
        }

        # Set timeout
        timeout = aiohttp.ClientTimeout(total=30)

        # Make request to external endpoint
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.EXTERNAL_ENDPOINT, json=payload, headers=headers
            ) as response:
                response_data = await response.json()
                response.raise_for_status()
                return response_data
