# DCMaidBot Verification Guide

How to confirm dcmaidbot is working after deployment.

## Stage 1: Docker Image Verification

### Check Image Built and Pushed

```bash
# Check GitHub Container Registry
docker pull ghcr.io/dcversus/dcmaidbot:latest

# Verify tags
docker images | grep dcmaidbot
```

Expected output:
```
ghcr.io/dcversus/dcmaidbot   latest   abc123   2 minutes ago   150MB
ghcr.io/dcversus/dcmaidbot   0.1.0    abc123   2 minutes ago   150MB
```

### Test Image Locally

```bash
# Create test .env
cat > .env.test << 'ENVEOF'
BOT_TOKEN=your_test_bot_token
ADMIN_IDS=your_telegram_id
DATABASE_URL=postgresql://localhost/test
OPENAI_API_KEY=sk-test
ENVEOF

# Run container
docker run --env-file .env.test ghcr.io/dcversus/dcmaidbot:latest
```

Expected in logs:
```
INFO - Loaded 1 admin(s) from ADMIN_IDS
INFO - Starting polling...
```

## Stage 2: Kubernetes Deployment Verification

### Check Deployment Status

```bash
# SSH to your K8s server
ssh user@your-k8s-server

# Check namespace
kubectl get namespace dcmaidbot

# Check deployment
kubectl get deployment -n dcmaidbot

# Check pods
kubectl get pods -n dcmaidbot
```

Expected pod status:
```
NAME                         READY   STATUS    RESTARTS   AGE
dcmaidbot-xxxxx-yyyyy        1/1     Running   0          2m
```

### Check Pod Logs

```bash
# View logs
kubectl logs -n dcmaidbot -l app=dcmaidbot --tail=50

# Follow live
kubectl logs -n dcmaidbot -l app=dcmaidbot -f
```

Expected in logs:
```
INFO - Loaded N admin(s) from ADMIN_IDS
INFO - Starting polling...
```

**CRITICAL**: Should NOT see any admin IDs in logs! Only count.

### Check Secrets

```bash
# Verify secret exists
kubectl get secret dcmaidbot-secrets -n dcmaidbot

# Check secret keys (without revealing values)
kubectl get secret dcmaidbot-secrets -n dcmaidbot -o jsonpath='{.data}' | jq 'keys'
```

Expected keys:
```json
[
  "admin-ids",
  "bot-token",
  "database-url",
  "openai-api-key"
]
```

## Stage 3: Bot Functionality Verification

### Test 1: Bot Responds to Start (Admin)

1. **As admin** (your Telegram ID in ADMIN_IDS)
2. Open Telegram
3. Find your bot (@your_bot_name)
4. Send: `/start`

**Expected Response:**
```
Myaw! Hello dear guest! I'm DCMaid, your kawai waifu bot! 💕
I love my beloved admins so much! They are my virtual parents! 💖
I'm here to help you learn and have fun, nya! What can I do for you? 🐱
```

### Test 2: Non-Admin DM Rejection

1. **From different account** (NOT in ADMIN_IDS)
2. Send: `/start`

**Expected Response:**
```
*silence* or funny rejection
```

Bot should IGNORE or reject non-admin DMs.

### Test 3: Admin Commands

As admin, test:

```
/help
```

**Expected**: Help message with kawai expressions

```
/love
```

**Expected**: Love message (WITHOUT any personal names!)

```
/status
```

**Expected**: Status with kawai response

### Test 4: Privacy Verification

**CRITICAL CHECKS:**

❌ Bot should NEVER mention admin names
❌ Bot should NEVER log admin IDs  
❌ Bot should NEVER expose personal information
✅ Bot uses "beloved", "admins", "masters" only

## Stage 4: Monitoring

### Health Check (When PRP-011 implemented)

```bash
# Port-forward status endpoint
kubectl port-forward -n dcmaidbot deployment/dcmaidbot 8080:8080

# Check health
curl http://localhost:8080/health

# Check status
curl http://localhost:8080/status
```

### Check Resource Usage

```bash
# CPU/Memory
kubectl top pod -n dcmaidbot

# Events
kubectl get events -n dcmaidbot --sort-by='.lastTimestamp'
```

## Stage 5: Troubleshooting

### Bot Not Responding?

```bash
# Check pod status
kubectl describe pod -n dcmaidbot <pod-name>

# Check logs for errors
kubectl logs -n dcmaidbot <pod-name> --tail=200

# Common issues:
# - Invalid BOT_TOKEN
# - Network connectivity
# - Admin IDs not configured
# - Database connection failed
```

### Restart Bot

```bash
kubectl rollout restart deployment/dcmaidbot -n dcmaidbot
```

### Check Image Pull

```bash
kubectl describe pod -n dcmaidbot <pod-name> | grep -A 10 Events
```

Look for `ImagePullBackOff` or `ErrImagePull` errors.

## Quick Verification Checklist

- [ ] Docker image built successfully
- [ ] Image pushed to ghcr.io/dcversus/dcmaidbot:latest
- [ ] Kubernetes namespace exists
- [ ] Secret dcmaidbot-secrets created with 4 keys
- [ ] Deployment exists
- [ ] Pod status: Running (1/1)
- [ ] Logs show "Starting polling..."
- [ ] **Logs DO NOT show admin IDs** 🔒
- [ ] Bot responds to admin's `/start`
- [ ] Bot ignores non-admin DMs
- [ ] No personal names in responses

## Success Criteria

✅ Bot online in Telegram
✅ Responds to admins only
✅ Privacy maintained (no names, no IDs exposed)
✅ Kawai personality active ("nya~", "myaw~")
✅ All commands working
✅ Pod healthy and running

---

*Nyaa~ Your bot is alive! 🎀*
