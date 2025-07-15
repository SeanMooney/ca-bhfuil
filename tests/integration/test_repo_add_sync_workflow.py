"""Integration tests for repo add -> sync workflow to prevent regression."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_registry
from ca_bhfuil.core import async_sync
from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.storage import sqlmodel_manager


class TestRepoAddSyncWorkflow:
    """Integration tests for repo add -> sync workflow."""

    @pytest.mark.asyncio
    async def test_repo_add_registers_in_database(self):
        """Test that repo add command registers repository in database."""
        # Create completely isolated test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            config_dir = tmp_path / "config"
            config_dir.mkdir()
            db_path = tmp_path / "test.db"
            repo_path = tmp_path / "repos" / "test-repo"
            repo_path.mkdir(parents=True)

            # Create fake .git directory
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            # Initialize database
            db_manager = sqlmodel_manager.SQLModelDatabaseManager(db_path)
            await db_manager.initialize()

            # Initialize config manager
            config_manager = async_config.AsyncConfigManager(config_dir)
            await config_manager.generate_default_config()

            # Initialize repo registry
            repo_registry = async_registry.AsyncRepositoryRegistry(
                config_manager, db_manager
            )

            try:
                # Create repository config
                repo_config = config.RepositoryConfig(
                    name="test-repo",
                    source={
                        "url": "https://github.com/test/repo.git",
                        "type": "git",
                        "path": str(repo_path),
                    },
                )

                # Simulate repo add command: add to config and register in database
                current_config = await config_manager.load_configuration()
                current_config.repos.append(repo_config)
                await config_manager.save_configuration(current_config)

                # Register in database (this is what we added to repo add command)
                repo_id = await repo_registry.register_repository(repo_config)
                assert repo_id > 0

                # Verify repository is registered
                state = await repo_registry.get_repository_state("test-repo")
                assert state is not None
                assert state["registered"] is True
                assert state["config"]["name"] == "test-repo"

            finally:
                # Cleanup
                await db_manager.close()

    @pytest.mark.asyncio
    async def test_sync_works_after_repo_add(self):
        """Test that sync command works after repo add (regression test)."""
        # Create completely isolated test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            config_dir = tmp_path / "config"
            config_dir.mkdir()
            db_path = tmp_path / "test.db"
            repo_path = tmp_path / "repos" / "test-repo"
            repo_path.mkdir(parents=True)

            # Create fake .git directory
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            # Initialize database
            db_manager = sqlmodel_manager.SQLModelDatabaseManager(db_path)
            await db_manager.initialize()

            # Initialize config manager
            config_manager = async_config.AsyncConfigManager(config_dir)
            await config_manager.generate_default_config()

            # Initialize components
            git_manager = async_git.AsyncGitManager()
            repo_registry = async_registry.AsyncRepositoryRegistry(
                config_manager, db_manager
            )
            synchronizer = async_sync.AsyncRepositorySynchronizer(
                config_manager, repo_registry, git_manager
            )

            try:
                # Create repository config
                repo_config = config.RepositoryConfig(
                    name="test-repo",
                    source={
                        "url": "https://github.com/test/repo.git",
                        "type": "git",
                        "path": str(repo_path),
                    },
                )

                # Simulate repo add command: add to config and register in database
                current_config = await config_manager.load_configuration()
                current_config.repos.append(repo_config)
                await config_manager.save_configuration(current_config)
                await repo_registry.register_repository(repo_config)

                # Mock the sync operation
                with (
                    mock.patch.object(
                        synchronizer.git_manager,
                        "run_in_executor",
                        return_value={"success": True, "commits_after": 10},
                    ),
                    mock.patch.object(
                        synchronizer,
                        "_update_registry_after_sync",
                    ),
                ):
                    # This should not fail with "Repository not found in database"
                    result = await synchronizer.sync_repository("test-repo")

                assert result.success is True
                assert result.error is None

            finally:
                # Cleanup
                await db_manager.close()
                git_manager.shutdown()

    @pytest.mark.asyncio
    async def test_sync_auto_heals_missing_database_entry(self):
        """Test that sync command auto-heals when repository is missing from database."""
        # Create completely isolated test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            config_dir = tmp_path / "config"
            config_dir.mkdir()
            db_path = tmp_path / "test.db"
            repo_path = tmp_path / "repos" / "test-repo"
            repo_path.mkdir(parents=True)

            # Create fake .git directory
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            # Initialize database
            db_manager = sqlmodel_manager.SQLModelDatabaseManager(db_path)
            await db_manager.initialize()

            # Initialize config manager
            config_manager = async_config.AsyncConfigManager(config_dir)
            await config_manager.generate_default_config()

            # Initialize components
            repo_registry = async_registry.AsyncRepositoryRegistry(
                config_manager, db_manager
            )

            try:
                # Create repository config
                repo_config = config.RepositoryConfig(
                    name="test-repo",
                    source={
                        "url": "https://github.com/test/repo.git",
                        "type": "git",
                        "path": str(repo_path),
                    },
                )

                # Simulate old behavior: only add to config, don't register in database
                current_config = await config_manager.load_configuration()
                current_config.repos.append(repo_config)
                await config_manager.save_configuration(current_config)

                # Test the auto-registration directly through update_repository_stats
                # This should auto-register the repository if it doesn't exist in the database
                success = await repo_registry.update_repository_stats(
                    "test-repo", 10, 5
                )
                assert success is True

                # Verify repository has the correct stats (proving it was registered and updated)
                state = await repo_registry.get_repository_state("test-repo")
                assert state["commit_count"] == 10
                assert state["branch_count"] == 5

            finally:
                # Cleanup
                await db_manager.close()

    @pytest.mark.asyncio
    async def test_update_repository_stats_auto_registration_integration(self):
        """Test that update_repository_stats auto-registers repositories."""
        # Create completely isolated test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            config_dir = tmp_path / "config"
            config_dir.mkdir()
            db_path = tmp_path / "test.db"
            repo_path = tmp_path / "repos" / "test-repo"
            repo_path.mkdir(parents=True)

            # Create fake .git directory
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            # Initialize database
            db_manager = sqlmodel_manager.SQLModelDatabaseManager(db_path)
            await db_manager.initialize()

            # Initialize config manager
            config_manager = async_config.AsyncConfigManager(config_dir)
            await config_manager.generate_default_config()

            # Initialize components
            repo_registry = async_registry.AsyncRepositoryRegistry(
                config_manager, db_manager
            )

            try:
                # Create repository config
                repo_config = config.RepositoryConfig(
                    name="test-repo",
                    source={
                        "url": "https://github.com/test/repo.git",
                        "type": "git",
                        "path": str(repo_path),
                    },
                )

                # Add to config but don't register in database
                current_config = await config_manager.load_configuration()
                current_config.repos.append(repo_config)
                await config_manager.save_configuration(current_config)

                # Call update_repository_stats directly (this is what sync calls)
                # This should auto-register the repository and update stats
                success = await repo_registry.update_repository_stats(
                    "test-repo", 100, 5
                )
                assert success is True

                # Verify repository has the correct stats (proving it was registered and updated)
                state = await repo_registry.get_repository_state("test-repo")
                assert state["commit_count"] == 100
                assert state["branch_count"] == 5

            finally:
                # Cleanup
                await db_manager.close()
