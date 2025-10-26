import pytest


def pytest_configure(config):
    """Configure pytest with asyncio settings."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as asyncio coroutine"
    )


@pytest.fixture(scope="session")
def asyncio_default_fixture_loop_scope():
    """Set default fixture loop scope to function."""
    return "function"
