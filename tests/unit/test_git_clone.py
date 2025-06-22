"""Unit tests for git cloning functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ca_bhfuil.core.config import RepositoryConfig
from ca_bhfuil.core.git.clone import (
    CloneLockManager,
    CloneProgress,
    CloneResult,
    RepositoryCloner,
    clone_repository_by_url,
    validate_repository_by_path,
)


class TestCloneProgress:
    """Test clone progress tracking."""

    def test_empty_progress(self):
        """Test empty progress calculation."""
        progress = CloneProgress()
        assert progress.objects_progress == 0.0
        assert progress.deltas_progress == 0.0
        assert progress.overall_progress == 0.0

    def test_partial_progress(self):
        """Test partial progress calculation."""
        progress = CloneProgress(
            received_objects=50,
            total_objects=100,
            indexed_deltas=25,
            total_deltas=50,
        )
        
        assert progress.objects_progress == 50.0
        assert progress.deltas_progress == 50.0
        # Weighted: 0.8 * 50 + 0.2 * 50 = 50.0
        assert progress.overall_progress == 50.0

    def test_complete_progress(self):
        """Test complete progress calculation."""
        progress = CloneProgress(
            received_objects=100,
            total_objects=100,
            indexed_deltas=50,
            total_deltas=50,
        )
        
        assert progress.objects_progress == 100.0
        assert progress.deltas_progress == 100.0
        assert progress.overall_progress == 100.0

    def test_no_deltas_progress(self):
        """Test progress with no deltas."""
        progress = CloneProgress(
            received_objects=75,
            total_objects=100,
            total_deltas=0,  # No deltas
        )
        
        assert progress.objects_progress == 75.0
        assert progress.deltas_progress == 0.0
        # Weighted: 0.8 * 75 + 0.2 * 0 = 60.0
        assert progress.overall_progress == 60.0


class TestCloneResult:
    """Test clone result structure."""

    def test_successful_result(self):
        """Test successful clone result."""
        repo_path = Path("/test/repo")
        state_path = Path("/test/state")
        
        result = CloneResult(
            success=True,
            repo_path=repo_path,
            state_path=state_path,
            duration=5.0,
            objects_count=100,
            refs_count=10,
        )
        
        assert result.success is True
        assert result.repo_path == repo_path
        assert result.state_path == state_path
        assert result.duration == 5.0
        assert result.objects_count == 100
        assert result.refs_count == 10
        assert result.error is None

    def test_failed_result(self):
        """Test failed clone result."""
        repo_path = Path("/test/repo")
        state_path = Path("/test/state")
        
        result = CloneResult(
            success=False,
            repo_path=repo_path,
            state_path=state_path,
            duration=2.0,
            error="Network timeout",
        )
        
        assert result.success is False
        assert result.error == "Network timeout"
        assert result.objects_count == 0
        assert result.refs_count == 0


class TestCloneLockManager:
    """Test clone lock management."""

    def test_lock_acquisition_and_release(self):
        """Test normal lock acquisition and release."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / "test-repo"
            
            # Test normal operation
            with CloneLockManager(repo_path) as lock:
                assert lock.acquired is True
                assert lock.lock_file.exists()
            
            # Lock should be released
            assert not lock.lock_file.exists()

    def test_concurrent_lock_prevention(self):
        """Test prevention of concurrent locks."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / "test-repo"
            repo_path.parent.mkdir(exist_ok=True)
            
            # Create existing lock
            lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
            lock_file.touch()
            
            # Should raise error for concurrent access
            with pytest.raises(RuntimeError, match="already in progress"):
                with CloneLockManager(repo_path):
                    pass

    def test_lock_cleanup_on_exception(self):
        """Test lock cleanup when exception occurs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / "test-repo"
            
            try:
                with CloneLockManager(repo_path):
                    raise ValueError("Test exception")
            except ValueError:
                pass
            
            # Lock should still be cleaned up
            lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
            assert not lock_file.exists()


class TestRepositoryCloner:
    """Test repository cloner functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Provide temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            yield {
                "cache": base_path / "cache",
                "state": base_path / "state",
            }


    def test_cloner_initialization(self):
        """Test repository cloner initialization."""
        cloner = RepositoryCloner()
        assert cloner.config_manager is not None

    def test_repository_validation(self, temp_dirs):
        """Test repository validation."""
        cloner = RepositoryCloner()
        repo_path = temp_dirs["cache"] / "test-repo"
        
        # Non-existent repository
        validation = cloner.validate_clone(repo_path)
        assert validation["path_exists"] is False
        assert validation["is_git_repo"] is False
        assert validation["healthy"] is False

    @patch("ca_bhfuil.core.git.clone.pygit2.clone_repository")
    @patch("ca_bhfuil.core.git.clone.pygit2.Repository")
    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_successful_clone_simulation(self, mock_state_dir, mock_cache_dir, mock_repo_class, mock_clone, temp_dirs):
        """Test successful clone operation (mocked)."""
        # Mock the XDG directories to use our temp dirs
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        
        # Mock the cloned repository
        mock_repo = Mock()
        mock_repo.is_bare = True
        mock_repo.references = ["refs/heads/main", "refs/heads/develop"]
        mock_repo.odb = [Mock() for _ in range(100)]  # 100 objects
        
        mock_clone.return_value = mock_repo
        mock_repo_class.return_value = mock_repo
        
        cloner = RepositoryCloner()
        result = cloner.clone_repository(config)
        
        assert result.success is True
        assert result.objects_count >= 0
        assert result.refs_count >= 0
        assert result.duration > 0
        assert result.error is None

    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_existing_repository_handling(self, mock_state_dir, mock_cache_dir, temp_dirs):
        """Test handling of existing repositories."""
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        
        # Create fake existing repository
        config.repo_path.mkdir(parents=True, exist_ok=True)
        
        with patch("ca_bhfuil.core.git.clone.RepositoryCloner._is_valid_repository") as mock_valid:
            mock_valid.return_value = True
            
            cloner = RepositoryCloner()
            result = cloner.clone_repository(config)
            
            assert result.success is True
            # Should not attempt actual clone for existing repo

    @patch("ca_bhfuil.core.git.clone.pygit2.clone_repository")
    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_clone_error_handling(self, mock_state_dir, mock_cache_dir, mock_clone, temp_dirs):
        """Test clone error handling."""
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        
        # Simulate clone failure
        mock_clone.side_effect = Exception("Network error")
        
        cloner = RepositoryCloner()
        result = cloner.clone_repository(config)
        
        assert result.success is False
        assert "Network error" in result.error
        assert result.duration > 0

    @patch("ca_bhfuil.core.git.clone.pygit2.clone_repository")
    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_progress_callback_integration(self, mock_state_dir, mock_cache_dir, mock_clone, temp_dirs):
        """Test progress callback integration."""
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        progress_updates = []
        
        def progress_callback(progress: CloneProgress):
            progress_updates.append(progress)
        
        # Mock successful clone
        mock_repo = Mock()
        mock_repo.is_bare = True
        mock_repo.references = []
        mock_repo.odb = []
        mock_clone.return_value = mock_repo
        
        cloner = RepositoryCloner()
        result = cloner.clone_repository(config, progress_callback)
        
        assert result.success is True

    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_repository_removal(self, mock_state_dir, mock_cache_dir, temp_dirs):
        """Test repository removal."""
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        
        # Create fake repository and state
        config.repo_path.mkdir(parents=True, exist_ok=True)
        config.state_path.mkdir(parents=True, exist_ok=True)
        
        cloner = RepositoryCloner()
        success = cloner.remove_repository(config)
        
        assert success is True
        assert not config.repo_path.exists()
        assert not config.state_path.exists()

    @patch("ca_bhfuil.core.config.get_cache_dir")
    @patch("ca_bhfuil.core.config.get_state_dir")
    def test_remove_with_active_lock(self, mock_state_dir, mock_cache_dir, temp_dirs):
        """Test removal prevention with active lock."""
        mock_cache_dir.return_value = temp_dirs["cache"]
        mock_state_dir.return_value = temp_dirs["state"]
        
        config = RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )
        
        # Create fake repository
        config.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Create lock file
        lock_file = config.repo_path.parent / f".{config.repo_path.name}.clone_lock"
        lock_file.touch()
        
        cloner = RepositoryCloner()
        success = cloner.remove_repository(config)
        
        assert success is False
        assert config.repo_path.exists()  # Should not be removed


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("ca_bhfuil.core.git.clone.RepositoryCloner.clone_repository")
    def test_clone_repository_by_url(self, mock_clone):
        """Test clone by URL convenience function."""
        mock_result = CloneResult(
            success=True,
            repo_path=Path("/test/repo"),
            state_path=Path("/test/state"),
            duration=1.0,
        )
        mock_clone.return_value = mock_result
        
        result = clone_repository_by_url("https://github.com/test/repo.git")
        
        assert result.success is True
        mock_clone.assert_called_once()

    @patch("ca_bhfuil.core.git.clone.RepositoryCloner.validate_clone")
    def test_validate_repository_by_path(self, mock_validate):
        """Test repository validation convenience function."""
        mock_validate.return_value = {"healthy": True, "path_exists": True}
        
        result = validate_repository_by_path(Path("/test/repo"))
        
        assert result["healthy"] is True
        mock_validate.assert_called_once_with(Path("/test/repo"))


class TestAuthenticationSetup:
    """Test authentication setup (mocked)."""

    @pytest.fixture
    def repo_config_with_auth(self):
        """Repository config with authentication."""
        return RepositoryConfig(
            name="auth-repo",
            source={"url": "git@github.com:private/repo.git", "type": "git"},
            auth_key="test-ssh",
        )

    def test_ssh_auth_setup(self, repo_config_with_auth):
        """Test SSH authentication setup."""
        cloner = RepositoryCloner()
        
        # Mock auth method
        with patch.object(cloner.config_manager, "get_auth_method") as mock_auth:
            from ca_bhfuil.core.config import AuthMethod
            
            mock_auth.return_value = AuthMethod(
                type="ssh_key",
                ssh_key_path="~/.ssh/id_ed25519",
            )
            
            auth_callbacks = cloner._setup_authentication(repo_config_with_auth)
            
            # Should have credentials callback
            assert "credentials" in auth_callbacks
            assert callable(auth_callbacks["credentials"])

    def test_token_auth_setup(self, repo_config_with_auth):
        """Test token authentication setup."""
        cloner = RepositoryCloner()
        
        with patch.object(cloner.config_manager, "get_auth_method") as mock_auth:
            from ca_bhfuil.core.config import AuthMethod
            
            mock_auth.return_value = AuthMethod(
                type="token",
                token_env="TEST_TOKEN",
            )
            
            with patch.dict("os.environ", {"TEST_TOKEN": "test-token-value"}):
                auth_callbacks = cloner._setup_authentication(repo_config_with_auth)
                
                assert "credentials" in auth_callbacks
                assert callable(auth_callbacks["credentials"])

    def test_no_auth_setup(self):
        """Test setup without authentication."""
        config = RepositoryConfig(
            name="public-repo",
            source={"url": "https://github.com/public/repo.git", "type": "git"},
        )
        
        cloner = RepositoryCloner()
        auth_callbacks = cloner._setup_authentication(config)
        
        assert auth_callbacks == {}