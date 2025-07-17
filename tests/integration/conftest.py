"""Integration test fixtures for ca-bhfuil."""

from contextlib import contextmanager
import pathlib
import tempfile
from unittest import mock

import pytest

from tests.fixtures import repositories


@pytest.fixture
def fake_home_dir():
    """Create a fake home directory with proper XDG structure.

    Creates a temporary directory structure that mimics a real user home directory:
    fake_home/
    ├── .config/          (XDG_CONFIG_HOME should point here)
    ├── .cache/           (XDG_CACHE_HOME should point here)
    └── .local/
        └── state/        (XDG_STATE_HOME should point here)

    Returns:
        Dict with paths to the fake home directory and XDG subdirectories.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = pathlib.Path(tmp_dir)

        # Create XDG directory structure
        config_dir = fake_home / ".config"
        cache_dir = fake_home / ".cache"
        state_dir = fake_home / ".local" / "state"

        config_dir.mkdir(parents=True)
        cache_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        yield {
            "home": fake_home,
            "config": config_dir,
            "cache": cache_dir,
            "state": state_dir,
        }


@pytest.fixture
def isolated_xdg_environment(fake_home_dir):
    """Set up isolated XDG environment variables.

    Sets XDG environment variables to point to the fake home directory
    structure, ensuring complete isolation from the real user environment.

    Args:
        fake_home_dir: The fake home directory fixture.

    Returns:
        Context manager that sets up and tears down XDG environment variables.
    """

    @contextmanager
    def xdg_context():
        with mock.patch.dict(
            "os.environ",
            {
                "XDG_CONFIG_HOME": str(fake_home_dir["config"]),
                "XDG_CACHE_HOME": str(fake_home_dir["cache"]),
                "XDG_STATE_HOME": str(fake_home_dir["state"]),
            },
            clear=False,
        ):
            yield fake_home_dir

    return xdg_context


@pytest.fixture
def temp_git_repo_dir():
    """Create a temporary directory for git repositories.

    This should be separate from the XDG directories to maintain
    proper separation between source repositories and application data.

    Returns:
        Path to temporary directory for git repositories.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield pathlib.Path(tmp_dir)


@pytest.fixture
def test_git_repository(temp_git_repo_dir):
    """Create a test git repository with sample commits.

    Creates a real git repository with actual commits for testing.

    Args:
        temp_git_repo_dir: Temporary directory for git repositories.

    Returns:
        TestRepository instance with sample commits.
    """
    repo_path = temp_git_repo_dir / "test-repo"
    test_repo = repositories.TestRepository(repo_path)

    # Add some sample commits
    test_repo.add_file("README.md", "# Test Repository\n")
    test_repo.commit("Initial commit")

    test_repo.add_file("file1.txt", "Content 1")
    test_repo.commit("Add file1")

    return test_repo


@pytest.fixture
def integration_test_environment(isolated_xdg_environment, test_git_repository):
    """Complete integration test environment setup.

    Combines XDG environment isolation with a test git repository
    for comprehensive integration testing.

    Args:
        isolated_xdg_environment: XDG environment fixture.
        test_git_repository: Test git repository fixture.

    Returns:
        Dict with environment context and test repository.
    """

    def setup_environment():
        xdg_context = isolated_xdg_environment()
        return {
            "xdg_context": xdg_context,
            "test_repo": test_git_repository,
        }

    return setup_environment
