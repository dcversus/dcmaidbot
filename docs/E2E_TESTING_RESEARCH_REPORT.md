# Modern E2E Testing Strategies with DDD Principles and Multi-Environment Execution

**Research Date**: November 2, 2025
**Researcher**: Robo-System-Analyst
**Target Project**: DCMaidBot - Multi-Environment Bot Architecture

## Executive Summary

This comprehensive research report analyzes modern E2E testing strategies for web applications with focus on Domain-Driven Design (DDD) principles, multi-environment execution, journey-based testing approaches, and pre-commit hook integration. The research is tailored for DCMaidBot's existing sophisticated testing infrastructure and provides practical implementation guidance for creating business-valued E2E tests.

## 1. Current State Analysis

### 1.1 Existing Testing Infrastructure

DCMaidBot demonstrates an advanced testing setup with:

**Multi-Database Support:**
- SQLite for pre-commit E2E tests (speed and isolation)
- PostgreSQL for integration and production-like testing
- Async SQLAlchemy with proper session management

**Sophisticated Test Organization:**
- Unit tests: `/tests/unit/` - Fast, isolated component testing
- E2E tests: `/tests/e2e/` - Full workflow testing with LLM judge
- Integration markers: `@pytest.mark.integration`, `@pytest.mark.llm_judge`

**Advanced Features:**
- LLM-as-Judge system for intelligent test evaluation
- Cross-environment test orchestration
- Containerized service mocking
- Performance baseline management

### 1.2 Current Challenges Identified

1. **Limited Web Application Testing**: Focus is primarily on bot functionality
2. **No Journey-Based Testing**: Missing user journey scenarios
3. **Limited DDD Implementation**: Tests focus on implementation details rather than domain behavior
4. **No Web UI Testing**: Missing browser automation for potential web interface

## 2. Top E2E Testing Frameworks with Multi-Environment Support

### 2.1 Playwright (Recommended for DCMaidBot)

**Strengths:**
- **Modern Architecture**: Built for modern web applications with async support
- **Multi-Language Support**: Excellent Python integration via `playwright-pytest`
- **Cross-Platform**: Windows, Linux, macOS with consistent behavior
- **Multi-Browser**: Chromium, WebKit, Firefox with identical APIs
- **Advanced Features**:
  - Auto-wait functionality eliminates flaky tests
  - Web-first assertions for reliability
  - Browser context isolation for parallel testing
  - Network interception and mocking
  - Mobile device emulation

**Multi-Environment Configuration:**
```python
# playwright.config.py
import os
from playwright.sync_api import Page, expect

def pytest_addoption(parser):
    parser.addoption("--environment", action="store", default="local")
    parser.addoption("--headed", action="store_true", default=False)

@pytest.fixture(scope="session")
def environment(request):
    return request.config.getoption("--environment")

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, environment):
    if environment == "ci":
        return {**browser_type_launch_args, "headless": True}
    return browser_type_launch_args
```

**Integration with DCMaidBot:**
```python
# tests/e2e/test_bot_web_interface.py
import pytest
from playwright.sync_api import Page, expect
from tests.conftest import async_session

@pytest.mark.e2e
async def test_bot_command_via_web_interface(page: Page, async_session):
    """Test bot functionality through web interface - DDD approach"""

    # Arrange: Set up test data through domain service
    await seed_test_user(async_session, {
        "id": 123456789,
        "is_admin": True,
        "username": "test_admin"
    })

    # Act: User performs business action
    await page.goto("/bot")
    await page.fill('[data-testid="command-input"]', "/search test query")
    await page.click('[data-testid="send-button"]')

    # Assert: Verify business outcome (not implementation details)
    await expect(page.locator('[data-testid="search-results"]')).to_be_visible()
    results = await page.locator('[data-testid="search-result-item"]').count()
    assert results > 0, "Search should return results"

    # Verify domain state change
    command_log = await get_command_history(async_session, user_id=123456789)
    assert any("search" in log.command for log in command_log)
```

### 2.2 Cypress (Alternative Consideration)

**Strengths:**
- **Developer Experience**: Excellent debugging and time-travel debugging
- **Real Browser**: Runs in real browsers, not simulations
- **AI-Powered**: Self-healing tests with visual debugging
- **Journey Testing**: Natural language prompts for user journeys

**Limitations for DCMaidBot:**
- JavaScript-centric (less Python-friendly)
- Limited async/await support compared to Playwright
- Smaller ecosystem for Python integration

### 2.3 Selenium WebDriver (Legacy Option)

**Current State**: Mature but declining in popularity
**Recommendation**: Not recommended for new DCMaidBot E2E tests
**Reason**: Playwright provides superior reliability, performance, and developer experience

## 3. DDD Testing Implementation Patterns

### 3.1 Core DDD Testing Principles

**Focus on Domain Behavior, Not Implementation:**
```python
# ❌ Implementation-focused test (Anti-pattern)
def test_web_search_api():
    response = requests.post("/api/tools/execute", json={
        "tool_name": "web_search",
        "arguments": {"query": "test"}
    })
    assert response.status_code == 200
    assert "results" in response.json()

# ✅ Domain-behavior test (DDD Pattern)
def test_user_can_search_web_information():
    """User searches for information and receives relevant results"""

    # User performs domain action
    search_result = bot.handle_message(
        user_id=test_admin.id,
        message="/search python testing"
    )

    # Verify business outcome
    assert "search results" in search_result.lower()
    assert any("python" in result["title"] for result in extract_search_results(search_result))
    assert len(extract_search_results(search_result)) > 0
```

### 3.2 Ubiquitous Language in Tests

**Test Names Reflect Business Language:**
```python
class TestBotSearchCapabilities:
    """Test suite for bot's information retrieval capabilities"""

    def test_admin_user_retrieves_information_from_web(self):
        """Admin users can access web search capabilities"""

    def test_friend_user_retrieves_information_with_magic_words(self):
        """Friend users can search using proper authentication"""

    def test_regular_user_cannot_access_web_search(self):
        """Regular users are restricted from web search"""

    def test_search_results_are_cached_for_performance(self):
        """Search performance is optimized through caching"""
```

### 3.3 Domain-Driven Test Organization

**Organize by Bounded Contexts:**
```
tests/e2e/
├── authentication_context/
│   ├── test_user_roles_and_permissions.py
│   ├── test_friend_system_authentication.py
│   └── test_admin_privileges.py
├── information_retrieval_context/
│   ├── test_web_search_capabilities.py
│   ├── test_search_result_formatting.py
│   └── test_search_caching_behavior.py
├── communication_context/
│   ├── test_message_processing.py
│   ├── test_response_generation.py
│   └── test_nudge_system.py
└── journey_tests/
    ├── test_admin_workflow.py
    ├── test_friend_user_workflow.py
    └── test_new_user_onboarding.py
```

### 3.4 Test Data Builders for Domain Objects

**Domain Object Builders:**
```python
# tests/builders/user_builder.py
from dataclasses import dataclass
from typing import Optional
from models.user import User

@dataclass
class UserBuilder:
    """Builder pattern for creating domain test users"""

    id: int = 123456789
    username: str = "test_user"
    is_admin: bool = False
    is_friend: bool = False
    permissions: list = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

    def as_admin(self) -> 'UserBuilder':
        return UserBuilder(
            id=self.id,
            username=self.username,
            is_admin=True,
            is_friend=self.is_friend,
            permissions=self.permissions + ["admin", "web_search", "curl_request"]
        )

    def as_friend(self) -> 'UserBuilder':
        return UserBuilder(
            id=self.id,
            username=self.username,
            is_admin=self.is_admin,
            is_friend=True,
            permissions=self.permissions + ["friend"]
        )

    def with_permissions(self, permissions: list) -> 'UserBuilder':
        return UserBuilder(
            id=self.id,
            username=self.username,
            is_admin=self.is_admin,
            is_friend=self.is_friend,
            permissions=permissions
        )

    async def build(self, async_session) -> User:
        """Build and persist user to database"""
        user = User(
            id=self.id,
            username=self.username,
            is_admin=self.is_admin,
            is_friend=self.is_friend,
            permissions=self.permissions
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user
```

## 4. Journey-Based Testing Design Principles

### 4.1 User Journey Mapping

**Define Critical User Journeys:**
```python
# tests/e2e/journey_tests/test_admin_complete_workflow.py
class TestAdminUserJourney:
    """Complete admin user journey from login to task completion"""

    @pytest.mark.journey
    @pytest.mark.asyncio
    async def test_admin_information_gathering_workflow(self):
        """Admin gathers information using multiple tools in sequence"""

        # Step 1: Admin authenticates and checks status
        status = await bot.handle_message(
            user_id=self.admin_user.id,
            message="/status"
        )
        assert "admin" in status.lower()

        # Step 2: Admin searches for information
        search_result = await bot.handle_message(
            user_id=self.admin_user.id,
            message="/search latest python frameworks"
        )
        assert "search results" in search_result.lower()

        # Step 3: Admin makes API call to get detailed information
        api_result = await bot.handle_message(
            user_id=self.admin_user.id,
            message="/curl https://api.github.com/repos/python/cpython"
        )
        assert "response" in api_result.lower()

        # Step 4: Admin stores important information in memory
        memory_result = await bot.handle_message(
            user_id=self.admin_user.id,
            message="/remember Python 3.12 was released in October 2023"
        )
        assert "remembered" in memory_result.lower()

        # Step 5: Admin retrieves stored information
        recall_result = await bot.handle_message(
            user_id=self.admin_user.id,
            message="/recall python release date"
        )
        assert "2023" in recall_result

        # Verify complete workflow success
        command_history = await get_command_history(self.admin_user.id)
        assert len(command_history) == 5  # All commands executed
        assert all(cmd.success for cmd in command_history)
```

### 4.2 Journey Test Framework

**Journey Test Base Class:**
```python
# tests/e2e/journey_tests/base_journey.py
import asyncio
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from tests.builders.user_builder import UserBuilder

class JourneyTest(ABC):
    """Base class for journey-based E2E tests"""

    @abstractmethod
    def get_journey_steps(self) -> List[Dict[str, Any]]:
        """Define journey steps with expectations"""
        pass

    @abstractmethod
    def get_user_context(self) -> UserBuilder:
        """Define user context for the journey"""
        pass

    async def execute_journey(self, bot_service, async_session) -> Dict[str, Any]:
        """Execute complete user journey"""

        # Set up user context
        user = await self.get_user_context().build(async_session)

        # Execute journey steps
        journey_results = []
        for step in self.get_journey_steps():
            result = await bot_service.handle_message(
                user_id=user.id,
                message=step["message"],
                chat_id=step.get("chat_id", 123456)
            )

            # Verify step expectations
            step_result = self.verify_step_expectations(result, step)
            journey_results.append({
                "step": step["name"],
                "message": step["message"],
                "result": result,
                "expectations_met": step_result["success"],
                "details": step_result["details"]
            })

        # Calculate journey success
        success_rate = sum(1 for r in journey_results if r["expectations_met"]) / len(journey_results)

        return {
            "journey_name": self.__class__.__name__,
            "user_id": user.id,
            "total_steps": len(journey_results),
            "successful_steps": sum(1 for r in journey_results if r["expectations_met"]),
            "success_rate": success_rate,
            "step_results": journey_results,
            "journey_success": success_rate >= 0.9  # 90% success rate required
        }

    def verify_step_expectations(self, result: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Verify individual step expectations"""
        expectations = step.get("expectations", [])
        details = []

        for expectation in expectations:
            if expectation["type"] == "contains_text":
                if expectation["text"] in result.lower():
                    details.append(f"✅ Contains expected text: {expectation['text']}")
                else:
                    details.append(f"❌ Missing expected text: {expectation['text']}")

            elif expectation["type"] == "not_contains_text":
                if expectation["text"] not in result.lower():
                    details.append(f"✅ Correctly excludes text: {expectation['text']}")
                else:
                    details.append(f"❌ Incorrectly contains text: {expectation['text']}")

            elif expectation["type"] == "regex_match":
                import re
                if re.search(expectation["pattern"], result):
                    details.append(f"✅ Matches expected pattern: {expectation['pattern']}")
                else:
                    details.append(f"❌ Does not match pattern: {expectation['pattern']}")

        success = all("✅" in detail for detail in details)
        return {"success": success, "details": details}
```

### 4.3 Multi-User Journey Testing

**Concurrent User Journeys:**
```python
# tests/e2e/journey_tests/test_concurrent_user_workflows.py
class TestConcurrentUserJourneys:
    """Test multiple users performing journeys simultaneously"""

    @pytest.mark.journey
    @pytest.mark.asyncio
    async def test_admin_and_friend_concurrent_workflows(self):
        """Admin and friend users work simultaneously without interference"""

        # Define concurrent journeys
        admin_journey = AdminInformationGatheringJourney()
        friend_journey = FriendCasualSearchJourney()

        # Execute journeys concurrently
        tasks = [
            admin_journey.execute_journey(self.bot_service, self.async_session),
            friend_journey.execute_journey(self.bot_service, self.async_session)
        ]

        results = await asyncio.gather(*tasks)

        # Verify both journeys succeed independently
        for result in results:
            assert result["journey_success"], f"Journey failed: {result['journey_name']}"

        # Verify no data interference
        admin_commands = await get_command_history(self.admin_user.id)
        friend_commands = await get_command_history(self.friend_user.id)

        assert admin_commands[-1].user_id != friend_commands[-1].user_id
        assert all(cmd.user_id == self.admin_user.id for cmd in admin_commands)
        assert all(cmd.user_id == self.friend_user.id for cmd in friend_commands)
```

## 5. Pre-Commit Hook Integration Strategies

### 5.1 E2E Test Pre-Commit Configuration

**Optimized Pre-Commit Setup:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  # E2E Testing Hook - SQLite for speed
  - repo: local
    hooks:
      - id: e2e-tests
        name: E2E Tests
        entry: bash -c 'DATABASE_URL="sqlite+aiosqlite:///./test_e2e_$(date +%s).db" pytest tests/e2e/test_critical_workflows.py -v --test-mode=e2e'
        language: system
        pass_filenames: false
        always_run: false
        files: '^tests/e2e/.*\.py$|^services/.*\.py$|^handlers/.*\.py$'

  # Journey Testing Hook - Critical user journeys only
  - repo: local
    hooks:
      - id: journey-tests
        name: Journey Tests
        entry: bash -c 'DATABASE_URL="sqlite+aiosqlite:///./test_journey_$(date +%s).db" pytest tests/e2e/journey_tests/test_critical_journeys.py -v --test-mode=journey'
        language: system
        pass_filenames: false
        always_run: false
        files: '^tests/e2e/journey_tests/.*\.py$|^services/.*\.py$'
```

### 5.2 Smart E2E Test Selection

**Change-Based Test Selection:**
```python
# scripts/smart_e2e_runner.py
import os
import subprocess
import json
from pathlib import Path
from typing import List, Set

class SmartE2ERunner:
    """Selects and runs only relevant E2E tests based on changes"""

    def __init__(self):
        self.change_mapping = {
            "services/tool_service.py": ["test_prp009_external_tools_integration.py"],
            "services/auth_service.py": ["test_user_permissions.py", "test_friend_system.py"],
            "services/memory_service.py": ["test_memory_lifecycle.py", "test_memory_advanced_features.py"],
            "handlers/": ["test_message_flow.py", "test_bot_integration_with_llm_judge.py"],
            "web/": ["test_web_interface.py"],
            "tools/": ["test_prp009_external_tools_integration.py", "test_agentic_tools_with_judge.py"]
        }

    def get_changed_files(self) -> List[str]:
        """Get list of changed files in current commit"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def map_changes_to_tests(self, changed_files: List[str]) -> Set[str]:
        """Map changed files to relevant E2E tests"""
        relevant_tests = set()

        for file_path in changed_files:
            for pattern, tests in self.change_mapping.items():
                if file_path.startswith(pattern):
                    relevant_tests.update(tests)

        # Always run critical journey tests if any E2E test is relevant
        if relevant_tests:
            relevant_tests.add("test_critical_journeys.py")

        return relevant_tests

    def run_selected_tests(self, test_files: Set[str]) -> int:
        """Run selected E2E tests with SQLite database"""
        if not test_files:
            print("No relevant E2E tests found for changes")
            return 0

        # Use SQLite for fast pre-commit testing
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///./test_precommit_{int(time.time())}.db"
        env["DISABLE_TG"] = "true"  # Disable Telegram for pre-commit

        test_args = ["pytest", "-v", "--test-mode=e2e"] + list(test_files)

        result = subprocess.run(test_args, env=env)
        return result.returncode

if __name__ == "__main__":
    runner = SmartE2ERunner()
    changed_files = runner.get_changed_files()
    relevant_tests = runner.map_changes_to_tests(changed_files)

    if relevant_tests:
        print(f"Running E2E tests: {', '.join(relevant_tests)}")
        exit_code = runner.run_selected_tests(relevant_tests)
        exit(exit_code)
    else:
        print("No E2E tests needed for current changes")
        exit(0)
```

### 5.3 Pre-Commit Hook Performance Optimization

**Parallel E2E Test Execution:**
```yaml
# .pre-commit-config.yaml (optimized version)
  - repo: local
    hooks:
      - id: fast-e2e-tests
        name: Fast E2E Tests
        entry: bash -c 'python scripts/smart_e2e_runner.py --parallel'
        language: system
        pass_filenames: false
        always_run: false
        files: '^tests/e2e/.*\.py$|^services/.*\.py$|^handlers/.*\.py$'
        # Timeout after 5 minutes to prevent hanging
        require_serial: false
```

**Test Parallelization Script:**
```python
# scripts/parallel_e2e_runner.py
import asyncio
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List

async def run_e2e_tests_parallel(test_files: List[str], max_workers: int = 4):
    """Run E2E tests in parallel using multiple processes"""

    def run_single_test(test_file: str) -> tuple:
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///./test_parallel_{test_file.replace('/', '_')}_{int(time.time())}.db"
        env["DISABLE_TG"] = "true"

        result = subprocess.run(
            ["pytest", "-v", "--test-mode=e2e", test_file],
            env=env,
            capture_output=True,
            text=True
        )
        return test_file, result.returncode, result.stdout, result.stderr

    # Run tests in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(run_single_test, test_files))

    # Report results
    failed_tests = []
    for test_file, returncode, stdout, stderr in results:
        if returncode != 0:
            print(f"❌ {test_file} failed")
            print(stderr)
            failed_tests.append(test_file)
        else:
            print(f"✅ {test_file} passed")

    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test(s) failed: {', '.join(failed_tests)}")
        return 1
    else:
        print(f"\n✅ All {len(test_files)} E2E tests passed")
        return 0
```

## 6. Environment Portability Solutions

### 6.1 Environment Configuration Management

**Centralized Environment Configuration:**
```python
# config/environments.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

@dataclass
class EnvironmentConfig:
    """Configuration for different testing environments"""

    name: str
    database_url: str
    external_services: Dict[str, Any]
    test_timeouts: Dict[str, int]
    parallel_workers: int
    mock_services: bool
    llm_judge_enabled: bool

    @classmethod
    def from_environment(cls, env_name: Optional[str] = None) -> 'EnvironmentConfig':
        """Create configuration from environment name"""

        if env_name is None:
            env_name = os.getenv("TEST_ENVIRONMENT", "local")

        configs = {
            "local": cls(
                name="local",
                database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_local.db"),
                external_services={"mock": True, "telegram": False, "openai": False},
                test_timeouts={"default": 30, "slow": 120},
                parallel_workers=2,
                mock_services=True,
                llm_judge_enabled=False
            ),

            "ci": cls(
                name="ci",
                database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://test:test@postgres-test:5432/test"),
                external_services={"mock": True, "telegram": False, "openai": False},
                test_timeouts={"default": 60, "slow": 180},
                parallel_workers=4,
                mock_services=True,
                llm_judge_enabled=True
            ),

            "staging": cls(
                name="staging",
                database_url=os.getenv("DATABASE_URL"),
                external_services={"mock": False, "telegram": True, "openai": True},
                test_timeouts={"default": 120, "slow": 300},
                parallel_workers=2,
                mock_services=False,
                llm_judge_enabled=True
            ),

            "production": cls(
                name="production",
                database_url=os.getenv("DATABASE_URL"),
                external_services={"mock": False, "telegram": True, "openai": True},
                test_timeouts={"default": 180, "slow": 600},
                parallel_workers=1,  # Conservative for production
                mock_services=False,
                llm_judge_enabled=True
            )
        }

        return configs.get(env_name, configs["local"])

# tests/conftest.py (enhanced)
@pytest.fixture(scope="session")
def environment_config():
    """Provide environment configuration for tests"""
    return EnvironmentConfig.from_environment()

@pytest.fixture(scope="session")
def test_database_url(environment_config):
    """Get database URL for current environment"""
    return environment_config.database_url

@pytest.fixture(scope="session")
def test_timeouts(environment_config):
    """Get test timeouts for current environment"""
    return environment_config.test_timeouts

@pytest.fixture
def mock_services(environment_config):
    """Determine if services should be mocked"""
    return environment_config.mock_services
```

### 6.2 Service Abstraction Layer

**Environment-Agnostic Service Interface:**
```python
# tests/factories/service_factory.py
from abc import ABC, abstractmethod
from typing import Any, Dict
import asyncio

class ExternalService(ABC):
    """Abstract base class for external services"""

    @abstractmethod
    async def initialize(self):
        """Initialize service for testing"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup service after testing"""
        pass

    @abstractmethod
    async def send_request(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Send request to service"""
        pass

class MockTelegramService(ExternalService):
    """Mock Telegram service for testing"""

    def __init__(self):
        self.messages = []
        self.responses = {}

    async def initialize(self):
        self.messages.clear()
        self.responses.clear()

    async def cleanup(self):
        self.messages.clear()
        self.responses.clear()

    async def send_message(self, chat_id: int, text: str) -> Dict[str, Any]:
        message = {"chat_id": chat_id, "text": text, "timestamp": asyncio.get_event_loop().time()}
        self.messages.append(message)
        return {"message_id": len(self.messages), "status": "ok"}

    async def get_updates(self) -> list:
        return []

class RealTelegramService(ExternalService):
    """Real Telegram service for staging/production"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.client = None

    async def initialize(self):
        # Initialize real Telegram client
        pass

    async def cleanup(self):
        # Cleanup real Telegram client
        pass

    async def send_message(self, chat_id: int, text: str) -> Dict[str, Any]:
        # Send real Telegram message
        pass

class ServiceFactory:
    """Factory for creating environment-appropriate services"""

    @staticmethod
    def create_telegram_service(environment_config: EnvironmentConfig) -> ExternalService:
        """Create Telegram service based on environment"""

        if environment_config.mock_services:
            return MockTelegramService()
        else:
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                raise ValueError("BOT_TOKEN required for real Telegram service")
            return RealTelegramService(bot_token)

    @staticmethod
    def create_openai_service(environment_config: EnvironmentConfig) -> ExternalService:
        """Create OpenAI service based on environment"""
        # Similar implementation for OpenAI service
        pass

# tests/conftest.py (service fixtures)
@pytest.fixture(scope="session")
async def telegram_service(environment_config):
    """Provide Telegram service based on environment"""
    service = ServiceFactory.create_telegram_service(environment_config)
    await service.initialize()
    yield service
    await service.cleanup()
```

### 6.3 Cross-Environment Test Validation

**Environment-Specific Test Behavior:**
```python
# tests/e2e/test_cross_environment_compatibility.py
import pytest
from config.environments import EnvironmentConfig

class TestCrossEnvironmentCompatibility:
    """Verify tests work consistently across environments"""

    @pytest.mark.asyncio
    async def test_basic_functionality_all_environments(self, bot_service, environment_config):
        """Test core functionality works in all environments"""

        # This test should pass regardless of environment
        result = await bot_service.handle_message(
            user_id=123456789,
            message="/help"
        )

        # Verify response structure (not content, which may vary)
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify bot didn't crash
        assert "error" not in result.lower() or "not found" in result.lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("environment", ["local", "ci", "staging"])
    async def test_environment_specific_features(self, bot_service, environment_config):
        """Test features specific to environment capabilities"""

        if environment_config.mock_services:
            # In mocked environments, test mocked behavior
            result = await bot_service.handle_message(
                user_id=123456789,
                message="/search test query"
            )
            assert "mock" in result.lower() or "search" in result.lower()

        else:
            # In real environments, test real behavior (but safely)
            if environment_config.name in ["staging", "production"]:
                # Use read-only or safe operations
                result = await bot_service.handle_message(
                    user_id=123456789,
                    message="/status"
                )
                assert "status" in result.lower()

class TestDataConsistency:
    """Verify data consistency across environments"""

    @pytest.mark.asyncio
    async def test_user_persistence(self, async_session, environment_config):
        """Test user data persistence works in all environments"""

        # Create test user
        user = User(id=999999999, username="cross_env_test", is_admin=False)
        async_session.add(user)
        await async_session.commit()

        # Retrieve user
        retrieved = await async_session.get(User, 999999999)
        assert retrieved is not None
        assert retrieved.username == "cross_env_test"

        # Cleanup
        await async_session.delete(retrieved)
        await async_session.commit()
```

## 7. Code Examples and Configuration Patterns

### 7.1 Complete E2E Test Example with DDD Principles

```python
# tests/e2e/test_complete_bot_workflow.py
import pytest
from tests.builders.user_builder import UserBuilder
from tests.factories.service_factory import ServiceFactory
from tests.e2e.journey_tests.base_journey import JourneyTest

class TestBotInformationManagementWorkflow(JourneyTest):
    """Complete DDD-based E2E test for bot information management"""

    def get_user_context(self):
        """Admin user with full permissions"""
        return UserBuilder(id=123456789, username="admin_user").as_admin()

    def get_journey_steps(self):
        """Define complete information management journey"""
        return [
            {
                "name": "User authenticates and checks status",
                "message": "/status",
                "expectations": [
                    {"type": "contains_text", "text": "admin"},
                    {"type": "contains_text", "text": "status"}
                ]
            },
            {
                "name": "User searches for technical information",
                "message": "/search pytest async testing",
                "expectations": [
                    {"type": "contains_text", "text": "search"},
                    {"type": "contains_text", "text": "results"}
                ]
            },
            {
                "name": "User retrieves specific API data",
                "message": "/curl https://api.github.com/repos/pytest-dev/pytest",
                "expectations": [
                    {"type": "contains_text", "text": "response"},
                    {"type": "contains_text", "text": "status"}
                ]
            },
            {
                "name": "User stores important findings",
                "message": "/remember pytest async fixtures are powerful for testing",
                "expectations": [
                    {"type": "contains_text", "text": "remembered"}
                ]
            },
            {
                "name": "User retrieves stored information",
                "message": "/recall pytest fixtures",
                "expectations": [
                    {"type": "contains_text", "text": "async"},
                    {"type": "contains_text", "text": "fixtures"}
                ]
            }
        ]

    @pytest.mark.e2e
    @pytest.mark.journey
    @pytest.mark.llm_judge
    async def test_complete_information_management_workflow(self, bot_service, async_session):
        """Execute complete information management journey"""

        # Execute journey
        journey_result = await self.execute_journey(bot_service, async_session)

        # Verify journey success
        assert journey_result["journey_success"], f"Journey failed: {journey_result}"

        # Verify business outcomes (domain-specific assertions)
        command_history = await get_command_history(123456789)

        # Verify all expected commands were executed
        expected_commands = ["status", "search", "curl", "remember", "recall"]
        actual_commands = [cmd.command for cmd in command_history]

        for expected_cmd in expected_commands:
            assert any(expected_cmd in actual_cmd for actual_cmd in actual_commands), \
                f"Expected command '{expected_cmd}' not found in history"

        # Verify all commands succeeded
        failed_commands = [cmd for cmd in command_history if not cmd.success]
        assert len(failed_commands) == 0, f"Failed commands: {failed_commands}"

        # Verify information was stored and retrieved correctly
        memories = await get_user_memories(123456789)
        assert len(memories) > 0, "No memories found"
        assert any("pytest" in memory.content and "async" in memory.content
                  for memory in memories), "Expected memory content not found"
```

### 7.2 Playwright Integration Example

```python
# tests/e2e/test_web_interface_playwright.py
import pytest
from playwright.sync_api import Page, expect
from tests.builders.user_builder import UserBuilder

class TestBotWebInterface:
    """E2E tests for bot web interface using Playwright"""

    @pytest.fixture
    async def authenticated_page(self, page: Page):
        """Provide authenticated page for testing"""

        # Navigate to login page
        await page.goto("/login")

        # Login as test user
        await page.fill('[data-testid="username"]', "test_admin")
        await page.fill('[data-testid="password"]', "test_password")
        await page.click('[data-testid="login-button"]')

        # Wait for successful login
        await expect(page.locator('[data-testid="dashboard"]')).to_be_visible()

        return page

    @pytest.mark.e2e
    async def test_search_functionality_via_web_interface(self, authenticated_page: Page):
        """Test search functionality through web interface"""

        # Navigate to search interface
        await authenticated_page.click('[data-testid="search-nav"]')
        await expect(authenticated_page.locator('[data-testid="search-page"]')).to_be_visible()

        # Perform search
        await authenticated_page.fill('[data-testid="search-input"]', "python testing frameworks")
        await authenticated_page.click('[data-testid="search-button"]')

        # Verify search results
        await expect(authenticated_page.locator('[data-testid="search-results"]')).to_be_visible()

        # Wait for results to load
        await authenticated_page.wait_for_selector('[data-testid="search-result-item"]')

        # Verify result structure
        results_count = await authenticated_page.locator('[data-testid="search-result-item"]').count()
        assert results_count > 0, "Search should return results"

        # Verify result content
        first_result = authenticated_page.locator('[data-testid="search-result-item"]').first
        await expect(first_result.locator('[data-testid="result-title"]')).to_be_visible()
        await expect(first_result.locator('[data-testid="result-snippet"]')).to_be_visible()
        await expect(first_result.locator('[data-testid="result-url"]')).to_be_visible()

    @pytest.mark.e2e
    async def test_memory_management_via_web_interface(self, authenticated_page: Page):
        """Test memory management through web interface"""

        # Navigate to memory interface
        await authenticated_page.click('[data-testid="memory-nav"]')
        await expect(authenticated_page.locator('[data-testid="memory-page"]')).to_be_visible()

        # Add new memory
        test_memory = "Playwright provides excellent E2E testing capabilities"
        await authenticated_page.fill('[data-testid="memory-input"]', test_memory)
        await authenticated_page.click('[data-testid="save-memory-button"]')

        # Verify memory was saved
        await expect(authenticated_page.locator('[data-testid="success-message"]')).to_be_visible()

        # Navigate to memory list
        await authenticated_page.click('[data-testid="memory-list-nav"]')
        await expect(authenticated_page.locator('[data-testid="memory-list"]')).to_be_visible()

        # Verify memory appears in list
        memory_items = authenticated_page.locator('[data-testid="memory-item"]')
        await expect(memory_items).to_contain_text(test_memory)

        # Test memory search
        await authenticated_page.fill('[data-testid="memory-search"]', "Playwright")
        await authenticated_page.click('[data-testid="search-memory-button"]')

        # Verify filtered results
        filtered_items = authenticated_page.locator('[data-testid="memory-item"]')
        await expect(filtered_items).to_have_count(1)
        await expect(filtered_items).to_contain_text(test_memory)
```

### 7.3 LLM Judge Integration with DDD Tests

```python
# tests/e2e/test_llm_judge_evaluation.py
import pytest
from tests.llm_judge import LLMJudge, TestSuiteEvaluator
from services.llm_service import LLMService

class TestLLMJudgeDDDIntegration:
    """LLM Judge evaluation with DDD-based tests"""

    @pytest.fixture
    async def llm_judge(self):
        """Initialize LLM judge for test evaluation"""
        llm_service = LLMService()
        return LLMJudge(llm_service)

    @pytest.fixture
    async def test_suite_evaluator(self, llm_judge):
        """Initialize test suite evaluator"""
        return TestSuiteEvaluator(llm_judge.llm_service)

    @pytest.mark.e2e
    @pytest.mark.llm_judge
    async def test_ddd_test_evaluation_with_llm_judge(
        self,
        llm_judge,
        test_suite_evaluator,
        bot_service,
        async_session
    ):
        """Evaluate DDD-based E2E tests using LLM judge"""

        # Execute DDD test suite
        test_results = {}

        # Test 1: User Authentication and Authorization
        auth_results = await self.test_user_authentication_workflows(bot_service, async_session)
        test_results["authentication"] = auth_results

        # Test 2: Information Retrieval Capabilities
        info_results = await self.test_information_retrieval_workflows(bot_service, async_session)
        test_results["information_retrieval"] = info_results

        # Test 3: Memory Management Features
        memory_results = await self.test_memory_management_workflows(bot_service, async_session)
        test_results["memory_management"] = memory_results

        # Define expected outcomes based on business requirements
        expected_outcomes = {
            "authentication": [
                "Admin users can access all bot features",
                "Friend users can access limited features with authentication",
                "Regular users are properly restricted from advanced features",
                "Authentication system prevents unauthorized access"
            ],
            "information_retrieval": [
                "Web search returns relevant results for queries",
                "API requests are properly authenticated and authorized",
                "Search results are cached for performance",
                "Rate limiting prevents abuse"
            ],
            "memory_management": [
                "Users can store and retrieve information",
                "Memory search returns relevant results",
                "Memory content persists across sessions",
                "Memory system respects user permissions"
            ]
        }

        # Define actual outcomes from test execution
        actual_outcomes = {
            "authentication": [
                f"Admin authentication success rate: {auth_results['admin_success_rate']:.1%}",
                f"Friend authentication success rate: {auth_results['friend_success_rate']:.1%}",
                f"Regular user restriction rate: {auth_results['restriction_rate']:.1%}",
                f"Unauthorized access prevention: {auth_results['security_success_rate']:.1%}"
            ],
            "information_retrieval": [
                f"Web search success rate: {info_results['search_success_rate']:.1%}",
                f"API request success rate: {info_results['api_success_rate']:.1%}",
                f"Cache hit rate: {info_results['cache_hit_rate']:.1%}",
                f"Rate limiting effectiveness: {info_results['rate_limiting_effectiveness']:.1%}"
            ],
            "memory_management": [
                f"Memory storage success rate: {memory_results['storage_success_rate']:.1%}",
                f"Memory search accuracy: {memory_results['search_accuracy']:.1%}",
                f"Memory persistence rate: {memory_results['persistence_rate']:.1%}",
                f"Permission compliance rate: {memory_results['permission_compliance']:.1%}"
            ]
        }

        # Evaluate each category with LLM judge
        evaluation_results = {}
        for category in test_results.keys():
            result = await llm_judge.evaluate_test_results(
                test_category=f"Bot {category.replace('_', ' ').title()}",
                test_results=test_results[category],
                expected_outcomes=expected_outcomes[category],
                actual_outcomes=actual_outcomes[category],
                additional_context={
                    "test_environment": "integration",
                    "user_count": len(test_results[category].get("test_users", [])),
                    "test_duration": test_results[category].get("duration_seconds", 0)
                }
            )
            evaluation_results[category] = result

        # Generate comprehensive report
        report = test_suite_evaluator.generate_evaluation_report(
            "DCMaidBot Core Functionality",
            evaluation_results
        )

        # Save report
        with open("test_reports/llm_judge_evaluation.md", "w") as f:
            f.write(report)

        # Assert overall quality meets standards
        overall_score = evaluation_results.get("overall", evaluation_results.get("authentication")).overall_score
        assert overall_score >= 0.8, f"Overall quality score {overall_score:.2f} below threshold 0.8"

        # Assert all categories pass LLM evaluation
        for category, result in evaluation_results.items():
            assert result.is_acceptable, f"Category '{category}' failed LLM evaluation: {result.summary}"

    async def test_user_authentication_workflows(self, bot_service, async_session):
        """Execute authentication workflow tests"""
        # Implementation would run all authentication-related tests
        # and return structured results
        pass

    async def test_information_retrieval_workflows(self, bot_service, async_session):
        """Execute information retrieval workflow tests"""
        # Implementation would run all information retrieval tests
        # and return structured results
        pass

    async def test_memory_management_workflows(self, bot_service, async_session):
        """Execute memory management workflow tests"""
        # Implementation would run all memory management tests
        # and return structured results
        pass
```

## 8. Implementation Roadmap for DCMaidBot

### 8.1 Phase 1: Foundation Setup (Week 1-2)

**Priority 1: Playwright Integration**
- [ ] Install Playwright and configure pytest-playwright
- [ ] Create environment-specific Playwright configuration
- [ ] Set up browser context management for parallel testing
- [ ] Implement basic web interface testing framework

**Priority 2: DDD Test Structure**
- [ ] Refactor existing E2E tests to follow DDD principles
- [ ] Create domain object builders (UserBuilder, MemoryBuilder, etc.)
- [ ] Implement journey test base classes
- [ ] Organize tests by bounded contexts

**Priority 3: Environment Configuration**
- [ ] Implement EnvironmentConfig system
- [ ] Create service factory for environment abstraction
- [ ] Set up cross-environment test validation

### 8.2 Phase 2: Journey Testing Implementation (Week 3-4)

**Priority 1: Critical User Journeys**
- [ ] Define and implement admin user workflow journey
- [ ] Define and implement friend user workflow journey
- [ ] Define and implement new user onboarding journey
- [ ] Create concurrent journey testing framework

**Priority 2: Smart Test Selection**
- [ ] Implement change-based test selection for pre-commit
- [ ] Create parallel E2E test execution
- [ ] Optimize test performance for CI/CD

### 8.3 Phase 3: Advanced Features (Week 5-6)

**Priority 1: LLM Judge Enhancement**
- [ ] Enhance LLM judge for DDD test evaluation
- [ ] Create domain-specific evaluation criteria
- [ ] Implement automated quality reporting

**Priority 2: Complete Integration**
- [ ] Integrate all components into existing testing infrastructure
- [ ] Create comprehensive documentation
- [ ] Implement monitoring and reporting

### 8.4 Success Metrics

**Quality Metrics:**
- E2E test coverage > 80% for critical user journeys
- Average test execution time < 5 minutes for pre-commit hooks
- LLM judge evaluation scores > 0.85 for all test categories
- Zero flaky tests in CI/CD pipeline

**Performance Metrics:**
- Pre-commit E2E test execution < 3 minutes
- Parallel test execution reduces total time by 60%
- Cross-environment test consistency > 95%

**Business Value Metrics:**
- Critical user journeys fully automated
- Business requirement validation through LLM judge
- Reduced manual testing time by 70%
- Faster feedback loops for developers

## 9. Best Practices and Recommendations

### 9.1 DDD Testing Best Practices

1. **Focus on Business Outcomes**: Test what users can do, not how the system works
2. **Use Ubiquitous Language**: Test names and structure should reflect business domain
3. **Test by Bounded Contexts**: Organize tests around domain boundaries
4. **Domain Object Builders**: Use builder pattern for creating test data
5. **Behavior Verification**: Verify business rules and invariants

### 9.2 Multi-Environment Testing Best Practices

1. **Environment Abstraction**: Use factory pattern for environment-specific services
2. **Configuration Management**: Centralize environment configuration
3. **Test Data Isolation**: Ensure tests don't interfere across environments
4. **Parallel Execution**: Maximize test parallelization while maintaining isolation
5. **Resource Management**: Monitor and limit resource usage in different environments

### 9.3 Journey Testing Best Practices

1. **User-Centric Scenarios**: Focus on complete user workflows
2. **Step Validation**: Verify each step of the journey meets expectations
3. **Error Handling**: Test error conditions and recovery scenarios
4. **Performance Validation**: Include performance criteria in journey tests
5. **Cross-User Testing**: Verify concurrent user interactions

### 9.4 Pre-Commit Integration Best Practices

1. **Smart Selection**: Run only relevant tests based on changes
2. **Fast Feedback**: Optimize for speed in pre-commit hooks
3. **Parallel Execution**: Use parallel processing for multiple tests
4. **Resource Management**: Limit memory and CPU usage
5. **Clear Error Reporting**: Provide actionable feedback for failures

## 10. Conclusion

This research report provides a comprehensive framework for implementing modern E2E testing strategies with DDD principles for DCMaidBot. The recommended approach leverages Playwright for web automation, implements domain-driven testing patterns, and maintains consistency across multiple environments.

**Key Recommendations:**

1. **Adopt Playwright** as the primary E2E testing framework for its superior reliability and Python integration
2. **Implement DDD Testing Principles** to focus on business value rather than implementation details
3. **Create Journey-Based Tests** that validate complete user workflows
4. **Enhance Pre-Commit Hooks** with smart test selection and parallel execution
5. **Leverage Existing LLM Judge System** for intelligent test evaluation

The proposed implementation maintains compatibility with DCMaidBot's existing sophisticated testing infrastructure while adding modern E2E testing capabilities. The phased approach ensures gradual adoption with measurable improvements at each stage.

**Expected Outcomes:**
- 80%+ E2E test coverage for critical user journeys
- 70% reduction in manual testing time
- 60% faster test execution through parallelization
- 95%+ cross-environment test consistency
- Enhanced business value validation through LLM judge integration

This comprehensive testing strategy will significantly improve DCMaidBot's quality assurance capabilities while maintaining alignment with modern software development best practices.

---

*Research conducted by Robo-System-Analyst for DCMaidBot project. Implementation guidance based on current codebase analysis and modern E2E testing best practices.*
