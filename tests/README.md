# DCMaidBot E2E Testing

This directory contains end-to-end tests for DCMaidBot in production.

## Test Files

### 1. `e2e_call_endpoint.py` - Direct Bot Logic Tests ⭐ **RECOMMENDED**
**NEW**: Tests bot functionality by calling `/call` endpoint directly, bypassing Telegram entirely.

This is the **simplest and most reliable** E2E testing approach:
- ✅ No Telegram API credentials needed
- ✅ No user interaction required
- ✅ Tests actual bot logic (LLM, commands, personality)
- ✅ Fast and deterministic
- ✅ Perfect for CI/CD

**How it works:**
- Calls `/call` endpoint with user_id and command/message
- Bot processes request using same logic as Telegram handlers
- Returns response directly (no Telegram involved)

**Usage:**
```bash
export NUDGE_SECRET="your_secret"
python tests/e2e_call_endpoint.py
```

**What It Tests:**
- Authentication (same secret as /nudge)
- `/start`, `/help`, `/status`, `/love` commands
- `/joke` command (LLM integration)
- Waifu personality with natural messages (LLM)

**Why This Approach:**
- Telegram bots can't message users who haven't initiated chat
- `/call` bypasses Telegram entirely
- Tests the actual bot logic, not Telegram API
- Can be automated in CI/CD without credentials

---

### 2. `e2e_production.py` - Infrastructure Tests
Tests infrastructure health and availability:
- `/health` endpoint
- Landing page
- Bot info (via Telegram API)
- Bot commands configuration
- Webhook configuration
- Database connection
- Redis connection
- Message sending capability

**Usage:**
```bash
export BOT_TOKEN="your_bot_token"
export TEST_ADMIN_ID="your_telegram_id"
python tests/e2e_production.py
```

### 3. `e2e_user_stories.py` - User Story Tests
Tests all user stories and bot features:
- Bot commands: /start, /help, /status, /joke, /love
- LLM integration: waifu personality, streaming responses
- Memory system: PostgreSQL, Redis
- /nudge endpoint for agent communication

**Usage:**
```bash
export BOT_TOKEN="your_bot_token"
export TEST_ADMIN_ID="your_telegram_id"
python tests/e2e_user_stories.py
```

### 4. `e2e_with_userbot.py` - Real User Interaction Tests (Advanced)
**NEW**: Tests bot responses using a real Telegram user account via Pyrogram.

This script acts as a **real user** to send messages to the bot and verify responses. This solves the "chat not found" error that occurs when a bot tries to message a user who hasn't initiated contact first.

**Why This Approach?**
- Bots cannot send messages to users who haven't started a chat
- Bots cannot message other bots directly
- Pyrogram uses MTProto (Telegram's native protocol) to act as a user
- Enables automated testing without manual user interaction

**Setup:**

1. **Get Telegram API credentials:**
   - Visit https://my.telegram.org/apps
   - Log in with your Telegram account
   - Create a new application
   - Copy your `api_id` and `api_hash`

2. **Set environment variables:**
   ```bash
   export TELEGRAM_API_ID="12345"
   export TELEGRAM_API_HASH="your_hash_here"
   export TELEGRAM_USER_PHONE="+1234567890"  # Your phone number
   ```

3. **Install Pyrogram:**
   ```bash
   pip install 'pyrogram[fast]' tgcrypto
   ```

4. **First run (authentication):**
   ```bash
   python tests/e2e_with_userbot.py
   ```
   - You'll receive a login code via Telegram
   - Enter the code when prompted
   - Session saved to `tests/userbot.session`
   - **Keep this file secure!** (like a password)

5. **Subsequent runs:**
   ```bash
   python tests/e2e_with_userbot.py
   ```
   - Uses saved session (no login prompt)

**What It Tests:**
- `/start` command and bot response
- `/help` command and bot response
- `/status` command and bot response
- `/joke` command and LLM-generated joke
- Waifu personality with natural messages

**Security Notes:**
- `userbot.session` contains your login session - **keep it secret!**
- Add `tests/*.session` to `.gitignore`
- Never commit session files to git
- Use a dedicated test account if possible

## GitHub Actions Integration

E2E tests run automatically after each deployment via `.github/workflows/e2e-production.yml`.

**Required Secrets:**
- `BOT_TOKEN`: Test bot token (@dcnotabot)
- `TEST_ADMIN_ID`: Admin Telegram ID for testing
- `TELEGRAM_API_ID`: Telegram API ID for user client tests
- `TELEGRAM_API_HASH`: Telegram API hash for user client tests

**Manual Trigger:**
```bash
gh workflow run e2e-production.yml
```

## Test Bots

### Production Bot: @dcmaidbot
- Used for production deployment
- Configured with webhook: https://dcmaidbot.theedgestory.org/webhook
- Full waifu personality and features

### Test Bot: @dcnotabot
- Used for E2E testing
- Test bot token: stored in `.env` and Kubernetes secrets
- No webhook configuration (not needed for testing)

## Recommended Testing Strategy

### For Automated CI/CD: Use `/call` Endpoint ⭐
```bash
export NUDGE_SECRET="your_secret"
python tests/e2e_call_endpoint.py
```
- **Fastest and most reliable**
- No Telegram credentials needed
- Tests actual bot logic
- Perfect for automated testing

### For Manual Verification: Real Telegram Testing
After deployment, manually test with real Telegram:
1. Open Telegram app
2. Send messages to @dcmaidbot
3. Verify responses match expected behavior
4. Check UI elements (buttons, formatting)

### For Advanced Telegram Integration Testing: Pyrogram
Only needed if testing Telegram-specific features:
- Callback queries
- Inline keyboards
- Message editing
- Media handling

## Local Testing

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with credentials:**
   ```env
   # For /call endpoint tests (RECOMMENDED)
   NUDGE_SECRET=your_nudge_secret_here

   # For Telegram API tests (optional)
   BOT_TOKEN=your_test_bot_token_here
   ADMIN_IDS=122657093,196907653
   TEST_ADMIN_ID=122657093

   # For userbot tests (advanced, optional)
   TELEGRAM_API_ID=12345
   TELEGRAM_API_HASH=your_hash_here
   TELEGRAM_USER_PHONE=+1234567890
   ```

3. **Run tests:**
   ```bash
   # Direct bot logic tests (RECOMMENDED)
   python tests/e2e_call_endpoint.py

   # Infrastructure tests
   python tests/e2e_production.py

   # User story tests
   python tests/e2e_user_stories.py

   # User client tests (advanced)
   python tests/e2e_with_userbot.py
   ```

## Expected Results

### Infrastructure Tests (e2e_production.py)
When using test bot:
- ✅ Health Endpoint: PASS
- ✅ Landing Page: PASS
- ✅ Bot Info: PASS
- ✅ Database Connection: PASS
- ✅ Redis Connection: PASS
- ❌ Bot Commands: FAIL (test bot has no commands)
- ❌ Webhook Config: FAIL (test bot has no webhook)
- ❌ Send Message: FAIL (no chat initiated)

### User Story Tests (e2e_user_stories.py)
When using test bot without initiated chat:
- ❌ All message tests: FAIL ("chat not found")
- ✅ Database tests: PASS
- ✅ Redis tests: PASS
- ✅ /nudge endpoint: PASS

### User Client Tests (e2e_with_userbot.py)
When using Pyrogram user client:
- ✅ ALL tests should PASS
- Bot responds to all commands
- LLM integration working
- Waifu personality active

## Troubleshooting

**"chat not found" error:**
- Use `e2e_with_userbot.py` instead
- Or manually start a chat with the bot first

**Pyrogram authentication issues:**
- Check TELEGRAM_API_ID and TELEGRAM_API_HASH are correct
- Delete `tests/userbot.session` and try again
- Verify phone number format: +1234567890

**"Flood wait" error:**
- You're sending messages too fast
- Wait a few minutes before retrying
- Telegram rate limits apply

**Session file security:**
- Never commit `tests/*.session` files
- Keep session files as secure as passwords
- Use `.gitignore` to exclude them

## Contributing

When adding new E2E tests:
1. Add test to appropriate file (infrastructure vs user stories)
2. Use the `log_test()` function for consistent output
3. Handle exceptions gracefully
4. Document expected behavior
5. Update this README if needed
