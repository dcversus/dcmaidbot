# E2E Integration Tests with LLM-as-Judge

This directory contains **REAL** end-to-end tests that validate the bot's actual behavior.

## What These Tests Do

Unlike unit tests that test individual functions, these E2E tests:

1. ✅ Start the bot locally with `DISABLE_TG=true` (no Telegram needed)
2. ✅ Make HTTP requests to `/call` endpoint
3. ✅ Test with REAL LLM integration (not mocked)
4. ✅ Validate responses using **LLM-as-judge** methodology
5. ✅ Verify bot uses memories, message history, and emotional context

## Why LLM-as-Judge?

Traditional assertion-based tests can't validate natural language quality. LLM-as-judge:

- Evaluates semantic meaning, not exact strings
- Checks if bot demonstrates memory/context awareness
- Validates emotional intelligence and empathy
- Provides reasoning for pass/fail decisions
- Returns confidence scores

## Running E2E Tests

### Step 1: Start Local Bot

```bash
# Set environment variables
export DISABLE_TG=true
export DATABASE_URL="postgresql+asyncpg://dcmaidbot:password@localhost:5432/dcmaidbot_test"
export OPENAI_API_KEY="your_key_here"
export ADMIN_IDS="199572554"
export NUDGE_SECRET="test_secret_for_e2e"

# Start bot on port 8080
python bot_webhook.py
```

### Step 2: Run E2E Tests (in separate terminal)

```bash
# Run all E2E integration tests
pytest tests/e2e/test_bot_integration_with_llm_judge.py -v -s --log-cli-level=INFO

# Run specific test
pytest tests/e2e/test_bot_integration_with_llm_judge.py::test_bot_remembers_message_history -v -s

# Run with integration marker
pytest -m integration -v -s
```

## Test Structure

Each E2E test follows this pattern:

```python
@pytest.mark.integration
async def test_feature():
    # 1. Setup: Create test data (memories, messages)

    # 2. Act: Call bot via HTTP /call endpoint
    response = await call_bot(client, user_id, message)

    # 3. Assert: Use LLM-as-judge to validate response
    judgment = await judge_response(
        llm_judge,
        user_message=message,
        bot_response=response["response"],
        criteria="Bot should demonstrate X"
    )

    assert judgment["passes"] is True
    assert judgment["score"] >= 0.7
```

## Expected Results (Current State)

These tests are **EXPECTED TO FAIL** until we integrate memories/history into bot handlers:

- ❌ `test_bot_remembers_message_history` - Bot doesn't fetch history from database
- ❌ `test_bot_uses_memories_in_response` - Bot doesn't fetch memories from database
- ❌ `test_bot_creates_memories_from_conversation` - Bot doesn't create memories
- ❌ `test_bot_uses_vad_emotions_in_context` - Bot doesn't consider emotional context
- ✅ `test_bot_responds_without_telegram` - Should pass (basic connectivity)

## What We Need to Fix

To make these tests pass, we need to:

1. Update `handlers/waifu.py:handle_message()` to:
   - Fetch recent messages from database (message history)
   - Fetch user memories from `MemoryService`
   - Fetch user facts/stats from database
   - Store new message to database after receiving it

2. Update `services/llm_service.py:construct_prompt()` to:
   - Include message history in context
   - Include relevant memories in context
   - Include VAD emotional context
   - Include user facts/stats

3. Update `handlers/call.py:handle_message()` to use same logic

## Observability

These tests provide observability into:

- Whether bot actually uses the features we implemented
- Quality of bot responses (via LLM judge scores)
- Integration gaps between database and handlers
- Emotional intelligence effectiveness

## CI/CD Integration

These tests should run:

- ✅ During development (locally with `DISABLE_TG=true`)
- ✅ In CI pipeline (pytest with integration marker)
- ✅ After each deployment (smoke tests against production `/call` endpoint)
- ✅ Nightly (full regression test suite)
