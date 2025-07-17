"""Tests for RepositoryManager orchestration layer."""

import datetime
import pathlib
import tempfile
import unittest.mock

import pytest
import sqlalchemy.ext.asyncio

from ca_bhfuil.core.managers import repository as repository_manager
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage.database import engine as db_engine
from tests.fixtures import alembic


class TestRepositoryManager:
    """Test RepositoryManager functionality."""

    @pytest.fixture
    async def db_session(self, tmp_path):
        """Provide a test database session."""
        # Create test database
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        # Create engine and session
        test_engine = db_engine.DatabaseEngine(db_path)
        session = sqlalchemy.ext.asyncio.AsyncSession(test_engine.engine)

        yield session

        # Cleanup
        await session.close()
        await test_engine.close()

    @pytest.fixture
    def mock_git_repo(self):
        """Provide a mocked git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock the git repository
            with unittest.mock.patch(
                "ca_bhfuil.core.git.repository.Repository"
            ) as mock_repo_class:
                mock_repo = unittest.mock.MagicMock()
                mock_repo_class.return_value = mock_repo

                # Configure mock repository
                mock_repo.repository_path = repo_path
                mock_repo.head_is_unborn = False
                mock_repo.get_repository_stats.return_value = {
                    "total_branches": 3,
                    "commit_count": 50,
                }

                # Mock the _repo.walk() method to return sample commits
                mock_commit = unittest.mock.MagicMock()
                mock_commit.id = "abc123def456789abc123def456789abc123def4"
                mock_commit.message = "feat: Add sample feature"
                mock_commit.author.name = "Test Author"
                mock_commit.author.email = "test@example.com"
                mock_commit.author.time = 1640995200  # 2022-01-01 00:00:00 UTC
                mock_commit.author.offset = 0
                mock_commit.committer.name = "Test Author"
                mock_commit.committer.email = "test@example.com"
                mock_commit.committer.time = 1640995200
                mock_commit.committer.offset = 0
                mock_commit.parents = []

                mock_repo._repo.head.target = "abc123def456789abc123def456789abc123def4"
                mock_repo._repo.walk.return_value = [mock_commit]

                # Mock the conversion method
                sample_commit = commit_models.CommitInfo(
                    sha="abc123def456789abc123def456789abc123def4",
                    short_sha="abc123d",
                    message="feat: Add sample feature",
                    author_name="Test Author",
                    author_email="test@example.com",
                    author_date=datetime.datetime(2022, 1, 1, 0, 0, 0),
                    committer_name="Test Author",
                    committer_email="test@example.com",
                    committer_date=datetime.datetime(2022, 1, 1, 0, 0, 0),
                    files_changed=3,
                    insertions=50,
                    deletions=10,
                )
                mock_repo._commit_to_model.return_value = sample_commit

                yield repo_path, mock_repo

    @pytest.fixture
    async def repository_manager(self, mock_git_repo, db_session):
        """Provide a RepositoryManager instance."""
        repo_path, mock_repo = mock_git_repo
        manager = repository_manager.RepositoryManager(repo_path, db_session)
        yield manager
        await manager.close()

    async def test_load_commits_from_git_first_time(self, repository_manager):
        """Test loading commits from git when no cache exists."""
        commits = await repository_manager.load_commits(from_cache=True, limit=10)

        assert len(commits) == 1
        assert isinstance(commits[0], commit_models.CommitInfo)
        assert commits[0].sha == "abc123def456789abc123def456789abc123def4"
        assert commits[0].message == "feat: Add sample feature"

    async def test_load_commits_without_cache(self, repository_manager):
        """Test loading commits directly from git without caching."""
        commits = await repository_manager.load_commits(from_cache=False, limit=10)

        assert len(commits) == 1
        assert isinstance(commits[0], commit_models.CommitInfo)
        assert commits[0].author_name == "Test Author"

    async def test_search_commits_pattern_matching(self, repository_manager):
        """Test commit search with pattern matching."""
        result = await repository_manager.search_commits("feature", limit=10)

        assert result.success
        assert len(result.commits) == 1
        assert result.total_count == 1
        assert result.search_pattern == "feature"
        assert result.commits[0].message == "feat: Add sample feature"

    async def test_search_commits_no_matches(self, repository_manager):
        """Test commit search with no matching pattern."""
        result = await repository_manager.search_commits("nonexistent", limit=10)

        assert result.success
        assert len(result.commits) == 0
        assert result.total_count == 0
        assert result.search_pattern == "nonexistent"

    async def test_analyze_repository_success(self, repository_manager):
        """Test repository analysis with successful result."""
        result = await repository_manager.analyze_repository()

        assert result.success
        assert result.commit_count == 1
        assert result.branch_count == 3
        assert len(result.recent_commits) == 1
        assert len(result.authors) == 1
        assert "Test Author" in result.authors
        assert "earliest" in result.date_range
        assert "latest" in result.date_range

    async def test_analyze_repository_high_impact_commits(self, repository_manager):
        """Test repository analysis identifies high impact commits."""
        # The sample commit should have medium-high impact (3 files + 50 insertions * 1.2 = 63.6, / 100 = 0.636)
        result = await repository_manager.analyze_repository()

        assert result.success
        # With impact score 0.636, it shouldn't be in high_impact_commits (>0.7)
        assert len(result.high_impact_commits) == 0

    async def test_sync_with_database_new_repository(self, repository_manager):
        """Test syncing a new repository to database."""
        await repository_manager.sync_with_database()

        # Verify repository was created in database
        db_repo = await repository_manager._get_db_repository()
        repo_record = await db_repo.repositories.get_by_path(
            str(repository_manager.repository_path)
        )

        assert repo_record is not None
        assert repo_record.path == str(repository_manager.repository_path)
        assert repo_record.commit_count == 1
        assert repo_record.branch_count == 3

    async def test_sync_with_database_existing_repository(self, repository_manager):
        """Test syncing an existing repository updates statistics."""
        # First sync to create repository
        await repository_manager.sync_with_database()

        # Second sync should update existing
        await repository_manager.sync_with_database()

        # Verify repository still exists with updated stats
        db_repo = await repository_manager._get_db_repository()
        repo_record = await db_repo.repositories.get_by_path(
            str(repository_manager.repository_path)
        )

        assert repo_record is not None
        assert repo_record.commit_count == 1

    async def test_load_commits_from_cache_after_sync(self, repository_manager):
        """Test loading commits from database cache after sync."""
        # First sync to populate database
        await repository_manager.sync_with_database()

        # Load commits from cache
        commits = await repository_manager.load_commits(from_cache=True, limit=10)

        assert len(commits) == 1
        assert commits[0].sha == "abc123def456789abc123def456789abc123def4"

    async def test_search_commits_with_cached_data(self, repository_manager):
        """Test search using cached commit data."""
        # Sync first to populate cache
        await repository_manager.sync_with_database()

        # Search should use cached data
        result = await repository_manager.search_commits("author", limit=10)

        assert result.success
        assert len(result.commits) == 1  # Should match "Test Author"

    async def test_repository_manager_close(self, repository_manager):
        """Test proper cleanup of repository manager."""
        # This should not raise any exceptions
        await repository_manager.close()

        # Manager should still be usable after close (creates new session)
        commits = await repository_manager.load_commits(from_cache=False, limit=1)
        assert len(commits) == 1


class TestRepositoryAnalysisResult:
    """Test RepositoryAnalysisResult model."""

    def test_repository_analysis_result_creation(self):
        """Test creating RepositoryAnalysisResult with all fields."""
        sample_commit = commit_models.CommitInfo(
            sha="test123",
            short_sha="test123",
            message="Test commit",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
        )

        result = repository_manager.RepositoryAnalysisResult(
            success=True,
            duration=1.5,
            repository_path="/path/to/repo",
            commit_count=100,
            branch_count=5,
            recent_commits=[sample_commit],
            high_impact_commits=[sample_commit],
            authors=["Author 1", "Author 2"],
            date_range={"earliest": "2024-01-01", "latest": "2024-01-15"},
        )

        assert result.success is True
        assert result.duration == 1.5
        assert result.repository_path == "/path/to/repo"
        assert result.commit_count == 100
        assert result.branch_count == 5
        assert len(result.recent_commits) == 1
        assert len(result.high_impact_commits) == 1
        assert len(result.authors) == 2
        assert result.date_range["earliest"] == "2024-01-01"


class TestCommitSearchResult:
    """Test CommitSearchResult model."""

    def test_commit_search_result_creation(self):
        """Test creating CommitSearchResult with search metadata."""
        sample_commit = commit_models.CommitInfo(
            sha="search123",
            short_sha="search1",
            message="Search result commit",
            author_name="Search Author",
            author_email="search@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Search Author",
            committer_email="search@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
        )

        result = repository_manager.CommitSearchResult(
            success=True,
            duration=0.5,
            commits=[sample_commit],
            total_count=25,
            search_pattern="test",
            repository_path="/path/to/search/repo",
        )

        assert result.success is True
        assert result.duration == 0.5
        assert len(result.commits) == 1
        assert result.total_count == 25
        assert result.search_pattern == "test"
        assert result.repository_path == "/path/to/search/repo"

    def test_commit_search_result_empty(self):
        """Test creating empty CommitSearchResult."""
        result = repository_manager.CommitSearchResult(
            success=True,
            duration=0.1,
            search_pattern="nonexistent",
        )

        assert result.success is True
        assert len(result.commits) == 0
        assert result.total_count == 0
        assert result.search_pattern == "nonexistent"
        assert result.repository_path is None
