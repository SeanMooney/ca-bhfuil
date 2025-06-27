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
    
    # Test loading a config (will return empty dict if file doesn't exist)
    config = await manager.get_config("repos")
    assert isinstance(config, dict)
    
    # Test loading the same config again (should hit cache)
    config2 = await manager.get_config("repos")
    assert config2 == config


@pytest.mark.asyncio  
async def test_async_database_manager():
    """Test AsyncDatabaseManager functionality."""
    import tempfile
    import pathlib
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = pathlib.Path(tmp.name)
    
    try:
        manager = AsyncDatabaseManager(str(db_path))
        await manager.connect(pool_size=2)
        
        # Test creating a simple table
        await manager.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Test inserting data
        await manager.execute("INSERT INTO test (name) VALUES (?)", ["test_name"])
        
        # Test querying data
        cursor = await manager.execute("SELECT * FROM test")
        # Note: cursor handling may need adjustment based on actual implementation
        
        await manager.close()
        
    finally:
        # Clean up
        if db_path.exists():
            db_path.unlink()
