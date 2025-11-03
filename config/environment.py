"""
Environment-Specific Configuration Management

Provides unified configuration management across environments with:
- Environment detection and validation
- Configurable test behavior per environment
- Automatic service discovery in containerized environments
- Environment-specific overrides and defaults
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class Environment(Enum):
    """Supported environments."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class TestMode(Enum):
    """Test execution modes."""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    pool_pre_ping: bool = True
    pool_recycle: int = 3600


@dataclass
class ExternalServiceConfig:
    """External service configuration."""

    base_url: str
    timeout: int = 30
    retries: int = 3
    api_key: Optional[str] = None
    mock_mode: bool = False
    mock_responses: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestConfig:
    """Test-specific configuration."""

    mode: TestMode
    parallel_workers: int = 1
    database_isolation: bool = True
    cleanup_after_test: bool = True
    mock_external_services: bool = True
    llm_judge_enabled: bool = True
    performance_baseline_file: Optional[str] = None
    coverage_threshold: float = 80.0


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""

    environment: Environment
    database: DatabaseConfig
    redis_url: str
    openai: ExternalServiceConfig
    telegram: ExternalServiceConfig
    test: Optional[TestConfig] = None
    debug: bool = False
    log_level: str = "INFO"
    features: Dict[str, bool] = field(default_factory=dict)


class EnvironmentManager:
    """Manages environment configuration and detection."""

    def __init__(self):
        """Initialize environment manager."""
        self._environment = None
        self._config = None
        self._load_environment()

    def _load_environment(self):
        """Detect and load current environment."""
        # Environment detection priority
        env_name = (
            os.getenv("ENVIRONMENT")
            or os.getenv("ENV")
            or os.getenv("CI_ENVIRONMENT_NAME")
            or self._detect_container_environment()
            or "local"
        ).lower()

        # Map to environment enum
        env_mapping = {
            "local": Environment.LOCAL,
            "development": Environment.DEVELOPMENT,
            "production": Environment.PRODUCTION,
        }

        self._environment = env_mapping.get(env_name, Environment.LOCAL)
        self._config = self._build_config()

    def _detect_container_environment(self) -> Optional[str]:
        """Detect if running in a container environment."""
        # Check for common container environment indicators
        if os.path.exists("/.dockerenv"):
            return "test"  # Default to test for containers

        # Check for Kubernetes service environment
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return "production"

        # Check for GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            return "test"

        # Check for other CI systems
        ci_indicators = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "JENKINS_URL",
            "TRAVIS",
            "CIRCLECI",
            "GITLAB_CI",
        ]
        if any(os.getenv(indicator) for indicator in ci_indicators):
            return "test"

        return None

    def _build_config(self) -> EnvironmentConfig:
        """Build environment-specific configuration."""
        if self._environment == Environment.LOCAL:
            return self._build_local_config()
        elif self._environment == Environment.TEST:
            return self._build_test_config()
        elif self._environment == Environment.STAGING:
            return self._build_staging_config()
        elif self._environment == Environment.PRODUCTION:
            return self._build_production_config()
        else:
            raise ValueError(f"Unsupported environment: {self._environment}")

    def _build_local_config(self) -> EnvironmentConfig:
        """Build local development configuration."""
        return EnvironmentConfig(
            environment=Environment.LOCAL,
            database=DatabaseConfig(
                url=os.getenv(
                    "DATABASE_URL", "sqlite+aiosqlite:///./dcmaidbot_local.db"
                ),
                echo=True,
                pool_size=5,
                max_overflow=10,
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            openai=ExternalServiceConfig(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=30,
                retries=3,
            ),
            telegram=ExternalServiceConfig(
                base_url="https://api.telegram.org",
                api_key=os.getenv("BOT_TOKEN"),
                timeout=30,
                retries=3,
            ),
            debug=True,
            log_level="DEBUG",
            features={
                "llm_judge": True,
                "performance_monitoring": False,
                "detailed_logging": True,
                "auto_cleanup": False,
            },
        )

    def _build_test_config(self) -> EnvironmentConfig:
        """Build test environment configuration."""
        # Detect if running in Docker container
        in_container = os.path.exists("/.dockerenv")

        # Auto-detect service URLs in container environment
        postgres_host = "postgres-test" if in_container else "localhost"
        postgres_port = "5432" if in_container else "5433"
        redis_host = "redis-test" if in_container else "localhost"
        redis_port = "6379" if in_container else "6380"

        return EnvironmentConfig(
            environment=Environment.TEST,
            database=DatabaseConfig(
                url=os.getenv(
                    "DATABASE_URL",
                    f"postgresql+asyncpg://dcmaidbot:test_password@{postgres_host}:{postgres_port}/dcmaidbot_test",
                ),
                echo=False,
                pool_size=5,
                max_overflow=10,
            ),
            redis_url=os.getenv("REDIS_URL", f"redis://{redis_host}:{redis_port}/0"),
            openai=ExternalServiceConfig(
                base_url=os.getenv("OPENAI_API_BASE", "http://mock-openai:1080"),
                api_key=os.getenv("OPENAI_API_KEY", "test-key"),
                timeout=10,
                retries=1,
                mock_mode=True,
            ),
            telegram=ExternalServiceConfig(
                base_url=os.getenv("TELEGRAM_API_BASE", "http://mock-telegram:1080"),
                api_key=os.getenv("BOT_TOKEN", "test-token"),
                timeout=10,
                retries=1,
                mock_mode=True,
            ),
            test=TestConfig(
                mode=TestMode.E2E,
                parallel_workers=4,
                database_isolation=True,
                cleanup_after_test=True,
                mock_external_services=True,
                llm_judge_enabled=True,
                coverage_threshold=70.0,
            ),
            debug=False,
            log_level="INFO",
            features={
                "llm_judge": True,
                "performance_monitoring": True,
                "detailed_logging": False,
                "auto_cleanup": True,
                "mock_services": True,
            },
        )

    def _build_staging_config(self) -> EnvironmentConfig:
        """Build staging environment configuration."""
        return EnvironmentConfig(
            environment=Environment.STAGING,
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL"), echo=False, pool_size=10, max_overflow=20
            ),
            redis_url=os.getenv("REDIS_URL"),
            openai=ExternalServiceConfig(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=30,
                retries=3,
            ),
            telegram=ExternalServiceConfig(
                base_url="https://api.telegram.org",
                api_key=os.getenv("BOT_TOKEN"),
                timeout=30,
                retries=3,
            ),
            debug=False,
            log_level="INFO",
            features={
                "llm_judge": True,
                "performance_monitoring": True,
                "detailed_logging": True,
                "auto_cleanup": False,
            },
        )

    def _build_production_config(self) -> EnvironmentConfig:
        """Build production environment configuration."""
        return EnvironmentConfig(
            environment=Environment.PRODUCTION,
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL"),
                echo=False,
                pool_size=20,
                max_overflow=40,
                pool_recycle=3600,
            ),
            redis_url=os.getenv("REDIS_URL"),
            openai=ExternalServiceConfig(
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=30,
                retries=5,
            ),
            telegram=ExternalServiceConfig(
                base_url="https://api.telegram.org",
                api_key=os.getenv("BOT_TOKEN"),
                timeout=30,
                retries=5,
            ),
            debug=False,
            log_level="WARNING",
            features={
                "llm_judge": True,
                "performance_monitoring": True,
                "detailed_logging": False,
                "auto_cleanup": False,
                "monitoring": True,
                "health_checks": True,
            },
        )

    @property
    def environment(self) -> Environment:
        """Get current environment."""
        return self._environment

    @property
    def config(self) -> EnvironmentConfig:
        """Get current environment configuration."""
        return self._config

    def is_test_environment(self) -> bool:
        """Check if running in test environment."""
        return self._environment in [Environment.TEST, Environment.STAGING]

    def is_container_environment(self) -> bool:
        """Check if running in container."""
        return os.path.exists("/.dockerenv") or os.getenv("KUBERNETES_SERVICE_HOST")

    def get_database_url(self) -> str:
        """Get database URL for current environment."""
        return self._config.database.url

    def get_service_config(self, service_name: str) -> Optional[ExternalServiceConfig]:
        """Get service configuration by name."""
        service_map = {"openai": self._config.openai, "telegram": self._config.telegram}
        return service_map.get(service_name)

    def override_for_test(self, test_mode: TestMode) -> EnvironmentConfig:
        """Create test-specific configuration override."""
        if self._config.test is None:
            self._config.test = TestConfig(mode=test_mode)
        else:
            self._config.test.mode = test_mode

        # Apply test mode specific overrides
        if test_mode == TestMode.UNIT:
            self._config.test.mock_external_services = True
            self._config.test.database_isolation = True
            self._config.test.parallel_workers = 1
        elif test_mode == TestMode.INTEGRATION:
            self._config.test.mock_external_services = False
            self._config.test.database_isolation = True
            self._config.test.parallel_workers = 2
        elif test_mode == TestMode.E2E:
            self._config.test.mock_external_services = False
            self._config.test.database_isolation = False
            self._config.test.parallel_workers = 1
        elif test_mode == TestMode.PERFORMANCE:
            self._config.test.mock_external_services = False
            self._config.test.database_isolation = False
            self._config.test.parallel_workers = 4

        return self._config

    def validate_config(self) -> List[str]:
        """Validate current configuration.

        Returns:
            List of validation errors
        """
        errors = []

        # Validate database URL
        try:
            parsed = urlparse(self._config.database.url)
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid database URL format")
        except Exception:
            errors.append("Failed to parse database URL")

        # Validate Redis URL
        try:
            parsed = urlparse(self._config.redis_url)
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid Redis URL format")
        except Exception:
            errors.append("Failed to parse Redis URL")

        # Validate required API keys in non-test environments
        if not self.is_test_environment():
            if not self._config.openai.api_key:
                errors.append("OpenAI API key required")
            if not self._config.telegram.api_key:
                errors.append("Telegram bot token required")

        return errors

    def export_config(self, output_file: Optional[str] = None) -> str:
        """Export configuration to JSON file.

        Args:
            output_file: Optional output file path

        Returns:
            Path to exported file
        """
        if output_file is None:
            output_file = f"config_{self._environment.value}.json"

        config_dict = {
            "environment": self._environment.value,
            "database": {
                "url": self._config.database.url,
                "pool_size": self._config.database.pool_size,
                "echo": self._config.database.echo,
            },
            "redis_url": self._config.redis_url,
            "openai": {
                "base_url": self._config.openai.base_url,
                "timeout": self._config.openai.timeout,
                "mock_mode": self._config.openai.mock_mode,
            },
            "telegram": {
                "base_url": self._config.telegram.base_url,
                "timeout": self._config.telegram.timeout,
                "mock_mode": self._config.telegram.mock_mode,
            },
            "debug": self._config.debug,
            "log_level": self._config.log_level,
            "features": self._config.features,
        }

        if self._config.test:
            config_dict["test"] = {
                "mode": self._config.test.mode.value,
                "parallel_workers": self._config.test.parallel_workers,
                "database_isolation": self._config.test.database_isolation,
                "mock_external_services": self._config.test.mock_external_services,
                "llm_judge_enabled": self._config.test.llm_judge_enabled,
            }

        with open(output_file, "w") as f:
            json.dump(config_dict, f, indent=2)

        return output_file

    def __str__(self) -> str:
        """String representation of environment configuration."""
        return (
            f"EnvironmentConfig(environment={self._environment.value}, "
            f"database={self._config.database.url.split('@')[1] if '@' in self._config.database.url else 'local'}, "
            f"features={len(self._config.features)} enabled)"
        )


# Global environment manager instance
env_manager = EnvironmentManager()


def get_environment() -> Environment:
    """Get current environment."""
    return env_manager.environment


def get_config() -> EnvironmentConfig:
    """Get current environment configuration."""
    return env_manager.config


def is_test_environment() -> bool:
    """Check if running in test environment."""
    return env_manager.is_test_environment()


def is_container_environment() -> bool:
    """Check if running in container environment."""
    return env_manager.is_container_environment()
