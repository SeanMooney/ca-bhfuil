"""Tests for async repository registry functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_registry
from ca_bhfuil.core import config
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage import sqlmodel_manager


@pytest.fixture
async def db_manager():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = pathlib.Path(temp_dir) / "test.db"
        manager = sqlmodel_manager.SQLModelDatabaseManager(db_path)
        await manager.initialize()
        yield manager
        await manager.close()


@pytest.fixture
def config_manager(tmp_path):
    return async_config.AsyncConfigManager(tmp_path)


@pytest.fixture
def repository_registry(config_manager, db_manager):
    return async_registry.AsyncRepositoryRegistry(config_manager, db_manager)


class TestAsyncRepositoryRegistry:
    """Test async repository registry operations."""

    @pytest.fixture
    def sample_repo_config(self, tmp_path):
        """Provide a sample repository configuration."""
        return config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

    @pytest.mark.asyncio
    async def test_repository_registry_initialization(self, repository_registry):
        """Test async repository registry initializes correctly."""
        assert repository_registry.config_manager is not None
        assert repository_registry.db_manager is not None
        assert repository_registry._lock is not None

    @pytest.mark.asyncio
    async def test_register_repository(self, repository_registry, sample_repo_config):
        """Test async repository registration."""
        # Mock the config manager to return the sample config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            repo_id = await repository_registry.register_repository(sample_repo_config)
            assert isinstance(repo_id, int)
            assert repo_id > 0

            # Verify it was stored
            repo_state = await repository_registry.get_repository_state("test-repo")
            assert repo_state is not None
            assert repo_state["config"]["name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_get_repository_state_not_found(self, repository_registry):
        """Test getting state for non-existent repository."""
        state = await repository_registry.get_repository_state("nonexistent")
        assert state is None

    @pytest.mark.asyncio
    async def test_get_repository_state_configured_only(
        self, repository_registry, sample_repo_config
    ):
        """Test getting state for repository that's configured but not registered."""
        with (
            mock.patch.object(
                repository_registry.config_manager,
                "get_repository_config_by_name",
                return_value=sample_repo_config,
            ),
            mock.patch.object(
                repository_registry.db_manager, "get_repository", return_value=None
            ),
        ):
            state = await repository_registry.get_repository_state("test-repo")

        assert state is not None
        assert state["config"]["name"] == "test-repo"
        assert state["registered"] is False

    @pytest.mark.asyncio
    async def test_list_repositories(self, repository_registry, sample_repo_config):
        """Test listing all repositories."""
        # Register a repository
        await repository_registry.register_repository(sample_repo_config)

        # Mock configuration loading
        global_config = config.GlobalConfig(repos=[sample_repo_config])
        with mock.patch.object(
            repository_registry.config_manager,
            "load_configuration",
            return_value=mock.AsyncMock(return_value=global_config),
        ) as mock_load:
            mock_load.return_value = global_config
            repositories = await repository_registry.list_repositories()

        assert len(repositories) == 1
        assert repositories[0]["config"]["name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_update_repository_stats(
        self, repository_registry, sample_repo_config
    ):
        """Test updating repository statistics."""
        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Register repository first
            await repository_registry.register_repository(sample_repo_config)

            # Update stats
            success = await repository_registry.update_repository_stats(
                "test-repo", 100, 5
            )
            assert success is True

            # Verify stats were updated
            state = await repository_registry.get_repository_state("test-repo")
            assert state["commit_count"] == 100
            assert state["branch_count"] == 5

    @pytest.mark.asyncio
    async def test_update_repository_stats_not_found(self, repository_registry):
        """Test updating stats for non-existent repository."""
        success = await repository_registry.update_repository_stats(
            "nonexistent", 100, 5
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_update_repository_stats_auto_registration(
        self, repository_registry, sample_repo_config, tmp_path
    ):
        """Test auto-registration of repository during stats update."""
        # Create a fake git repository directory
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()

        # Update the sample config to point to our test path
        sample_repo_config.source["path"] = str(repo_path)

        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Don't register repository first - let update_repository_stats auto-register it
            success = await repository_registry.update_repository_stats(
                "test-repo", 100, 5
            )
            assert success is True

            # Verify repository was auto-registered and stats were updated
            state = await repository_registry.get_repository_state("test-repo")
            assert state["registered"] is True
            assert state["commit_count"] == 100
            assert state["branch_count"] == 5

    @pytest.mark.asyncio
    async def test_add_commit(self, repository_registry, sample_repo_config):
        """Test adding a commit to the repository."""
        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Register repository first
            await repository_registry.register_repository(sample_repo_config)

            # Create sample commit
            commit_info = commit_models.CommitInfo(
                sha="abc123def456",
                short_sha="abc123d",
                message="Test commit",
                author_name="Test Author",
                author_email="test@example.com",
                author_date="2024-01-01T12:00:00+00:00",
                committer_name="Test Author",
                committer_email="test@example.com",
                committer_date="2024-01-01T12:00:00+00:00",
                parents=["def456ghi789"],
            )

            # Add commit
            success = await repository_registry.add_commit("test-repo", commit_info)
            assert success is True

    @pytest.mark.asyncio
    async def test_add_commit_auto_register(
        self, repository_registry, sample_repo_config
    ):
        """Test adding a commit auto-registers repository."""
        # Mock configuration to return the repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=mock.AsyncMock(return_value=sample_repo_config),
        ) as mock_get_config:
            mock_get_config.return_value = sample_repo_config

            commit_info = commit_models.CommitInfo(
                sha="abc123def456",
                short_sha="abc123d",
                message="Test commit",
                author_name="Test Author",
                author_email="test@example.com",
                author_date="2024-01-01T12:00:00+00:00",
                committer_name="Test Author",
                committer_email="test@example.com",
                committer_date="2024-01-01T12:00:00+00:00",
                parents=["def456ghi789"],
            )

            # Add commit should auto-register
            success = await repository_registry.add_commit("test-repo", commit_info)
            assert success is True

    @pytest.mark.asyncio
    async def test_search_commits(self, repository_registry, sample_repo_config):
        """Test searching commits in repository."""
        commit_info = commit_models.CommitInfo(
            sha="abc123def456",
            short_sha="abc123d",
            message="Fix memory leak",
            author_name="Test Author",
            author_email="test@example.com",
            author_date="2024-01-01T12:00:00+00:00",
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date="2024-01-01T12:00:00+00:00",
            parents=["def456ghi789"],
        )
        mock_repo = mock.Mock(spec=sqlmodel_manager.models.RepositoryRead)
        mock_repo.id = 1
        with (
            mock.patch.object(
                repository_registry.config_manager,
                "get_repository_config_by_name",
                return_value=sample_repo_config,
            ),
            mock.patch.object(
                repository_registry.db_manager, "get_repository", return_value=mock_repo
            ),
            mock.patch.object(
                repository_registry.db_manager,
                "find_commits",
                return_value=[commit_info],
            ),
        ):
            # Search by SHA
            commits = await repository_registry.search_commits(
                "test-repo", sha_pattern="abc123"
            )
            assert len(commits) == 1
            assert commits[0].sha == "abc123def456"

            # Search by message
            commits = await repository_registry.search_commits(
                "test-repo", message_pattern="memory"
            )
            assert len(commits) == 1
            assert "memory" in commits[0].message

    @pytest.mark.asyncio
    async def test_search_commits_not_found(self, repository_registry):
        """Test searching commits in non-existent repository."""
        commits = await repository_registry.search_commits(
            "nonexistent", sha_pattern="abc123"
        )
        assert len(commits) == 0

    @pytest.mark.asyncio
    async def test_get_registry_stats(self, repository_registry, sample_repo_config):
        """Test getting registry statistics."""
        with (
            mock.patch.object(
                repository_registry.config_manager,
                "load_configuration",
                return_value=config.GlobalConfig(repos=[sample_repo_config]),
            ),
            mock.patch.object(
                repository_registry.db_manager,
                "get_stats",
                return_value={
                    "repositories": 1,
                    "commits": 0,
                    "branches": 0,
                },
            ),
        ):
            stats = await repository_registry.get_registry_stats()

        assert stats["configured_repositories"] == 1
        assert stats["registered_repositories"] == 1
        assert "database_path" in stats

    @pytest.mark.asyncio
    async def test_sync_repository_state_not_found(self, repository_registry):
        """Test syncing state for non-existent repository."""
        result = await repository_registry.sync_repository_state("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_repository_state(self, repository_registry):
        """Test syncing repository state."""
        # Mock the repository state
        mock_state = {
            "config": {
                "name": "test-repo",
                "source": {"url": "https://github.com/test/repo.git"},
                "repo_path": "/tmp/test-repo",
            },
            "exists": False,
            "is_git_repo": False,
            "registered": True,
        }

        with mock.patch.object(
            repository_registry,
            "get_repository_state",
            return_value=mock.AsyncMock(return_value=mock_state),
        ) as mock_get_state:
            mock_get_state.return_value = mock_state
            result = await repository_registry.sync_repository_state("test-repo")

        assert result["success"] is True
        assert result["repository"] == "test-repo"
        assert result["exists"] is False
        assert result["is_git_repo"] is False


class TestAsyncRepositoryRegistryGlobalInstance:
    """Test global async repository registry instance."""

    @pytest.mark.asyncio
    async def test_get_async_repository_registry(self):
        """Test getting global async repository registry."""
        registry1 = await async_registry.get_async_repository_registry()
        registry2 = await async_registry.get_async_repository_registry()

        # Should return the same instance
        assert registry1 is registry2
        assert isinstance(registry1, async_registry.AsyncRepositoryRegistry)
