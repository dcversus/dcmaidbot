#!/bin/bash
# DCMAIDBot Rollback Script
# Usage: ./scripts/rollback.sh [deployment-type] [target-version] [--environment]

set -euo pipefail

# Default values
ENVIRONMENT="production"
DEPLOYMENT_TYPE="stable"
TARGET_VERSION=""
NAMESPACE="dcmaidbot"
STABLE_RELEASE="dcmaidbot"
CANARY_RELEASE="dcmaidbot-canary"
TIMEOUT=300
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
        stable|canary)
            DEPLOYMENT_TYPE="$1"
            shift
            ;;
        --version|-v)
            TARGET_VERSION="$2"
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
            echo "Usage: $0 [stable|canary] [OPTIONS]"
            echo "Positional arguments:"
            echo "  stable              Rollback stable deployment (default)"
            echo "  canary              Rollback canary deployment"
            echo ""
            echo "Options:"
            echo "  --version, -v       Target version to rollback to"
            echo "  --environment, -e   Environment [default: production]"
            echo "  --namespace, -n     Kubernetes namespace [default: dcmaidbot]"
            echo "  --timeout, -t       Rollback timeout in seconds [default: 300]"
            echo "  --dry-run, -d       Show what would be done without doing it"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 stable --version v1.2.3"
            echo "  $0 canary --environment development"
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

# Set release name based on deployment type
if [[ "$DEPLOYMENT_TYPE" == "canary" ]]; then
    RELEASE_NAME="$CANARY_RELEASE"
else
    RELEASE_NAME="$STABLE_RELEASE"
fi

# Check dependencies
command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is required but not installed."; exit 1; }
command -v helm >/dev/null 2>&1 || { log_error "helm is required but not installed."; exit 1; }

# Check Kubernetes connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    log_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Show rollback info
log_info "Rollback Configuration:"
log_info "  Deployment Type: $DEPLOYMENT_TYPE"
log_info "  Environment: $ENVIRONMENT"
log_info "  Namespace: $NAMESPACE"
log_info "  Release Name: $RELEASE_NAME"
log_info "  Target Version: $TARGET_VERSION"
log_info "  Dry Run: $DRY_RUN"

# Check if deployment exists
if ! kubectl get deployment "$RELEASE_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    log_error "Deployment $RELEASE_NAME not found in namespace $NAMESPACE"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(kubectl get deployment "$RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
log_info "Current version: $CURRENT_VERSION"

# Get available versions from Helm
log_info "Available versions from Helm history..."
helm history "$RELEASE_NAME" -n "$NAMESPACE" --output json | jq -r '.[] | "\(.revision): \(.app_version) (\(.status))"' || log_warning "Could not fetch Helm history"

# Get target version if not specified
if [[ -z "$TARGET_VERSION" ]]; then
    log_info "No target version specified, will rollback to previous stable version"

    # Get previous stable revision from Helm
    PREVIOUS_REVISION=$(helm history "$RELEASE_NAME" -n "$NAMESPACE" --output json | jq -r '.[] | select(.status == "deployed") | .revision' | tail -2 | head -1)

    if [[ -n "$PREVIOUS_REVISION" ]]; then
        TARGET_VERSION=$(helm history "$RELEASE_NAME" -n "$NAMESPACE" --output json | jq -r ".[] | select(.revision == $PREVIOUS_REVISION) | .app_version")
        log_info "Previous stable version: $TARGET_VERSION (revision $PREVIOUS_REVISION)"
    else
        log_error "Could not determine previous stable version"
        exit 1
    fi
fi

# Get current deployment status
log_info "Current deployment status:"
kubectl get deployment "$RELEASE_NAME" -n "$NAMESPACE" -o wide

# Get current pods status
log_info "Current pods status:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot" -o wide

# Dry run mode
if [[ "$DRY_RUN" == true ]]; then
    log_info "DRY RUN - Would perform the following actions:"
    log_info "1. Rollback $RELEASE_NAME to version: $TARGET_VERSION"
    log_info "2. Wait for deployment rollout"
    log_info "3. Verify deployment health"
    log_info "4. Update monitoring systems"
    exit 0
fi

# Prompt for confirmation
read -p "Are you sure you want to rollback $DEPLOYMENT_TYPE deployment from $CURRENT_VERSION to $TARGET_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Rollback cancelled"
    exit 0
fi

# Create rollback backup
log_info "Creating backup before rollback..."
BACKUP_DIR="rollback-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current deployment
kubectl get deployment "$RELEASE_NAME" -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/deployment-$RELEASE_NAME.yaml"
kubectl get service "$RELEASE_NAME" -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/service-$RELEASE_NAME.yaml"
kubectl get ingress "$RELEASE_NAME" -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/ingress-$RELEASE_NAME.yaml"

# Backup pod logs
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot" -o jsonpath='{.items[*].metadata.name}' | xargs -I {} sh -c "kubectl logs {} -n $NAMESPACE > $BACKUP_DIR/pod-{}.log" || log_warning "Could not backup some pod logs"

log_success "Backup created in $BACKUP_DIR"

# Perform rollback
log_info "Rolling back $RELEASE_NAME to version $TARGET_VERSION..."

if helm rollback "$RELEASE_NAME" -n "$NAMESPACE" --wait --timeout="${TIMEOUT"s; then
    log_success "Helm rollback completed successfully"
else
    log_error "Helm rollback failed"
    exit 1
fi

# Wait for deployment rollout
log_info "Waiting for deployment rollout..."

if kubectl rollout status "deployment/$RELEASE_NAME" -n "$NAMESPACE" --timeout="$TIMEOUT"s; then
    log_success "Deployment rollout completed successfully"
else
    log_error "Deployment rollout failed"
    log_error "Manual intervention may be required"
    exit 1
fi

# Verify deployment health
log_info "Verifying deployment health..."
REPLICAS=$(kubectl get deployment "$RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
if [[ "$REPLICAS" == "0" || -z "$REPLICAS" ]]; then
    log_error "Deployment is not healthy after rollback"
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

# Health check
log_info "Performing health check..."
if curl -f "$URL/health" --connect-timeout 10 --max-time 30 >/dev/null 2>&1; then
    log_success "Health check passed"
else
    log_error "Health check failed"
    log_warning "Rollback may need manual verification"
fi

# Clean up if canary rollback
if [[ "$DEPLOYMENT_TYPE" == "canary" ]]; then
    log_info "Cleaning up canary resources..."
    kubectl delete service "$CANARY_RELEASE" -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete ingress "$CANARY_RELEASE" -n "$NAMESPACE" --ignore-not-found=true
fi

# Update monitoring systems
log_info "Updating monitoring systems..."

# Reset error budget (if using SLO monitoring)
if command -v curl >/dev/null 2>&1 && [[ -n "${MONITORING_WEBHOOK_URL:-}" ]]; then
    curl -X POST "$MONITORING_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"action\": \"rollback\",
            \"deployment_type\": \"$DEPLOYMENT_TYPE\",
            \"from_version\": \"$CURRENT_VERSION\",
            \"to_version\": \"$TARGET_VERSION\",
            \"environment\": \"$ENVIRONMENT\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"backup_location\": \"$BACKUP_DIR\"
        }" || log_warning "Failed to update monitoring systems"
fi

# Show final status
log_success "Rollback completed successfully!"
log_info "Deployment Type: $DEPLOYMENT_TYPE"
log_info "From Version: $CURRENT_VERSION"
log_info "To Version: $TARGET_VERSION"
log_info "Environment: $ENVIRONMENT"
log_info "URL: $URL"
log_info "Backup Location: $BACKUP_DIR"

# Show deployment status
log_info "Current deployment status:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot" -o wide

# Show resource usage
log_info "Current resource usage:"
kubectl top pods -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot" 2>/dev/null || log_warning "Metrics server not available"

# Show recent events
log_info "Recent events:"
kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10

log_info "Rollback completed at $(date -u)"

# Provide next steps
log_info "Next steps:"
log_info "1. Monitor application health for next 30 minutes"
log_info "2. Check logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=dcmaidbot -f"
log_info "3. Monitor metrics in your dashboard"
log_info "4. Review rollback cause and prevent recurrence"
log_info "5. Consider updating deployment pipeline if needed"

if [[ "$DEPLOYMENT_TYPE" == "stable" ]]; then
    log_warning "Note: Canary deployment may still be active. Consider removing it if not needed."
    log_info "To remove canary: helm uninstall $CANARY_RELEASE -n $NAMESPACE"
fi
