#!/bin/bash
# Enhanced E2E Test Runner with Cross-Environment Support

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
TEST_REPORTS_DIR="$PROJECT_ROOT/test-reports"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.test.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."

    # Stop and remove containers
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v --remove-orphans || true
    fi

    # Cleanup any remaining processes
    pkill -f "python.*bot_webhook.py" || true
    pkill -f "python.*bot.py" || true

    log_success "Cleanup completed"
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Create directories
mkdir -p "$TEST_RESULTS_DIR"
mkdir -p "$TEST_REPORTS_DIR"

# Parse command line arguments
TEST_MODE=${1:-"e2e"}
PARALLEL_WORKERS=${2:-1}
ENVIRONMENT=${3:-"test"}
ENABLE_LLM_JUDGE=${4:-"true"}

log_info "Starting E2E Test Runner"
log_info "Test Mode: $TEST_MODE"
log_info "Parallel Workers: $PARALLEL_WORKERS"
log_info "Environment: $ENVIRONMENT"
log_info "LLM Judge: $ENABLE_LLM_JUDGE"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    log_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Set environment variables
export ENVIRONMENT="$ENVIRONMENT"
export TEST_MODE="$TEST_MODE"
export PARALLEL_WORKERS="$PARALLEL_WORKERS"

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service_name to be ready..."

    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_success "$service_name is ready!"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done

    log_error "$service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to wait for database to be ready
wait_for_database() {
    local db_url=$1
    local max_attempts=30
    local attempt=1

    log_info "Waiting for database to be ready..."

    while [[ $attempt -le $max_attempts ]]; do
        if python -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def check_db():
    try:
        parsed = urlparse('$db_url')
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],
            timeout=5
        )
        await conn.close()
        return True
    except Exception as e:
        return False

result = asyncio.run(check_db())
print('READY' if result else 'NOT_READY')
        " 2>/dev/null | grep -q "READY"; then
            log_success "Database is ready!"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts: Database not ready yet..."
        sleep 2
        ((attempt++))
    done

    log_error "Database failed to become ready after $max_attempts attempts"
    return 1
}

# Function to run tests with proper error handling
run_tests() {
    local test_command=$1
    local test_description=$2

    log_info "Running: $test_description"

    # Create test results file
    local test_results_file="$TEST_RESULTS_DIR/${test_description// /_}_$(date +%Y%m%d_%H%M%S).xml"

    # Run tests
    if eval "$test_command"; then
        log_success "$test_description completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "$test_description failed with exit code $exit_code"
        return $exit_code
    fi
}

# Main execution
main() {
    log_info "Setting up test environment..."

    # Start test infrastructure
    log_info "Starting test infrastructure with Docker Compose..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres-test redis-test mock-openai mock-telegram

    # Wait for services to be ready
    wait_for_service "PostgreSQL" "localhost" "5433"
    wait_for_service "Redis" "localhost" "6380"
    wait_for_service "Mock OpenAI" "localhost" "1080"
    wait_for_service "Mock Telegram" "localhost" "1081"

    # Wait for database to be ready
    wait_for_database "postgresql://dcmaidbot:test_password@localhost:5433/dcmaidbot_test"

    # Seed test data
    log_info "Seeding test data..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm test-data-seeder; then
        log_success "Test data seeded successfully"
    else
        log_error "Failed to seed test data"
        exit 1
    fi

    # Determine test command based on mode
    local test_command=""
    local test_description=""

    case "$TEST_MODE" in
        "unit")
            test_command="pytest tests/unit/ -v --tb=short --junitxml=$TEST_RESULTS_DIR/unit_tests.xml"
            test_description="Unit Tests"
            ;;
        "integration")
            test_command="pytest tests/unit/test_*.py tests/e2e/test_api_*.py -v --tb=short --junitxml=$TEST_RESULTS_DIR/integration_tests.xml"
            test_description="Integration Tests"
            ;;
        "e2e")
            if [[ "$ENABLE_LLM_JUDGE" == "true" ]]; then
                test_command="pytest tests/e2e/ -v --tb=short --junitxml=$TEST_RESULTS_DIR/e2e_tests.xml --llm-judge --html=$TEST_REPORTS_DIR/e2e_report.html --self-contained-html"
                test_description="E2E Tests with LLM Judge"
            else
                test_command="pytest tests/e2e/ -v --tb=short --junitxml=$TEST_RESULTS_DIR/e2e_tests.xml --html=$TEST_REPORTS_DIR/e2e_report.html --self-contained-html"
                test_description="E2E Tests"
            fi
            ;;
        "performance")
            test_command="pytest tests/e2e/test_prp008_load_benchmark.py -v --benchmark-only --benchmark-json=$TEST_RESULTS_DIR/performance_results.json"
            test_description="Performance Tests"
            ;;
        "security")
            test_command="pytest tests/e2e/test_*security*.py -v --tb=short --junitxml=$TEST_RESULTS_DIR/security_tests.xml"
            test_description="Security Tests"
            ;;
        *)
            log_error "Unknown test mode: $TEST_MODE"
            exit 1
            ;;
    esac

    # Add parallel execution if specified
    if [[ $PARALLEL_WORKERS -gt 1 ]]; then
        test_command="$test_command --numprocesses=$PARALLEL_WORKERS"
    fi

    # Set environment for tests
    export DATABASE_URL="postgresql://dcmaidbot:test_password@localhost:5433/dcmaidbot_test"
    export REDIS_URL="redis://localhost:6380/0"
    export OPENAI_API_BASE="http://localhost:1080"
    export TELEGRAM_API_BASE="http://localhost:1081"
    export DISABLE_TG="true"
    export SKIP_MIGRATION_CHECK="true"

    # Run the tests
    if run_tests "$test_command" "$test_description"; then
        log_success "All tests completed successfully!"

        # Generate summary report
        log_info "Generating test summary report..."
        python -c "
import os
import json
from datetime import datetime

results_dir = '$TEST_RESULTS_DIR'
reports_dir = '$TEST_REPORTS_DIR'

# Create summary report
summary = {
    'test_run': {
        'timestamp': datetime.utcnow().isoformat(),
        'mode': '$TEST_MODE',
        'environment': '$ENVIRONMENT',
        'parallel_workers': $PARALLEL_WORKERS,
        'llm_judge_enabled': $ENABLE_LLM_JUDGE
    },
    'results': {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0
    },
    'files_generated': []
}

# Scan for test result files
for file in os.listdir(results_dir):
    if file.endswith('.xml'):
        summary['files_generated'].append(f'results/{file}')
    elif file.endswith('.json'):
        summary['files_generated'].append(f'results/{file}')

for file in os.listdir(reports_dir):
    if file.endswith('.html'):
        summary['files_generated'].append(f'reports/{file}')

# Save summary
with open(os.path.join(reports_dir, 'test_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print('Test summary report generated!')
print(f'Results directory: {results_dir}')
print(f'Reports directory: {reports_dir}')
        "

        log_success "Test execution completed successfully!"
        log_info "Test results available in: $TEST_RESULTS_DIR"
        log_info "Test reports available in: $TEST_REPORTS_DIR"

        exit 0
    else
        log_error "Test execution failed!"
        log_info "Check the logs above for details"
        log_info "Test results available in: $TEST_RESULTS_DIR"

        exit 1
    fi
}

# Check if this script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
