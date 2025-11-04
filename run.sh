#!/bin/bash

# DCMAIDBOT Run Script
# Controls all aspects of running, testing, and deploying the bot

set -e

# Define colors
ORANGE='\033[38;5;208m'  # accent_orange #FF9A38
PURPLE='\033[38;5;147m'  # robo-aqa #B48EAD
RED='\033[38;5;167m'  # robo-quality-control #E06C75
YELLOW='\033[38;5;221m'  # warn #FFCC66
GREEN='\033[38;5;114m'  # robo-devops-sre #98C379
BLUE='\033[38;5;75m'   # robo-developer #61AFEF
GRAY='\033[38;5;244m'   # muted #9AA0A6
HEADER='\033[38;5;244m'  # header #FFB56B
NC='\033[0m'            # No Color

# Background color variations for logs
BLUE_BG='\033[1;48;5;75m\033[38;5;232m'  # blue bg with dark bold text
GREEN_BG='\033[1;48;5;114m\033[38;5;232m'  # green bg with dark bold text
YELLOW_BG='\033[1;48;5;221m\033[38;5;232m'  # yellow bg with dark bold text
RED_BG='\033[1;48;5;167m\033[38;5;232m'  # red bg with dark bold text
ORANGE_BG='\033[1;48;5;208m\033[38;5;232m'  # orange bg with dark bold text

# Default values
COMMAND="dev"  # Default command is dev
DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./dcmaidbot.db}"
TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"
COVERAGE=false
VERBOSE=false
EXTRA_ARGS=""  # Initialize extra arguments
CLEAN_TEST_DB=true  # Always clean test DB after tests

# Helper functions
log_info() {
    echo -e "${BLUE_BG}[INFO ⛿]${NC} $1"
}

log_success() {
    echo -e "${GREEN_BG}[SUCCESS ⛱]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW_BG}[WARNING ⚠]${NC} $1"
}

log_error() {
    echo -e "${RED_BG}[ERROR ⛆]${NC} $1"
}

# Check environment and display warnings
check_environment() {
    local mode="$1"

    # Check for required variables based on mode
    case $mode in
        "prod")
            if [ -z "$BOT_TOKEN" ]; then
                log_error "BOT_TOKEN is required for production mode"
                return 1
            fi
            if [ -z "$BASE_URL" ]; then
                log_warning "BASE_URL not set, will use polling mode"
            fi
            ;;
        "prod-test")
            if [ -z "$BASE_URL" ]; then
                log_error "BASE_URL is required for production testing"
                return 1
            fi
            if [ -z "$ADMIN_IDS" ]; then
                log_error "ADMIN_IDS is required for production testing"
                return 1
            fi
            ;;
        "test-e2e")
            if [ -z "$OPENAI_API_KEY" ]; then
                log_warning "OPENAI_API_KEY not set, will skip LLM judge steps"
            fi
            ;;
    esac

    # Always check database
    if [ -z "$DATABASE_URL" ] && [ -z "$DB_PATH" ]; then
        log_info "Using default SQLite database: dcmaidbot.db"
    fi

    # Show what's disabled
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "LLM Judge features disabled (OPENAI_API_KEY not set)"
    fi

    if [ -z "$BOT_TOKEN" ]; then
        log_warning "Telegram integration disabled (BOT_TOKEN not set)"
    fi

    if [ -z "$ADMIN_IDS" ] && [ ! -z "$BOT_TOKEN" ]; then
        log_error "ADMIN_IDS is required when BOT_TOKEN is set"
        return 1
    fi

    return 0
}

# Load .env file if it exists (after log functions are defined)
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    # Only show the message when not running help
    if [ "$1" != "help" ]; then
        log_info "Loaded environment variables from .env file"
    fi
fi

# Show help with DCMAIDBOT branding
show_help() {
    # Header with accent color
    echo -e "${ORANGE_BG} DCMAIDBOT: Ня! ${NC}"
    echo

    # Check environment and display warnings
    check_environment "help" 2>/dev/null || true
    echo

    # Usage section with colored braces
    echo -e "${HEADER}[USAGE]${NC}"
    echo -e "  ${NC}./run.sh${NC} ${PURPLE}[COMMAND]${NC} ${PURPLE}[OPTIONS]${NC}"
    echo

    # Commands section
    echo -e "${HEADER}[COMMANDS]${NC}"
    echo -e "  ${ORANGE}dev${NC}                       ${GRAY}Run development mode (default, polling)${NC}"
    echo -e "  ${BLUE}prod${NC}                      ${GRAY}Run with webhook from BASE_URL${NC}"
    echo -e "  ${BLUE}prod-test${NC}                 ${GRAY}Run e2e tests with LLM judge for production${NC}"
    echo -e "  ${PURPLE}test${NC}                      ${GRAY}Run unit and e2e tests locally${NC}"
    echo -e "  ${BLUE}test-unit${NC}                 ${GRAY}Run unit tests only${NC}"
    echo -e "  ${BLUE}test-e2e${NC}                  ${GRAY}Run end-to-end tests only${NC}"
    echo -e "  ${PURPLE}lint${NC}                      ${GRAY}Run code style checks${NC}"
    echo -e "  ${BLUE}fix${NC}                       ${GRAY}Run code style checks with auto-fix${NC}"
    echo -e "  ${PURPLE}types${NC}                     ${GRAY}Run type checking${NC}"
    echo -e "  ${BLUE}help${NC}                      ${GRAY}Show this help message${NC}"
    echo

    # Options section
    echo -e "${HEADER}[OPTIONS]${NC}"
    echo -e "  --db ${GRAY}PATH                 Alias for DATABASE_URL (default: dcmaidbot.db)${NC}"
    echo -e "  --coverage                ${GRAY}Generate coverage report${NC}"
    echo -e "  --verbose                 ${GRAY}Verbose output${NC}"
    echo

    # Examples section
    echo -e "${HEADER}[EXAMPLES]${NC}"
    echo -e "  ./run.sh                  ${GRAY}Run in development mode${NC}"
    echo -e "  ./run.sh prod             ${GRAY}Run in production mode${NC}"
    echo -e "  ./run.sh test --coverage  ${GRAY}Run tests with coverage${NC}"
    echo -e "  ./run.sh fix              ${GRAY}Fix code style issues${NC}"
    echo

    # Environment variables section
    echo -e "${HEADER}[ENVIRONMENT VARIABLES]${NC}"
    echo -e "  DATABASE_URL              ${GRAY}Database connection string${NC}"
    echo -e "  BASE_URL                  ${GRAY}Webhook base URL (production)${NC}"
    echo -e "  WEBHOOK_URL               ${GRAY}Webhook path (default: /webhook)${NC}"
    echo -e "  OPENAI_API_KEY            ${GRAY}OpenAI API key for LLM features${NC}"
    echo -e "  BOT_TOKEN                 ${GRAY}Telegram bot token${NC}"
    echo -e "  ADMIN_IDS                 ${GRAY}Comma-separated admin IDs${NC}"
    echo -e "  NUDGE_SECRET              ${GRAY}Webhook secret for /nudge endpoint${NC}"
}

# Clean test database
clean_test_db() {
    local cleaned=false

    # Remove test database files
    for db_file in test.db test.sqlite test.sqlite3 *.db; do
        if [ -f "$db_file" ]; then
            log_info "Cleaning up $db_file"
            rm -f "$db_file"
            cleaned=true
        fi
    done

    # Remove SQLite journal files
    for journal_file in *.db-journal *.sqlite-journal *.sqlite3-journal; do
        if [ -f "$journal_file" ]; then
            log_info "Cleaning up journal file: $journal_file"
            rm -f "$journal_file"
            cleaned=true
        fi
    done

    if [ "$cleaned" = true ]; then
        log_success "Test database files removed"
    fi
}

# Check if running in production mode
is_production() {
    [ "$PRODUCTION" = true ]
}

# Run code style checks
run_lint() {
    local fix=false
    if [ "$1" = "fix" ]; then
        fix=true
        log_info "Running code style checks with auto-fix..."
    else
        log_info "Running code style checks..."
    fi

    # Check if ruff is installed
    if ! command -v ruff &> /dev/null; then
        log_error "ruff is not installed. Install with: pip install ruff"
        exit 1
    fi

    if [ "$fix" = true ]; then
        ruff check . --fix
        ruff format .
    else
        ruff check .
        ruff format . --check
    fi

    log_success "Code style checks passed"
}

# Run type checking
run_types() {
    log_info "Running type checks..."

    # Check if mypy is installed
    if ! command -v mypy &> /dev/null; then
        log_warning "mypy is not installed. Install with: pip install mypy"
        return 0
    fi

    mypy main.py src/

    log_success "Type checks passed"
}

# Run tests
run_tests() {
    local test_type="$1"

    # Set up test environment
    export DATABASE_URL="$TEST_DATABASE_URL"

    if [ "$CLEAN_TEST_DB" = true ]; then
        clean_test_db
    fi

    # Build pytest command
    local pytest_cmd="python3 -m pytest"

    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v -s"
    else
        pytest_cmd="$pytest_cmd -v"
    fi

    # Handle coverage
    if [ "$COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=src --cov-report=html --cov-report=term-missing"
    fi

    # Handle OPENAI_API_KEY for LLM judge features
    # Note: --llm-judge is not a valid pytest option, LLM judge runs automatically when OPENAI_API_KEY is set
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "LLM Judge features disabled (OPENAI_API_KEY not set)"
        log_info "Tests requiring LLM judge will be skipped automatically via pytest markers"
    fi

    case $test_type in
        "all")
            log_info "Running all tests (unit, integration, and e2e)..."
            # Run all tests except manual ones
            $pytest_cmd tests/ -m "not manual" --ignore=tests/business/production_validation
            ;;
        "unit")
            log_info "Running unit and integration tests..."
            # Check if unit/integration directories exist, otherwise run business tests
            if [ -d "tests/unit" ] || [ -d "tests/integration" ]; then
                if [ -d "tests/unit" ]; then
                    $pytest_cmd tests/unit/
                fi
                if [ -d "tests/integration" ]; then
                    $pytest_cmd tests/integration/
                fi
            else
                log_info "No dedicated unit/integration test directories found, running business validation tests..."
                $pytest_cmd tests/business/ -m "not slow and not manual"
            fi
            ;;
        "e2e")
            log_info "Running end-to-end tests..."
            # Run e2e tests with proper environment setup
            if [ -n "$OPENAI_API_KEY" ]; then
                log_info "OPENAI_API_KEY detected - LLM Judge evaluation enabled"
            else
                log_warning "OPENAI_API_KEY not set - tests requiring LLM Judge will be skipped"
            fi
            $pytest_cmd tests/e2e/ -m "not manual"
            ;;
        *)
            # Check if it's a specific test file
            if [ -f "$test_type" ]; then
                log_info "Running specific test file: $test_type"
                $pytest_cmd "$test_type"
            else
                log_error "Unknown test type or file not found: $test_type"
                log_info "Available test types: all, unit, e2e"
                log_info "Or specify a path to a test file"
                exit 1
            fi
            ;;
    esac

    # Cleanup test database after tests
    if [ "$CLEAN_TEST_DB" = true ]; then
        clean_test_db
        log_success "Test database cleaned up"
    fi

    log_success "Tests completed"
}

# Run production tests
run_prod_tests() {
    log_info "Running production tests against $BASE_URL"

    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "OPENAI_API_KEY is required for production testing"
        exit 1
    fi

    if [ -z "$BASE_URL" ]; then
        log_error "BASE_URL is required for production testing"
        exit 1
    fi

    if [ -z "$ADMIN_IDS" ]; then
        log_error "ADMIN_IDS is required for production testing"
        exit 1
    fi

    # Extract first admin ID from ADMIN_IDS
    local first_admin_id=$(echo $ADMIN_IDS | cut -d',' -f1)

    log_info "OPENAI_API_KEY detected - LLM Judge evaluation enabled for production tests"
    log_info "Testing against BASE_URL: $BASE_URL"
    log_info "Using admin ID: $first_admin_id"

    # Run production e2e tests with LLM Judge (OPENAI_API_KEY ensures it runs)
    python3 -m pytest tests/e2e/ \
        --base-url="$BASE_URL" \
        -v \
        -m "not manual"

    log_success "Production tests completed"
}

# Run the bot
run_bot() {
    local mode="$1"

    # Export DATABASE_URL for the bot process
    export DATABASE_URL

    if [ "$mode" = "prod" ]; then
        log_info "Starting bot in PRODUCTION mode..."
        if [ -n "$BASE_URL" ]; then
            # Remove trailing slash from BASE_URL if present
            BASE_URL=$(echo "$BASE_URL" | sed 's:/*$::')
            export WEBHOOK_FULL_URL="${BASE_URL}${WEBHOOK_URL:-/webhook}"
            log_info "Webhook URL: ${WEBHOOK_FULL_URL}"
        fi
    else
        log_info "Starting bot in DEVELOPMENT mode..."
    fi

    # Log database info
    log_info "Using database: $DATABASE_URL"

    # Start the bot
    exec python3 main.py
}

# Clean generated files
run_clean() {
    log_info "Cleaning up generated files..."

    # Remove cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    # Remove test databases
    rm -f *.db *.sqlite *.sqlite3
    rm -f *.db-journal

    # Remove coverage files
    rm -rf .coverage htmlcov/ .pytest_cache/

    # Remove build artifacts
    rm -rf build/ dist/

    log_success "Cleanup completed"
}

# Parse command line arguments
# Allow options to appear before or after command
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|prod|prod-test|test|test-unit|test-e2e|lint|fix|types|help)
            COMMAND="$1"
            shift
            ;;
        --db)
            if [[ $# -lt 2 ]]; then
                log_error "--db option requires a PATH argument"
                show_help
                exit 1
            fi
            DB_PATH="$2"
            # Set DATABASE_URL immediately to override default
            DATABASE_URL="sqlite+aiosqlite:///$DB_PATH"
            shift 2
            ;;
        --coverage)
            COVERAGE=true
            # Add to EXTRA_ARGS for any functions that might need it
            EXTRA_ARGS="$EXTRA_ARGS --coverage"
            shift
            ;;
        --verbose)
            VERBOSE=true
            # Add to EXTRA_ARGS for any functions that might need it
            EXTRA_ARGS="$EXTRA_ARGS --verbose"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # If command is 'test' and next argument is a file path, store it
            if [ "$COMMAND" = "test" ] && [[ "$1" == tests/* ]] && [ -f "$1" ]; then
                TEST_FILE="$1"
                shift
            else
                log_error "Unknown option: $1"
                show_help
                exit 1
            fi
            ;;
    esac
done

# Execute command
case $COMMAND in
    "dev")
        check_environment "dev" || exit 1
        run_bot "dev"
        ;;
    "prod")
        check_environment "prod" || exit 1
        run_bot "prod"
        ;;
    "prod-test")
        check_environment "prod-test" || exit 1
        run_prod_tests
        ;;
    "test")
        check_environment "test" || exit 1
        # Check if a specific test file is provided
        if [ -n "$TEST_FILE" ] && [ -f "$TEST_FILE" ]; then
            run_tests "$TEST_FILE"
        else
            run_tests "all"
        fi
        ;;
    "test-unit")
        check_environment "test-unit" || exit 1
        run_tests "unit"
        ;;
    "test-e2e")
        check_environment "test-e2e" || exit 1
        run_tests "e2e"
        ;;
    "lint")
        run_lint
        ;;
    "fix")
        run_lint "fix"
        ;;
    "types")
        run_types
        ;;
    "help")
        show_help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
