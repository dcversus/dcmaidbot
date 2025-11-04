"""HTTP Client utility for testing /call endpoint."""

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp


class HttpClient:
    """Simple HTTP client for testing bot API endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def call(
        self,
        message: str,
        user_id: int,
        is_admin: bool = False,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make a call to the /call endpoint.

        Args:
            message: The message to send
            user_id: Telegram user ID
            is_admin: Whether the user is an admin
            api_key: Optional API key for authentication

        Returns:
            Response dictionary
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = urljoin(self.base_url, "/call")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        data = {"message": message, "user_id": user_id, "is_admin": is_admin}

        try:
            async with self.session.post(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    return {
                        "status": "error",
                        "error": f"HTTP {resp.status}",
                        "details": text,
                    }
        except Exception as e:
            return {"status": "error", "error": "connection_error", "details": str(e)}

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
