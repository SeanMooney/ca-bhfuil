"""Async integration tests."""

import asyncio

import pytest

from ca_bhfuil.core.async_config import AsyncConfigManager
from ca_bhfuil.storage.async_database import AsyncDatabaseManager


@pytest.mark.asyncio
async def test_async_fixture():
    """Test that the async event loop fixture is working."""
    await asyncio.sleep(0.01)
    # Get the current running loop to verify it's working
    loop = asyncio.get_running_loop()
    assert loop.is_running()


@pytest.mark.asyncio
async def test_async_config_manager():
    """Test AsyncConfigManager functionality."""
    manager = AsyncConfigManager()

    # Test loading configuration (will return empty GlobalConfig if file doesn't exist)
    config = await manager.load_configuration()
    assert hasattr(config, "repos")
    assert hasattr(config, "version")

    # Test loading the same config again
    config2 = await manager.load_configuration()
    assert config2.version == config.version


@pytest.mark.asyncio
async def test_async_database_manager():
    """Test AsyncDatabaseManager functionality."""
    import pathlib
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = pathlib.Path(tmp.name)

    try:
        manager = AsyncDatabaseManager(db_path)
        await manager.initialize(max_workers=2)

        # Test adding a repository
        repo_id = await manager.add_repository("/test/path", "test-repo")
        assert isinstance(repo_id, int)

        # Test getting repository by path
        repo = await manager.get_repository("/test/path")
        assert repo is not None
        assert repo["name"] == "test-repo"

        # Test getting stats
        stats = await manager.get_stats()
        assert isinstance(stats, dict)

        await manager.shutdown()

    finally:
        # Clean up
        if db_path.exists():
            db_path.unlink()
