#!/bin/bash
# DCMAIDBot Canary Promotion Script
# Usage: ./scripts/promote-canary.sh [version] [--environment]

set -euo pipefail

# Default values
ENVIRONMENT="production"
VERSION=""
NAMESPACE="dcmaidbot"
CANARY_RELEASE="dcmaidbot-canary"
STABLE_RELEASE="dcmaidbot"
TIMEOUT=600
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            VERSION="$2"
            shift 2
            ;;
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --dry-run|-d)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --version, -v        Version to promote"
            echo "  --environment, -e    Environment [default: production]"
            echo "  --namespace, -n      Kubernetes namespace [default: dcmaidbot]"
            echo "  --timeout, -t        Deployment timeout in seconds [default: 600]"
            echo "  --dry-run, -d        Show what would be done without doing it"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(production|development|staging)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be one of: production, development, staging"
    exit 1
fi

# Set namespace based on environment
if [[ "$ENVIRONMENT" == "development" ]]; then
    NAMESPACE="dcmaidbot-dev"
fi

# Check dependencies
command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is required but not installed."; exit 1; }
command -v helm >/dev/null 2>&1 || { log_error "helm is required but not installed."; exit 1; }

# Check Kubernetes connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    log_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Get version from canary if not provided
if [[ -z "$VERSION" ]]; then
    log_info "Getting version from canary deployment..."
    VERSION=$(kubectl get deployment $CANARY_RELEASE -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
    if [[ -z "$VERSION" ]]; then
        log_error "Could not determine version from canary deployment"
        exit 1
    fi
fi

# Show promotion info
log_info "Canary Promotion Configuration:"
log_info "  Environment: $ENVIRONMENT"
log_info "  Version: $VERSION"
log_info "  Namespace: $NAMESPACE"
log_info "  Canary Release: $CANARY_RELEASE"
log_info "  Stable Release: $STABLE_RELEASE"
log_info "  Dry Run: $DRY_RUN"

# Check if canary deployment exists
if ! kubectl get deployment $CANARY_RELEASE -n $NAMESPACE >/dev/null 2>&1; then
    log_error "Canary deployment $CANARY_RELEASE not found in namespace $NAMESPACE"
    exit 1
fi

# Check canary deployment health
log_info "Checking canary deployment health..."
CANARY_REPLICAS=$(kubectl get deployment $CANARY_RELEASE -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
if [[ "$CANARY_REPLICAS" == "0" || -z "$CANARY_REPLICAS" ]]; then
    log_error "Canary deployment is not healthy (ready replicas: $CANARY_REPLICAS)"
    exit 1
fi

# Get canary metrics
log_info "Gathering canary performance metrics..."

# Get canary pod metrics
CANARY_PODS=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=canary -o jsonpath='{.items[*].metadata.name}')
CANARY_CPU_USAGE=""
CANARY_MEMORY_USAGE=""

for pod in $CANARY_PODS; do
    CPU=$(kubectl top pod $pod -n $NAMESPACE --no-headers 2>/dev/null | awk '{print $2}' || echo "0m")
    MEMORY=$(kubectl top pod $pod -n $NAMESPACE --no-headers 2>/dev/null | awk '{print $3}' || echo "0Mi")
    CANARY_CPU_USAGE="$CANARY_CPU_USAGE $CPU"
    CANARY_MEMORY_USAGE="$CANARY_MEMORY_USAGE $MEMORY"
done

log_info "Canary pod CPU usage: $CANARY_CPU_USAGE"
log_info "Canary pod memory usage: $CANARY_MEMORY_USAGE"

# Check canary logs for errors
log_info "Checking canary logs for errors..."
ERROR_COUNT=$(kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=canary --since=10m 2>/dev/null | grep -i error | wc -l || echo "0")
log_info "Error count in last 10 minutes: $ERROR_COUNT"

# Dry run mode
if [[ "$DRY_RUN" == true ]]; then
    log_info "DRY RUN - Would perform the following actions:"
    log_info "1. Update stable deployment to version: $VERSION"
    log_info "2. Wait for stable deployment rollout"
    log_info "3. Remove canary deployment"
    log_info "4. Update GitOps repository"
    exit 0
fi

# Prompt for confirmation
read -p "Are you sure you want to promote canary version $VERSION to stable? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Promotion cancelled"
    exit 0
fi

# Backup current stable deployment
log_info "Backing up current stable deployment..."
kubectl get deployment $STABLE_RELEASE -n $NAMESPACE -o yaml > "backup-${STABLE_RELEASE}-$(date +%Y%m%d-%H%M%S).yaml"

# Update stable deployment
log_info "Updating stable deployment to version $VERSION..."

if helm upgrade --install "$STABLE_RELEASE" "./helm/dcmaidbot" \
    --namespace "$NAMESPACE" \
    --set "image.tag=$VERSION" \
    --set "environment=$ENVIRONMENT" \
    --set "canary.enabled=false" \
    --wait \
    --timeout="${TIMEOUT}s"; then

    log_success "Stable deployment updated successfully"
else
    log_error "Failed to update stable deployment"
    exit 1
fi

# Wait for stable deployment rollout
log_info "Waiting for stable deployment rollout..."

if kubectl rollout status "deployment/$STABLE_RELEASE" -n "$NAMESPACE" --timeout="$TIMEOUT"s; then
    log_success "Stable deployment rollout completed successfully"
else
    log_error "Stable deployment rollout failed"
    log_warning "Keeping canary deployment for fallback"
    exit 1
fi

# Verify stable deployment health
log_info "Verifying stable deployment health..."
STABLE_REPLICAS=$(kubectl get deployment $STABLE_RELEASE -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
if [[ "$STABLE_REPLICAS" == "0" || -z "$STABLE_REPLICAS" ]]; then
    log_error "Stable deployment is not healthy after promotion"
    log_warning "Keeping canary deployment for fallback"
    exit 1
fi

# Get endpoint URL
if [[ "$ENVIRONMENT" == "production" ]]; then
    URL="https://dcmaidbot.theedgestory.org"
elif [[ "$ENVIRONMENT" == "development" ]]; then
    URL="https://dcmaidbot-dev.theedgestory.org"
else
    URL="https://dcmaidbot-${ENVIRONMENT}.theedgestory.org"
fi

# Health check on stable deployment
log_info "Performing health check on stable deployment..."
if curl -f "$URL/health" --connect-timeout 10 --max-time 30 >/dev/null 2>&1; then
    log_success "Stable deployment health check passed"
else
    log_error "Stable deployment health check failed"
    log_warning "Keeping canary deployment for fallback"
    exit 1
fi

# Remove canary deployment
log_info "Removing canary deployment..."

if helm uninstall "$CANARY_RELEASE" -n "$NAMESPACE"; then
    log_success "Canary deployment removed successfully"
else
    log_warning "Failed to remove canary deployment (may need manual cleanup)"
fi

# Clean up any remaining canary resources
log_info "Cleaning up remaining canary resources..."
kubectl delete service $CANARY_RELEASE -n $NAMESPACE --ignore-not-found=true
kubectl delete ingress $CANARY_RELEASE -n $NAMESPACE --ignore-not-found=true

# Update GitOps repository
log_info "Triggering GitOps repository update..."
if command -v curl >/dev/null 2>&1 && [[ -n "${GITOPS_WEBHOOK_URL:-}" ]]; then
    curl -X POST "$GITOPS_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"action\": \"promotion\",
            \"version\": \"$VERSION\",
            \"environment\": \"$ENVIRONMENT\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
        }" || log_warning "Failed to trigger GitOps update"
else
    log_info "GitOps webhook not configured, skipping automated update"
fi

# Show final status
log_success "Canary promotion completed successfully!"
log_info "Version $VERSION is now serving stable traffic"
log_info "Environment: $ENVIRONMENT"
log_info "URL: $URL"

# Show deployment status
log_info "Current deployment status:"
kubectl get pods -n $NAMESPACE -l "app.kubernetes.io/name=dcmaidbot" -o wide

# Show resource usage
log_info "Current resource usage:"
kubectl top pods -n $NAMESPACE -l "app.kubernetes.io/name=dcmaidbot" 2>/dev/null || log_warning "Metrics server not available"

log_info "Promotion completed at $(date -u)"
log_info "To rollback: ./scripts/rollback.sh stable $VERSION"
