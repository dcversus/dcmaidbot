# Post-Deployment Verification Guide

**Purpose**: Verify all implemented features are working after deployment to production.

**Run this checklist after EVERY deployment!**

---

## Quick Start

After merging PR and watching deploy workflow succeed:

```bash
# 1. Check deployment happened
kubectl get pods -n prod-core -l app=dcmaidbot

# 2. Check new pod is running
kubectl logs -n prod-core <new-pod-name> --tail=50

# 3. Run verification sections below
```

---

## Section 1: Infrastructure Verification (PRP-001)

**Source**: See `PRPs/PRP-001.md` for full checklist

### Pre-Deployment Checks
- [ ] Docker image built successfully in CI
  ```bash
  # Check latest workflow run
  gh run list --workflow=deploy.yml --limit 1
  ```

- [ ] Image pushed to GHCR (ghcr.io/dcversus/dcmaidbot)
  ```bash
  # Check in GitHub Packages
  # https://github.com/dcversus?tab=packages
  ```

- [ ] Image tagged with version from version.txt
  ```bash
  cat version.txt
  # Should match image tag in deployment
  ```

- [ ] GitHub release created with changelog
  ```bash
  gh release list --limit 1
  ```

### Deployment Checks
- [ ] ArgoCD shows deployment synced
  ```bash
  # Check ArgoCD UI or:
  kubectl get applications -n argocd | grep dcmaidbot
  ```

- [ ] Pod is running
  ```bash
  kubectl get pods -n prod-core -l app=dcmaidbot
  # Expected: 1/1 Running
  ```

- [ ] Pod logs show bot started
  ```bash
  kubectl logs -n prod-core <pod-name> --tail=50
  # Look for: "Bot started" or similar
  ```

- [ ] No error messages in pod logs
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i error | tail -20
  # Should be empty or only old errors
  ```

### Bot Functionality Checks
- [ ] Bot is online in Telegram
  ```
  Open Telegram, search for @dcmaidbot
  Check: Green dot (online) or "last seen recently"
  ```

- [ ] Bot responds to /start command
  ```
  Send: /start
  Expected: Bot replies with greeting
  ```

- [ ] Bot environment variables loaded correctly
  ```bash
  kubectl exec -n prod-core <pod-name> -- env | grep BOT_TOKEN | wc -c
  # Should be > 40 (token length)
  ```

### Infrastructure Checks
- [ ] Service exists
  ```bash
  kubectl get svc -n prod-core | grep dcmaidbot
  ```

- [ ] Ingress exists (if webhook mode)
  ```bash
  kubectl get ingress -n prod-core | grep dcmaidbot
  ```

- [ ] DNS resolves correctly (if webhook)
  ```bash
  nslookup dcmaidbot.theedgestory.org
  ```

- [ ] HTTPS certificate valid (if webhook)
  ```bash
  curl -I https://dcmaidbot.theedgestory.org/webhook
  ```

### Rollback Plan
- [ ] Previous version documented
  ```bash
  # Note current version before deploying
  kubectl get deployment dcmaidbot-prod -n prod-core -o jsonpath='{.spec.template.spec.containers[0].image}'
  ```

- [ ] Rollback command ready
  ```bash
  # If needed:
  kubectl rollout undo deployment dcmaidbot-prod -n prod-core
  ```

**Result**: ✅ PASS / ❌ FAIL

---

## Section 2: Waifu Personality & Admin System (PRP-002)

**Source**: See `PRPs/PRP-002.md` for full checklist

**NOTE**: Many PRP-002 features are NOT yet implemented (see PRP_AUDIT.md)

### Admin System Checks
- [ ] Bot responds to admin messages in DM
  ```
  From admin account, send DM: "Hello"
  Expected: Bot replies with kawai response
  ```

- [ ] Bot responds to admin messages in group chat
  ```
  Add bot to test group with admin
  Admin sends: "Test message"
  Expected: Bot replies
  ```

- [ ] Bot ignores non-admin messages in DM ⚠️ NOT IMPLEMENTED
  ```
  From non-admin account, send DM: "Hello"
  Expected: Bot ignores (currently responds to all)
  Status: ❌ Gap in PRP-002
  ```

- [ ] Bot ignores non-admin messages in group ⚠️ NOT IMPLEMENTED
  ```
  Non-admin in group: "Test"
  Expected: Bot ignores unless admin present
  Status: ❌ Gap in PRP-002
  ```

- [ ] ADMIN_IDS loaded correctly from .env
  ```bash
  kubectl exec -n prod-core <pod-name> -- env | grep ADMIN_IDS
  # Should show your admin IDs
  ```

### Waifu Personality Checks
- [ ] Bot uses "nya", "myaw", "kawai" in responses
  ```
  Send message to bot
  Expected: Response includes kawai expressions
  Status: 🟡 Partial (some responses have them)
  ```

- [ ] Bot expresses love for admins
  ```
  Mention "master" or "admin" in message
  Expected: Bot responds with love message
  ```

- [ ] Bot mentions Vasilisa and Daniil affectionately ⚠️ HARDCODED CHECK
  ```
  Check: handlers/waifu.py for mentions
  Status: 🟡 Basic mentions exist
  ```

- [ ] Bot uses Papa's emoji: 💕 <3 👅
  ```
  Check bot responses for these emoji
  Status: 🟡 Some responses have them
  ```

### Bilingual Checks ⚠️ NOT IMPLEMENTED
- [ ] Bot responds in Russian to Russian messages
  ```
  Send: "Привет"
  Expected: Russian response
  Status: ❌ Not implemented
  ```

- [ ] Bot responds in English to English messages
  ```
  Send: "Hello"
  Expected: English response
  Status: ✅ Working (default)
  ```

- [ ] Bot uses emoji in responses
  ```
  Check: Most responses should have emoji
  Status: 🟡 Some have emoji
  ```

- [ ] Bot transliterates playfully ⚠️ NOT IMPLEMENTED
  ```
  Expected: комфортный = comfortny
  Status: ❌ Not implemented
  ```

### Protector Mode Checks ⚠️ NOT IMPLEMENTED
- [ ] Bot detects aggressive behavior toward admins
  ```
  Test: Send aggressive message about admin
  Expected: Bot warns
  Status: ❌ Not implemented
  ```

- [ ] Bot warns enemies of admins
  ```
  Status: ❌ Not implemented
  ```

- [ ] Bot can kick users (if admin in group)
  ```
  Status: ❌ Not implemented
  ```

- [ ] Bot logs protector mode activations
  ```
  Status: ❌ Not implemented
  ```

### Edge Cases
- [ ] Bot handles unknown commands gracefully
  ```
  Send: /unknowncommand
  Expected: Bot responds politely or ignores
  ```

- [ ] Bot handles media messages (photos, videos)
  ```
  Send photo to bot
  Expected: Bot acknowledges or responds
  ```

- [ ] Bot handles forwarded messages
  ```
  Forward a message to bot
  Expected: Bot handles without crashing
  ```

- [ ] Bot doesn't crash on malformed input
  ```
  Send: Very long message (> 4096 chars)
  Expected: Bot handles gracefully
  ```

**Result**: 🟡 PARTIAL (many features not implemented yet)

**Note**: See `PRPs/PRP_AUDIT.md` for complete gap analysis

---

## Section 3: PostgreSQL Database (PRP-003)

**Source**: See `PRPs/PRP-003.md` for full checklist

### Database Connection Checks
- [ ] DATABASE_URL configured in .env
  ```bash
  kubectl get secret dcmaidbot-secrets -n prod-core -o jsonpath='{.data.database-url}' | base64 -d | head -c 20
  # Should show: postgresql://...
  ```

- [ ] Bot connects to PostgreSQL successfully
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i "database\|postgres\|connect"
  # Look for: "Connected to database" or similar
  ```

- [ ] Connection pooling working (no connection errors)
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i "pool\|connection"
  # No "too many connections" errors
  ```

- [ ] Bot logs show "Database connected" or similar
  ```bash
  kubectl logs -n prod-core <pod-name> --tail=100 | grep -i database
  ```

### Schema Validation
- [ ] All 6 tables exist: users, messages, facts, stats, memories, jokes
  ```bash
  # Connect to database and run:
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import engine
  from sqlalchemy import inspect
  import asyncio
  async def check():
      async with engine.connect() as conn:
          result = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
          print('Tables:', result)
  asyncio.run(check())
  "
  ```

- [ ] alembic_version table exists
  ```bash
  # Check via database or:
  kubectl exec -n prod-core <pod-name> -- alembic current
  # Should show: current migration version
  ```

- [ ] Current migration matches alembic_version
  ```bash
  kubectl exec -n prod-core <pod-name> -- alembic current
  # Expected: 36d7ed86833d (initial migration)
  ```

- [ ] No migration errors in logs
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i "alembic\|migration"
  # No error messages
  ```

### Data Persistence Checks
- [ ] Messages are stored in database
  ```bash
  # Send test message to bot, then check:
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import async_session_maker
  from models import Message
  from sqlalchemy import select
  import asyncio
  async def check():
      async with async_session_maker() as session:
          result = await session.execute(select(Message).limit(5))
          messages = result.scalars().all()
          print(f'Messages in DB: {len(messages)}')
          for msg in messages:
              print(f'  - {msg.text[:50]}...')
  asyncio.run(check())
  "
  ```

- [ ] User records are created on first message
  ```bash
  # Check users table has entries
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import async_session_maker
  from models import User
  from sqlalchemy import select
  import asyncio
  async def check():
      async with async_session_maker() as session:
          result = await session.execute(select(User))
          users = result.scalars().all()
          print(f'Users in DB: {len(users)}')
  asyncio.run(check())
  "
  ```

- [ ] Timestamps are stored correctly (UTC)
  ```bash
  # Check message timestamps
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import async_session_maker
  from models import Message
  from sqlalchemy import select
  import asyncio
  async def check():
      async with async_session_maker() as session:
          result = await session.execute(select(Message).limit(1))
          msg = result.scalar_one_or_none()
          if msg:
              print(f'Latest message timestamp: {msg.timestamp}')
  asyncio.run(check())
  "
  ```

- [ ] Foreign keys work (message.user_id → users.id)
  ```bash
  # Send message and check it links to user correctly
  # Should not see foreign key constraint errors in logs
  kubectl logs -n prod-core <pod-name> | grep -i "foreign key\|constraint"
  ```

### Performance Checks
- [ ] Query response times < 100ms
  ```bash
  # Monitor slow query logs or check in pod
  kubectl logs -n prod-core <pod-name> | grep -i "slow\|timeout"
  # Should be empty
  ```

- [ ] No connection pool exhaustion warnings
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i "pool.*exhaust\|too many connections"
  # Should be empty
  ```

- [ ] Database doesn't grow unbounded (retention policy?)
  ```bash
  # Check database size (if accessible)
  # Plan: Implement cleanup cron job later
  ```

- [ ] Indexes working (check query plans if slow)
  ```bash
  # If queries are slow, check EXPLAIN output
  # For now: monitor performance
  ```

### Migration Testing
- [ ] Run: `alembic current` shows correct version
  ```bash
  kubectl exec -n prod-core <pod-name> -- alembic current
  # Expected: 36d7ed86833d
  ```

- [ ] Run: `alembic upgrade head` works without errors
  ```bash
  kubectl exec -n prod-core <pod-name> -- alembic upgrade head
  # Expected: "Running upgrade..."
  ```

- [ ] Run: `alembic downgrade -1` works without errors
  ```bash
  kubectl exec -n prod-core <pod-name> -- alembic downgrade -1
  # Expected: "Running downgrade..."
  # WARNING: Only do this in testing!
  ```

- [ ] Run: `alembic upgrade head` again to restore
  ```bash
  kubectl exec -n prod-core <pod-name> -- alembic upgrade head
  ```

### Data Integrity Checks
- [ ] No duplicate user records (telegram_id is unique)
  ```bash
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import async_session_maker
  from models import User
  from sqlalchemy import select, func
  import asyncio
  async def check():
      async with async_session_maker() as session:
          result = await session.execute(
              select(User.telegram_id, func.count(User.id))
              .group_by(User.telegram_id)
              .having(func.count(User.id) > 1)
          )
          duplicates = result.all()
          if duplicates:
              print(f'Duplicate users found: {duplicates}')
          else:
              print('No duplicate users ✅')
  asyncio.run(check())
  "
  ```

- [ ] No orphaned messages (all have valid user_id)
  ```bash
  # Check foreign key constraints are enforced
  kubectl logs -n prod-core <pod-name> | grep -i "foreign key.*violat"
  # Should be empty
  ```

- [ ] Timestamps are in correct timezone
  ```bash
  # Check timestamps are UTC
  kubectl exec -n prod-core <pod-name> -- python3 -c "
  from database import async_session_maker
  from models import Message
  from sqlalchemy import select
  import asyncio
  async def check():
      async with async_session_maker() as session:
          result = await session.execute(select(Message).limit(1))
          msg = result.scalar_one_or_none()
          if msg:
              print(f'Timestamp: {msg.timestamp}')
              print(f'Timezone info: {msg.timestamp.tzinfo}')
  asyncio.run(check())
  "
  ```

- [ ] Data types match schema (no type errors)
  ```bash
  kubectl logs -n prod-core <pod-name> | grep -i "type error\|datatype"
  # Should be empty
  ```

**Result**: ✅ PASS / ❌ FAIL

---

## Section 4: Quick Smoke Tests

**Run these for every deployment (fast checks)**

### 5-Minute Smoke Test
```bash
# 1. Pod is running
kubectl get pods -n prod-core -l app=dcmaidbot
# Expected: 1/1 Running

# 2. No recent errors in logs
kubectl logs -n prod-core <pod-name> --since=5m | grep -i error
# Expected: Empty

# 3. Bot responds to /start
# Send /start to @dcmaidbot in Telegram
# Expected: Bot replies

# 4. Database connection working
kubectl logs -n prod-core <pod-name> | grep -i "database\|postgres" | tail -5
# Expected: Connection messages, no errors

# 5. Check version
kubectl exec -n prod-core <pod-name> -- cat version.txt
# Expected: Matches deployed version
```

### 15-Minute Deep Check
```bash
# Run all checks from Sections 1-3 above
# Focus on:
# - Database persistence (send message, verify stored)
# - Admin detection (test with admin account)
# - Error logs (no errors in 15 minutes)
# - Performance (no slow queries)
```

---

## Section 5: Monitoring & Alerts

### What to Monitor (24 hours post-deploy)

**Kubernetes**:
```bash
# Pod restarts (should be 0)
kubectl get pods -n prod-core -l app=dcmaidbot -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'

# Pod resource usage
kubectl top pod -n prod-core -l app=dcmaidbot

# Events
kubectl get events -n prod-core --sort-by='.lastTimestamp' | grep dcmaidbot | tail -20
```

**Application Logs**:
```bash
# Error count (should be low)
kubectl logs -n prod-core <pod-name> --since=1h | grep -c ERROR

# Warning count
kubectl logs -n prod-core <pod-name> --since=1h | grep -c WARNING

# Connection issues
kubectl logs -n prod-core <pod-name> --since=1h | grep -i "connection\|pool"
```

**Database**:
```bash
# Connection pool health
kubectl logs -n prod-core <pod-name> | grep -i "pool" | tail -10

# Slow queries
kubectl logs -n prod-core <pod-name> | grep -i "slow"

# Database errors
kubectl logs -n prod-core <pod-name> | grep -i "database error\|sqlalchemy error"
```

### Alert Thresholds
- ⚠️ Pod restarts > 0 in 1 hour
- ⚠️ Errors > 10 in 1 hour
- ⚠️ Memory usage > 400MB (limit is 512MB)
- ⚠️ CPU usage > 80% for 5 minutes
- 🚨 Pod not running for > 2 minutes
- 🚨 Database connection errors

---

## Section 6: Rollback Decision Tree

**When to rollback?**

### Immediate Rollback (P0)
- [ ] Pod won't start (CrashLoopBackOff)
- [ ] Database migration failed
- [ ] Bot not responding to ANY messages
- [ ] Critical errors in logs (> 50/minute)
- [ ] Data loss or corruption

### Consider Rollback (P1)
- [ ] New features not working
- [ ] Performance degradation (> 50% slower)
- [ ] Memory leaks detected
- [ ] Some features broken

### Monitor & Fix Forward (P2)
- [ ] Minor bugs in new features
- [ ] Non-critical warnings in logs
- [ ] Edge case failures
- [ ] Documentation issues

### Rollback Commands
```bash
# Option 1: Kubectl rollback
kubectl rollout undo deployment dcmaidbot-prod -n prod-core
kubectl rollout status deployment dcmaidbot-prod -n prod-core

# Option 2: Database rollback (if needed)
kubectl exec -n prod-core <pod-name> -- alembic downgrade -1

# Option 3: Git revert + redeploy
git revert <merge-commit-sha>
git push origin main
# Wait for deploy workflow
```

---

## Section 7: Sign-Off Checklist

**Complete this after running all verification sections**

### Deployment Success Criteria
- [ ] All Section 1 checks passing (Infrastructure)
- [ ] Most Section 2 checks passing (Waifu/Admin) - some features not implemented
- [ ] All Section 3 checks passing (Database)
- [ ] Smoke tests passing
- [ ] No P0 or P1 issues found

### Sign-Off
- **Verified by**: _______________
- **Date**: _______________
- **Version deployed**: _______________
- **Issues found**: _______________
- **Action taken**: _______________

### Deployment Status
- [ ] ✅ APPROVED - Production ready
- [ ] 🟡 APPROVED WITH ISSUES - Monitor closely
- [ ] ❌ ROLLBACK REQUIRED - Critical issues

---

## Quick Reference

### Useful Commands
```bash
# Get pod name
export POD=$(kubectl get pod -n prod-core -l app=dcmaidbot -o jsonpath='{.items[0].metadata.name}')

# View logs
kubectl logs -n prod-core $POD --tail=100 -f

# Execute command in pod
kubectl exec -n prod-core $POD -- <command>

# Check deployment status
kubectl rollout status deployment dcmaidbot-prod -n prod-core

# Get pod details
kubectl describe pod -n prod-core $POD

# Check resource usage
kubectl top pod -n prod-core $POD
```

### Where to Find Full Checklists
- **PRP-001**: `PRPs/PRP-001.md` - Infrastructure validation
- **PRP-002**: `PRPs/PRP-002.md` - Waifu/Admin validation
- **PRP-003**: `PRPs/PRP-003.md` - Database validation
- **Audit**: `PRPs/PRP_AUDIT.md` - Known gaps and issues
- **Fixes**: `PRPs/FIXES_APPLIED.md` - Recent fixes applied

---

**Created**: 2025-10-27
**Last Updated**: 2025-10-27
**Maintained by**: Development Team

Nyaa~ Use this checklist after EVERY deployment to ensure everything works! 💕👅
