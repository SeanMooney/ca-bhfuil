"""Tests for async repository manager functionality."""

import pathlib
import tempfile
from unittest import mock

import pygit2
import pytest

from ca_bhfuil.core import async_repository
from ca_bhfuil.core import config
from ca_bhfuil.core.git import repository as repository_module
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.core.models import results as results_models


class TestAsyncRepositoryManager:
    """Test AsyncRepositoryManager core functionality."""

    @pytest.fixture
    def temp_repo_path(self):
        """Provide a temporary repository path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def async_repo_manager(self):
        """Provide an async repository manager."""
        return async_repository.AsyncRepositoryManager(max_concurrent_tasks=3)

    @pytest.fixture
    def sample_commit_info(self):
        """Provide a sample commit info object."""
        return commit_models.CommitInfo(
            sha="abc123def456789",
            short_sha="abc123d",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date="2024-01-01T12:00:00+00:00",
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date="2024-01-01T12:00:00+00:00",
            parents=["parent123"],
        )

    def test_async_repository_manager_initialization(self, async_repo_manager):
        """Test async repository manager initialization."""
        assert async_repo_manager._semaphore._value == 3
        assert async_repo_manager.git_manager is not None

    @pytest.mark.asyncio
    async def test_run_concurrently_success(self, async_repo_manager):
        """Test concurrent task execution with successful tasks."""

        async def mock_task(value):
            return value * 2

        tasks = [mock_task(1), mock_task(2), mock_task(3)]
        results = await async_repo_manager.run_concurrently(tasks)

        assert results == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_run_concurrently_with_exceptions(self, async_repo_manager):
        """Test concurrent task execution with exceptions."""

        async def success_task():
            return "success"

        async def failing_task():
            raise ValueError("Task failed")

        tasks = [success_task(), failing_task(), success_task()]
        results = await async_repo_manager.run_concurrently(tasks)

        assert len(results) == 3
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert results[2] == "success"

    @pytest.mark.asyncio
    async def test_detect_repository_success(self, async_repo_manager, temp_repo_path):
        """Test successful repository detection."""
        # Mock the discovery and validation
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            # First call returns discovered path, second call returns validation
            mock_executor.side_effect = [
                str(temp_repo_path),  # _discover_repository
                True,  # _validate_repository
            ]

            result = await async_repo_manager.detect_repository(temp_repo_path)

            assert result.success is True
            assert result.result["repository_path"] == str(temp_repo_path)
            assert result.duration > 0

    @pytest.mark.asyncio
    async def test_detect_repository_not_found(
        self, async_repo_manager, temp_repo_path
    ):
        """Test repository detection when no repository found."""
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.return_value = None  # No repository found

            result = await async_repo_manager.detect_repository(temp_repo_path)

            assert result.success is False
            assert "No git repository found" in result.error

    @pytest.mark.asyncio
    async def test_detect_repository_invalid(self, async_repo_manager, temp_repo_path):
        """Test repository detection with invalid repository."""
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.side_effect = [
                str(temp_repo_path),  # Found but invalid
                False,  # Validation fails
            ]

            result = await async_repo_manager.detect_repository(temp_repo_path)

            assert result.success is False
            assert "Invalid repository found" in result.error

    @pytest.mark.asyncio
    async def test_detect_repository_exception(
        self, async_repo_manager, temp_repo_path
    ):
        """Test repository detection with exception."""
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.side_effect = pygit2.GitError("Git error")

            result = await async_repo_manager.detect_repository(temp_repo_path)

            assert result.success is False
            assert "Git error" in result.error

    @pytest.mark.asyncio
    async def test_get_repository_info_success(
        self, async_repo_manager, temp_repo_path
    ):
        """Test getting repository information."""
        mock_info = {
            "path": str(temp_repo_path),
            "branches": ["main", "develop"],
            "head": "main",
        }

        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.return_value = mock_info

            result = await async_repo_manager.get_repository_info(temp_repo_path)

            assert result.success is True
            assert result.result == mock_info

    @pytest.mark.asyncio
    async def test_get_repository_info_exception(
        self, async_repo_manager, temp_repo_path
    ):
        """Test getting repository information with exception."""
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.side_effect = Exception("Info error")

            result = await async_repo_manager.get_repository_info(temp_repo_path)

            assert result.success is False
            assert "Info error" in result.error

    @pytest.mark.asyncio
    async def test_get_repository_success(self, async_repo_manager, temp_repo_path):
        """Test getting repository wrapper."""
        mock_repo = mock.Mock(spec=repository_module.Repository)

        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.return_value = mock_repo

            result = await async_repo_manager.get_repository(temp_repo_path)

            assert result.success is True
            assert result.result == mock_repo

    @pytest.mark.asyncio
    async def test_get_repository_exception(self, async_repo_manager, temp_repo_path):
        """Test getting repository wrapper with exception."""
        with mock.patch.object(
            async_repo_manager.git_manager, "run_in_executor"
        ) as mock_executor:
            mock_executor.side_effect = pygit2.GitError("Repository error")

            result = await async_repo_manager.get_repository(temp_repo_path)

            assert result.success is False
            assert "Repository error" in result.error

    @pytest.mark.asyncio
    async def test_lookup_commit_success(
        self, async_repo_manager, temp_repo_path, sample_commit_info
    ):
        """Test successful commit lookup."""
        mock_repo = mock.Mock(spec=repository_module.Repository)
        mock_repo.get_commit.return_value = sample_commit_info

        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )

            with mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor:
                mock_executor.return_value = sample_commit_info

                result = await async_repo_manager.lookup_commit(
                    temp_repo_path, "abc123"
                )

                assert result.success is True
                assert result.result == sample_commit_info

    @pytest.mark.asyncio
    async def test_lookup_commit_not_found(self, async_repo_manager, temp_repo_path):
        """Test commit lookup when commit not found."""
        mock_repo = mock.Mock(spec=repository_module.Repository)

        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )

            with mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor:
                mock_executor.return_value = None

                result = await async_repo_manager.lookup_commit(
                    temp_repo_path, "nonexistent"
                )

                assert result.success is False
                assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_lookup_commit_repository_error(
        self, async_repo_manager, temp_repo_path
    ):
        """Test commit lookup when repository loading fails."""
        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=False, duration=0.1, error="Repository not found"
            )

            result = await async_repo_manager.lookup_commit(temp_repo_path, "abc123")

            assert result.success is False
            assert "Repository not found" in result.error

    @pytest.mark.asyncio
    async def test_search_commits_success(
        self, async_repo_manager, temp_repo_path, sample_commit_info
    ):
        """Test successful commit search."""
        mock_repo = mock.Mock(spec=repository_module.Repository)

        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )

            with mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor:
                mock_executor.return_value = [sample_commit_info]

                result = await async_repo_manager.search_commits(
                    temp_repo_path, "test", 10
                )

                assert result.success is True
                assert len(result.matches) == 1
                assert result.matches[0] == sample_commit_info

    @pytest.mark.asyncio
    async def test_search_commits_no_results(self, async_repo_manager, temp_repo_path):
        """Test commit search with no results."""
        mock_repo = mock.Mock(spec=repository_module.Repository)

        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )

            with mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor:
                mock_executor.return_value = []

                result = await async_repo_manager.search_commits(
                    temp_repo_path, "nonexistent", 10
                )

                assert result.success is True
                assert len(result.matches) == 0

    @pytest.mark.asyncio
    async def test_search_commits_repository_error(
        self, async_repo_manager, temp_repo_path
    ):
        """Test commit search when repository loading fails."""
        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=False, duration=0.1, error="Repository error"
            )

            result = await async_repo_manager.search_commits(temp_repo_path, "test", 10)

            assert result.success is False
            assert "Repository error" in result.error

    @pytest.mark.asyncio
    async def test_get_branches_success(self, async_repo_manager, temp_repo_path):
        """Test successful branch retrieval."""
        mock_repo = mock.Mock(spec=repository_module.Repository)
        mock_branches = ["main", "develop", "feature/test"]

        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )

            with mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor:
                mock_executor.return_value = mock_branches

                result = await async_repo_manager.get_branches(temp_repo_path)

                assert result.success is True
                assert result.result == mock_branches

    @pytest.mark.asyncio
    async def test_get_branches_repository_error(
        self, async_repo_manager, temp_repo_path
    ):
        """Test branch retrieval when repository loading fails."""
        with mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo:
            mock_get_repo.return_value = results_models.OperationResult(
                success=False, duration=0.1, error="Repository error"
            )

            result = await async_repo_manager.get_branches(temp_repo_path)

            assert result.success is False
            assert "Repository error" in result.error

    def test_discover_repository_success(self, async_repo_manager, temp_repo_path):
        """Test the sync discover repository method."""
        # Create a .git directory to simulate a git repository
        git_dir = temp_repo_path / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)

        result = async_repo_manager._discover_repository(temp_repo_path)

        # Use resolve() to handle path symlinks (like /private/var vs /var on macOS)
        assert result.resolve() == temp_repo_path.resolve()

    def test_discover_repository_not_found(self, async_repo_manager, temp_repo_path):
        """Test discover repository when none found."""
        # Don't create any .git directory - should return None
        result = async_repo_manager._discover_repository(temp_repo_path)

        assert result is None

    def test_discover_repository_exception(self, async_repo_manager, temp_repo_path):
        """Test discover repository with exception."""
        # Mock pathlib.Path to raise an exception during resolve
        with mock.patch("pathlib.Path.resolve", side_effect=OSError("Path error")):
            result = async_repo_manager._discover_repository(temp_repo_path)

            assert result is None

    def test_validate_repository_success(self, async_repo_manager, temp_repo_path):
        """Test repository validation success."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()
            mock_repo_class.return_value = mock_repo

            result = async_repo_manager._validate_repository(temp_repo_path)

            assert result is True

    def test_validate_repository_failure(self, async_repo_manager, temp_repo_path):
        """Test repository validation failure."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo_class.side_effect = pygit2.GitError("Invalid repository")

            result = async_repo_manager._validate_repository(temp_repo_path)

            assert result is False

    def test_get_repository_info_sync(self, async_repo_manager, temp_repo_path):
        """Test the sync get repository info method."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()

            # Mock branches properly
            mock_branches = mock.Mock()
            mock_branches.local = ["main", "develop"]
            mock_branches.remote = ["origin/main"]
            mock_repo.branches = mock_branches

            # Mock remotes
            mock_remote = mock.Mock()
            mock_remote.name = "origin"
            mock_repo.remotes = [mock_remote]

            # Mock head info
            mock_repo.head_is_unborn = False
            mock_repo.head.shorthand = "main"
            mock_repo.head.target = "abc123"

            mock_repo_class.return_value = mock_repo

            result = async_repo_manager._get_repository_info(temp_repo_path)

            assert "path" in result
            assert "head_branch" in result
            assert "local_branches" in result
            assert result["path"] == str(temp_repo_path)
            assert result["local_branches"] == 2
            assert result["head_branch"] == "main"

    def test_get_repository_info_sync_no_head(self, async_repo_manager, temp_repo_path):
        """Test get repository info when repository has no HEAD."""
        with mock.patch("pygit2.Repository") as mock_repo_class:
            mock_repo = mock.Mock()

            # Mock empty branches
            mock_branches = mock.Mock()
            mock_branches.local = []
            mock_branches.remote = []
            mock_repo.branches = mock_branches

            # Mock empty remotes
            mock_repo.remotes = []

            # Mock unborn head
            mock_repo.head_is_unborn = True

            mock_repo_class.return_value = mock_repo

            result = async_repo_manager._get_repository_info(temp_repo_path)

            assert result["head_branch"] is None
            assert result["local_branches"] == 0

    def test_commit_to_model_integration(self, async_repo_manager):
        """Test commit to model conversion integration."""
        # Create a complete mock commit
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "abc123def456789"
        mock_commit.message = "Integration test commit"
        mock_commit.author.name = "Integration Author"
        mock_commit.author.email = "integration@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Integration Committer"
        mock_commit.committer.email = "integration_committer@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0
        mock_commit.parents = []

        result = async_repo_manager._commit_to_model(mock_commit)

        assert isinstance(result, commit_models.CommitInfo)
        assert result.sha == "abc123def456789"
        assert result.message == "Integration test commit"
        assert result.author_name == "Integration Author"

    def test_shutdown(self, async_repo_manager):
        """Test manager shutdown."""
        # Mock the git manager shutdown
        with mock.patch.object(
            async_repo_manager.git_manager, "shutdown"
        ) as mock_shutdown:
            async_repo_manager.shutdown()
            mock_shutdown.assert_called_once()


class TestAsyncRepositoryManagerRegistryIntegration:
    """Test AsyncRepositoryManager integration with registry."""

    @pytest.fixture
    def async_repo_manager(self):
        """Provide an async repository manager."""
        return async_repository.AsyncRepositoryManager()

    @pytest.fixture
    def sample_repo_config(self):
        """Provide a sample repository configuration."""
        return config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

    @pytest.mark.asyncio
    async def test_register_repository_with_tracking_success(
        self, async_repo_manager, sample_repo_config
    ):
        """Test repository registration with tracking."""
        mock_registry = mock.AsyncMock()
        mock_registry.register_repository.return_value = 123
        mock_registry.update_repository_stats.return_value = None

        with (
            mock.patch(
                "ca_bhfuil.core.async_registry.get_async_repository_registry",
                return_value=mock_registry,
            ),
            mock.patch.object(
                type(sample_repo_config), "repo_path", new_callable=mock.PropertyMock
            ) as mock_path,
        ):
            mock_path_obj = mock.Mock()
            mock_path_obj.exists.return_value = False
            mock_path.return_value = mock_path_obj

            result = await async_repo_manager.register_repository_with_tracking(
                sample_repo_config
            )

            assert result.success is True
            assert result.result["repository_id"] == 123
            assert result.result["name"] == "test-repo"
            mock_registry.register_repository.assert_called_once_with(
                sample_repo_config
            )

    @pytest.mark.asyncio
    async def test_register_repository_with_existing_repo(
        self, async_repo_manager, sample_repo_config
    ):
        """Test repository registration when repository exists on disk."""
        mock_registry = mock.AsyncMock()
        mock_registry.register_repository.return_value = 123
        mock_registry.update_repository_stats.return_value = None

        mock_repo = mock.Mock()
        mock_repo.list_branches.return_value = ["main", "develop"]

        with (
            mock.patch(
                "ca_bhfuil.core.async_registry.get_async_repository_registry",
                return_value=mock_registry,
            ),
            mock.patch.object(
                type(sample_repo_config), "repo_path", new_callable=mock.PropertyMock
            ) as mock_path,
            mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo,
            mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor,
        ):
            mock_path_obj = mock.Mock()
            mock_path_obj.exists.return_value = True
            mock_path.return_value = mock_path_obj
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )
            mock_executor.return_value = ["main", "develop"]

            result = await async_repo_manager.register_repository_with_tracking(
                sample_repo_config
            )

            assert result.success is True
            mock_registry.update_repository_stats.assert_called_once_with(
                "test-repo", 0, 2
            )

    @pytest.mark.asyncio
    async def test_register_repository_with_tracking_exception(
        self, async_repo_manager, sample_repo_config
    ):
        """Test repository registration with exception."""
        with mock.patch(
            "ca_bhfuil.core.async_registry.get_async_repository_registry",
            side_effect=Exception("Registry error"),
        ):
            result = await async_repo_manager.register_repository_with_tracking(
                sample_repo_config
            )

            assert result.success is False
            assert "Registry error" in result.error

    @pytest.mark.asyncio
    async def test_analyze_and_store_repository_success(self, async_repo_manager):
        """Test repository analysis and storage."""
        mock_config_manager = mock.AsyncMock()
        mock_repo_config = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        mock_config_manager.get_repository_config_by_name.return_value = (
            mock_repo_config
        )

        mock_registry = mock.AsyncMock()
        mock_registry.update_repository_stats.return_value = None

        mock_repo = mock.Mock()

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager",
                return_value=mock_config_manager,
            ),
            mock.patch(
                "ca_bhfuil.core.async_registry.get_async_repository_registry",
                return_value=mock_registry,
            ),
            mock.patch.object(async_repo_manager, "get_repository") as mock_get_repo,
            mock.patch.object(
                async_repo_manager.git_manager, "run_in_executor"
            ) as mock_executor,
        ):
            mock_get_repo.return_value = results_models.OperationResult(
                success=True, duration=0.1, result=mock_repo
            )
            mock_executor.return_value = ["main", "develop", "feature/test"]

            result = await async_repo_manager.analyze_and_store_repository("test-repo")

            assert result.success is True
            assert result.result["repository"] == "test-repo"
            assert result.result["branches"] == 3
            assert result.result["commits_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_analyze_and_store_repository_not_found(self, async_repo_manager):
        """Test repository analysis when repo not in config."""
        mock_config_manager = mock.AsyncMock()
        mock_config_manager.get_repository_config_by_name.return_value = None

        with mock.patch(
            "ca_bhfuil.core.async_config.AsyncConfigManager",
            return_value=mock_config_manager,
        ):
            result = await async_repo_manager.analyze_and_store_repository(
                "nonexistent"
            )

            assert result.success is False
            assert "not found in configuration" in result.error

    @pytest.mark.asyncio
    async def test_get_repository_state_success(self, async_repo_manager):
        """Test getting repository state from registry."""
        mock_registry = mock.AsyncMock()
        mock_state = {
            "config": {"name": "test-repo"},
            "exists": True,
            "is_git_repo": True,
        }
        mock_registry.get_repository_state.return_value = mock_state

        with mock.patch(
            "ca_bhfuil.core.async_registry.get_async_repository_registry",
            return_value=mock_registry,
        ):
            result = await async_repo_manager.get_repository_state("test-repo")

            assert result.success is True
            assert result.result == mock_state

    @pytest.mark.asyncio
    async def test_get_repository_state_not_found(self, async_repo_manager):
        """Test getting repository state when not found."""
        mock_registry = mock.AsyncMock()
        mock_registry.get_repository_state.return_value = None

        with mock.patch(
            "ca_bhfuil.core.async_registry.get_async_repository_registry",
            return_value=mock_registry,
        ):
            result = await async_repo_manager.get_repository_state("nonexistent")

            assert result.success is False
            assert "not found" in result.error
