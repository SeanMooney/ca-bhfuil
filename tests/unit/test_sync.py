"""Tests for repository synchronization functionality."""

import pathlib
import tempfile
from unittest import mock

import pygit2
import pytest

from ca_bhfuil.core import config
from ca_bhfuil.core import registry
from ca_bhfuil.core import sync
from ca_bhfuil.core.models import results as results_models


class TestRepositorySynchronizer:
    """Test RepositorySynchronizer functionality."""

    @pytest.fixture
    def temp_repo_path(self):
        """Provide a temporary repository path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def mock_config_manager(self):
        """Provide a mock configuration manager."""
        return mock.Mock(spec=config.ConfigManager)

    @pytest.fixture
    def mock_repo_registry(self):
        """Provide a mock repository registry."""
        return mock.Mock(spec=registry.RepositoryRegistry)

    @pytest.fixture
    def synchronizer(self, mock_config_manager, mock_repo_registry):
        """Provide a repository synchronizer."""
        return sync.RepositorySynchronizer(mock_config_manager, mock_repo_registry)

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

    def test_synchronizer_initialization(
        self, synchronizer, mock_config_manager, mock_repo_registry
    ):
        """Test synchronizer initialization."""
        assert synchronizer.config_manager == mock_config_manager
        assert synchronizer.repo_registry == mock_repo_registry

    def test_synchronizer_default_initialization(self):
        """Test synchronizer initialization with defaults."""
        with (
            mock.patch("ca_bhfuil.core.config.get_config_manager") as mock_get_config,
            mock.patch(
                "ca_bhfuil.core.registry.get_repository_registry"
            ) as mock_get_registry,
        ):
            mock_config = mock.Mock()
            mock_registry = mock.Mock()
            mock_get_config.return_value = mock_config
            mock_get_registry.return_value = mock_registry

            synchronizer = sync.RepositorySynchronizer()

            assert synchronizer.config_manager == mock_config
            assert synchronizer.repo_registry == mock_registry

    def test_sync_repository_success(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test successful repository synchronization."""
        # Mock git directory exists
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        # Mock the sync operation
        sync_result = {
            "success": True,
            "repository": "test-repo",
            "refs_before": 10,
            "refs_after": 12,
            "new_refs": 2,
            "commits_before": 100,
            "commits_after": 105,
            "new_commits": 5,
            "remote": "origin",
        }

        with (
            mock.patch.object(synchronizer, "_perform_sync", return_value=sync_result),
            mock.patch.object(
                synchronizer, "_update_registry_after_sync"
            ) as mock_update,
        ):
            result = synchronizer.sync_repository("test-repo")

            assert result.success is True
            assert result.result == sync_result
            mock_update.assert_called_once_with(sample_repo_config, sync_result)

    def test_sync_repository_not_found_in_config(self, synchronizer):
        """Test sync when repository not found in configuration."""
        synchronizer.config_manager.get_repository_config_by_name.return_value = None

        result = synchronizer.sync_repository("nonexistent")

        assert result.success is False
        assert "not found in configuration" in result.error

    def test_sync_repository_path_not_exists(self, synchronizer, sample_repo_config):
        """Test sync when repository path doesn't exist."""
        # Use a non-existent path
        with mock.patch("pathlib.Path.exists", return_value=False):
            synchronizer.config_manager.get_repository_config_by_name.return_value = (
                sample_repo_config
            )

            result = synchronizer.sync_repository("test-repo")

            assert result.success is False
            assert "does not exist" in result.error

    def test_sync_repository_not_git_repo(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test sync when path exists but is not a git repository."""
        # Create directory but no .git subdirectory
        temp_repo_path.mkdir(exist_ok=True)

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        result = synchronizer.sync_repository("test-repo")

        assert result.success is False
        assert "Not a git repository" in result.error

    def test_sync_repository_sync_failure(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test sync when sync operation fails."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        sync_result = {
            "success": False,
            "error": "Remote not found",
        }

        with mock.patch.object(synchronizer, "_perform_sync", return_value=sync_result):
            result = synchronizer.sync_repository("test-repo")

            assert result.success is False
            assert result.result == sync_result

    def test_sync_repository_exception(self, synchronizer, sample_repo_config):
        """Test sync with unexpected exception."""
        synchronizer.config_manager.get_repository_config_by_name.side_effect = (
            Exception("Unexpected error")
        )

        result = synchronizer.sync_repository("test-repo")

        assert result.success is False
        assert "Unexpected error" in result.error

    def test_perform_sync_success(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test successful sync operation."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_remote = mock.Mock()
            mock_repo.remotes = {"origin": mock_remote}

            # Mock initial state
            mock_branches = ["main", "develop", "feature/test"]
            mock_commits = [mock.Mock() for _ in range(10)]

            # Mock post-fetch state (more branches and commits)
            mock_branches_after = mock_branches + ["feature/new", "hotfix/fix"]
            mock_commits_after = mock_commits + [mock.Mock() for _ in range(3)]

            # Mock the listall_branches method with side_effect
            def listall_branches_side_effect():
                if hasattr(listall_branches_side_effect, "call_count"):
                    listall_branches_side_effect.call_count += 1
                else:
                    listall_branches_side_effect.call_count = 1

                if listall_branches_side_effect.call_count == 1:
                    return mock_branches  # Before fetch
                return mock_branches_after  # After fetch

            mock_repo.listall_branches.side_effect = listall_branches_side_effect

            # Mock the walk method properly
            def walk_side_effect(start_commit):
                if hasattr(walk_side_effect, "call_count"):
                    walk_side_effect.call_count += 1
                else:
                    walk_side_effect.call_count = 1

                if walk_side_effect.call_count == 1:
                    return iter(mock_commits)
                return iter(mock_commits_after)

            mock_repo.walk.side_effect = walk_side_effect

            mock_repo.head.target = "head_commit"
            mock_repo_class.return_value = mock_repo

            result = synchronizer._perform_sync(sample_repo_config)

            assert result["success"] is True
            assert result["repository"] == "test-repo"
            assert result["new_refs"] == 2  # 5 - 3 = 2 new branches
            assert result["new_commits"] == 3
            mock_remote.fetch.assert_called_once()

    def test_perform_sync_no_remote(self, synchronizer, sample_repo_config):
        """Test sync when remote doesn't exist."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {}  # No remotes
            mock_repo_class.return_value = mock_repo

            result = synchronizer._perform_sync(sample_repo_config)

            assert result["success"] is False
            assert "Remote 'origin' not found" in result["error"]

    def test_perform_sync_git_error(self, synchronizer, sample_repo_config):
        """Test sync with pygit2 GitError."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo_class.side_effect = pygit2.GitError("Repository error")

            result = synchronizer._perform_sync(sample_repo_config)

            assert result["success"] is False
            assert "Git error" in result["error"]

    def test_perform_sync_unexpected_error(self, synchronizer, sample_repo_config):
        """Test sync with unexpected error."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo_class.side_effect = Exception("Unexpected error")

            result = synchronizer._perform_sync(sample_repo_config)

            assert result["success"] is False
            assert "Unexpected error" in result["error"]

    def test_update_registry_after_sync_success(self, synchronizer, sample_repo_config):
        """Test registry update after successful sync."""
        sync_result = {
            "commits_after": 105,
        }

        mock_repo_wrapper = mock.Mock()
        mock_repo_wrapper.list_branches.return_value = ["main", "develop", "feature"]

        with mock.patch(
            "ca_bhfuil.core.git.repository.Repository", return_value=mock_repo_wrapper
        ):
            synchronizer._update_registry_after_sync(sample_repo_config, sync_result)

            synchronizer.repo_registry.update_repository_stats.assert_called_once_with(
                "test-repo", 105, 3
            )

    def test_update_registry_after_sync_exception(
        self, synchronizer, sample_repo_config
    ):
        """Test registry update with exception (should not fail)."""
        sync_result = {"commits_after": 105}

        with mock.patch(
            "ca_bhfuil.core.git.repository.Repository",
            side_effect=Exception("Registry error"),
        ):
            # Should not raise exception
            synchronizer._update_registry_after_sync(sample_repo_config, sync_result)

    def test_sync_all_repositories_success(self, synchronizer):
        """Test syncing all repositories."""
        repo1 = config.RepositoryConfig(name="repo1", source={"url": "url1"})
        repo2 = config.RepositoryConfig(name="repo2", source={"url": "url2"})
        global_config = config.GlobalConfig(repos=[repo1, repo2])

        synchronizer.config_manager.load_configuration.return_value = global_config

        # Mock sync results
        result1 = results_models.OperationResult(success=True, duration=1.0, result={})
        result2 = results_models.OperationResult(
            success=False, duration=0.5, error="Sync failed"
        )

        with mock.patch.object(
            synchronizer, "sync_repository", side_effect=[result1, result2]
        ):
            results = synchronizer.sync_all_repositories()

            assert len(results) == 2
            assert results[0].success is True
            assert results[1].success is False

    def test_sync_all_repositories_empty(self, synchronizer):
        """Test syncing when no repositories configured."""
        global_config = config.GlobalConfig(repos=[])
        synchronizer.config_manager.load_configuration.return_value = global_config

        results = synchronizer.sync_all_repositories()

        assert len(results) == 0

    def test_get_sync_status_success(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test getting sync status for repository."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {"origin": mock.Mock()}
            mock_repo.head.shorthand = "main"
            mock_repo.head.target = "commit123"
            mock_repo_class.return_value = mock_repo

            with mock.patch("pathlib.Path.stat") as mock_stat:
                mock_stat_result = mock.Mock()
                mock_stat_result.st_mtime = 1640995200
                mock_stat.return_value = mock_stat_result

                status = synchronizer.get_sync_status("test-repo")

                assert status["repository"] == "test-repo"
                assert status["exists"] is True
                assert status["can_sync"] is True
                assert status["has_remote"] is True
                assert status["head_ref"] == "main"
                assert status["head_commit"] == "commit123"

    def test_get_sync_status_not_found_in_config(self, synchronizer):
        """Test sync status when repository not in configuration."""
        synchronizer.config_manager.get_repository_config_by_name.return_value = None

        status = synchronizer.get_sync_status("nonexistent")

        assert status["success"] is False
        assert "not found in configuration" in status["error"]

    def test_get_sync_status_path_not_exists(self, synchronizer, sample_repo_config):
        """Test sync status when repository path doesn't exist."""
        # Mock that the repository path doesn't exist
        with mock.patch("pathlib.Path.exists", return_value=False):
            synchronizer.config_manager.get_repository_config_by_name.return_value = (
                sample_repo_config
            )

            status = synchronizer.get_sync_status("test-repo")

            assert status["repository"] == "test-repo"
            assert status["exists"] is False
            assert status["can_sync"] is False

    def test_get_sync_status_not_git_repo(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test sync status when path exists but not a git repository."""
        temp_repo_path.mkdir(exist_ok=True)
        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        status = synchronizer.get_sync_status("test-repo")

        assert status["repository"] == "test-repo"
        assert status["exists"] is True
        assert status["can_sync"] is False
        assert "Not a git repository" in status["reason"]

    def test_get_sync_status_no_remote(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test sync status when repository has no remote."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {}  # No remotes
            mock_repo_class.return_value = mock_repo

            status = synchronizer.get_sync_status("test-repo")

            assert status["can_sync"] is False
            assert status["has_remote"] is False

    def test_get_sync_status_no_head(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test sync status when repository has no HEAD."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {"origin": mock.Mock()}
            mock_repo.head = None
            mock_repo_class.return_value = mock_repo

            status = synchronizer.get_sync_status("test-repo")

            assert status["head_ref"] is None
            assert status["head_commit"] is None

    def test_get_sync_status_exception(self, synchronizer):
        """Test sync status with exception."""
        synchronizer.config_manager.get_repository_config_by_name.side_effect = (
            Exception("Status error")
        )

        status = synchronizer.get_sync_status("test-repo")

        assert status["repository"] == "test-repo"
        assert status["success"] is False
        assert "Status error" in status["error"]

    def test_check_for_updates_success(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test checking for updates."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {"origin": mock.Mock()}
            mock_repo.head.target = "current_commit"
            mock_repo_class.return_value = mock_repo

            result = synchronizer.check_for_updates("test-repo")

            assert result["repository"] == "test-repo"
            assert result["can_check"] is True
            assert result["head_commit"] == "current_commit"

    def test_check_for_updates_not_found_in_config(self, synchronizer):
        """Test checking updates when repository not in configuration."""
        synchronizer.config_manager.get_repository_config_by_name.return_value = None

        result = synchronizer.check_for_updates("nonexistent")

        assert result["success"] is False
        assert "not found in configuration" in result["error"]

    def test_check_for_updates_not_available(self, synchronizer, sample_repo_config):
        """Test checking updates when repository not available locally."""
        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        result = synchronizer.check_for_updates("test-repo")

        assert result["repository"] == "test-repo"
        assert result["can_check"] is False
        assert "not available locally" in result["reason"]

    def test_check_for_updates_no_remote(
        self, synchronizer, sample_repo_config, temp_repo_path
    ):
        """Test checking updates when repository has no remote."""
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir()

        synchronizer.config_manager.get_repository_config_by_name.return_value = (
            sample_repo_config
        )

        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo.remotes = {}
            mock_repo_class.return_value = mock_repo

            result = synchronizer.check_for_updates("test-repo")

            assert result["can_check"] is False
            assert "Remote 'origin' not found" in result["reason"]

    def test_check_for_updates_exception(self, synchronizer):
        """Test checking updates with exception."""
        synchronizer.config_manager.get_repository_config_by_name.side_effect = (
            Exception("Update check error")
        )

        result = synchronizer.check_for_updates("test-repo")

        assert result["repository"] == "test-repo"
        assert result["success"] is False
        assert "Update check error" in result["error"]


class TestRepositorySynchronizerGlobalInstance:
    """Test global repository synchronizer instance."""

    def test_get_repository_synchronizer(self):
        """Test getting global repository synchronizer."""
        sync1 = sync.get_repository_synchronizer()
        sync2 = sync.get_repository_synchronizer()

        # Should return the same instance
        assert sync1 is sync2
        assert isinstance(sync1, sync.RepositorySynchronizer)
