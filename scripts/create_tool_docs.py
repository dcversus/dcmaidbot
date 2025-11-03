#!/usr/bin/env python3
"""
Auto-create tool documentation from Python source files.
Extracts tool definitions and generates comprehensive documentation.
"""

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolInfo:
    """Information about a tool function."""

    name: str
    description: str
    parameters: List[Dict[str, Any]]
    required_params: List[str]
    access_level: str = "public"  # public, friend, admin


class ToolDocumentationGenerator:
    """Generates documentation for tool files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools_dir = project_root / "tools"
        self.docs_dir = project_root / "tools"  # Documentation is in tools/ directly
        self.template_path = self.docs_dir / "_template.md"

        # Ensure docs directory exists
        self.docs_dir.mkdir(exist_ok=True)

    def generate_documentation(self, tool_name: str) -> str:
        """Generate documentation for a specific tool."""
        tool_file = self.tools_dir / f"{tool_name}_tools.py"

        if not tool_file.exists():
            raise FileNotFoundError(f"Tool file not found: {tool_file}")

        # Parse Python file to extract tool definitions
        tools_info = self._extract_tools_info(tool_file)

        # Extract file-level docstring
        file_docstring = self._extract_file_docstring(tool_file)

        # Generate documentation
        doc_content = self._generate_markdown(tool_name, tools_info, file_docstring)

        return doc_content

    def _extract_file_docstring(self, tool_file: Path) -> str:
        """Extract the file-level docstring."""
        try:
            with open(tool_file, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)
            ):
                return ast.get_docstring(tree) or ""
        except Exception:
            pass

        return "Tool functionality for enhanced bot capabilities."

    def _extract_tools_info(self, tool_file: Path) -> List[ToolInfo]:
        """Extract tool information from Python source file."""
        with open(tool_file, "r", encoding="utf-8") as f:
            source = f.read()

        tools_info = []

        # Look for TOOLS lists/dicts in the source
        tools_match = re.search(r"(\w+_TOOLS)\s*=\s*\[(.*?)\]", source, re.DOTALL)
        if not tools_match:
            # Try to find any variable that ends with _TOOLS
            tools_matches = re.findall(
                r"(\w+_TOOLS)\s*=\s*\[(.*?)\]", source, re.DOTALL
            )
            if not tools_matches:
                return []
            tools_match = tools_matches[0]

        tools_list_str = tools_match[1]

        # Parse each tool definition
        tool_patterns = re.findall(
            r'\{\s*"type":\s*"function"[^}]*"function":\s*\{([^}]+)\}[^}]*\}',
            tools_list_str,
            re.DOTALL,
        )

        for tool_def in tool_patterns:
            tool_info = self._parse_single_tool(tool_def)
            if tool_info:
                tools_info.append(tool_info)

        return tools_info

    def _parse_single_tool(self, tool_def: str) -> Optional[ToolInfo]:
        """Parse a single tool definition from JSON-like string."""
        try:
            # Extract name and description
            name_match = re.search(r'"name":\s*"([^"]+)"', tool_def)
            desc_match = re.search(r'"description":\s*"([^"]+)"', tool_def)

            if not name_match or not desc_match:
                return None

            name = name_match.group(1)
            description = desc_match.group(1)

            # Extract parameters
            params_match = re.search(
                r'"parameters":\s*\{([^}]+)\}', tool_def, re.DOTALL
            )
            parameters = []
            required_params = []

            if params_match:
                params_str = params_match.group(1)

                # Extract properties
                props_match = re.search(
                    r'"properties":\s*\{([^}]+)\}', params_str, re.DOTALL
                )
                if props_match:
                    props_str = props_match.group(1)
                    param_matches = re.findall(
                        r'"([^"]+)":\s*\{([^}]+)\}', props_str, re.DOTALL
                    )

                    for param_name, param_def in param_matches:
                        type_match = re.search(r'"type":\s*"([^"]+)"', param_def)
                        desc_match = re.search(r'"description":\s*"([^"]+)"', param_def)

                        param_info = {
                            "name": param_name,
                            "type": type_match.group(1) if type_match else "unknown",
                            "description": desc_match.group(1)
                            if desc_match
                            else "No description available",
                        }
                        parameters.append(param_info)

                # Extract required parameters
                required_match = re.search(r'"required":\s*\[([^\]]+)\]', params_str)
                if required_match:
                    required_str = required_match.group(1)
                    required_params = [
                        p.strip().strip('"')
                        for p in required_str.split(",")
                        if p.strip()
                    ]

            # Determine access level from name or description
            access_level = "public"
            if any(
                keyword in name.lower() for keyword in ["admin", "manage", "config"]
            ):
                access_level = "admin"
            elif any(keyword in name.lower() for keyword in ["friend", "special"]):
                access_level = "friend"

            return ToolInfo(
                name=name,
                description=description,
                parameters=parameters,
                required_params=required_params,
                access_level=access_level,
            )

        except Exception as e:
            print(f"Warning: Failed to parse tool definition: {e}")
            return None

    def _generate_markdown(
        self, tool_name: str, tools_info: List[ToolInfo], file_docstring: str
    ) -> str:
        """Generate markdown documentation."""
        template = self._load_template()

        # Generate tools list section
        tools_list = self._format_tools_list(tools_info)

        # Generate examples section
        examples = self._generate_examples(tool_name, tools_info)

        # Generate integration notes
        integration_notes = self._generate_integration_notes(tool_name, tools_info)

        # Generate rate limits section
        rate_limits = self._generate_rate_limits_section(tools_info)

        # Replace template variables
        doc_content = template.replace("{tool_name}", tool_name)
        doc_content = doc_content.replace("{tool_description}", file_docstring)
        doc_content = doc_content.replace("{tools_list}", tools_list)
        doc_content = doc_content.replace("{examples}", examples)
        doc_content = doc_content.replace("{integration_notes}", integration_notes)
        doc_content = doc_content.replace("{rate_limits}", rate_limits)

        return doc_content

    def _format_tools_list(self, tools_info: List[ToolInfo]) -> str:
        """Format the tools list for documentation."""
        if not tools_info:
            return "No tools found in this module."

        tools_md = []
        for tool in tools_info:
            access_emoji = {"admin": "🔒", "friend": "👥", "public": "🌍"}.get(
                tool.access_level, "🌍"
            )

            params_md = []
            for param in tool.parameters:
                required_mark = "✅" if param["name"] in tool.required_params else "⭕"
                params_md.append(
                    f"- `{param['name']}` ({param['type']}) {required_mark}: {param['description']}"
                )

            tools_md.append(f"""
### `{tool.name}` {access_emoji}

**Purpose**: {tool.description}

**Access Level**: {tool.access_level.title()}

**Parameters**:
{chr(10).join(params_md) if params_md else "No parameters"}

**Required Parameters**: {", ".join(f"`{p}`" for p in tool.required_params) if tool.required_params else "None"}
""")

        return "\n".join(tools_md)

    def _generate_examples(self, tool_name: str, tools_info: List[ToolInfo]) -> str:
        """Generate usage examples for tools."""
        if not tools_info:
            return "No examples available."

        examples = []
        for tool in tools_info[:3]:  # Limit to first 3 tools
            # Generate example based on parameters
            if tool.parameters:
                required_params = {
                    p["name"]: f'"{p["name"]}_value"'
                    for p in tool.parameters
                    if p["name"] in tool.required_params
                }
                if required_params:
                    example_call = f"result = await {tool.name}({', '.join(f'{k}={v}' for k, v in required_params.items())})"
                else:
                    example_call = f"result = await {tool.name}()"
            else:
                example_call = f"result = await {tool.name}()"

            examples.append(f"""
```python
# Example: {tool.name}
{example_call}
print(result)
```
""")

        if not examples:
            return "No examples available yet."

        return "\n".join(examples)

    def _generate_integration_notes(
        self, tool_name: str, tools_info: List[ToolInfo]
    ) -> str:
        """Generate integration notes."""
        notes = []

        # Add general integration notes
        notes.append(
            f"- The `{tool_name}` module is automatically loaded by the ToolExecutor"
        )
        notes.append(
            "- Tools are available to the LLM agent based on access control rules"
        )

        # Add access level specific notes
        admin_tools = [t for t in tools_info if t.access_level == "admin"]
        if admin_tools:
            notes.append(
                f"- Admin-only tools: {', '.join(f'`{t.name}`' for t in admin_tools)}"
            )

        friend_tools = [t for t in tools_info if t.access_level == "friend"]
        if friend_tools:
            notes.append(
                f"- Friend-accessible tools: {', '.join(f'`{t.name}`' for t in friend_tools)}"
            )

        return "\n".join(notes) if notes else "No special integration requirements."

    def _generate_rate_limits_section(self, tools_info: List[ToolInfo]) -> str:
        """Generate rate limits and restrictions section."""
        limits = [
            "- Standard rate limiting: 10 requests per minute per user",
            "- Admin users bypass rate limiting restrictions",
            "- Tool execution is logged for security and monitoring",
            "- Response size limits apply to prevent abuse",
        ]

        # Add tool-specific limits if applicable
        if any("search" in tool.name.lower() for tool in tools_info):
            limits.insert(0, "- Search tools: Results limited to 10 items maximum")

        if any(
            "create" in tool.name.lower() or "delete" in tool.name.lower()
            for tool in tools_info
        ):
            limits.insert(0, "- Modification tools: Additional validation required")

        return "\n".join(limits)

    def _load_template(self) -> str:
        """Load documentation template."""
        if self.template_path.exists():
            with open(self.template_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return self._generate_default_template()

    def _generate_default_template(self) -> str:
        """Generate default documentation template."""
        return """# Tool Name Documentation

## Overview
[Tool description goes here]

## Available Tools

[List of available tools goes here]

## Usage Examples

[Usage examples go here]

## Integration Notes

[Integration notes go here]

## Rate Limits & Restrictions

[Rate limits information goes here]

## Error Handling

All tools return standardized error responses:
- Success: Result data as specified in tool description
- Permission denied: `{"error": "Access denied", "message": "Insufficient permissions"}`
- Rate limited: `{"error": "Rate limited", "message": "Too many requests"}`
- Invalid parameters: `{"error": "Invalid parameters", "message": "Specific error details"}`

## Testing

Tools are automatically tested by the validation system:
- Unit tests verify individual tool functionality
- E2E tests verify integration with the bot system
- LLM judge validation ensures proper tool responses

---

*This documentation was auto-generated on 2025-11-02. Please review and enhance with additional details and real-world examples.*"""


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python create_tool_docs.py <tool_name> [--force]")
        print("  tool_name: Name of the tool (e.g., 'memory', 'web_search')")
        print("  --force:   Overwrite existing documentation")
        sys.exit(1)

    tool_name = sys.argv[1]
    force_overwrite = "--force" in sys.argv

    project_root = Path(__file__).parent.parent
    generator = ToolDocumentationGenerator(project_root)

    # Check if documentation already exists
    doc_file = project_root / "tools" / f"{tool_name}.md"
    if doc_file.exists() and not force_overwrite:
        print(f"❌ Documentation already exists: {doc_file}")
        print("   Use --force to overwrite existing documentation")
        sys.exit(1)

    try:
        doc_content = generator.generate_documentation(tool_name)

        # Write documentation file
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(doc_content)

        print(f"✅ Documentation created: {doc_file}")
        print("📝 Please review and enhance the generated documentation with:")
        print("   - Real-world usage examples")
        print("   - Additional integration details")
        print("   - Security considerations")
        print("   - Troubleshooting information")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"   Make sure the tool file exists: tools/{tool_name}_tools.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
