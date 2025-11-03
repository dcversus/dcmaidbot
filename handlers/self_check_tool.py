"""
Self-Check Tool Handler

Provides self-check diagnostics accessible via /call command and Telegram.
"""

import logging
from typing import Any, Dict

from services.thoughts_background_service import thoughts_background_service

logger = logging.getLogger(__name__)


async def handle_self_check_command(
    user_id: int, force: bool = False, verbose: bool = False
) -> Dict[str, Any]:
    """
    Handle self-check tool command.

    Args:
        user_id: User ID requesting the check
        force: Force fresh diagnostics bypassing cache
        verbose: Include detailed tool-by-tool results

    Returns:
        Dict: Self-check results and Lilith's analysis
    """
    try:
        logger.info(
            f"Self-check requested by user {user_id}, force={force}, verbose={verbose}"
        )

        # Generate self-check thoughts
        if force:
            # Force fresh generation
            self_check_result = (
                await thoughts_background_service._generate_self_check_thoughts_now()
            )
        else:
            # Get latest stored thoughts
            thoughts = thoughts_background_service.get_stored_thoughts()
            self_check_result = thoughts.get("self_check_thoughts", {})

            # If no recent results, generate fresh ones
            if not self_check_result or not self_check_result.get("available"):
                self_check_result = await thoughts_background_service._generate_self_check_thoughts_now()

        if not self_check_result.get("available"):
            return {
                "success": False,
                "message": "❌ Self-check failed to complete",
                "error": self_check_result.get("error", "Unknown error"),
                "suggestion": "Please try again in a few minutes or contact an administrator.",
            }

        # Format results for user
        response_data = {
            "success": True,
            "message": "🔍 Self-check diagnostics completed successfully!",
            "summary": format_self_check_summary(self_check_result),
            "lilith_opinion": self_check_result.get(
                "lilith_honest_opinion", "I'm still gathering my thoughts..."
            ),
            "metrics": {
                "total_time": self_check_result.get("total_time", 0),
                "tools_tested": len(self_check_result.get("tool_results", [])),
                "tokens_used": self_check_result.get("tokens_used", 0),
                "timestamp": self_check_result.get("last_updated"),
            },
        }

        # Add detailed results if verbose
        if verbose:
            response_data["detailed_results"] = format_detailed_results(
                self_check_result
            )

        return response_data

    except Exception as e:
        logger.error(f"Self-check command failed: {e}")
        return {
            "success": False,
            "message": "❌ Self-check encountered an error",
            "error": str(e),
            "suggestion": "Please try again later or report this issue to an administrator.",
        }


def format_self_check_summary(self_check_result: Dict[str, Any]) -> str:
    """
    Format self-check results into a user-friendly summary.

    Args:
        self_check_result: Self-check results data

    Returns:
        str: Formatted summary
    """
    try:
        tool_results = self_check_result.get("tool_results", [])

        if not tool_results:
            return "⚠️ No tool results available"

        # Count results by status
        working = sum(1 for tool in tool_results if tool.get("status") == "working")
        failing = sum(1 for tool in tool_results if tool.get("status") == "failing")
        missing = sum(1 for tool in tool_results if tool.get("status") == "missing")

        # Create status summary
        status_emoji = "✅" if failing == 0 else "⚠️" if failing <= 1 else "❌"

        summary_lines = [
            f"{status_emoji} **System Health Overview:**",
            f"• Working: {working} {'tool' if working == 1 else 'tools'}",
            f"• Failing: {failing} {'tool' if failing == 1 else 'tools'}",
            f"• Missing: {missing} {'tool' if missing == 1 else 'tools'}",
            f"• Total tools tested: {len(tool_results)}",
            f"• Completion time: {self_check_result.get('total_time', 0):.1f}s",
        ]

        # Add specific tool statuses
        summary_lines.append("\n📊 **Tool Statuses:**")
        for tool in tool_results:
            status = tool.get("status", "unknown")
            emoji = {"working": "✅", "failing": "❌", "missing": "⚠️"}.get(status, "❓")
            name = tool.get("name", "Unknown Tool")

            if status == "working":
                summary_lines.append(f"  {emoji} {name}: Operational")
            elif status == "failing":
                result = tool.get("test_result", "No details available")
                summary_lines.append(f"  {emoji} {name}: {result}")
            else:
                summary_lines.append(f"  {emoji} {name}: Not available")

        return "\n".join(summary_lines)

    except Exception as e:
        logger.error(f"Failed to format self-check summary: {e}")
        return "⚠️ Error formatting self-check summary"


def format_detailed_results(self_check_result: Dict[str, Any]) -> str:
    """
    Format detailed self-check results for verbose output.

    Args:
        self_check_result: Self-check results data

    Returns:
        str: Formatted detailed results
    """
    try:
        tool_results = self_check_result.get("tool_results", [])
        detailed_lines = ["\n🔧 **Detailed Diagnostic Results:**\n"]

        for tool in tool_results:
            name = tool.get("name", "Unknown Tool")
            status = tool.get("status", "unknown")
            confidence = tool.get("confidence_score", 0)
            test_result = tool.get("test_result", "No result available")
            expectation = tool.get("expectations", "No expectations specified")
            explanation = tool.get("explanation_reflect", "No explanation provided")

            status_emoji = {"working": "✅", "failing": "❌", "missing": "⚠️"}.get(
                status, "❓"
            )

            detailed_lines.append(f"**{status_emoji} {name}**")
            detailed_lines.append(f"• Status: {status.title()}")
            detailed_lines.append(f"• Confidence: {confidence}/10")
            detailed_lines.append(f"• Expected: {expectation}")
            detailed_lines.append(f"• Actual: {test_result}")
            detailed_lines.append(f"• Analysis: {explanation}")
            detailed_lines.append("")  # Empty line for readability

        return "\n".join(detailed_lines)

    except Exception as e:
        logger.error(f"Failed to format detailed results: {e}")
        return "⚠️ Error formatting detailed results"


async def handle_telegram_self_check(user_id: int) -> str:
    """
    Handle self-check command from Telegram bot.

    Args:
        user_id: Telegram user ID

    Returns:
        str: Formatted response for Telegram
    """
    result = await handle_self_check_command(user_id, force=False, verbose=False)

    if result["success"]:
        response = f"""
{result["message"]}

{result["summary"]}

💭 **Lilith's Honest Opinion:**
{result["lilith_opinion"]}

⏱️ **Metrics:**
• Completed in: {result["metrics"]["total_time"]:.1f}s
• Tools tested: {result["metrics"]["tools_tested"]}
• Tokens used: {result["metrics"]["tokens_used"]}
• Last check: {result["metrics"]["timestamp"]}

💡 **Tip:** Use `/call self_check verbose=true` for detailed results.
        """.strip()

        return response
    else:
        return result["message"]


async def handle_call_self_check(user_id: int, args: list = None) -> str:
    """
    Handle self-check command from /call interface.

    Args:
        user_id: User ID requesting the check
        args: Command arguments

    Returns:
        str: Formatted response for /call
    """
    # Parse arguments
    force = False
    verbose = False

    if args:
        for arg in args:
            if arg.lower() in ["force", "refresh"]:
                force = True
            elif arg.lower() in ["verbose", "detailed", "v"]:
                verbose = True

    result = await handle_self_check_command(user_id, force=force, verbose=verbose)

    if result["success"]:
        response = f"""
🔍 **Self-Check Diagnostics**

{result["summary"]}

💭 **Lilith's Honest Opinion:**
{result["lilith_opinion"]}

📊 **Performance Metrics:**
• Completion time: {result["metrics"]["total_time"]:.1f} seconds
• Tools tested: {result["metrics"]["tools_tested"]}
• Tokens consumed: {result["metrics"]["tokens_used"]}
• Timestamp: {result["metrics"]["timestamp"]}
        """.strip()

        # Add detailed results if requested
        if verbose and "detailed_results" in result:
            response += f"\n\n{result['detailed_results']}"

        # Add cache info if not forced
        if not force:
            response += "\n\n💡 *Note: Results from cache. Use `force=true` for fresh diagnostics.*"

        return response
    else:
        return f"❌ **Self-Check Failed**\n\n{result['message']}"


# Tool registration for the tool system
SELF_CHECK_TOOL_INFO = {
    "name": "self_check",
    "description": "Run comprehensive system diagnostics with Lilith's honest analysis",
    "category": "system",
    "permissions": ["status:read"],
    "parameters": {
        "force": {
            "type": "boolean",
            "default": False,
            "description": "Force fresh diagnostics bypassing cache",
        },
        "verbose": {
            "type": "boolean",
            "default": False,
            "description": "Include detailed tool-by-tool results",
        },
    },
    "examples": [
        "/call self_check",
        "/call self_check force=true",
        "/call self_check verbose=true",
        "/call self_check force=true verbose=true",
    ],
}
