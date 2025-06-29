"""Tests for repository registry functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.core import config
from ca_bhfuil.core import registry
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage.database import schema


class TestRepositoryRegistry:
    """Test repository registry operations."""

    @pytest.fixture
    def temp_config_dir(self):
        """Provide a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def temp_db_path(self):
        """Provide a temporary database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir) / "test.db"

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Provide a test configuration manager."""
        return config.ConfigManager(temp_config_dir)

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Provide a test database manager."""
        return schema.DatabaseManager(temp_db_path)

    @pytest.fixture
    def repository_registry(self, config_manager, db_manager):
        """Provide a test repository registry."""
        return registry.RepositoryRegistry(config_manager, db_manager)

    @pytest.fixture
    def sample_repo_config(self, temp_config_dir):
        """Provide a sample repository configuration."""
        return config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

    def test_repository_registry_initialization(self, repository_registry):
        """Test repository registry initializes correctly."""
        assert repository_registry.config_manager is not None
        assert repository_registry.db_manager is not None

    def test_register_repository(self, repository_registry, sample_repo_config):
        """Test repository registration."""
        # First add the config to the config manager so it can be found later
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            repo_id = repository_registry.register_repository(sample_repo_config)
            assert isinstance(repo_id, int)
            assert repo_id > 0

            # Verify it was stored
            repo_state = repository_registry.get_repository_state("test-repo")
            assert repo_state is not None
            assert repo_state["config"]["name"] == "test-repo"

    def test_get_repository_state_not_found(self, repository_registry):
        """Test getting state for non-existent repository."""
        state = repository_registry.get_repository_state("nonexistent")
        assert state is None

    def test_get_repository_state_configured_only(
        self, repository_registry, sample_repo_config, config_manager
    ):
        """Test getting state for repository that's configured but not registered."""
        # Add to configuration but not database
        global_config = config.GlobalConfig(repos=[sample_repo_config])

        with (
            mock.patch.object(
                config_manager, "load_configuration", return_value=global_config
            ),
            mock.patch.object(
                config_manager,
                "get_repository_config_by_name",
                return_value=sample_repo_config,
            ),
        ):
            state = repository_registry.get_repository_state("test-repo")

        assert state is not None
        assert state["config"]["name"] == "test-repo"
        assert state["registered"] is False

    def test_list_repositories(
        self, repository_registry, sample_repo_config, config_manager
    ):
        """Test listing all repositories."""
        # Register a repository
        repository_registry.register_repository(sample_repo_config)

        # Mock configuration loading
        global_config = config.GlobalConfig(repos=[sample_repo_config])
        with mock.patch.object(
            config_manager, "load_configuration", return_value=global_config
        ):
            repositories = repository_registry.list_repositories()

        assert len(repositories) == 1
        assert repositories[0]["config"]["name"] == "test-repo"

    def test_update_repository_stats(self, repository_registry, sample_repo_config):
        """Test updating repository statistics."""
        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Register repository first
            repository_registry.register_repository(sample_repo_config)

            # Update stats
            success = repository_registry.update_repository_stats("test-repo", 100, 5)
            assert success is True

            # Verify stats were updated
            state = repository_registry.get_repository_state("test-repo")
            assert state["commit_count"] == 100
            assert state["branch_count"] == 5

    def test_update_repository_stats_not_found(self, repository_registry):
        """Test updating stats for non-existent repository."""
        success = repository_registry.update_repository_stats("nonexistent", 100, 5)
        assert success is False

    def test_add_commit(self, repository_registry, sample_repo_config):
        """Test adding a commit to the repository."""
        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Register repository first
            repository_registry.register_repository(sample_repo_config)

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
            success = repository_registry.add_commit("test-repo", commit_info)
            assert success is True

    def test_add_commit_auto_register(
        self, repository_registry, sample_repo_config, config_manager
    ):
        """Test adding a commit auto-registers repository."""
        # Mock configuration to return the repo config
        with mock.patch.object(
            config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
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
            success = repository_registry.add_commit("test-repo", commit_info)
            assert success is True

    def test_search_commits(self, repository_registry, sample_repo_config):
        """Test searching commits in repository."""
        # Mock config manager to return repo config
        with mock.patch.object(
            repository_registry.config_manager,
            "get_repository_config_by_name",
            return_value=sample_repo_config,
        ):
            # Register repository and add commit
            repository_registry.register_repository(sample_repo_config)

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
            repository_registry.add_commit("test-repo", commit_info)

            # Search by SHA
            commits = repository_registry.search_commits(
                "test-repo", sha_pattern="abc123"
            )
            assert len(commits) == 1
            assert commits[0].sha == "abc123def456"

            # Search by message
            commits = repository_registry.search_commits(
                "test-repo", message_pattern="memory"
            )
            assert len(commits) == 1
            assert commits[0].message == "Fix memory leak"

    def test_search_commits_not_found(self, repository_registry):
        """Test searching commits in non-existent repository."""
        commits = repository_registry.search_commits(
            "nonexistent", sha_pattern="abc123"
        )
        assert len(commits) == 0

    def test_get_registry_stats(self, repository_registry, sample_repo_config):
        """Test getting registry statistics."""
        # Register repository
        repository_registry.register_repository(sample_repo_config)

        # Mock configuration
        global_config = config.GlobalConfig(repos=[sample_repo_config])
        with mock.patch.object(
            repository_registry.config_manager,
            "load_configuration",
            return_value=global_config,
        ):
            stats = repository_registry.get_registry_stats()

        assert stats["configured_repositories"] == 1
        assert stats["registered_repositories"] == 1
        assert "database_path" in stats

    def test_sync_repository_state_not_found(self, repository_registry):
        """Test syncing state for non-existent repository."""
        result = repository_registry.sync_repository_state("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_sync_repository_state(
        self, repository_registry, sample_repo_config, config_manager
    ):
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
            repository_registry, "get_repository_state", return_value=mock_state
        ):
            result = repository_registry.sync_repository_state("test-repo")

        assert result["success"] is True
        assert result["repository"] == "test-repo"
        assert result["exists"] is False
        assert result["is_git_repo"] is False


class TestRepositoryRegistryGlobalInstance:
    """Test global repository registry instance."""

    def test_get_repository_registry(self):
        """Test getting global repository registry."""
        registry1 = registry.get_repository_registry()
        registry2 = registry.get_repository_registry()

        # Should return the same instance
        assert registry1 is registry2
        assert isinstance(registry1, registry.RepositoryRegistry)
