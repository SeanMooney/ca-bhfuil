"""Utilities for gradual migration to asynchronous operations."""

import os


def is_async_enabled() -> bool:
    """Check if async operations are enabled via an environment variable."""
    return os.environ.get("CA_BHFUIL_ASYNC_ENABLED", "false").lower() == "true"
