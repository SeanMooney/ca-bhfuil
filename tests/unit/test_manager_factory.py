"""Tests for ManagerFactory and convenience functions."""

import pathlib
import tempfile
import unittest.mock

import pytest

from ca_bhfuil.core.managers import factory as manager_factory
from ca_bhfuil.core.managers import repository as repository_manager
from tests.fixtures import alembic


class TestManagerFactory:
    """Test ManagerFactory functionality."""

    @pytest.fixture
    async def factory(self, tmp_path):
        """Provide a manager factory with test database."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        factory = manager_factory.ManagerFactory(db_path)
        yield factory
        await factory.close()

    async def test_factory_initialization(self, tmp_path):
        """Test factory initialization process."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        factory = manager_factory.ManagerFactory(db_path)

        assert factory._initialized is False
        assert factory._db_manager is None

        await factory.initialize()

        assert factory._initialized is True
        assert factory._db_manager is not None
        assert factory._registry is not None

        await factory.close()

    async def test_get_repository_manager(self, factory):
        """Test creating repository manager through factory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock git repository
            with unittest.mock.patch(
                "ca_bhfuil.core.git.repository.Repository"
            ) as mock_repo_class:
                mock_repo = unittest.mock.MagicMock()
                mock_repo_class.return_value = mock_repo

                repo_manager = await factory.get_repository_manager(repo_path)

                assert isinstance(repo_manager, repository_manager.RepositoryManager)
                assert repo_manager.repository_path == repo_path
                assert repo_manager._db_manager is factory._db_manager

    async def test_get_multiple_repository_managers(self, factory):
        """Test creating multiple repository managers shares resources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path1 = pathlib.Path(temp_dir) / "repo1"
            repo_path2 = pathlib.Path(temp_dir) / "repo2"
            repo_path1.mkdir()
            repo_path2.mkdir()

            # Mock git repository
            with unittest.mock.patch(
                "ca_bhfuil.core.git.repository.Repository"
            ) as mock_repo_class:
                mock_repo_class.return_value = unittest.mock.MagicMock()

                repo_manager1 = await factory.get_repository_manager(repo_path1)
                repo_manager2 = await factory.get_repository_manager(repo_path2)

                # Should share the same database manager
                assert repo_manager1._db_manager is repo_manager2._db_manager
                assert repo_manager1._db_manager is factory._db_manager

    async def test_factory_as_context_manager(self, tmp_path):
        """Test factory as async context manager."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        async with manager_factory.ManagerFactory(db_path) as factory:
            assert factory._initialized is True
            assert factory._db_manager is not None

        # Should be cleaned up after context exit
        assert factory._initialized is False
        assert factory._db_manager is None

    async def test_factory_close_cleanup(self, factory):
        """Test that factory close cleans up all resources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock git repository
            with unittest.mock.patch(
                "ca_bhfuil.core.git.repository.Repository"
            ) as mock_repo_class:
                mock_repo_class.return_value = unittest.mock.MagicMock()

                # Create a repository manager
                await factory.get_repository_manager(repo_path)

                # Factory should have resources
                assert factory._initialized is True
                assert factory._db_manager is not None

                # Close factory
                await factory.close()

                # Should be cleaned up
                assert factory._initialized is False
                assert factory._db_manager is None

    async def test_get_registry(self, factory):
        """Test getting registry from factory."""
        registry = await factory.get_registry()

        assert registry is factory._registry
        assert factory._initialized is True


class TestGlobalFactory:
    """Test global factory convenience functions."""

    async def test_get_global_factory(self, tmp_path):
        """Test getting global factory instance."""
        # Clean up any existing global factory first
        await manager_factory.close_global_factory()

        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        # Get global factory
        factory1 = await manager_factory.get_manager_factory(db_path)
        factory2 = await manager_factory.get_manager_factory(db_path)

        # Should be the same instance
        assert factory1 is factory2
        assert factory1._initialized is True

        # Clean up
        await manager_factory.close_global_factory()

    async def test_get_repository_manager_convenience(self, tmp_path):
        """Test convenience function for getting repository manager."""
        # Clean up any existing global factory first
        await manager_factory.close_global_factory()

        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock git repository
            with unittest.mock.patch(
                "ca_bhfuil.core.git.repository.Repository"
            ) as mock_repo_class:
                mock_repo_class.return_value = unittest.mock.MagicMock()

                repo_manager = await manager_factory.get_repository_manager(
                    repo_path, db_path
                )

                assert isinstance(repo_manager, repository_manager.RepositoryManager)
                assert repo_manager.repository_path == repo_path

        # Clean up
        await manager_factory.close_global_factory()

    async def test_close_global_factory(self, tmp_path):
        """Test closing global factory."""
        # Clean up any existing global factory first
        await manager_factory.close_global_factory()

        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        # Create global factory
        factory = await manager_factory.get_manager_factory(db_path)
        assert factory is not None
        assert factory._initialized is True

        # Close global factory
        await manager_factory.close_global_factory()

        # Global factory should be None
        assert manager_factory._global_factory is None

    async def test_multiple_calls_to_close_global_factory(self):
        """Test that multiple calls to close_global_factory don't error."""
        await manager_factory.close_global_factory()
        await manager_factory.close_global_factory()  # Should not error

    @pytest.fixture(autouse=True)
    async def cleanup_global_factory(self):
        """Ensure global factory is cleaned up after each test."""
        yield
        await manager_factory.close_global_factory()


class TestFactoryIntegration:
    """Test factory integration with real components."""

    async def test_factory_with_real_database_operations(self, tmp_path):
        """Test factory with actual database operations."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        async with manager_factory.ManagerFactory(db_path) as factory:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = pathlib.Path(temp_dir)

                # Mock git repository to avoid needing actual git repo
                with unittest.mock.patch(
                    "ca_bhfuil.core.git.repository.Repository"
                ) as mock_repo_class:
                    mock_repo = unittest.mock.MagicMock()
                    mock_repo.head_is_unborn = False
                    mock_repo.get_repository_stats.return_value = {"total_branches": 1}
                    mock_repo_class.return_value = mock_repo

                    repo_manager = await factory.get_repository_manager(repo_path)

                    # Should be able to sync with database
                    await repo_manager.sync_with_database()

                    # Should be able to analyze repository
                    result = await repo_manager.analyze_repository()
                    assert result.success is True
