# Cross-Environment Testing Strategy for DCMaidBot

This comprehensive guide covers the advanced cross-environment testing infrastructure implemented for DCMaidBot, ensuring consistent test execution across local development, CI/CD pipelines, and production validation.

## Overview

The cross-environment testing system provides:

- **Unified Configuration**: Environment-specific test configuration with automatic detection
- **Containerized Testing**: Docker-based test environments for consistency
- **Test Data Management**: Automated seeding, cleanup, and isolation across environments
- **Advanced Orchestration**: Intelligent test execution with dependency resolution
- **Performance Monitoring**: Baseline comparison and regression detection
- **LLM Judge Integration**: AI-powered test evaluation and quality assessment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Orchestrator                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Unit Tests    │  │ Integration     │  │ E2E Tests    │ │
│  │                 │  │ Tests           │  │              │ │
│  │ • Fast          │  │ • Database      │  │ • Real APIs  │ │
│  │ • Isolated      │  │ • External APIs │  │ • Mocks      │ │
│  │ • No external   │  │ • Service Auth  │  │ • LLM Judge  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Environment Mgr   │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│ Local Dev      │   │ CI/CD Pipeline  │   │ Production     │
│                │   │                 │   │ Validation     │
│ • SQLite       │   │ • PostgreSQL    │   │ • Real APIs    │
│ • Mocks        │   │ • Containers    │   │ • Monitoring   │
│ • Hot Reload   │   │ • Parallel      │   │ • Performance  │
└────────────────┘   └─────────────────┘   └────────────────┘
```

## Environment Types

### Local Development
- **Database**: SQLite (in-memory) or local PostgreSQL
- **External Services**: Mocked responses
- **Performance**: Relaxed thresholds
- **Features**: Debug logging, auto-reload

### Test Environment (CI/CD)
- **Database**: PostgreSQL in containers
- **External Services**: MockServer instances
- **Performance**: Standard thresholds
- **Features**: Parallel execution, comprehensive coverage

### Staging Environment
- **Database**: Staging PostgreSQL
- **External Services**: Staging APIs
- **Performance**: Production-like thresholds
- **Features**: Full functionality, monitoring

### Production Environment
- **Database**: Production PostgreSQL
- **External Services**: Real APIs
- **Performance**: Strict thresholds
- **Features**: Read-only testing, monitoring

## Quick Start

### 1. Local Development Testing

```bash
# Run unit tests with local SQLite
pytest tests/unit/ -v --test-mode=unit

# Run integration tests with local PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/dcmaidbot_test pytest tests/unit/test_*.py tests/e2e/test_api_*.py -v --test-mode=integration

# Run full E2E tests with mocked services
DISABLE_TG=true pytest tests/e2e/ -v --test-mode=e2e --llm-judge
```

### 2. Containerized Testing

```bash
# Start test infrastructure
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
scripts/wait-for-services.sh

# Run tests with container orchestration
scripts/run_e2e_tests_with_server.sh e2e 4 test true

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### 3. Advanced Test Orchestration

```bash
# Run orchestrated test suite
python scripts/test_orchestrator.py --suite all --parallel-workers 4 --llm-judge

# Run specific test suite
python scripts/test_orchestrator.py --suite unit --parallel-workers 8

# Run performance tests with baseline comparison
python scripts/test_orchestrator.py --suite performance --llm-judge
```

## Configuration

### Environment Detection

The system automatically detects the environment based on:

1. **Environment Variables**: `ENVIRONMENT`, `ENV`, `CI_ENVIRONMENT_NAME`
2. **Container Detection**: Docker, Kubernetes
3. **CI System Detection**: GitHub Actions, Jenkins, GitLab CI

### Configuration Override

```bash
# Override environment
export ENVIRONMENT=staging

# Override test mode
export TEST_MODE=performance

# Override parallel workers
export PARALLEL_WORKERS=8

# Enable/disable LLM judge
export LLM_JUDGE_ENABLED=true
```

### Test Mode Selection

| Mode | Description | Use Case | Resources |
|------|-------------|----------|-----------|
| `unit` | Fast, isolated tests | Component testing | Minimal |
| `integration` | Service interactions | API testing | Moderate |
| `e2e` | Full workflow testing | System testing | High |
| `performance` | Load and benchmark | Performance testing | Maximum |
| `security` | Security validation | Security testing | Moderate |

## Test Data Management

### Automated Seeding

```python
from scripts.test_data_seeder import TestDataSeeder

# Seed test data
seeder = TestDataSeeder(environment="test")
results = await seeder.seed_all()

# Clean up test data
await seeder.cleanup_test_data(session)

# Export test data
files = await seeder.export_test_data("/backup")

# Restore test data
counts = await seeder.restore_test_data("/backup")
```

### Data Isolation

- **Unit Tests**: In-memory database, unique per test
- **Integration Tests**: Isolated database schema per test session
- **E2E Tests**: Shared test database with transaction rollback
- **Performance Tests**: Dedicated performance database

## Containerized Services

### Available Services

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| PostgreSQL | 5433 | Test database | `pg_isready` |
| Redis | 6380 | Cache/Session store | `redis-cli ping` |
| Mock OpenAI | 1080 | AI API mocking | HTTP health check |
| Mock Telegram | 1081 | Bot API mocking | HTTP health check |

### Custom Mock Services

Create custom mock configurations in `test-configs/`:

```json
{
  "expectations": [
    {
      "httpRequest": {
        "method": "POST",
        "path": "/custom/endpoint"
      },
      "httpResponse": {
        "statusCode": 200,
        "body": {"result": "success"}
      }
    }
  ]
}
```

## Performance Testing

### Baseline Management

```python
from scripts.test_orchestrator import PerformanceBaselineManager

# Load baselines
baseline_mgr = PerformanceBaselineManager()

# Compare with baseline
result = baseline_mgr.compare_with_baseline(
    test_name="my_test",
    metric_name="response_time",
    value=1.5  # seconds
)

if result["status"] == "regression":
    print(f"Performance regression detected: {result['percent_change']:.1f}%")
```

### Performance Thresholds

Update `test-data/performance_baselines.json`:

```json
{
  "thresholds": {
    "response_time_warning_ms": 1000,
    "response_time_critical_ms": 3000,
    "memory_usage_warning_percent": 75,
    "memory_usage_critical_percent": 90
  }
}
```

## LLM Judge Integration

### Test Evaluation

```python
from tests.llm_judge import LLMJudge, TestSuiteEvaluator
from services.llm_service import LLMService

# Initialize LLM judge
llm_service = LLMService()
evaluator = TestSuiteEvaluator(llm_service)

# Evaluate test results
results = await evaluator.evaluate_prp_compliance(
    prp_name="My Feature",
    test_results=test_results,
    dod_criteria=definition_of_done,
    test_categories=test_categories
)

# Generate report
report = evaluator.generate_evaluation_report("My Feature", results)
```

### Custom Evaluation Criteria

Define expected outcomes in your test:

```python
expected_outcomes = [
    "All API endpoints return correct responses",
    "Database operations complete within 100ms",
    "Memory usage stays below 512MB",
    "Error handling works correctly"
]
```

## CI/CD Integration

### GitHub Actions Workflow

The enhanced CI workflow provides:

1. **Environment Detection**: Automatic environment setup
2. **Parallel Testing**: Multiple test modes in parallel
3. **Container Services**: Automated service provisioning
4. **Result Aggregation**: Combined test reporting
5. **Performance Comparison**: Baseline regression detection
6. **Failure Notification**: Automatic issue creation

### Workflow Triggers

```yaml
# Manual trigger with custom parameters
on:
  workflow_dispatch:
    inputs:
      test_mode:
        description: 'Test execution mode'
        default: 'e2e'
      environment:
        description: 'Target environment'
        default: 'test'
```

### Result Reporting

- **JUnit XML**: Standard test result format
- **HTML Reports**: Detailed test reports
- **Performance Metrics**: Benchmark comparison
- **LLM Evaluation**: AI quality assessment

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL container
docker ps | grep postgres

# Check database connectivity
docker-compose -f docker-compose.test.yml exec postgres-test psql -U dcmaidbot -d dcmaidbot_test -c "SELECT 1;"

# Reset database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d postgres-test
```

#### Service Timeouts

```bash
# Wait for services manually
scripts/wait-for-services.sh

# Check service logs
docker-compose -f docker-compose.test.yml logs postgres-test
docker-compose -f docker-compose.test.yml logs redis-test
```

#### Memory Issues

```bash
# Limit parallel workers
export PARALLEL_WORKERS=2

# Use SQLite for unit tests
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Monitor memory usage
python scripts/test_orchestrator.py --suite unit --parallel-workers 1
```

#### Test Isolation Problems

```bash
# Enable database isolation
export DATABASE_ISOLATION=true

# Use fresh database per test
export DATABASE_URL="sqlite+aiosqlite:///./test_$(date +%s).db"

# Cleanup between tests
export CLEANUP_AFTER_TEST=true
```

### Debug Mode

```bash
# Enable debug logging
export LOGLEVEL=DEBUG

# Run single test with verbose output
pytest tests/unit/test_specific.py::test_function -v -s --tb=long

# Run with database echo
export DATABASE_ECHO=true
pytest tests/unit/test_database.py -v
```

## Best Practices

### Test Organization

1. **Separate Concerns**: Unit vs Integration vs E2E
2. **Clear Naming**: Descriptive test names and categories
3. **Proper Tagging**: Use tags for test categorization
4. **Dependency Management**: Declare test dependencies explicitly

### Performance Optimization

1. **Parallel Execution**: Use parallel workers for independent tests
2. **Resource Management**: Monitor and limit resource usage
3. **Smart Selection**: Run only relevant tests based on changes
4. **Baseline Updates**: Regularly update performance baselines

### Environment Consistency

1. **Container Services**: Use same service versions across environments
2. **Configuration Management**: Centralized environment configuration
3. **Data Consistency**: Use same test data across environments
4. **Version Alignment**: Keep tool versions synchronized

### Quality Assurance

1. **LLM Evaluation**: Use AI judge for intelligent assessment
2. **Coverage Thresholds**: Maintain minimum test coverage
3. **Performance Gates**: Prevent performance regressions
4. **Security Testing**: Include security validation

## Advanced Usage

### Custom Test Suites

```python
# Create custom test suite
custom_suite = TestSuite(
    name="custom",
    description="Custom test suite for specific feature",
    tests=custom_tests,
    setup_tasks=["setup_custom_data"],
    teardown_tasks=["cleanup_custom_data"],
    parallel=True,
    max_workers=4
)

# Run custom suite
result = await orchestrator.run_test_suite("custom")
```

### Resource Monitoring

```python
# Monitor resources during test
from scripts.test_orchestrator import ResourceMonitor

monitor = ResourceMonitor()
await monitor.start_monitoring()

# Run tests
result = await run_tests()

# Get resource summary
summary = monitor.get_summary()
print(f"Peak CPU: {summary['cpu']['max']:.1f}%")
print(f"Peak Memory: {summary['memory']['max']:.1f}%")
```

### Integration with External Systems

```python
# Integrate with external monitoring
async def notify_test_results(results):
    # Send to Slack
    await slack_client.send_test_summary(results)

    # Update dashboard
    await dashboard.update_metrics(results)

    # Store in database
    await db.store_test_run(results)

# Add to test workflow
await notify_test_results(test_results)
```

## Contributing

When contributing to the testing infrastructure:

1. **Update Documentation**: Keep this documentation current
2. **Add Tests**: Test your changes with the new infrastructure
3. **Performance Impact**: Consider performance implications
4. **Backward Compatibility**: Maintain compatibility with existing tests
5. **Configuration**: Update configuration files when needed

## Support

For issues or questions:

1. **Check Logs**: Review test and service logs
2. **Documentation**: Consult this guide and inline documentation
3. **GitHub Issues**: Create issues for bugs or feature requests
4. **Discussions**: Use GitHub Discussions for questions

---

This testing infrastructure provides DCMaidBot with reliable, consistent testing across all environments, ensuring high-quality releases and preventing regressions.
