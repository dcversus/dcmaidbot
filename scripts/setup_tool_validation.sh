#!/bin/bash
# Quick setup script for tool documentation validation system

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Main setup function
main() {
    log_info "Setting up Tool Documentation Validation System for DCMaidBot..."

    # Get project root
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"

    # 1. Backup existing configuration
    if [[ -f ".pre-commit-config.yaml" ]]; then
        log_info "Backing up existing pre-commit configuration..."
        cp .pre-commit-config.yaml .pre-commit-config.yaml.backup
        log_success "Backup created: .pre-commit-config.yaml.backup"
    fi

    # 2. Install enhanced configuration
    log_info "Installing enhanced pre-commit configuration..."
    cp .pre-commit-config.enhanced.yaml .pre-commit-config.yaml
    log_success "Enhanced configuration installed"

    # 3. Ensure directories exist
    log_info "Creating required directories..."
    mkdir -p tools/docs
    mkdir -p scripts
    log_success "Directories created"

    # 4. Install pre-commit hooks
    log_info "Installing pre-commit hooks..."
    pre-commit install
    pre-commit install --hook-type commit-msg
    log_success "Pre-commit hooks installed"

    # 5. Test documentation generation
    log_info "Testing documentation generation..."
    if python scripts/create_tool_docs.py memory --force; then
        log_success "Documentation generation test passed"
    else
        log_warning "Documentation generation test failed - please check dependencies"
    fi

    # 6. Validate setup
    log_info "Validating setup..."
    if [[ -f "tools/docs/memory.md" ]]; then
        log_success "Documentation validation test passed"
    else
        log_warning "Documentation validation test failed"
    fi

    # 7. Create example usage
    log_info "Creating example usage..."
    cat > example_tool_validation.md << 'EOF'
# Example: Tool Documentation Validation

## Test the validation system:

1. Modify an existing tool:
   ```bash
   echo "# Modified for testing" >> tools/memory_tools.py
   ```

2. Stage and commit:
   ```bash
   git add tools/memory_tools.py
   git commit -m "test: tool documentation validation"
   ```

3. Follow the suggestions to create documentation:
   ```bash
   python scripts/create_tool_docs.py memory --force
   ```

4. Commit with documentation:
   ```bash
   git add tools/docs/memory.md
   git commit -m "feat: add memory tools documentation"
   ```

## Validation Levels:
- 🟢 **Guidance Mode**: New contributors get helpful suggestions
- 🟡 **Standard Mode**: Regular contributors see warnings
- 🔴 **Strict Mode**: Production branches require documentation

## Commands:
- `python scripts/create_tool_docs.py <tool_name>` - Generate documentation
- `python scripts/validate_tool_documentation.py` - Manual validation
- Check `.tool-docs-exclude` to exclude tools temporarily
EOF

    log_success "Example usage guide created: example_tool_validation.md"

    # 8. Final instructions
    echo ""
    log_success "🎉 Tool Documentation Validation System setup complete!"
    echo ""
    log_info "Next steps:"
    echo "1. Review the implementation guide: IMPLEMENTATION_GUIDE.md"
    echo "2. Test with: cat example_tool_validation.md"
    echo "3. Customize validation levels in scripts/validate_tool_documentation.py"
    echo "4. Update tools/docs/_template.md for your documentation standards"
    echo ""
    log_info "The validation system will now run automatically when you commit tool changes."
    log_warning "Remember to commit both tool changes AND documentation together!"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 > /dev/null; then
        echo "❌ Python 3 is required but not installed"
        exit 1
    fi

    # Check pre-commit
    if ! command -v pre-commit > /dev/null; then
        echo "❌ pre-commit is required but not installed"
        echo "Install with: pip install pre-commit"
        exit 1
    fi

    # Check git
    if ! command -v git > /dev/null; then
        echo "❌ git is required but not installed"
        exit 1
    fi

    log_success "All dependencies satisfied"
}

# Run setup
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_dependencies
    main
fi
