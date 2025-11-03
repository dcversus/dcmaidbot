#!/bin/bash
# DCMAIDBot Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version] [--canary] [--dry-run]

set -euo pipefail

# Default values
ENVIRONMENT="production"
VERSION=""
CANARY=false
DRY_RUN=false
NAMESPACE="dcmaidbot"
CHART_PATH="./helm/dcmaidbot"
TIMEOUT=600

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
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --version|-v)
            VERSION="$2"
            shift 2
            ;;
        --canary|-c)
            CANARY=true
            shift
            ;;
        --dry-run|-d)
            DRY_RUN=true
            shift
            ;;
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --environment, -e    Environment (production|development|staging) [default: production]"
            echo "  --version, -v        Version to deploy"
            echo "  --canary, -c         Deploy as canary (10% traffic)"
            echo "  --dry-run, -d        Show what would be deployed without doing it"
            echo "  --namespace, -n      Kubernetes namespace [default: dcmaidbot]"
            echo "  --timeout, -t        Deployment timeout in seconds [default: 600]"
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

# Get version if not provided
if [[ -z "$VERSION" ]]; then
    VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "latest")
    log_info "Using version: $VERSION"
fi

# Set release name
if [[ "$CANARY" == true ]]; then
    RELEASE_NAME="dcmaidbot-canary"
    DEPLOYMENT_NAME="dcmaidbot-canary"
else
    RELEASE_NAME="dcmaidbot"
    DEPLOYMENT_NAME="dcmaidbot"
fi

# Show deployment info
log_info "Deployment Configuration:"
log_info "  Environment: $ENVIRONMENT"
log_info "  Version: $VERSION"
log_info "  Release Name: $RELEASE_NAME"
log_info "  Namespace: $NAMESPACE"
log_info "  Canary: $CANARY"
log_info "  Dry Run: $DRY_RUN"

# Prepare Helm values
HELM_VALUES=(
    "--set" "image.tag=$VERSION"
    "--set" "environment=$ENVIRONMENT"
)

if [[ "$CANARY" == true ]]; then
    HELM_VALUES+=(
        "--set" "canary.enabled=true"
        "--set" "canary.image.tag=$VERSION"
        "--set" "canary.trafficPercentage=10"
    )
    log_info "  Canary Traffic: 10%"
fi

# Environment-specific configurations
case $ENVIRONMENT in
    production)
        HELM_VALUES+=(
            "--set" "replicaCount=3"
            "--set" "autoscaling.enabled=true"
            "--set" "ingress.hosts[0].host=dcmaidbot.theedgestory.org"
            "--set" "resources.limits.cpu=500m"
            "--set" "resources.limits.memory=512Mi"
        )
        ;;
    development)
        HELM_VALUES+=(
            "--set" "replicaCount=1"
            "--set" "autoscaling.enabled=false"
            "--set" "ingress.hosts[0].host=dcmaidbot-dev.theedgestory.org"
            "--set" "resources.limits.cpu=250m"
            "--set" "resources.limits.memory=256Mi"
        )
        ;;
    staging)
        HELM_VALUES+=(
            "--set" "replicaCount=2"
            "--set" "autoscaling.enabled=true"
            "--set" "ingress.hosts[0].host=dcmaidbot-staging.theedgestory.org"
            "--set" "resources.limits.cpu=300m"
            "--set" "resources.limits.memory=384Mi"
        )
        ;;
esac

# Create namespace if it doesn't exist
if [[ "$DRY_RUN" == false ]]; then
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    log_success "Namespace $NAMESPACE ready"
fi

# Dry run mode
if [[ "$DRY_RUN" == true ]]; then
    log_info "DRY RUN - Showing Helm command that would be executed:"
    echo "helm upgrade --install $RELEASE_NAME $CHART_PATH \\"
    echo "  --namespace $NAMESPACE \\"
    for value in "${HELM_VALUES[@]}"; do
        echo "  $value \\"
    done
    echo "  --wait --timeout=${TIMEOUT}s --debug --dry-run"
    exit 0
fi

# Deploy with Helm
log_info "Deploying $RELEASE_NAME to $NAMESPACE..."

if helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
    --namespace "$NAMESPACE" \
    "${HELM_VALUES[@]}" \
    --wait \
    --timeout="${TIMEOUT}s" \
    --debug; then

    log_success "Helm deployment completed successfully"
else
    log_error "Helm deployment failed"
    exit 1
fi

# Wait for deployment rollout
log_info "Waiting for deployment rollout..."

DEPLOYMENT_RESOURCE=""
if [[ "$CANARY" == true ]]; then
    DEPLOYMENT_RESOURCE="deployment/$DEPLOYMENT_NAME"
else
    DEPLOYMENT_RESOURCE="deployment/$DEPLOYMENT_NAME"
fi

if kubectl rollout status "$DEPLOYMENT_RESOURCE" -n "$NAMESPACE" --timeout="$TIMEOUT"s; then
    log_success "Deployment rollout completed successfully"
else
    log_error "Deployment rollout failed"
    exit 1
fi

# Show deployment status
log_info "Deployment status:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot" -o wide

# Show service status
log_info "Service status:"
kubectl get services -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot"

# Show ingress status
log_info "Ingress status:"
kubectl get ingress -n "$NAMESPACE" -l "app.kubernetes.io/name=dcmaidbot"

# Get external URL
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
    log_warning "Health check failed - deployment may need troubleshooting"
fi

# Show final information
log_success "Deployment completed successfully!"
log_info "Environment: $ENVIRONMENT"
log_info "Version: $VERSION"
log_info "URL: $URL"
log_info "Canary: $CANARY"

if [[ "$CANARY" == true ]]; then
    log_info "Canary is now receiving 10% of traffic"
    log_info "Monitor canary performance before promoting to production"
    log_info "To promote: ./scripts/promote-canary.sh $VERSION"
    log_info "To rollback: ./scripts/rollback.sh canary"
else
    log_info "Application is now live and receiving production traffic"
fi

log_info "To check logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=dcmaidbot -f"
log_info "To scale: kubectl scale deployment $DEPLOYMENT_NAME -n $NAMESPACE --replicas=3"
