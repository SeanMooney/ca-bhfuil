"""Tests for manager resource management fixes."""

import pathlib
import tempfile
import unittest.mock

import pytest

from ca_bhfuil.core.managers import factory as manager_factory
from tests.fixtures import alembic


class TestManagerResourceManagement:
    """Test the fixed resource management issues."""

    async def test_manager_registry_key_collision_fix(self, tmp_path):
        """Test that manager registry now properly tracks separate instances."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        async with manager_factory.ManagerFactory(db_path) as factory:
            with tempfile.TemporaryDirectory() as temp_dir1, \
                 tempfile.TemporaryDirectory() as temp_dir2:

                repo_path1 = pathlib.Path(temp_dir1)
                repo_path2 = pathlib.Path(temp_dir2)

                # Mock git repository to avoid needing actual git repos
                with unittest.mock.patch(
                    "ca_bhfuil.core.git.repository.Repository"
                ) as mock_repo_class:
                    mock_repo = unittest.mock.MagicMock()
                    mock_repo.head_is_unborn = False
                    mock_repo.get_repository_stats.return_value = {"total_branches": 1}
                    mock_repo_class.return_value = mock_repo

                    # Create two different repository managers
                    repo_manager1 = await factory.get_repository_manager(repo_path1)
                    repo_manager2 = await factory.get_repository_manager(repo_path2)

                    # Verify they are different instances
                    assert repo_manager1 is not repo_manager2

                    # Verify they have different repository paths
                    assert repo_manager1.repository_path != repo_manager2.repository_path

                    # Verify both are registered in the registry
                    registry = await factory.get_registry()
                    manager1_key = f"repository:{repo_path1}"
                    manager2_key = f"repository:{repo_path2}"

                    retrieved_manager1 = registry.get(manager1_key)
                    retrieved_manager2 = registry.get(manager2_key)

                    assert retrieved_manager1 is repo_manager1
                    assert retrieved_manager2 is repo_manager2

    async def test_repository_manager_no_incorrect_session_closing(self, tmp_path):
        """Test that RepositoryManager no longer overrides close() method."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        async with manager_factory.ManagerFactory(db_path) as factory:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = pathlib.Path(temp_dir)

                # Mock git repository
                with unittest.mock.patch(
                    "ca_bhfuil.core.git.repository.Repository"
                ) as mock_repo_class:
                    mock_repo = unittest.mock.MagicMock()
                    mock_repo.head_is_unborn = False
                    mock_repo.get_repository_stats.return_value = {"total_branches": 1}
                    mock_repo_class.return_value = mock_repo

                    repo_manager = await factory.get_repository_manager(repo_path)

                    # Verify the manager doesn't override close method
                    # (close method should come from BaseManager)
                    from ca_bhfuil.core.managers import base as base_manager
                    assert repo_manager.__class__.close is base_manager.BaseManager.close

                    # Verify the manager still has close method from BaseManager
                    assert hasattr(repo_manager, 'close')

                    # Verify calling close doesn't cause issues
                    await repo_manager.close()

    async def test_manager_registry_string_keys(self, tmp_path):
        """Test that manager registry properly handles string keys."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        factory = manager_factory.ManagerFactory(db_path)
        await factory.initialize()

        try:
            registry = await factory.get_registry()

            # Test with a mock manager that has an async close method
            mock_manager = unittest.mock.MagicMock()
            mock_manager.close = unittest.mock.AsyncMock()
            test_key = "test_manager_instance"

            # Register with string key
            registry.register(test_key, mock_manager)

            # Retrieve with string key
            retrieved_manager = registry.get(test_key)

            assert retrieved_manager is mock_manager

            # Test error case
            with pytest.raises(KeyError, match="Manager key 'nonexistent' not registered"):
                registry.get("nonexistent")
        finally:
            await factory.close()
