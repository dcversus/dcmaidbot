#!/bin/bash
# Production deployment script with safety checks and rollbacks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIGRATION_SCRIPT="$PROJECT_ROOT/scripts/migrate.py"

# Default values
ENVIRONMENT="${ENVIRONMENT:-production}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
DRY_RUN="${DRY_RUN:-false}"
FORCE="${FORCE:-false}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"

# Parse arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --health-check-timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            cat <<EOF
Production deployment script for DCMAIDBot

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --env <name>           Environment to deploy to (default: production)
    --skip-backup          Skip database backup
    --dry-run              Show what would be done without executing
    --force                Skip confirmation prompts
    --health-check-timeout <seconds>
                           Timeout for health checks (default: 300)
    -h, --help            Show this help

EXAMPLES:
    $0 --env staging
    $0 --dry-run
    $0 --skip-backup --force

EOF
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${GREEN}✓ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/main.py" ]]; then
        error "main.py not found. Are you in the project root?"
        exit 1
    fi

    # Check if migration script exists
    if [[ ! -f "$MIGRATION_SCRIPT" ]]; then
        error "Migration script not found: $MIGRATION_SCRIPT"
        exit 1
    fi

    # Check database connection
    if [[ -z "${DATABASE_URL:-}" ]]; then
        error "DATABASE_URL environment variable is required"
        exit 1
    fi

    # Check required tools
    for tool in python3 docker git; do
        if ! command -v "$tool" &> /dev/null; then
            error "Required tool not found: $tool"
            exit 1
        fi
    done

    info "Prerequisites check passed"
}

# Create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        warn "Skipping backup as requested"
        return 0
    fi

    log "Creating database backup..."
    if python3 "$MIGRATION_SCRIPT" --backup; then
        info "Backup created successfully"
    else
        warn "Backup failed, continuing anyway..."
    fi
}

# Run migrations
run_migrations() {
    log "Running database migrations..."

    local cmd=(python3 "$MIGRATION_SCRIPT" upgrade)
    if [[ "$DRY_RUN" == "true" ]]; then
        cmd+=(--dry-run)
    fi

    if "${cmd[@]}"; then
        info "Migrations completed successfully"
    else
        error "Migration failed!"
        return 1
    fi
}

# Build Docker image
build_image() {
    log "Building Docker image..."

    local image_name="dcmaidbot"
    local image_tag="${image_tag:-$(date +%Y%m%d_%H%M%S)}"
    local full_image="${image_name}:${image_tag}"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would build image: $full_image"
        return 0
    fi

    if docker build -t "$full_image" .; then
        info "Docker image built successfully: $full_image"

        # Tag as latest
        docker tag "$full_image" "${image_name}:latest"

        # Export image name for later use
        export DEPLOYED_IMAGE="$full_image"
    else
        error "Docker build failed!"
        return 1
    fi
}

# Deploy to Kubernetes
deploy_k8s() {
    log "Deploying to Kubernetes..."

    if [[ -z "${KUBECONFIG:-}" ]] && [[ ! -f "$HOME/.kube/config" ]]; then
        warn "No Kubernetes configuration found, skipping K8s deployment"
        return 0
    fi

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        warn "kubectl not found, skipping K8s deployment"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would deploy to Kubernetes"
        return 0
    fi

    # Get current deployment
    local namespace="${KUBE_NAMESPACE:-dcmaidbot}"
    local deployment="${DEPLOYMENT_NAME:-dcmaidbot}"

    # Update deployment with new image
    if kubectl set image deployment/"$deployment" "$deployment=$DEPLOYED_IMAGE" -n "$namespace"; then
        info "Kubernetes deployment updated"

        # Wait for rollout
        if kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout="${HEALTH_CHECK_TIMEOUT}s"; then
            info "Rollout completed successfully"
        else
            error "Rollout failed!"
            return 1
        fi
    else
        error "Failed to update Kubernetes deployment"
        return 1
    fi
}

# Health check
health_check() {
    log "Performing health checks..."

    local health_url="${HEALTH_URL:-http://localhost:8080/health}"
    local timeout="$HEALTH_CHECK_TIMEOUT"
    local interval=5
    local elapsed=0

    while [[ $elapsed -lt $timeout ]]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            info "Health check passed"
            return 0
        fi

        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    error "Health check failed after ${timeout}s"
    return 1
}

# Rollback on failure
rollback() {
    error "Deployment failed! Initiating rollback..."

    # Rollback migrations
    log "Rolling back migrations..."
    if python3 "$MIGRATION_SCRIPT" downgrade -1; then
        info "Migration rollback completed"
    else
        error "Migration rollback failed!"
    fi

    # Rollback Kubernetes deployment
    if command -v kubectl &> /dev/null && [[ -n "${KUBECONFIG:-}" || -f "$HOME/.kube/config" ]]; then
        log "Rolling back Kubernetes deployment..."
        local namespace="${KUBE_NAMESPACE:-dcmaidbot}"
        local deployment="${DEPLOYMENT_NAME:-dcmaidbot}"

        if kubectl rollout undo deployment/"$deployment" -n "$namespace"; then
            info "Kubernetes rollback completed"
        else
            error "Kubernetes rollback failed!"
        fi
    fi

    error "Rollback completed. Please investigate the failure."
}

# Main deployment flow
main() {
    log "Starting DCMAIDBot deployment to $ENVIRONMENT environment"

    # Confirmation prompt
    if [[ "$FORCE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo
        warn "You are about to deploy to $ENVIRONMENT environment"
        warn "This will:"
        warn "  1. Create a database backup (unless --skip-backup is used)"
        warn "  2. Run database migrations"
        warn "  3. Build and deploy a new Docker image"
        warn "  4. Update Kubernetes deployment"
        echo
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi

    # Run deployment steps
    check_prerequisites
    create_backup || true  # Don't fail on backup error

    if ! run_migrations; then
        rollback
        exit 1
    fi

    if ! build_image; then
        rollback
        exit 1
    fi

    if ! deploy_k8s; then
        rollback
        exit 1
    fi

    if ! health_check; then
        rollback
        exit 1
    fi

    # Success!
    echo
    info "=================================="
    info "✅ Deployment completed successfully!"
    info "=================================="
    info "Deployed image: ${DEPLOYED_IMAGE:-N/A}"
    info "Environment: $ENVIRONMENT"
    info "Time: $(date)"
    echo
}

# Error handling
trap 'error "Script failed at line $LINENO"' ERR

# Run main function
main "${ARGS[@]}"
