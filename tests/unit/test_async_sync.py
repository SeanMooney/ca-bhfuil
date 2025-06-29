"""Tests for async repository synchronization functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_registry
from ca_bhfuil.core import async_sync
from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.models import results as results_models


class TestAsyncRepositorySynchronizer:
    """Test AsyncRepositorySynchronizer functionality."""

    @pytest.fixture
    def temp_repo_path(self):
        """Provide a temporary repository path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def mock_config_manager(self):
        """Provide a mock async configuration manager."""
        return mock.AsyncMock(spec=async_config.AsyncConfigManager)

    @pytest.fixture
    def mock_repo_registry(self):
        """Provide a mock async repository registry."""
        return mock.AsyncMock(spec=async_registry.AsyncRepositoryRegistry)

    @pytest.fixture
    def mock_git_manager(self):
        """Provide a mock async git manager."""
        return mock.AsyncMock(spec=async_git.AsyncGitManager)

    @pytest.fixture
    def async_synchronizer(
        self, mock_config_manager, mock_repo_registry, mock_git_manager
    ):
        """Provide an async repository synchronizer."""
        return async_sync.AsyncRepositorySynchronizer(
            mock_config_manager, mock_repo_registry, mock_git_manager
        )

    @pytest.fixture
    def sample_repo_config(self, temp_repo_path):
        """Provide a sample repository configuration."""
        repo_config = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        # Mock the repo_path property
        with mock.patch.object(
            type(repo_config), "repo_path", new_callable=mock.PropertyMock
        ) as mock_path:
            mock_path.return_value = temp_repo_path
            yield repo_config

    def test_async_synchronizer_initialization(
        self,
        async_synchronizer,
        mock_config_manager,
        mock_repo_registry,
        mock_git_manager,
    ):
        """Test async synchronizer initialization."""
        assert async_synchronizer.config_manager == mock_config_manager
        assert async_synchronizer.repo_registry == mock_repo_registry
        assert async_synchronizer.git_manager == mock_git_manager
        assert async_synchronizer._sync_semaphore._value == 3

    def test_async_synchronizer_default_initialization(self):
        """Test async synchronizer initialization with defaults."""
        with (
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_config_class,
            mock.patch(
                "ca_bhfuil.core.async_registry.AsyncRepositoryRegistry"
            ) as mock_registry_class,
            mock.patch(
                "ca_bhfuil.core.git.async_git.AsyncGitManager"
            ) as mock_git_class,
        ):
            mock_config = mock.AsyncMock()
            mock_registry = mock.AsyncMock()
            mock_git = mock.AsyncMock()
            mock_config_class.return_value = mock_config
            mock_registry_class.return_value = mock_registry
            mock_git_class.return_value = mock_git

            synchronizer = async_sync.AsyncRepositorySynchronizer()

            assert synchronizer.config_manager == mock_config
            assert synchronizer.repo_registry == mock_registry
            assert synchronizer.git_manager == mock_git

    @pytest.mark.asyncio
    async def test_sync_repository_success(
        self, async_synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test successful async repository synchronization."""
        # Mock git directory exists
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        async_synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        # Mock the sync operation
        sync_result = {
            "success": True,
            "repository": "test-repo",
            "new_refs": 2,
            "new_commits": 5,
        }

        with (
            mock.patch.object(
                async_synchronizer.git_manager,
                "run_in_executor",
                return_value=sync_result,
            ),
            mock.patch.object(
                async_synchronizer, "_update_registry_after_sync"
            ) as mock_update,
        ):
            result = await async_synchronizer.sync_repository("test-repo")

            assert result.success is True
            assert result.result == sync_result
            mock_update.assert_called_once_with(sample_repo_config, sync_result)

    @pytest.mark.asyncio
    async def test_sync_repository_not_found_in_config(self, async_synchronizer):
        """Test async sync when repository not found in configuration."""
        async_synchronizer.config_manager.get_repository_config_by_name.return_value = (
            None
        )

        result = await async_synchronizer.sync_repository("nonexistent")

        assert result.success is False
        assert "not found in configuration" in result.error

    @pytest.mark.asyncio
    async def test_sync_repository_path_not_exists(
        self, async_synchronizer, sample_repo_config
    ):
        """Test async sync when repository path doesn't exist."""
        # Mock path doesn't exist by patching pathlib.Path.exists
        with mock.patch("pathlib.Path.exists", return_value=False):
            async_synchronizer.config_manager.get_repository_config_by_name.return_value = sample_repo_config

            result = await async_synchronizer.sync_repository("test-repo")

            assert result.success is False
            assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_sync_repository_not_git_repo(
        self, async_synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test async sync when path exists but is not a git repository."""
        # Create directory but no .git subdirectory
        temp_repo_path.mkdir(exist_ok=True)

        async_synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        result = await async_synchronizer.sync_repository("test-repo")

        assert result.success is False
        assert "Not a git repository" in result.error

    @pytest.mark.asyncio
    async def test_sync_repository_sync_failure(
        self, async_synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test async sync when sync operation fails."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        async_synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        sync_result = {
            "success": False,
            "error": "Remote not found",
        }

        with mock.patch.object(
            async_synchronizer.git_manager, "run_in_executor", return_value=sync_result
        ):
            result = await async_synchronizer.sync_repository("test-repo")

            assert result.success is False
            assert result.result == sync_result

    @pytest.mark.asyncio
    async def test_sync_repository_exception(self, async_synchronizer):
        """Test async sync with unexpected exception."""
        async_synchronizer.config_manager.get_repository_config_by_name.side_effect = (
            Exception("Unexpected error")
        )

        result = await async_synchronizer.sync_repository("test-repo")

        assert result.success is False
        assert "Unexpected error" in result.error

    def test_perform_sync_sync_integration(
        self, async_synchronizer, sample_repo_config
    ):
        """Test the sync manager integration."""
        # This tests the _perform_sync_sync method that delegates to sync manager
        with mock.patch(
            "ca_bhfuil.core.async_sync.AsyncRepositorySynchronizer._perform_sync_sync",
            return_value={"success": True},
        ):
            result = async_synchronizer._perform_sync_sync(sample_repo_config)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_registry_after_sync_success(
        self, async_synchronizer, sample_repo_config
    ):
        """Test async registry update after successful sync."""
        sync_result = {"commits_after": 105}

        mock_repo_wrapper = mock.Mock()
        mock_repo_wrapper.list_branches.return_value = ["main", "develop", "feature"]

        with mock.patch(
            "ca_bhfuil.core.git.repository.Repository", return_value=mock_repo_wrapper
        ):
            async_synchronizer.git_manager.run_in_executor.side_effect = [
                mock_repo_wrapper,  # Repository creation
                ["main", "develop", "feature"],  # list_branches call
            ]

            await async_synchronizer._update_registry_after_sync(
                sample_repo_config, sync_result
            )

            async_synchronizer.repo_registry.update_repository_stats.assert_called_once_with(
                "test-repo", 105, 3
            )

    @pytest.mark.asyncio
    async def test_update_registry_after_sync_exception(
        self, async_synchronizer, sample_repo_config
    ):
        """Test async registry update with exception (should not fail)."""
        sync_result = {"commits_after": 105}

        async_synchronizer.git_manager.run_in_executor.side_effect = Exception(
            "Registry error"
        )

        # Should not raise exception
        await async_synchronizer._update_registry_after_sync(
            sample_repo_config, sync_result
        )

    @pytest.mark.asyncio
    async def test_sync_repositories_concurrently_success(self, async_synchronizer):
        """Test concurrent synchronization of multiple repositories."""
        repo_names = ["repo1", "repo2", "repo3"]

        # Mock successful results
        success_result = results_models.OperationResult(
            success=True, duration=1.0, result={}
        )

        with mock.patch.object(
            async_synchronizer, "sync_repository", return_value=success_result
        ):
            results = await async_synchronizer.sync_repositories_concurrently(
                repo_names
            )

            assert len(results) == 3
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_sync_repositories_concurrently_with_failures(
        self, async_synchronizer
    ):
        """Test concurrent synchronization with some failures."""
        repo_names = ["repo1", "repo2", "repo3"]

        # Mock mixed results
        def mock_sync_side_effect(repo_name):
            if repo_name == "repo2":
                return results_models.OperationResult(
                    success=False, duration=0.5, error="Sync failed"
                )
            return results_models.OperationResult(success=True, duration=1.0, result={})

        with mock.patch.object(
            async_synchronizer, "sync_repository", side_effect=mock_sync_side_effect
        ):
            results = await async_synchronizer.sync_repositories_concurrently(
                repo_names
            )

            assert len(results) == 3
            assert results[0].success is True
            assert results[1].success is False
            assert results[2].success is True

    @pytest.mark.asyncio
    async def test_sync_repositories_concurrently_with_exceptions(
        self, async_synchronizer
    ):
        """Test concurrent synchronization with exceptions."""
        repo_names = ["repo1", "repo2"]

        async def mock_sync_side_effect(repo_name):
            if repo_name == "repo1":
                raise Exception("Sync exception")
            return results_models.OperationResult(success=True, duration=1.0, result={})

        with mock.patch.object(
            async_synchronizer, "sync_repository", side_effect=mock_sync_side_effect
        ):
            results = await async_synchronizer.sync_repositories_concurrently(
                repo_names
            )

            assert len(results) == 2
            assert results[0].success is False  # Exception converted to failed result
            assert "Exception during sync" in results[0].error
            assert results[1].success is True

    @pytest.mark.asyncio
    async def test_sync_all_repositories_success(self, async_synchronizer):
        """Test syncing all repositories."""
        repo1 = config.RepositoryConfig(name="repo1", source={"url": "url1"})
        repo2 = config.RepositoryConfig(name="repo2", source={"url": "url2"})
        global_config = config.GlobalConfig(repos=[repo1, repo2])

        async_synchronizer.config_manager.load_configuration.return_value = (
            global_config
        )

        # Mock sync results
        success_result = results_models.OperationResult(
            success=True, duration=1.0, result={}
        )

        with mock.patch.object(
            async_synchronizer,
            "sync_repositories_concurrently",
            return_value=[success_result, success_result],
        ):
            results = await async_synchronizer.sync_all_repositories()

            assert len(results) == 2
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_sync_all_repositories_empty(self, async_synchronizer):
        """Test syncing when no repositories configured."""
        global_config = config.GlobalConfig(repos=[])
        async_synchronizer.config_manager.load_configuration.return_value = (
            global_config
        )

        results = await async_synchronizer.sync_all_repositories()

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_sync_status_success(self, async_synchronizer):
        """Test getting sync status."""
        expected_status = {
            "repository": "test-repo",
            "success": True,
            "exists": True,
            "is_git_repo": True,
            "registered": True,
            "last_analyzed": "2025-06-29T12:00:00",
            "commit_count": 100,
            "branch_count": 5,
        }

        with mock.patch.object(
            async_synchronizer.repo_registry,
            "get_repository_state",
            return_value=expected_status,
        ):
            status = await async_synchronizer.get_sync_status("test-repo")

        assert status == expected_status

    @pytest.mark.asyncio
    async def test_get_sync_status_exception(self, async_synchronizer):
        """Test getting sync status with exception."""
        async_synchronizer.repo_registry.get_repository_state.side_effect = Exception(
            "Status error"
        )

        status = await async_synchronizer.get_sync_status("test-repo")

        assert status["repository"] == "test-repo"
        assert status["success"] is False
        assert "Status error" in status["error"]

    @pytest.mark.asyncio
    async def test_check_for_updates_success(self, async_synchronizer):
        """Test checking for updates."""
        repo_config = config.RepositoryConfig(
            name="test-repo", source={"url": "https://github.com/test/repo.git"}
        )
        with (
            mock.patch.object(
                async_synchronizer.config_manager,
                "get_repository_config_by_name",
                return_value=repo_config,
            ),
            mock.patch("pathlib.Path.exists", return_value=True),
        ):
            result = await async_synchronizer.check_for_updates("test-repo")

        assert result["success"] is True
        assert result["updates_available"] is False

    @pytest.mark.asyncio
    async def test_check_for_updates_exception(self, async_synchronizer):
        """Test checking for updates with exception."""
        async_synchronizer.config_manager.get_repository_config_by_name.side_effect = (
            Exception("Update check error")
        )

        result = await async_synchronizer.check_for_updates("test-repo")

        assert result["repository"] == "test-repo"
        assert result["success"] is False
        assert "Update check error" in result["error"]

    @pytest.mark.asyncio
    async def test_get_all_sync_status_success(self, async_synchronizer):
        """Test getting sync status for all repositories."""
        repo1 = config.RepositoryConfig(name="repo1", source={"url": "url1"})
        repo2 = config.RepositoryConfig(name="repo2", source={"url": "url2"})
        global_config = config.GlobalConfig(repos=[repo1, repo2])

        async_synchronizer.config_manager.load_configuration.return_value = (
            global_config
        )

        status1 = {"repository": "repo1", "can_sync": True}
        status2 = {"repository": "repo2", "can_sync": False}

        with mock.patch.object(
            async_synchronizer, "get_sync_status", side_effect=[status1, status2]
        ):
            status_list = await async_synchronizer.get_all_sync_status()

            assert len(status_list) == 2
            assert status_list[0] == status1
            assert status_list[1] == status2

    @pytest.mark.asyncio
    async def test_get_all_sync_status_empty(self, async_synchronizer):
        """Test getting sync status when no repositories configured."""
        global_config = config.GlobalConfig(repos=[])
        async_synchronizer.config_manager.load_configuration.return_value = (
            global_config
        )

        status_list = await async_synchronizer.get_all_sync_status()

        assert len(status_list) == 0

    @pytest.mark.asyncio
    async def test_get_all_sync_status_with_exceptions(self, async_synchronizer):
        """Test getting sync status with some exceptions."""
        repo1 = config.RepositoryConfig(name="repo1", source={"url": "url1"})
        repo2 = config.RepositoryConfig(name="repo2", source={"url": "url2"})
        global_config = config.GlobalConfig(repos=[repo1, repo2])

        async_synchronizer.config_manager.load_configuration.return_value = (
            global_config
        )

        async def mock_status_side_effect(repo_name):
            if repo_name == "repo1":
                raise Exception("Status error")
            return {"repository": repo_name, "can_sync": True}

        with mock.patch.object(
            async_synchronizer, "get_sync_status", side_effect=mock_status_side_effect
        ):
            status_list = await async_synchronizer.get_all_sync_status()

            assert len(status_list) == 2
            assert status_list[0]["repository"] == "repo1"
            assert status_list[0]["success"] is False
            assert status_list[1]["repository"] == "repo2"
            assert status_list[1]["can_sync"] is True

    @pytest.mark.asyncio
    async def test_get_sync_summary_success(self, async_synchronizer):
        """Test getting sync summary."""
        status_list = [
            {"repository": "repo1", "can_sync": True, "success": True},
            {"repository": "repo2", "can_sync": False, "success": True},
            {"repository": "repo3", "can_sync": True, "success": False},
        ]

        registry_stats = {
            "total_commits": 1000,
            "total_branches": 50,
        }

        with (
            mock.patch.object(
                async_synchronizer, "get_all_sync_status", return_value=status_list
            ),
            mock.patch.object(
                async_synchronizer.repo_registry,
                "get_registry_stats",
                return_value=registry_stats,
            ),
        ):
            summary = await async_synchronizer.get_sync_summary()

            assert summary["total_repositories"] == 3
            assert summary["can_sync"] == 2
            assert summary["cannot_sync"] == 1
            assert summary["has_errors"] == 1
            assert summary["registry_stats"] == registry_stats
            assert "last_check" in summary

    def test_shutdown(self, async_synchronizer):
        """Test async synchronizer shutdown."""
        async_synchronizer.shutdown()
        async_synchronizer.git_manager.shutdown.assert_called_once()


class TestAsyncRepositorySynchronizerGlobalInstance:
    """Test global async repository synchronizer instance."""

    @pytest.mark.asyncio
    async def test_get_async_repository_synchronizer(self):
        """Test getting global async repository synchronizer."""
        sync1 = await async_sync.get_async_repository_synchronizer()
        sync2 = await async_sync.get_async_repository_synchronizer()

        # Should return the same instance
        assert sync1 is sync2
        assert isinstance(sync1, async_sync.AsyncRepositorySynchronizer)
