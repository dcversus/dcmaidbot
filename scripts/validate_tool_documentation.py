#!/usr/bin/env python3
"""
Smart tool documentation validation hook for DCMaidBot.
Provides helpful guidance rather than hard blocking.
Implements progressive enforcement based on context.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set


@dataclass
class ValidationResult:
    """Result of tool documentation validation."""

    is_valid: bool
    missing_docs: List[str]
    suggestions: List[str]
    auto_fix_commands: List[str]
    should_block: bool = False
    validation_level: str = "guidance"


class ToolDocumentationValidator:
    """Smart tool documentation validator with progressive enforcement."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools_dir = project_root / "tools"
        self.docs_dir = project_root / "tools"  # Documentation is in tools/ directly
        self.exclude_file = project_root / ".tool-docs-exclude"

    def validate_changed_tools(self, changed_files: List[str]) -> ValidationResult:
        """
        Validate documentation for changed tool files.
        Provides guidance and auto-fix suggestions.
        """
        changed_tools = self._extract_changed_tools(changed_files)
        excluded_tools = self._load_excluded_tools()

        missing_docs = []
        suggestions = []
        auto_fix_commands = []

        # Determine validation level
        validation_level = self._get_validation_level()

        for tool_name in changed_tools:
            if tool_name in excluded_tools:
                continue

            # Check for possible documentation file names
            possible_doc_names = [
                f"{tool_name}.md",
                f"{tool_name}_service.md",
                f"{tool_name}_thoughts.md",
                f"{tool_name}_integration.md",
            ]

            doc_exists = False
            for doc_name in possible_doc_names:
                doc_path = self.docs_dir / doc_name
                if doc_path.exists():
                    doc_exists = True
                    break

            if not doc_exists:
                missing_docs.append(tool_name)

                # Generate contextual suggestion
                suggestion = self._generate_documentation_suggestion(
                    tool_name, validation_level
                )
                suggestions.append(suggestion)

                # Generate auto-fix command
                create_cmd = self._generate_create_command(tool_name)
                auto_fix_commands.append(create_cmd)

        # Determine if this should be blocking
        should_block = self._should_be_blocking(validation_level, missing_docs)

        return ValidationResult(
            is_valid=len(missing_docs) == 0,
            missing_docs=missing_docs,
            suggestions=suggestions,
            auto_fix_commands=auto_fix_commands,
            should_block=should_block,
            validation_level=validation_level,
        )

    def _get_validation_level(self) -> str:
        """Determine validation level based on context."""
        try:
            # Get current branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            return "guidance"

        # Get commit author
        try:
            author = subprocess.check_output(
                ["git", "config", "user.name"], cwd=self.project_root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            author = "unknown"

        # Environment override
        env_level = os.getenv("TOOL_DOCS_LEVEL", "").lower()
        if env_level in ["guidance", "standard", "strict"]:
            return env_level

        # Production branches: Strict enforcement
        if branch in ["main", "master", "production"]:
            return "strict"

        # Core contributors: Standard enforcement
        if author.lower() in ["dcversus", "vasilisa-vs", "daniil-shark"]:
            return "standard"

        # Default: Guidance mode
        return "guidance"

    def _should_be_blocking(
        self, validation_level: str, missing_docs: List[str]
    ) -> bool:
        """Determine if validation should be blocking."""
        if validation_level == "strict":
            return True

        # Block if environment variable is set
        if os.getenv("TOOL_DOCS_ENFORCE", "false").lower() == "true":
            return True

        return False

    def _load_excluded_tools(self) -> Set[str]:
        """Load list of excluded tools from .tool-docs-exclude file."""
        if not self.exclude_file.exists():
            return set()

        try:
            with open(self.exclude_file, "r", encoding="utf-8") as f:
                return set(
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                )
        except Exception:
            return set()

    def _generate_documentation_suggestion(
        self, tool_name: str, validation_level: str
    ) -> str:
        """Generate contextual documentation suggestion."""
        level_messages = {
            "guidance": {
                "emoji": "💡",
                "title": "Suggestion",
                "action": "Consider adding",
                "priority": "helpful but optional",
            },
            "standard": {
                "emoji": "⚠️",
                "title": "Warning",
                "action": "Should add",
                "priority": "recommended for code quality",
            },
            "strict": {
                "emoji": "❌",
                "title": "Error",
                "action": "Must add",
                "priority": "required for commit",
            },
        }

        msg = level_messages.get(validation_level, level_messages["guidance"])

        return f"""
{msg["emoji"]} **{msg["title"]}: Missing Documentation**

I noticed you've modified `{tool_name}_tools.py` but the corresponding documentation is missing.

**Required Documentation**: `tools/{tool_name}.md`

**Why this matters**:
- Other developers need to understand tool usage and parameters
- Documentation enables proper testing and integration
- Essential for production deployment and team collaboration
- Helps new contributors understand tool capabilities

**Quick fix options**:
1. 🚀 **Auto-create template**: `python scripts/create_tool_docs.py {tool_name}`
2. 📋 **Manual template**: Copy from `tools/_template.md`
3. 📝 **Skip temporarily**: Add `{tool_name}` to `.tool-docs-exclude` (not recommended)

**Documentation priority**: {msg["priority"]}
"""

    def _generate_create_command(self, tool_name: str) -> str:
        """Generate command to create missing documentation."""
        return f"python scripts/create_tool_docs.py {tool_name}"

    def _extract_changed_tools(self, changed_files: List[str]) -> List[str]:
        """Extract tool names from changed files."""
        tool_files = [
            f for f in changed_files if f.startswith("tools/") and f.endswith(".py")
        ]
        tool_names = []

        for tool_file in tool_files:
            # Skip __init__.py and other non-tool files
            if any(
                exclude in tool_file
                for exclude in ["__init__.py", "test_", "conftest.py"]
            ):
                continue

            # Extract tool name from path (tools/memory_tools.py -> memory)
            parts = Path(tool_file).parts
            if len(parts) >= 2:
                file_name = parts[-1]  # memory_tools.py
                if file_name.endswith("_tools.py"):
                    tool_name = file_name.replace("_tools.py", "")
                    tool_names.append(tool_name)

        return list(set(tool_names))  # Remove duplicates

    def print_results(self, result: ValidationResult):
        """Print validation results with appropriate formatting."""
        level_prefixes = {
            "guidance": "🌱 **Developer Guidance**",
            "standard": "📋 **Standard Validation**",
            "strict": "🔒 **Strict Validation**",
        }

        prefix = level_prefixes.get(result.validation_level, level_prefixes["guidance"])

        print(f"\n{prefix}")
        print("=" * 50)

        if not result.is_valid:
            for suggestion in result.suggestions:
                print(suggestion)

            if result.auto_fix_commands:
                print("\n🛠️ **Auto-Fix Commands:**")
                for cmd in result.auto_fix_commands:
                    print(f"  $ {cmd}")

            if result.should_block:
                print("\n❌ **Blocking Commit**: Missing required documentation")
                print("   Please run the suggested commands above, then commit again.")
                print(
                    "   Or add tools to `.tool-docs-exclude` to skip validation (not recommended for production)."
                )
            else:
                print("\n⚠️ **Non-blocking**: Documentation missing but commit allowed")
                print(
                    "   Consider adding documentation for better developer experience."
                )

        print(f"\n✅ Validation complete (Level: {result.validation_level})")


def get_git_changed_files(project_root: Path) -> List[str]:
    """Get list of changed files from git."""
    try:
        # Get staged files for pre-commit hook
        changed_files = (
            subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"], cwd=project_root, text=True
            )
            .strip()
            .split("\n")
        )

        # Filter out empty lines
        return [f for f in changed_files if f.strip()]
    except subprocess.CalledProcessError:
        print("❌ Unable to get changed files from git")
        sys.exit(1)


def main():
    """Main validation hook entry point."""
    # Get project root
    project_root = Path(__file__).parent.parent
    if not (project_root / "tools").exists():
        print("❌ Not in a valid dcmaidbot project directory")
        sys.exit(1)

    validator = ToolDocumentationValidator(project_root)

    # Get changed files
    changed_files = get_git_changed_files(project_root)

    if not changed_files:
        print("ℹ️ No files changed, skipping validation")
        sys.exit(0)

    # Validate tools
    result = validator.validate_changed_tools(changed_files)

    # Print results
    validator.print_results(result)

    # Exit with appropriate code
    if result.should_block:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
