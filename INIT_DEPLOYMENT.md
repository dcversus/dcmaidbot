# 🚀 Initial Deployment Instructions

Follow these steps to deploy dcmaidbot for the FIRST time on your Kubernetes cluster.

## Prerequisites

- ✅ SSH access to your Kubernetes server
- ✅ kubectl configured and working
- ✅ PR #15 merged to uz0/core-charts (or manual kubectl approach)

---

## 🔧 Step-by-Step Deployment

### Step 1: SSH to Your K8s Server

```bash
ssh user@your-k8s-server-ip
```

### Step 2: Verify kubectl Works

```bash
kubectl get nodes
kubectl get namespaces
```

Expected: You should see your cluster nodes and namespaces.

### Step 3: Create dcmaidbot Namespace

```bash
kubectl create namespace dcmaidbot
```

Verify:
```bash
kubectl get namespace dcmaidbot
```

### Step 4: Create Secrets

**⚠️ IMPORTANT: Replace with your actual values!**

```bash
kubectl create secret generic dcmaidbot-secrets \
  --namespace=dcmaidbot \
  --from-literal=bot-token='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz' \
  --from-literal=admin-vasilisa-id='123456789' \
  --from-literal=admin-daniil-id='987654321' \
  --from-literal=database-url='postgresql://dcmaidbot:password@postgres-service.default.svc.cluster.local:5432/dcmaidbot' \
  --from-literal=openai-api-key='sk-proj-...'
```

Verify secret created:
```bash
kubectl get secret dcmaidbot-secrets -n dcmaidbot
kubectl describe secret dcmaidbot-secrets -n dcmaidbot
```

### Step 5: Deploy dcmaidbot

**Option A: Using GitOps (After PR #15 merged)**

Create ArgoCD Application:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: dcmaidbot
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/uz0/core-charts.git
    targetRevision: main
    path: charts/dcmaidbot
    helm:
      valueFiles:
        - values.yaml
        - prod.tag.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dcmaidbot
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

**Option B: Direct kubectl (Manual, for testing)**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmaidbot
  namespace: dcmaidbot
  labels:
    app: dcmaidbot
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

### Step 6: Watch Deployment

```bash
# Watch pod creation
kubectl get pods -n dcmaidbot -w
```

Expected output:
```
NAME                         READY   STATUS    RESTARTS   AGE
dcmaidbot-xxxxx-yyyyy        1/1     Running   0          30s
```

Press `Ctrl+C` to stop watching.

### Step 7: Check Bot is Running

```bash
# View logs
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=50

# Follow logs in real-time
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=50 -f
```

Expected in logs:
```
Starting polling...
INFO - Bot started successfully
```

### Step 8: Test Bot in Telegram

1. Open Telegram
2. Find your bot (@your_bot_name)
3. Send `/start`
4. Expected: "Myaw! Hello dear guest! I'm DCMaid, your kawai waifu bot! 💕"

---

## 🔄 After GitOps is Setup (One-Time Only)

Once PR #15 is merged to uz0/core-charts, you only need to update version tags for deployments:

### Update to New Version

**In uz0/core-charts repo** (or your fork if you have write access):

```bash
# For production
cd charts/dcmaidbot
echo 'image:
  tag: "0.2.0"' > prod.tag.yaml
git add prod.tag.yaml
git commit -m "Update dcmaidbot to v0.2.0"
git push
```

ArgoCD automatically deploys within ~1 minute.

---

## 📊 Monitoring Commands

### Check Deployment Status
```bash
kubectl get deployment -n dcmaidbot
kubectl describe deployment dcmaidbot -n dcmaidbot
```

### Check Pod Health
```bash
kubectl get pods -n dcmaidbot
kubectl describe pod -n dcmaidbot <pod-name>
```

### View Logs
```bash
# Last 100 lines
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=100

# Follow live
kubectl logs -n dcmaidbot -l app=dcmaidbot -f

# Previous crashed pod (if restarted)
kubectl logs -n dcmaidbot -l app=dcmaidbot --previous
```

### Restart Bot
```bash
kubectl rollout restart deployment/dcmaidbot -n dcmaidbot
```

### Delete and Redeploy
```bash
kubectl delete deployment dcmaidbot -n dcmaidbot
# Then re-apply the deployment manifest from Step 5
```

---

## 🐛 Troubleshooting

### Pod not starting?
```bash
kubectl describe pod -n dcmaidbot <pod-name>
# Look for ImagePullBackOff, CrashLoopBackOff, etc.
```

### Image pull error?
```bash
# Check if image exists
docker pull ghcr.io/dcversus/dcmaidbot:latest

# May need image pull secret for private registry
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=dcversus \
  --docker-password=<GITHUB_PAT> \
  --namespace=dcmaidbot
```

### Bot not responding?
```bash
# Check logs for errors
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=200

# Common issues:
# - Invalid BOT_TOKEN
# - Network connectivity
# - Database connection failed
```

### Check secret values
```bash
kubectl get secret dcmaidbot-secrets -n dcmaidbot -o yaml
# Values are base64 encoded
kubectl get secret dcmaidbot-secrets -n dcmaidbot -o jsonpath='{.data.bot-token}' | base64 -d
```

---

## ✅ Success Checklist

- [ ] SSH to server successful
- [ ] kubectl commands work
- [ ] Namespace `dcmaidbot` created
- [ ] Secret `dcmaidbot-secrets` created with all 5 keys
- [ ] Deployment created
- [ ] Pod status: Running (1/1)
- [ ] Logs show "Starting polling..."
- [ ] Bot responds to `/start` in Telegram

---

## 🎯 Summary Commands (Quick Copy-Paste)

```bash
# 1. SSH
ssh user@your-server

# 2. Create namespace
kubectl create namespace dcmaidbot

# 3. Create secrets (REPLACE VALUES!)
kubectl create secret generic dcmaidbot-secrets \
  --namespace=dcmaidbot \
  --from-literal=bot-token='YOUR_BOT_TOKEN' \
  --from-literal=admin-vasilisa-id='YOUR_ID' \
  --from-literal=admin-daniil-id='YOUR_ID' \
  --from-literal=database-url='postgresql://...' \
  --from-literal=openai-api-key='sk-...'

# 4. Deploy (see Step 5 for full manifest)

# 5. Watch
kubectl get pods -n dcmaidbot -w

# 6. Check logs
kubectl logs -n dcmaidbot -l app=dcmaidbot -f
```

That's it! Nyaa~ 🎀
