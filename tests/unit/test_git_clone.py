"""Tests for async git clone functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.git import clone as async_clone_module
from ca_bhfuil.core.models import progress as progress_models


@pytest.mark.asyncio
class TestAsyncCloneLockManager:
    """Test async clone lock manager functionality."""

    async def test_lock_acquisition_and_release(self):
        """Test lock acquisition and release."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = pathlib.Path(tmp_dir) / "test-repo"

            async with async_clone_module.AsyncCloneLockManager(repo_path):
                lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
                assert lock_file.exists()

            assert not lock_file.exists()

    async def test_concurrent_lock_prevention(self):
        """Test that concurrent locks are prevented."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = pathlib.Path(tmp_dir) / "test-repo"

            async with async_clone_module.AsyncCloneLockManager(repo_path):
                with pytest.raises(RuntimeError, match="Clone already in progress"):
                    async with async_clone_module.AsyncCloneLockManager(repo_path):
                        pass

    async def test_lock_cleanup_on_exception(self):
        """Test lock cleanup when exception occurs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = pathlib.Path(tmp_dir) / "test-repo"

            try:
                async with async_clone_module.AsyncCloneLockManager(repo_path):
                    raise ValueError("Test exception")
            except ValueError:
                pass

            lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
            assert not lock_file.exists()


@pytest.mark.asyncio
class TestAsyncRepositoryCloner:
    """Test async repository cloner functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Provide temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = pathlib.Path(tmp_dir)
            yield {
                "cache": base_path / "cache",
                "state": base_path / "state",
            }

    @pytest.fixture
    def mock_git_manager(self):
        """Mock AsyncGitManager."""
        return mock.AsyncMock(spec=async_git.AsyncGitManager)

    async def test_cloner_initialization(self, mock_git_manager):
        """Test repository cloner initialization."""
        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
        assert cloner.config_manager is not None

    async def test_successful_clone_simulation(self, mock_git_manager, temp_dirs):
        """Test successful clone operation (mocked)."""
        conf = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

        mock_git_manager.run_in_executor.return_value = (
            None  # For pygit2.clone_repository
        )
        mock_git_manager.run_in_executor.side_effect = [
            True,  # For _is_valid_repository
            None,  # For pygit2.clone_repository
        ]

        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
        result = await cloner.clone_repository(conf)

        assert result.success is True
        assert result.repository_path == str(conf.repo_path)
        assert result.error is None

    async def test_existing_repository_handling(self, mock_git_manager, temp_dirs):
        """Test handling of existing repositories."""
        conf = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

        # Create fake existing repository
        conf.repo_path.mkdir(parents=True, exist_ok=True)

        mock_git_manager.run_in_executor.return_value = True  # For _is_valid_repository

        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
        result = await cloner.clone_repository(conf)

        assert result.success is True
        mock_git_manager.run_in_executor.assert_awaited_once_with(
            cloner._is_valid_repository, conf.repo_path
        )

    async def test_clone_error_handling(self, mock_git_manager, temp_dirs):
        """Test clone error handling."""
        conf = config.RepositoryConfig(
            name="unique-repo",
            source={"url": "https://github.com/test/unique-repo.git", "type": "git"},
        )

        # Mock the clone method to avoid lock conflicts
        with mock.patch.object(
            async_clone_module.AsyncRepositoryCloner, "_perform_clone"
        ) as mock_perform_clone:
            mock_perform_clone.side_effect = Exception("Network error")

            cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
            result = await cloner.clone_repository(conf)

            assert result.success is False
            assert result.error is not None
            assert "Network error" in result.error

    async def test_progress_callback_integration(self, mock_git_manager, temp_dirs):
        """Test progress callback integration."""
        conf = config.RepositoryConfig(
            name="progress-repo",
            source={"url": "https://github.com/test/progress-repo.git", "type": "git"},
        )
        progress_updates = []

        def progress_callback(progress: progress_models.CloneProgress):
            progress_updates.append(progress)

        # Mock the clone method to avoid lock conflicts
        with mock.patch.object(
            async_clone_module.AsyncRepositoryCloner, "_perform_clone"
        ) as mock_perform_clone:
            mock_perform_clone.return_value = mock.Mock()
            mock_perform_clone.return_value.success = True
            mock_perform_clone.return_value.duration = 1.0
            mock_perform_clone.return_value.repository_path = str(conf.repo_path)

            cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
            result = await cloner.clone_repository(conf, progress_callback)

            assert result.success is True


@pytest.mark.asyncio
class TestAuthenticationSetup:
    """Test authentication setup (mocked)."""

    @pytest.fixture
    def repo_config_with_auth(self):
        """Repository config with authentication."""
        return config.RepositoryConfig(
            name="auth-repo",
            source={"url": "git@github.com:private/repo.git", "type": "git"},
            auth_key="test-ssh",
        )

    @pytest.fixture
    def mock_git_manager(self):
        """Mock AsyncGitManager."""
        return mock.AsyncMock(spec=async_git.AsyncGitManager)

    async def test_ssh_auth_setup(self, repo_config_with_auth, mock_git_manager):
        """Test SSH authentication setup."""
        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)

        with (
            mock.patch.object(
                cloner.config_manager, "get_auth_method"
            ) as mock_get_auth_method,
            mock.patch("pathlib.Path.exists") as mock_exists,
            mock.patch("pygit2.Keypair") as mock_keypair,
        ):
            mock_get_auth_method.return_value = config.AuthMethod(
                type="ssh_key",
                ssh_key_path="~/.ssh/id_ed25519",
            )
            mock_exists.return_value = True

            callbacks = await cloner._setup_callbacks(repo_config_with_auth, None)

            # Verify the credentials callback was set using getattr (since we use setattr in production)
            credentials_func = getattr(callbacks, "credentials", None)
            assert credentials_func is not None
            # Test the credentials callback directly
            credentials_func("url", "user", 1)  # Mock allowed_types
            mock_keypair.assert_called_once()

    async def test_token_auth_setup(self, repo_config_with_auth, mock_git_manager):
        """Test token authentication setup."""
        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)

        with (
            mock.patch.object(
                cloner.config_manager, "get_auth_method"
            ) as mock_get_auth_method,
            mock.patch("pygit2.UserPass") as mock_userpass,
        ):
            mock_get_auth_method.return_value = config.AuthMethod(
                type="token",
                token_env="TEST_TOKEN",
            )

            with mock.patch.dict("os.environ", {"TEST_TOKEN": "test-token-value"}):
                callbacks = await cloner._setup_callbacks(repo_config_with_auth, None)

                # Verify the credentials callback was set using getattr (since we use setattr in production)
                credentials_func = getattr(callbacks, "credentials", None)
                assert credentials_func is not None
                # Test the credentials callback directly
                credentials_func("url", "user", 1)  # Mock allowed_types
                mock_userpass.assert_called_once()

    async def test_no_auth_setup(self, mock_git_manager):
        """Test setup without authentication."""
        conf = config.RepositoryConfig(
            name="public-repo",
            source={"url": "https://github.com/public/repo.git", "type": "git"},
        )

        cloner = async_clone_module.AsyncRepositoryCloner(mock_git_manager)
        callbacks = await cloner._setup_callbacks(conf, None)

        assert callbacks.credentials is None
