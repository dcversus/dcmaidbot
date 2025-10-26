# DCMaidBot Deployment Guide

## Architecture Overview

```
dcmaidbot (this repo)     uz0/core-charts (GitOps repo)
     ↓                            ↓
  Docker Build              Helm Charts ✅ PR #15
     ↓                            ↓
GitHub Container Registry    ArgoCD watches
     ↓                            ↓
  ghcr.io/dcversus/         Kubernetes Cluster
    dcmaidbot:latest
```

**GitOps PR**: https://github.com/uz0/core-charts/pull/15

## Part 1: Docker Image (Already Configured ✅)

This repo automatically builds and pushes to GHCR when merging to `main`:
- Registry: `ghcr.io/dcversus/dcmaidbot`
- Tags: `latest`, `v0.1.0`, `0.1`, `0`
- Workflow: `.github/workflows/deploy.yml`
- Status: ✅ Ready to push on merge

## Part 2: GitOps Setup (PR Created ✅)

**PR to uz0/core-charts**: https://github.com/uz0/core-charts/pull/15

Helm chart following core-pipeline pattern with:
- Version tag files (`prod.tag.yaml`, `dev.tag.yaml`)
- ArgoCD-compatible manifests
- Secret management
- Resource limits

## Part 2-OLD: GitOps Manifests Reference (Now in PR #15)

### Create these files in uz0/core-charts:

#### 1. `charts/dcmaidbot/Chart.yaml`
```yaml
apiVersion: v2
name: dcmaidbot
description: Kawai AI-driven waifu Telegram bot
type: application
version: 0.1.0
appVersion: "0.1.0"
```

#### 2. `charts/dcmaidbot/values.yaml`
```yaml
replicaCount: 1

image:
  repository: ghcr.io/dcversus/dcmaidbot
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

env:
  # These will be overridden by secrets
  BOT_TOKEN: ""
  ADMIN_VASILISA_ID: ""
  ADMIN_DANIIL_ID: ""
  DATABASE_URL: ""
  OPENAI_API_KEY: ""

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

nodeSelector: {}
tolerations: []
affinity: {}
```

#### 3. `charts/dcmaidbot/templates/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "dcmaidbot.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    app: dcmaidbot
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: dcmaidbot
  template:
    metadata:
      labels:
        app: dcmaidbot
    spec:
      containers:
      - name: dcmaidbot
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        env:
        - name: BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: bot-token
        - name: ADMIN_VASILISA_ID
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: admin-vasilisa-id
        - name: ADMIN_DANIIL_ID
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: admin-daniil-id
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: openai-api-key
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

#### 4. `charts/dcmaidbot/templates/_helpers.tpl`
```yaml
{{- define "dcmaidbot.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
```

#### 5. `charts/dcmaidbot/prod.tag.yaml`
```yaml
image:
  tag: "0.1.0"
```

#### 6. `charts/dcmaidbot/dev.tag.yaml`
```yaml
image:
  tag: "latest"
```

## Part 3: Manual Deployment (kubectl commands)

### Step 1: SSH to your Kubernetes server
```bash
ssh user@your-k8s-server
```

### Step 2: Clone this repo on the server
```bash
cd ~
git clone https://github.com/dcversus/dcmaidbot.git
cd dcmaidbot
```

### Step 3: Create namespace
```bash
kubectl create namespace dcmaidbot
```

### Step 4: Create secrets
```bash
kubectl create secret generic dcmaidbot-secrets \
  --namespace=dcmaidbot \
  --from-literal=bot-token='YOUR_BOT_TOKEN' \
  --from-literal=admin-vasilisa-id='VASILISA_TELEGRAM_ID' \
  --from-literal=admin-daniil-id='DANIIL_TELEGRAM_ID' \
  --from-literal=database-url='postgresql://user:password@postgres:5432/dcmaidbot' \
  --from-literal=openai-api-key='YOUR_OPENAI_KEY'
```

### Step 5: Create deployment manually (temporary, before GitOps)
```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmaidbot
  namespace: dcmaidbot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dcmaidbot
  template:
    metadata:
      labels:
        app: dcmaidbot
    spec:
      containers:
      - name: dcmaidbot
        image: ghcr.io/dcversus/dcmaidbot:latest
        imagePullPolicy: Always
        env:
        - name: BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: bot-token
        - name: ADMIN_VASILISA_ID
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: admin-vasilisa-id
        - name: ADMIN_DANIIL_ID
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: admin-daniil-id
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: openai-api-key
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 128Mi
EOF
```

### Step 6: Check deployment status
```bash
# Watch deployment
kubectl get pods -n dcmaidbot -w

# Check logs
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=100 -f

# Check deployment status
kubectl get deployment -n dcmaidbot
kubectl describe deployment dcmaidbot -n dcmaidbot
```

### Step 7: Update image (for new versions)
```bash
kubectl set image deployment/dcmaidbot \
  dcmaidbot=ghcr.io/dcversus/dcmaidbot:v0.1.0 \
  -n dcmaidbot

# Or rollout restart
kubectl rollout restart deployment/dcmaidbot -n dcmaidbot
```

## Part 4: GitOps Setup (After PR to uz0/core-charts)

### Create PR to uz0/core-charts
1. Fork `https://github.com/uz0/core-charts`
2. Add the files listed in Part 2 to your fork
3. Create PR with title: "Add dcmaidbot deployment"
4. Wait for PR review and merge

### After PR merge, ArgoCD will auto-deploy
ArgoCD will watch the `charts/dcmaidbot/` directory and automatically deploy when:
- `prod.tag.yaml` or `dev.tag.yaml` is updated
- Any Helm chart files change

### Update dcmaidbot version via GitOps
```bash
# In uz0/core-charts repo
cd charts/dcmaidbot
echo "image:
  tag: \"0.2.0\"" > prod.tag.yaml
git add prod.tag.yaml
git commit -m "Update dcmaidbot to v0.2.0"
git push

# ArgoCD automatically deploys new version
```

## Troubleshooting

### Check if image is accessible
```bash
# On k8s server
docker pull ghcr.io/dcversus/dcmaidbot:latest
```

### Check pod logs
```bash
kubectl logs -n dcmaidbot <pod-name>
```

### Describe pod for errors
```bash
kubectl describe pod -n dcmaidbot <pod-name>
```

### Delete and recreate
```bash
kubectl delete deployment dcmaidbot -n dcmaidbot
# Then re-apply the deployment manifest
```

## Next Steps After Initial Deployment

1. ✅ Manual kubectl deployment working
2. Create PR to uz0/core-charts with manifests
3. After PR merged, ArgoCD takes over
4. All future updates via GitOps (update tag files in core-charts)
5. This repo (dcmaidbot) only builds and pushes Docker images
