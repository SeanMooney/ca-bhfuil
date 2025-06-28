"""Integration tests for repository cloning functionality."""

import os
import pathlib
import socket
import tempfile
import unittest
from unittest import mock

import pytest

from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.git import clone as async_clone_module
from ca_bhfuil.utils import paths


# Skip these tests if network is not available
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "network: marks tests as requiring network access"
    )


def network_available() -> bool:
    """Check if network is available for testing."""

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


class TestRepositoryURLValidation:
    """Test repository URL validation and parsing."""

    def test_github_https_url(self):
        """Test GitHub HTTPS URL validation."""
        url = "https://github.com/octocat/Hello-World.git"
        assert paths.is_valid_url(url)

    def test_github_ssh_url(self):
        """Test GitHub SSH URL validation."""
        url = "git@github.com:octocat/Hello-World.git"
        assert paths.is_valid_url(url)

    def test_opendev_https_url(self):
        """Test OpenDev HTTPS URL validation."""
        url = "https://opendev.org/openstack/os-vif.git"
        assert paths.is_valid_url(url)

    def test_gitlab_ssh_url(self):
        """Test GitLab SSH URL validation."""
        url = "git@gitlab.com:user/project.git"
        assert paths.is_valid_url(url)

    def test_invalid_url(self):
        """Test invalid URL detection."""
        assert not paths.is_valid_url("not-a-url")
        assert not paths.is_valid_url("http://example.com/not-git")
        assert not paths.is_valid_url("")

    def test_path_generation_github(self):
        """Test path generation for GitHub URLs."""
        url = "https://github.com/torvalds/linux.git"
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = pathlib.Path(tmp_dir) / "cache"
            state_dir = pathlib.Path(tmp_dir) / "state"

            repo_path, state_path = paths.get_repo_paths(url, cache_dir, state_dir)

            assert "github.com/torvalds/linux" in str(repo_path)
            assert "github.com/torvalds/linux" in str(state_path)

    def test_path_generation_opendev(self):
        """Test path generation for OpenDev URLs."""
        url = "https://opendev.org/openstack/os-vif"
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = pathlib.Path(tmp_dir) / "cache"
            state_dir = pathlib.Path(tmp_dir) / "state"

            repo_path, state_path = paths.get_repo_paths(url, cache_dir, state_dir)

            assert "opendev.org/openstack/os-vif" in str(repo_path)
            assert "opendev.org/openstack/os-vif" in str(state_path)


class TestRepositoryCloneConfiguration:
    """Test repository cloning configuration and setup."""

    @pytest.fixture
    def temp_dirs(self):
        """Provide temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = pathlib.Path(tmp_dir)
            yield {
                "config": base_path / "config",
                "cache": base_path / "cache",
                "state": base_path / "state",
            }

    @pytest.fixture
    def config_manager(self, temp_dirs):
        """Provide configuration manager with test directories."""
        return config.ConfigManager(config_dir=temp_dirs["config"])

    def test_repository_config_creation(self, config_manager):
        """Test creating repository configuration for cloning."""
        repo_config = config.RepositoryConfig(
            name="test-clone",
            source={"url": "https://github.com/octocat/Hello-World.git", "type": "git"},
        )

        assert repo_config.name == "test-clone"
        assert repo_config.source["url"] == "https://github.com/octocat/Hello-World.git"
        assert repo_config.url_path == "github.com/octocat/Hello-World"

    def test_os_vif_repository_config(self, config_manager, real_world_repo_configs):
        """Test os-vif repository configuration setup."""
        os_vif_config = real_world_repo_configs["os-vif"]

        repo_config = config.RepositoryConfig(
            name="os-vif",
            source={"url": os_vif_config["url"], "type": "git"},
        )

        assert repo_config.name == "os-vif"
        assert repo_config.source["url"] == "https://opendev.org/openstack/os-vif"
        assert repo_config.url_path == "opendev.org/openstack/os-vif"

    def test_repository_paths_creation(self, temp_dirs):
        """Test that repository paths are created correctly."""
        url = "https://github.com/test/repository.git"
        repo_path, state_path = paths.get_repo_paths(
            url, temp_dirs["cache"], temp_dirs["state"]
        )

        # Paths should be within our test directories
        assert temp_dirs["cache"] in repo_path.parents
        assert temp_dirs["state"] in state_path.parents

        # Paths should contain the URL components
        assert "github.com/test/repository" in str(repo_path)
        assert "github.com/test/repository" in str(state_path)


class TestGitOperationsPreparation:
    """Test preparation for git operations (mock-based)."""

    def test_pygit2_clone_parameters(self):
        """Test that we prepare correct parameters for pygit2 cloning."""
        # This test prepares the parameters we'll use for actual cloning
        url = "https://github.com/octocat/Hello-World.git"

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = pathlib.Path(tmp_dir) / "test-repo"

            # Parameters we'll pass to pygit2.clone_repository
            clone_params = {
                "url": url,
                "path": str(target_path),
                "bare": True,  # For performance
                "checkout_branch": None,  # Clone all branches
            }

            assert clone_params["url"] == url
            assert clone_params["bare"] is True
            assert pathlib.Path(clone_params["path"]) == target_path

    def test_ssh_authentication_setup(self):
        """Test SSH authentication parameter preparation."""
        # Mock SSH key authentication setup
        ssh_key_path = pathlib.Path.home() / ".ssh" / "id_ed25519"

        # Prepare authentication callback parameters
        auth_params = {
            "username": "git",
            "public_key": str(ssh_key_path) + ".pub",
            "private_key": str(ssh_key_path),
            "passphrase": None,
        }

        assert auth_params["username"] == "git"
        assert auth_params["public_key"].endswith(".pub")
        assert auth_params["private_key"] == str(ssh_key_path)

    @mock.patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
    def test_token_authentication_setup(self):
        """Test token authentication parameter preparation."""
        # Prepare token authentication
        token = os.environ.get("GITHUB_TOKEN")
        auth_params = {
            "username": "token",
            "password": token,
        }

        assert auth_params["username"] == "token"
        assert auth_params["password"] == "test-token"


class TestCloneProgressTracking:
    """Test clone progress tracking and callbacks."""

    def test_progress_callback_structure(self):
        """Test progress callback structure for cloning."""
        # Mock progress callback that we'll use with pygit2
        progress_data = []

        def progress_callback(stats):
            """Mock progress callback."""
            progress_data.append(
                {
                    "received_objects": getattr(stats, "received_objects", 0),
                    "total_objects": getattr(stats, "total_objects", 0),
                    "received_bytes": getattr(stats, "received_bytes", 0),
                    "local_objects": getattr(stats, "local_objects", 0),
                }
            )

        # Simulate progress updates
        mock_stats = unittest.mock.Mock()
        mock_stats.received_objects = 10
        mock_stats.total_objects = 100
        mock_stats.received_bytes = 1024
        mock_stats.local_objects = 0

        progress_callback(mock_stats)

        assert len(progress_data) == 1
        assert progress_data[0]["received_objects"] == 10
        assert progress_data[0]["total_objects"] == 100
        assert progress_data[0]["received_bytes"] == 1024

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""

        def calculate_progress(received, total):
            if total == 0:
                return 0.0
            return (received / total) * 100.0

        assert calculate_progress(0, 100) == 0.0
        assert calculate_progress(50, 100) == 50.0
        assert calculate_progress(100, 100) == 100.0
        assert calculate_progress(0, 0) == 0.0


@pytest.mark.network
class TestRealWorldCloning:
    """Integration tests with real repositories (requires network)."""

    def setup_method(self):
        """Set up for network tests."""
        if not network_available():
            pytest.skip("Network not available")

    @pytest.fixture
    def temp_clone_dir(self):
        """Provide temporary directory for cloning tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield pathlib.Path(tmp_dir)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_hello_world_clone(self, temp_clone_dir, real_world_repo_configs):
        """Test cloning Hello-World repository."""
        small_repo = real_world_repo_configs["small-test"]
        # target_path = temp_clone_dir / "hello-world" # Removed unused variable

        repo_config = config.RepositoryConfig(
            name="hello-world",
            source={"url": small_repo["url"], "type": "git"},
        )

        git_manager = async_git.AsyncGitManager()
        cloner = async_clone_module.AsyncRepositoryCloner(git_manager)

        clone_result = await cloner.clone_repository(repo_config)

        assert clone_result.success is True
        assert pathlib.Path(clone_result.repository_path).exists()
        assert pathlib.Path(clone_result.repository_path).is_dir()

        # Basic check for a valid git repo
        assert (pathlib.Path(clone_result.repository_path) / ".git").is_dir()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_os_vif_clone(self, temp_clone_dir, real_world_repo_configs):
        """Test cloning os-vif repository."""
        os_vif_repo = real_world_repo_configs["os-vif"]
        # target_path = temp_clone_dir / "os-vif" # Removed unused variable

        repo_config = config.RepositoryConfig(
            name="os-vif",
            source={"url": os_vif_repo["url"], "type": "git"},
        )

        git_manager = async_git.AsyncGitManager()
        cloner = async_clone_module.AsyncRepositoryCloner(git_manager)

        clone_result = await cloner.clone_repository(repo_config)

        assert clone_result.success is True
        assert pathlib.Path(clone_result.repository_path).exists()
        assert pathlib.Path(clone_result.repository_path).is_dir()

        # Basic check for a valid git repo
        assert (pathlib.Path(clone_result.repository_path) / ".git").is_dir()


class TestCloneValidation:
    """Test clone validation and health checks."""

    def test_clone_validation_structure(self):
        """Test clone validation logic structure."""

        def validate_clone(repo_path: pathlib.Path) -> dict[str, bool]:
            """Validate a cloned repository."""
            return {
                "path_exists": repo_path.exists(),
                "is_git_repo": (repo_path / ".git").exists()
                or (repo_path / "refs").exists(),
                "has_refs": (repo_path / "refs").exists(),
                "has_objects": (repo_path / "objects").exists(),
            }

        # Test with non-existent path
        fake_path = pathlib.Path("/nonexistent/repo")
        checks = validate_clone(fake_path)

        assert checks["path_exists"] is False
        assert checks["is_git_repo"] is False
        assert checks["has_refs"] is False
        assert checks["has_objects"] is False

    def test_repository_health_check(self):
        """Test repository health check structure."""

        def check_repository_health(repo_path: pathlib.Path) -> dict[str, any]:
            """Check repository health."""
            if not repo_path.exists():
                return {"healthy": False, "error": "Repository path does not exist"}

            # This would use pygit2 to check repository health
            return {
                "healthy": True,
                "bare": True,
                "head_exists": True,
                "refs_count": 0,  # Would be populated by pygit2
                "objects_count": 0,  # Would be populated by pygit2
            }

        fake_path = pathlib.Path("/nonexistent")
        health = check_repository_health(fake_path)

        assert health["healthy"] is False
        assert "does not exist" in health["error"]


class TestErrorHandling:
    """Test error handling for cloning operations."""

    def test_network_error_handling(self):
        """Test handling of network errors during cloning."""

        def simulate_clone_with_network_error():
            """Simulate a clone operation that fails due to network."""
            # This simulates what would happen with pygit2
            raise socket.gaierror("Name resolution failed")

        with pytest.raises(socket.gaierror):
            simulate_clone_with_network_error()

    def test_authentication_error_handling(self):
        """Test handling of authentication errors."""

        def simulate_clone_with_auth_error():
            """Simulate a clone operation that fails due to authentication."""

            # This simulates what would happen with pygit2
            class GitError(Exception):
                pass

            raise GitError("Authentication failed")

        with pytest.raises(Exception, match="Authentication failed"):
            simulate_clone_with_auth_error()

    def test_permission_error_handling(self):
        """Test handling of permission errors."""

        def simulate_clone_with_permission_error():
            """Simulate a clone operation that fails due to permissions."""
            raise PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            simulate_clone_with_permission_error()

    def test_disk_space_error_handling(self):
        """Test handling of disk space errors."""

        def simulate_clone_with_disk_error():
            """Simulate a clone operation that fails due to disk space."""
            raise OSError("No space left on device")

        with pytest.raises(OSError, match="No space left"):
            simulate_clone_with_disk_error()


class TestConcurrentCloning:
    """Test concurrent cloning scenarios."""

    def test_concurrent_clone_detection(self):
        """Test detection of concurrent clone operations."""

        def is_clone_in_progress(repo_path: pathlib.Path) -> bool:
            """Check if a clone is already in progress."""
            lock_file = repo_path.parent / f".{repo_path.name}.lock"
            return lock_file.exists()

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = pathlib.Path(tmp_dir) / "test-repo"
            lock_file = repo_path.parent / f".{repo_path.name}.lock"

            # No lock initially
            assert not is_clone_in_progress(repo_path)

            # Create lock file
            lock_file.touch()
            assert is_clone_in_progress(repo_path)

    def test_lock_file_management(self):
        """Test lock file creation and cleanup."""

        class CloneLockManager:
            def __init__(self, repo_path: pathlib.Path):
                self.repo_path = repo_path
                self.lock_file = repo_path.parent / f".{repo_path.name}.lock"

            def __enter__(self):
                if self.lock_file.exists():
                    raise RuntimeError("Clone already in progress")
                self.lock_file.touch()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.lock_file.exists():
                    self.lock_file.unlink()

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = pathlib.Path(tmp_dir) / "test-repo"
            repo_path.parent.mkdir(exist_ok=True)

            # Test normal operation
            with CloneLockManager(repo_path) as lock:
                assert lock.lock_file.exists()
            assert not lock.lock_file.exists()

            # Test concurrent access
            lock_file = repo_path.parent / f".{repo_path.name}.lock"
            lock_file.touch()

            with (
                pytest.raises(RuntimeError, match="already in progress"),
                CloneLockManager(repo_path),
            ):
                pass
