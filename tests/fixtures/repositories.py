"""Test repository fixtures for ca-bhfuil testing."""

import collections.abc
from datetime import datetime
from datetime import timezone
import pathlib
import shutil
import tempfile

import pygit2
import pytest


class TestRepository:
    """A test git repository with known commit history."""

    def __init__(self, path: pathlib.Path):
        """Initialize test repository."""
        self.path = path
        self.repo = pygit2.init_repository(str(path))
        self.commits: dict[str, str] = {}  # name -> sha mapping
        self._setup_signature()

    def _setup_signature(self) -> None:
        """Set up default signature for commits."""
        self.signature = pygit2.Signature(
            "Test Author",
            "test@example.com",
            int(datetime.now(timezone.utc).timestamp()),
            0,
        )

    def add_file(self, filename: str, content: str) -> None:
        """Add a file to the repository."""
        file_path = self.path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.repo.index.add(filename)
        self.repo.index.write()

    def commit(self, message: str, name: str | None = None) -> str:
        """Create a commit and optionally store it by name."""
        tree = self.repo.index.write_tree()
        parents = []
        if not self.repo.is_empty:
            parents = [self.repo.head.target]

        commit_sha = self.repo.create_commit(
            "HEAD", self.signature, self.signature, message, tree, parents
        )

        if name:
            self.commits[name] = str(commit_sha)

        return str(commit_sha)

    def create_branch(self, name: str, from_commit: str | None = None) -> None:
        """Create a new branch."""
        commit = self.repo.get(from_commit) if from_commit else self.repo.head.peel()

        self.repo.branches.local.create(name, commit)

    def checkout_branch(self, name: str) -> None:
        """Checkout a branch."""
        branch = self.repo.branches[name]
        ref = self.repo.lookup_reference(branch.name)
        self.repo.checkout(ref)

    def create_tag(
        self, name: str, message: str = "", commit: str | None = None
    ) -> None:
        """Create a tag."""
        target = self.repo.get(commit) if commit else self.repo.head.peel()

        if message:
            self.repo.create_tag(name, target, self.signature, message)
        else:
            self.repo.create_reference(f"refs/tags/{name}", target.id)

    def get_commit_sha(self, name: str) -> str:
        """Get commit SHA by name."""
        return self.commits[name]


@pytest.fixture
def temp_git_dir() -> collections.abc.Generator[pathlib.Path, None, None]:
    """Provide a temporary directory for git operations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield pathlib.Path(tmp_dir)


@pytest.fixture
def minimal_repo(temp_git_dir: pathlib.Path) -> TestRepository:
    """Create a minimal repository with a single commit."""
    repo = TestRepository(temp_git_dir / "minimal")
    repo.add_file("README.md", "# Minimal Test Repository\n")
    repo.commit("Initial commit", "initial")
    return repo


@pytest.fixture
def multi_branch_repo(temp_git_dir: pathlib.Path) -> TestRepository:
    """Create a repository with multiple branches and commits."""
    repo = TestRepository(temp_git_dir / "multi_branch")

    # Initial commit on main
    repo.add_file("README.md", "# Multi-Branch Test Repository\n")
    repo.commit("Initial commit", "initial")

    # Add some commits on main
    repo.add_file("file1.txt", "Content 1")
    repo.commit("Add file1", "file1")

    repo.add_file("file2.txt", "Content 2")
    repo.commit("Add file2", "file2")

    # Create feature branch
    repo.create_branch("feature", repo.get_commit_sha("file1"))
    repo.checkout_branch("feature")

    repo.add_file("feature.txt", "Feature content")
    repo.commit("Add feature", "feature")

    repo.add_file("feature.txt", "Feature content updated")
    repo.commit("Update feature", "feature_update")

    # Create stable branch
    repo.create_branch("stable", repo.get_commit_sha("initial"))
    repo.checkout_branch("stable")

    repo.add_file("stable.txt", "Stable content")
    repo.commit("Add stable feature", "stable")

    # Back to main for merge
    repo.checkout_branch("main")

    return repo


@pytest.fixture
def tagged_repo(temp_git_dir: pathlib.Path) -> TestRepository:
    """Create a repository with tags."""
    repo = TestRepository(temp_git_dir / "tagged")

    # Initial release
    repo.add_file("README.md", "# Tagged Repository\n")
    repo.add_file("version.txt", "1.0.0")
    repo.commit("Release 1.0.0", "v1.0.0")
    repo.create_tag("v1.0.0", "Release version 1.0.0")

    # Bug fix
    repo.add_file("version.txt", "1.0.1")
    repo.commit("Bugfix release 1.0.1", "v1.0.1")
    repo.create_tag("v1.0.1", "Bugfix release 1.0.1")

    # Feature release
    repo.add_file("feature.txt", "New feature")
    repo.add_file("version.txt", "1.1.0")
    repo.commit("Feature release 1.1.0", "v1.1.0")
    repo.create_tag("v1.1.0", "Feature release 1.1.0")

    return repo


@pytest.fixture
def complex_history_repo(temp_git_dir: pathlib.Path) -> TestRepository:
    """Create a repository with complex history including merges."""
    repo = TestRepository(temp_git_dir / "complex")

    # Initial commit
    repo.add_file("README.md", "# Complex History Repository\n")
    repo.commit("Initial commit", "initial")

    # Main branch development
    repo.add_file("main.txt", "Main development")
    repo.commit("Main development", "main_dev")

    # Create and develop feature branch
    repo.create_branch("feature", repo.get_commit_sha("initial"))
    repo.checkout_branch("feature")

    repo.add_file("feature.txt", "Feature work")
    repo.commit("Feature development", "feature_dev")

    repo.add_file("feature.txt", "Feature work continued")
    repo.commit("Continue feature work", "feature_cont")

    # Create hotfix branch from initial
    repo.create_branch("hotfix", repo.get_commit_sha("initial"))
    repo.checkout_branch("hotfix")

    repo.add_file("hotfix.txt", "Critical fix")
    repo.commit("Critical hotfix", "hotfix")

    # Back to main to merge hotfix
    repo.checkout_branch("main")

    # Simulate merge (simplified - just add the hotfix file)
    repo.add_file("hotfix.txt", "Critical fix")
    repo.commit("Merge hotfix into main", "merge_hotfix")

    return repo


@pytest.fixture
def empty_repo(temp_git_dir: pathlib.Path) -> TestRepository:
    """Create an empty repository."""
    return TestRepository(temp_git_dir / "empty")


# Real-world repository configurations for testing
REAL_WORLD_REPOS = {
    "os-vif": {
        "url": "https://opendev.org/openstack/os-vif",
        "description": "OpenStack os-vif library - medium-sized Python project",
        "expected_branches": ["master", "stable/2023.1", "stable/2023.2"],
        "expected_tags_pattern": r"^\d+\.\d+\.\d+$",
        "approximate_commits": 500,  # Rough estimate for validation
    },
    "small-test": {
        "url": "https://github.com/octocat/Hello-World",
        "description": "GitHub's hello world repository - minimal test case",
        "expected_branches": ["master"],
        "expected_tags_pattern": None,
        "approximate_commits": 10,
    },
}


@pytest.fixture
def real_world_repo_configs() -> dict:
    """Provide real-world repository configurations for testing."""
    return REAL_WORLD_REPOS


@pytest.fixture
def os_vif_config() -> dict:
    """Provide os-vif repository configuration."""
    return REAL_WORLD_REPOS["os-vif"]


def create_test_repo_config(repo_url: str, local_path: pathlib.Path) -> dict:
    """Create a repository configuration for testing."""
    return {
        "url": repo_url,
        "local_path": str(local_path),
        "description": f"Test repository at {repo_url}",
        "sync_enabled": True,
        "analysis_enabled": True,
    }


def cleanup_test_repos(base_path: pathlib.Path) -> None:
    """Clean up test repositories."""
    if base_path.exists():
        shutil.rmtree(base_path)
