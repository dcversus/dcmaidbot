# Business-Focused Test Suite

This directory contains business-critical tests that validate user journeys, business outcomes, and Definition of Done (DoD) criteria. All technical implementation tests have been moved to backup directories.

## 🎯 Business Test Philosophy

**Only business-critical tests that validate:**
- ✅ User journeys and experiences
- ✅ Business outcomes and requirements
- ✅ Definition of Done (DoD) criteria
- ✅ Production readiness

**No technical implementation tests:**
- ❌ Unit tests (moved to backup)
- ❌ API contract tests (moved to backup)
- ❌ Performance benchmarks (moved to backup)
- ❌ Component testing (moved to backup)

## 📁 Test Structure

### 🧭 User Journeys (`business/user_journeys/`)
Tests that validate actual user experiences and workflows:

- **`e2e_user_stories.py`** - Complete user story validation (start, help, status, jokes, etc.)
- **`test_memory_lifecycle.py`** - User journey: memory creation, search, and management
- **`test_message_flow.py`** - User journey: message storage and retrieval workflow
- **`test_bot_integration_with_llm_judge.py`** - User journey: bot responses with LLM validation

### ✅ DoD Validation (`business/dod_validation/`)
Tests that validate PRP Definition of Done criteria:

- **`test_prp009_external_tools_integration.py`** - PRP-009 External Tools DoD validation
- **`test_prp009_llm_judge_evaluation.py`** - LLM Judge evaluation for PRP-009
- **`test_prp007_comprehensive_llm_judge_e2e.py`** - PRP-007 LLM Integration DoD validation
- **`test_prp017_rbac_with_judge.py`** - PRP-017 RBAC DoD validation

### 🚀 Production Validation (`business/production_validation/`)
Tests that validate production readiness:

- **`e2e_production.py`** - Production environment validation

### 🧠 LLM Judge Framework (`llm_judge.py`, `llm_tile_judge.py`)
Core LLM-as-judge evaluation framework for automated business requirement validation.

## 🏃‍♂️ Running Business Tests

### User Journey Tests
```bash
# Run all user journey tests
python -m pytest tests/business/user_journeys/ -v

# Run specific user story validation
python tests/business/user_journeys/e2e_user_stories.py
```

### DoD Validation Tests
```bash
# Run all DoD validation tests
python -m pytest tests/business/dod_validation/ -v

# Run PRP-009 validation
python -m pytest tests/business/dod_validation/test_prp009_* -v
```

### Production Validation
```bash
# Run production validation
python tests/business/production_validation/e2e_production.py
```

### All Business Tests
```bash
# Run complete business test suite
python -m pytest tests/business/ -v

# Include LLM Judge evaluations
python -m pytest tests/business/ tests/llm_judge.py -v
```

## 📊 Business Outcomes Validated

### User Experience
- ✅ Users can interact with bot naturally
- ✅ Admin tools work as expected
- ✅ Memory systems store and retrieve user data
- ✅ LLM responses are appropriate and helpful

### Business Requirements
- ✅ Access control works (admin vs regular users)
- ✅ External tools integrate properly
- ✅ Rate limiting prevents abuse
- ✅ Data persistence and reliability

### Production Readiness
- ✅ Bot responds in production environment
- ✅ All critical features function correctly
- ✅ Error handling works gracefully
- ✅ Performance meets business requirements

## 🗄️ Backup Technical Tests

All technical implementation tests have been preserved in:
- `tests/technical_tests_backup/` - Technical E2E tests
- `tests/unit_backup_YYYYMMDD_HHMMSS/` - Unit tests

These can be restored if needed for development debugging, but are not part of the business validation suite.

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
