"""Pytest configuration and shared fixtures."""

# Import all fixtures from the fixtures module to make them available
from tests.fixtures.repositories import *  # noqa: F401, F403
from tests.fixtures.async_fixtures import *  # noqa: F401, F403
