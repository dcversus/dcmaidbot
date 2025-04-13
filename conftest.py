import pytest
from pytest_asyncio import plugin
import logging

# Silence deprecation warnings
logging.getLogger("pytest_asyncio").setLevel(logging.ERROR)

# Configure pytest-asyncio for the project
def pytest_configure(config):
    plugin.LOOP_SCOPE = "function" 