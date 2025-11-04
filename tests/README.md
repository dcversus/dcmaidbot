# DCMAIDBot Testing Suite

This document describes the complete testing strategy for DCMAIDBot, following the refined approach with only 3 E2E tests and focused unit tests aligned with PRPs.

## 🎯 Testing Philosophy

**Streamlined to 3 Core Tests:**
1. **Comprehensive Conversation Journey** - Single long conversation covering all features (with optional LLM Judge evaluation)
2. **Status Check** - Single status call with automated analysis
3. **Platform Integration** - Manual TG/Discord testing

**Behavioral Unit Tests:**
- Focus on PRP requirements and DoD validation
- Test user-visible behavior, not implementation details
- Aligned with business outcomes

## 📁 Refined Test Structure

### 🚀 E2E Tests (3 Core Tests)

#### 1. **Comprehensive Conversation Journey**
- **File**: `tests/e2e/test_comprehensive_conversation_journey.py`
- **Coverage**: Single natural conversation testing all features
- **PRP Coverage**: PRP-002 (Call Endpoint), PRP-005 (Emotional Memory), PRP-009 (External Tools)
- **When to Run**: Automated in CI, pre/post-release
- **Test Cases**:
  - Memory creation and recall (line 65-85) → PRP-005 DOD: Memory Persistence
  - Lessons system (line 88-98) → PRP-002 DOD: Educational Content
  - VAD and mood tracking (line 101-117) → PRP-005 DOD: Emotional Intelligence
  - Complex reasoning (line 138-155) → PRP-002 DOD: Problem Solving
  - External tools (line 158-170) → PRP-009 DOD: Tool Integration
  - Admin features (line 173-190) → PRP-017 DOD: RBAC
- **Optional LLM Judge Evaluation**: Runs automatically if OPENAI_API_KEY is set (line 340-397)

#### 2. **Status Check with Thoughts**
- **File**: `tests/e2e/test_status_check.py`
- **Purpose**: Single status call with thoughts polling and LLM Judge analysis
- **Coverage**: System health, version thoughts, self-check thoughts, crypto thoughts
- **When to Run**: CI monitoring, post-release health check
- **Features**:
  - Calls /status endpoint
  - Polls for thoughts generation (version, self-check, crypto)
  - LLM Judge evaluation of status and thoughts
  - Component health validation
  - Minimum 70% health requirement

#### 3. **Platform Integration (Manual)**
- **File**: `tests/e2e/test_platform_integration_manual.py`
- **Purpose**: Manual TG/Discord validation
- **Coverage**: Real platform functionality
- **When to Run**: Pre-release (staging), Post-release (production)
- **Manual Steps**:
  - Telegram functionality (line 45-85)
  - Discord functionality (line 90-130)
  - Cross-platform consistency (line 135-165)

### 🧪 Unit Tests
**Status**: No unit tests currently - all implementation-focused tests were removed
**Focus**: Business/DoD validation tests are used instead

### 🧠 LLM Judge Framework (Evaluation Tool)
- **Core**: `tests/llm_judge.py`
- **Purpose**: AI evaluation framework (NOT a test)
- **Used By**: E2E journey test as optional post-conversation analysis

## 🏃‍♂️ Running Tests

### Quick Start
```bash
# Start test server (for E2E tests)
python3 run_test_server.py --port 8000 --db sqlite &

# Run comprehensive conversation journey (includes optional LLM Judge)
PYTHONPATH=/Users/dcversus/Documents/GitHub/dcmaidbot pytest tests/e2e/test_comprehensive_conversation_journey.py -v -s

# Run business validation tests
pytest tests/business/dod_validation/ -v
```

### Development Tests (Fast)
```bash
# Business validation tests only
pytest tests/business/dod_validation/ -v --maxfail=1

# Code quality
ruff check . && ruff format .
mypy src/
```

### Pre-Release Tests (Comprehensive)
```bash
# Full test suite
pytest tests/e2e/test_comprehensive_conversation_journey.py -v
pytest tests/business/dod_validation/ -v

# Manual platform testing (staging)
pytest tests/e2e/test_platform_integration_manual.py -v -s
```

### Post-Release Tests (Validation)
```bash
# Production health check
curl -f https://your-bot-url/health

# E2E validation
pytest tests/e2e/test_comprehensive_conversation_journey.py -v

# Manual platform verification
pytest tests/e2e/test_platform_integration_manual.py -v -s
```

## 📊 Test Coverage Mapping

### PRP-002: Call Endpoint & Command System
| DOD Item | Test File | Line | Status |
|----------|-----------|------|--------|
| Natural message handling | test_comprehensive_conversation_journey.py | 65-75 | ✅ |
| Command recognition | test_comprehensive_conversation_journey.py | 211-225 | ✅ |
| Educational content delivery | test_comprehensive_conversation_journey.py | 88-98 | ✅ |
| Complex problem solving | test_comprehensive_conversation_journey.py | 138-155 | ✅ |

### PRP-005: Emotional Memory System
| DOD Item | Test File | Line | Status |
|----------|-----------|------|--------|
| Memory creation & storage | test_comprehensive_conversation_journey.py | 65-75 | ✅ |
| Memory recall & retrieval | test_comprehensive_conversation_journey.py | 120-135 | ✅ |
| VAD emotional scoring | test_comprehensive_conversation_journey.py | 101-117 | ✅ |
| Mood tracking | test_comprehensive_conversation_journey.py | 101-117 | ✅ |
| Relationship progression | test_comprehensive_conversation_journey.py | 120-135 | ✅ |
| TDD RED-GREEN cycle | test_prp005_emotional_memory_tdd.py | 25-45 | ✅ |

### PRP-009: External Tools Integration
| DOD Item | Test File | Line | Status |
|----------|-----------|------|--------|
| Web search functionality | test_comprehensive_conversation_journey.py | 158-170 | ✅ |
| cURL/HTTP requests | test_comprehensive_conversation_journey.py | 158-170 | ✅ |
| Admin access control | test_comprehensive_conversation_journey.py | 173-190 | ✅ |
| Tool result formatting | test_comprehensive_conversation_journey.py | 158-170 | ✅ |

### PRP-017: Role-Based Access Control
| DOD Item | Test File | Line | Status |
|----------|-----------|------|--------|
| Admin command access | test_comprehensive_conversation_journey.py | 173-190 | ✅ |
| Non-admin denial | test_comprehensive_conversation_journey.py | 173-190 | ✅ |
| Permission validation | test_comprehensive_conversation_journey.py | 173-190 | ✅ |

## 🗂️ Deprecated Tests (To Be Removed)

The following test files are deprecated and will be removed:
- `tests/business/dod_validation/test_prp005_emotional_memory.py` → Replaced by comprehensive journey
- `tests/business/dod_validation/test_prp005_tdd_complete.py` → Replaced by unit tests
- `tests/business/user_journeys/test_*` → Consolidated into comprehensive journey
- `tests/business/dod_validation/test_prp009_*` → Integrated into journey test
- `tests/e2e/test_lesson_injection_e2e.py` → Part of comprehensive journey
- `tests/e2e/test_webapp_events.py` → Not needed

## 🛠️ Environment Setup

### Local Development Environment
```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# 3. Initialize test database
createdb dcmaidbot_test
alembic upgrade head

# 4. Start test server
python3 run_test_server.py --port 8000 --db sqlite &

# 5. Run tests
pytest tests/ -v
```

### Required Environment Variables
```bash
# Core functionality
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=122657093
DATABASE_URL=postgresql://user:password@localhost:5432/dcmaidbot
OPENAI_API_KEY=your_openai_api_key

# External tools (optional)
SERPAPI_API_KEY=your_serpapi_key
REDIS_URL=redis://localhost:6379

# LLM Judge evaluation
OPENAI_API_KEY=your_openai_api_key  # Required for LLM Judge tests
```

### Docker Environment
```bash
# Build test image
docker build -t dcmaidbot-test .

# Run tests in Docker
docker run --rm -v $(pwd):/app dcmaidbot-test pytest tests/ -v
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Server connection failed
```
❌ Could not connect to server at http://localhost:8000
```
**Solution**: Ensure test server is running:
```bash
python3 run_test_server.py --port 8000 --db sqlite &
```

#### 2. OpenAI API key not set
```
OPENAI_API_KEY not set in environment
```
**Solution**: Set the API key in your environment:
```bash
export OPENAI_API_KEY=your_key_here
```

#### 3. Database connection errors
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: Use SQLite for testing or set up PostgreSQL:
```bash
# For SQLite testing
export DATABASE_URL=sqlite:///./test.db

# For PostgreSQL
createdb dcmaidbot_test
export DATABASE_URL=postgresql://user:password@localhost:5432/dcmaidbot_test
```

#### 4. VAD/Mood features not working
**Symptoms**: `/mood` command doesn't show VAD scores
**Solution**: VAD requires:
- Database tables created via migrations
- OpenAI API key set
- Emotional analysis service enabled

#### 5. External tools not responding
**Symptoms**: Web search returns empty results
**Solution**: Check API keys:
```bash
# For SerpAPI
export SERPAPI_API_KEY=your_key

# Or use DuckDuckGo (no key needed)
export WEB_SEARCH_ENGINE=duckduckgo
```

### Debug Mode
Enable debug logging:
```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

## 📋 Legacy Testing Information

The original E2E testing approach has been preserved in the technical backup. For reference on how testing was previously structured, see `tests/technical_tests_backup/README.md`.

## 🎯 Business Test Examples

### User Journey Example
```python
async def test_user_can_start_conversation():
    """Business Requirement: User can start conversation with /start"""
    # Test actual user experience, not internal implementation
    user_sends_message("/start")
    bot_responds_with_welcome_message()
    assert "welcome" in bot_response
```

### DoD Validation Example
```python
async def test_prp009_external_tools_dod():
    """Validate PRP-009 DoD: External tools work for admin users"""
    admin_user_uses_web_search()
    assert search_results_returned()
    non_admin_tries_tools()
    assert access_denied()
```

## 🔍 Test Criteria

Business tests must meet ALL of these criteria:
1. **User-Focused**: Tests user experience, not technical implementation
2. **Journey-Based**: Validates complete user workflows
3. **Outcome-Driven**: Confirms business requirements are met
4. **DoD-Aligned**: Validates Definition of Done criteria
5. **Production-Relevant**: Tests what matters in production

Tests failing any criterion should be moved to technical backup.

## 📊 Best Practices

### Writing Good Tests
1. **Test Behavior, Not Implementation**
   ```python
   # Good: Tests user-visible behavior
   async def test_user_can_retrieve_memories():
       response = await call_bot("/memories", user_id, is_admin=True)
       assert "memories found" in response["response"]

   # Bad: Tests internal implementation
   async def test_memory_service_called():
       # Don't test internal service calls
       pass
   ```

2. **Use Realistic Data**
   ```python
   # Good: Realistic user message
   "Hi! I'm Sarah, a data scientist from San Francisco"

   # Bad: Unhelpful test data
   "test message 123"
   ```

3. **Test Error Scenarios**
   ```python
   # Test both success and failure cases
   async def test_admin_access_control():
       # Admin should succeed
       admin_response = await call_bot("/memories", admin_id, is_admin=True)
       assert "found" in admin_response["response"]

       # Non-admin should be denied
       user_response = await call_bot("/memories", user_id, is_admin=False)
       assert "access denied" in user_response["response"]
   ```

### Test Maintenance
- Review and update tests when features change
- Keep test data and fixtures up to date
- Remove duplicate or redundant tests
- Add new tests for new features immediately

### CI/CD Integration
- Run all tests in CI/CD pipeline
- Use pytest markers for different test categories
- Fail fast on critical test failures
- Generate test reports for review

## 🚀 Quick Start Checklist

For new developers joining the project:

1. **[ ]** Install dependencies
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

2. **[ ]** Set up environment
   ```bash
   cp .env.example .env
   # Edit .env with required API keys
   ```

3. **[ ]** Start test server
   ```bash
   python3 run_test_server.py --port 8000 &
   ```

4. **[ ]** Run unit tests (fast)
   ```bash
   pytest tests/business/dod_validation/ -v --maxfail=1
   ```

5. **[ ]** Run E2E tests (comprehensive)
   ```bash
   pytest tests/e2e/test_comprehensive_conversation_journey.py -v -s
   ```

6. **[ ]** Check code quality
   ```bash
   ruff check . && ruff format .
   mypy src/
   ```

7. **[ ]** Run LLM Judge evaluation (requires OpenAI key)
   ```bash
   pytest tests/e2e/test_llm_judge_evaluation.py -v
   ```

## 📞 Getting Help

- **Documentation**: Check this README and PRP files for detailed requirements
- **Debug Mode**: Use `-s -v --log-cli-level=DEBUG` with pytest
- **Team Communication**: Use `/nudge` endpoint for async questions
- **Test Issues**: Check troubleshooting section above

---

**Remember**: Tests are our safety net. Keep them clean, focused, and valuable! 🎯
