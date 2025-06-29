"""Tests for core git repository operations."""

import datetime
import pathlib
import tempfile
from unittest import mock

import pygit2
import pytest

from ca_bhfuil.core.git import repository as repository_module
from ca_bhfuil.core.models import commit as commit_models


class TestRepositoryWrapper:
    """Test the Repository wrapper class."""

    @pytest.fixture
    def temp_repo_path(self):
        """Provide a temporary repository path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def mock_pygit2_repo(self):
        """Provide a mock pygit2 repository."""
        return mock.Mock(spec=pygit2.Repository)

    @pytest.fixture
    def repository_wrapper(self, temp_repo_path, mock_pygit2_repo):
        """Provide a repository wrapper instance."""
        with mock.patch("pygit2.Repository", return_value=mock_pygit2_repo):
            return repository_module.Repository(temp_repo_path)

    def test_repository_initialization(self, temp_repo_path, mock_pygit2_repo):
        """Test repository wrapper initialization."""
        with mock.patch(
            "pygit2.Repository", return_value=mock_pygit2_repo
        ) as mock_repo_class:
            repo = repository_module.Repository(temp_repo_path)

            assert repo.path == temp_repo_path
            assert repo._repo == mock_pygit2_repo
            mock_repo_class.assert_called_once_with(str(temp_repo_path))

    def test_repository_initialization_with_string_path(
        self, temp_repo_path, mock_pygit2_repo
    ):
        """Test repository wrapper initialization with string path."""
        with mock.patch("pygit2.Repository", return_value=mock_pygit2_repo):
            repo = repository_module.Repository(str(temp_repo_path))

            assert repo.path == temp_repo_path

    def test_get_commit_success(self, repository_wrapper, mock_pygit2_repo):
        """Test successful commit retrieval."""
        # Mock commit object
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "abc123def456789abc123def456789abc123def4"
        mock_commit.message = "Test commit message"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.author.time = 1640995200  # 2022-01-01 00:00:00 UTC
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Test Committer"
        mock_commit.committer.email = "committer@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0
        mock_commit.parents = []

        # Mock repository behavior for full SHA
        repository_wrapper._repo = mock_pygit2_repo
        mock_pygit2_repo.__getitem__ = mock.Mock(return_value=mock_commit)

        # Mock isinstance check in repository module
        with mock.patch("ca_bhfuil.core.git.repository.isinstance", return_value=True):
            result = repository_wrapper.get_commit(
                "abc123def456789abc123def456789abc123def4"
            )

        assert result is not None
        assert isinstance(result, commit_models.CommitInfo)
        assert result.sha == "abc123def456789abc123def456789abc123def4"
        assert result.message == "Test commit message"
        assert result.author_name == "Test Author"
        assert result.author_email == "test@example.com"

    def test_get_commit_partial_sha(self, repository_wrapper, mock_pygit2_repo):
        """Test commit retrieval with partial SHA."""
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "abc123def456789"
        mock_commit.message = "Test commit message"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Test Committer"
        mock_commit.committer.email = "committer@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0
        mock_commit.parents = []

        # Mock repository behavior for partial SHA
        mock_pygit2_repo.revparse_single.return_value = mock_commit

        result = repository_wrapper.get_commit("abc123")

        assert result is not None
        assert result.sha == "abc123def456789"
        mock_pygit2_repo.revparse_single.assert_called_once_with("abc123")

    def test_get_commit_not_found(self, repository_wrapper, mock_pygit2_repo):
        """Test commit retrieval when commit doesn't exist."""
        repository_wrapper._repo = mock_pygit2_repo
        mock_pygit2_repo.__getitem__ = mock.Mock(
            side_effect=KeyError("Commit not found")
        )

        result = repository_wrapper.get_commit("nonexistent")

        assert result is None

    def test_get_commit_invalid_object(self, repository_wrapper, mock_pygit2_repo):
        """Test commit retrieval when object is not a commit."""
        repository_wrapper._repo = mock_pygit2_repo
        mock_tree = mock.Mock(spec=pygit2.Tree)
        mock_pygit2_repo.__getitem__ = mock.Mock(return_value=mock_tree)

        result = repository_wrapper.get_commit("abc123")

        assert result is None

    def test_get_commit_git_error(self, repository_wrapper, mock_pygit2_repo):
        """Test commit retrieval when git error occurs."""
        mock_pygit2_repo.revparse_single.side_effect = pygit2.GitError("Git error")

        result = repository_wrapper.get_commit("abc123")

        assert result is None

    def test_list_branches(self, repository_wrapper, mock_pygit2_repo):
        """Test branch listing."""
        # Mock repository branches
        mock_branches = mock.Mock()
        mock_branches.local = ["main", "develop"]
        mock_branches.remote = ["origin/main", "origin/feature"]
        mock_pygit2_repo.branches = mock_branches
        repository_wrapper._repo = mock_pygit2_repo

        branches = repository_wrapper.list_branches()

        assert "main" in branches["local"]
        assert "develop" in branches["local"]
        assert "origin/main" in branches["remote"]
        assert len(branches["local"]) == 2
        assert len(branches["remote"]) == 2

    def test_list_branches_empty(self, repository_wrapper, mock_pygit2_repo):
        """Test branch listing when no branches exist."""
        mock_branches = mock.Mock()
        mock_branches.local = []
        mock_branches.remote = []
        mock_pygit2_repo.branches = mock_branches
        repository_wrapper._repo = mock_pygit2_repo

        branches = repository_wrapper.list_branches()

        assert branches == {"local": [], "remote": []}

    def test_get_commits_by_pattern(self, repository_wrapper, mock_pygit2_repo):
        """Test commit search by message pattern."""
        # Mock commits
        mock_commit1 = mock.Mock(spec=pygit2.Commit)
        mock_commit1.id = "commit1"
        mock_commit1.message = "Fix memory leak in parser"
        mock_commit1.author.name = "Author 1"
        mock_commit1.author.email = "author1@example.com"
        mock_commit1.author.time = 1640995200
        mock_commit1.author.offset = 0
        mock_commit1.committer.name = "Author 1"
        mock_commit1.committer.email = "author1@example.com"
        mock_commit1.committer.time = 1640995200
        mock_commit1.committer.offset = 0
        mock_commit1.parents = []

        mock_commit2 = mock.Mock(spec=pygit2.Commit)
        mock_commit2.id = "commit2"
        mock_commit2.message = "Add new feature"
        mock_commit2.author.name = "Author 2"
        mock_commit2.author.email = "author2@example.com"
        mock_commit2.author.time = 1640995300
        mock_commit2.author.offset = 0
        mock_commit2.committer.name = "Author 2"
        mock_commit2.committer.email = "author2@example.com"
        mock_commit2.committer.time = 1640995300
        mock_commit2.committer.offset = 0
        mock_commit2.parents = []

        # Mock walking behavior
        repository_wrapper._repo = mock_pygit2_repo
        mock_pygit2_repo.walk.return_value = [mock_commit1, mock_commit2]
        mock_pygit2_repo.head.target = "head_commit"

        with mock.patch("ca_bhfuil.core.git.repository.isinstance", return_value=True):
            results = repository_wrapper.get_commits_by_pattern(
                "memory", max_results=10
            )

        assert len(results) == 1
        assert results[0].message == "Fix memory leak in parser"
        assert results[0].sha == "commit1"

    def test_get_commits_by_pattern_no_matches(
        self, repository_wrapper, mock_pygit2_repo
    ):
        """Test commit search with no matches."""
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.message = "Add new feature"
        mock_commit.author.name = "Author"
        mock_commit.author.email = "author@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Author"
        mock_commit.committer.email = "author@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0
        mock_commit.parents = []

        repository_wrapper._repo = mock_pygit2_repo
        mock_pygit2_repo.walk.return_value = [mock_commit]
        mock_pygit2_repo.head.target = "head_commit"

        results = repository_wrapper.get_commits_by_pattern(
            "nonexistent", max_results=10
        )

        assert len(results) == 0

    def test_get_commits_by_pattern_with_limit(
        self, repository_wrapper, mock_pygit2_repo
    ):
        """Test commit search with limit."""
        # Create multiple matching commits
        commits = []
        for i in range(5):
            mock_commit = mock.Mock(spec=pygit2.Commit)
            mock_commit.id = f"commit{i}"
            mock_commit.message = f"Fix issue {i}"
            mock_commit.author.name = f"Author {i}"
            mock_commit.author.email = f"author{i}@example.com"
            mock_commit.author.time = 1640995200 + i
            mock_commit.author.offset = 0
            mock_commit.committer.name = f"Author {i}"
            mock_commit.committer.email = f"author{i}@example.com"
            mock_commit.committer.time = 1640995200 + i
            mock_commit.committer.offset = 0
            mock_commit.parents = []
            commits.append(mock_commit)

        repository_wrapper._repo = mock_pygit2_repo
        mock_pygit2_repo.walk.return_value = commits
        mock_pygit2_repo.head.target = "head_commit"

        with mock.patch("ca_bhfuil.core.git.repository.isinstance", return_value=True):
            results = repository_wrapper.get_commits_by_pattern("Fix", max_results=3)

        assert len(results) == 3

    def test_get_commits_by_pattern_no_head(self, repository_wrapper, mock_pygit2_repo):
        """Test commit search when repository has no HEAD."""
        mock_pygit2_repo.head = None

        results = repository_wrapper.get_commits_by_pattern("test", max_results=10)

        assert len(results) == 0

    def test_find_commit_in_branches(self, repository_wrapper, mock_pygit2_repo):
        """Test finding which branches contain a commit."""
        # Mock branch structure
        mock_branches = mock.Mock()

        # Mock branch objects
        mock_main_branch = mock.Mock()
        mock_main_branch.target = "commit3"
        mock_develop_branch = mock.Mock()
        mock_develop_branch.target = "commit2"

        def get_local_branch_side_effect(branch_name):
            if branch_name == "main":
                return mock_main_branch
            if branch_name == "develop":
                return mock_develop_branch
            return None

        # Mock local and remote branch collections
        mock_local_branches = mock.Mock()
        mock_local_branches.__iter__ = mock.Mock(return_value=iter(["main", "develop"]))
        mock_local_branches.get = mock.Mock(side_effect=get_local_branch_side_effect)

        mock_remote_branches = mock.Mock()
        mock_remote_branches.__iter__ = mock.Mock(return_value=iter([]))
        mock_remote_branches.get = mock.Mock(return_value=None)

        mock_branches.local = mock_local_branches
        mock_branches.remote = mock_remote_branches
        mock_pygit2_repo.branches = mock_branches

        # Mock merge_base to simulate commit reachability
        def merge_base_side_effect(commit_oid, branch_target):
            # If target is commit2 or commit3, then commit2 is reachable
            if str(commit_oid) == "commit2" and branch_target in ["commit2", "commit3"]:
                return commit_oid
            return None

        mock_pygit2_repo.merge_base = mock.Mock(side_effect=merge_base_side_effect)
        repository_wrapper._repo = mock_pygit2_repo

        with mock.patch("pygit2.Oid") as mock_oid:
            mock_oid.return_value = "commit2"
            branches = repository_wrapper.find_commit_in_branches("commit2")

        assert "main" in branches
        assert "develop" in branches
        assert len(branches) == 2

    def test_find_commit_in_branches_not_found(
        self, repository_wrapper, mock_pygit2_repo
    ):
        """Test finding branches when commit doesn't exist in any."""
        mock_pygit2_repo.references = {
            "refs/heads/main": mock.Mock(target="commit2"),
        }

        mock_pygit2_repo.walk.return_value = [mock.Mock(id="commit2")]

        branches = repository_wrapper.find_commit_in_branches("nonexistent")

        assert len(branches) == 0

    def test_find_commit_in_branches_git_error(
        self, repository_wrapper, mock_pygit2_repo
    ):
        """Test finding branches when git error occurs."""
        mock_pygit2_repo.references = {
            "refs/heads/main": mock.Mock(target="commit1"),
        }

        mock_pygit2_repo.walk.side_effect = pygit2.GitError("Git error")

        branches = repository_wrapper.find_commit_in_branches("commit1")

        assert len(branches) == 0

    def test_commit_to_model_conversion(self, repository_wrapper):
        """Test conversion of pygit2 commit to CommitInfo model."""
        # Create a mock commit with all required attributes
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "abc123def456789"
        mock_commit.message = "Test commit\n\nDetailed description"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Test Committer"
        mock_commit.committer.email = "committer@example.com"
        mock_commit.committer.time = 1640995300
        mock_commit.committer.offset = 60  # +1 hour offset

        # Mock parent commits
        mock_parent = mock.Mock()
        mock_parent.id = "parent123"
        mock_commit.parents = [mock_parent]

        # Call the private method directly for testing
        result = repository_wrapper._commit_to_model(mock_commit)

        assert isinstance(result, commit_models.CommitInfo)
        assert result.sha == "abc123def456789"
        assert result.short_sha == "abc123d"
        assert result.message == "Test commit\n\nDetailed description"
        assert result.author_name == "Test Author"
        assert result.author_email == "test@example.com"
        assert result.committer_name == "Test Committer"
        assert result.committer_email == "committer@example.com"
        assert result.parents == ["parent123"]

        # Check timezone handling
        assert isinstance(result.author_date, datetime.datetime)
        assert isinstance(result.committer_date, datetime.datetime)

    def test_commit_to_model_no_parents(self, repository_wrapper):
        """Test commit model conversion for commit with no parents (initial commit)."""
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "initial123"
        mock_commit.message = "Initial commit"
        mock_commit.author.name = "Initial Author"
        mock_commit.author.email = "initial@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Initial Author"
        mock_commit.committer.email = "initial@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0
        mock_commit.parents = []

        result = repository_wrapper._commit_to_model(mock_commit)

        assert result.parents == []

    def test_commit_to_model_multiple_parents(self, repository_wrapper):
        """Test commit model conversion for merge commit with multiple parents."""
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "merge123"
        mock_commit.message = "Merge branch 'feature'"
        mock_commit.author.name = "Merge Author"
        mock_commit.author.email = "merge@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = 0
        mock_commit.committer.name = "Merge Author"
        mock_commit.committer.email = "merge@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 0

        # Mock multiple parents
        mock_parent1 = mock.Mock()
        mock_parent1.id = "parent1"
        mock_parent2 = mock.Mock()
        mock_parent2.id = "parent2"
        mock_commit.parents = [mock_parent1, mock_parent2]

        result = repository_wrapper._commit_to_model(mock_commit)

        assert result.parents == ["parent1", "parent2"]


class TestRepositoryInitializationErrors:
    """Test repository initialization error cases."""

    def test_repository_initialization_git_error(self):
        """Test repository initialization when pygit2 raises error."""
        with (
            mock.patch(
                "pygit2.Repository", side_effect=pygit2.GitError("Not a git repository")
            ),
            pytest.raises(pygit2.GitError),
        ):
            repository_module.Repository("/nonexistent/path")

    def test_repository_initialization_permission_error(self):
        """Test repository initialization with permission error."""
        with (
            mock.patch(
                "pygit2.Repository", side_effect=PermissionError("Permission denied")
            ),
            pytest.raises(PermissionError),
        ):
            repository_module.Repository("/no/permission")


class TestRepositoryEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def repository_wrapper(self):
        """Provide a repository wrapper with mock."""
        mock_repo = mock.Mock(spec=pygit2.Repository)
        with mock.patch("pygit2.Repository", return_value=mock_repo):
            wrapper = repository_module.Repository("/test/path")
            wrapper._repo = mock_repo
            return wrapper

    def test_get_commits_by_pattern_walk_error(self, repository_wrapper):
        """Test commit pattern search when walk fails."""
        repository_wrapper._repo.head.target = "head_commit"
        repository_wrapper._repo.walk.side_effect = pygit2.GitError("Walk failed")

        results = repository_wrapper.get_commits_by_pattern("test", max_results=10)

        assert len(results) == 0

    def test_list_branches_with_invalid_refs(self, repository_wrapper):
        """Test branch listing with invalid reference names."""
        mock_branches = mock.Mock()
        mock_branches.local = ["valid-branch"]
        mock_branches.remote = []
        repository_wrapper._repo.branches = mock_branches

        branches = repository_wrapper.list_branches()

        assert branches == {"local": ["valid-branch"], "remote": []}

    def test_commit_model_with_timezone_edge_cases(self, repository_wrapper):
        """Test commit model creation with edge case timezones."""
        mock_commit = mock.Mock(spec=pygit2.Commit)
        mock_commit.id = "tz_test"
        mock_commit.message = "Timezone test"
        mock_commit.author.name = "TZ Author"
        mock_commit.author.email = "tz@example.com"
        mock_commit.author.time = 1640995200
        mock_commit.author.offset = -480  # Pacific time (-8 hours)
        mock_commit.committer.name = "TZ Committer"
        mock_commit.committer.email = "tz_committer@example.com"
        mock_commit.committer.time = 1640995200
        mock_commit.committer.offset = 330  # India time (+5:30 hours)
        mock_commit.parents = []

        result = repository_wrapper._commit_to_model(mock_commit)

        # Verify timezone offsets are handled correctly
        assert result.author_date.utcoffset().total_seconds() == -480 * 60
        assert result.committer_date.utcoffset().total_seconds() == 330 * 60
