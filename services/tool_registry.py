"""Tool registry for OpenAI function calling."""

from typing import Any, Callable


class ToolRegistry:
    """Registry for bot tools (functions that can be called by LLM)."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: dict[str, Callable] = {}
        self.tool_schemas: list[dict[str, Any]] = []

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        function: Callable,
    ) -> None:
        """
        Register a tool that can be called by the LLM.

        Args:
            name: Tool name (e.g., "search_web")
            description: What the tool does
            parameters: OpenAI function parameters schema
            function: The actual function to call
        """
        # Register function
        self.tools[name] = function

        # Register OpenAI schema
        self.tool_schemas.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """
        Call a registered tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry")

        function = self.tools[name]
        return await function(**arguments)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """
        Get all tool schemas for OpenAI API.

        Returns:
            List of OpenAI tool schemas
        """
        return self.tool_schemas

    def get_tool_names(self) -> list[str]:
        """
        Get names of all registered tools.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())


# Global tool registry instance
tool_registry = ToolRegistry()


# Example tool: Echo (for testing)
async def echo_tool(message: str) -> str:
    """Echo back a message (test tool)."""
    return f"Echo: {message}"


# Register test tool
tool_registry.register_tool(
    name="echo",
    description="Echo back a message (for testing)",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message to echo back",
            }
        },
        "required": ["message"],
    },
    function=echo_tool,
)
