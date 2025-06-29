"""Tests for CLI functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest
from typer.testing import CliRunner

from ca_bhfuil.cli import main


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Provide a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield pathlib.Path(temp_dir)


class TestConfigCommands:
    """Test configuration management commands."""

    def test_config_init_success(self, cli_runner, temp_config_dir):
        """Test successful configuration initialization."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            # Mock that the repositories file doesn't exist (so init can proceed)
            mock_manager.repositories_file.exists.return_value = False
            mock_manager.generate_default_config.return_value = True
            mock_manager.config_dir = temp_config_dir
            mock_manager.repositories_file = temp_config_dir / "repos.yaml"
            mock_manager.global_settings_file = temp_config_dir / "global.yaml"
            mock_manager.auth_file = temp_config_dir / "auth.yaml"

            result = cli_runner.invoke(main.app, ["config", "init"])
            assert result.exit_code == 0
            assert "Configuration initialized successfully" in result.stdout
            mock_manager.generate_default_config.assert_called_once()

    def test_config_status(self, cli_runner, temp_config_dir):
        """Test configuration status display."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.config.get_state_dir",
                return_value=temp_config_dir / "state",
            ),
            mock.patch(
                "ca_bhfuil.core.config.get_cache_dir",
                return_value=temp_config_dir / "cache",
            ),
        ):
            result = cli_runner.invoke(main.app, ["config", "status"])
            assert result.exit_code == 0
            assert "Configuration Status" in result.stdout


class TestRepoCommands:
    """Test repository management commands."""

    def test_repo_add_success(self, cli_runner, temp_config_dir):
        """Test successful repository addition."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
            mock.patch(
                "ca_bhfuil.core.git.clone.AsyncRepositoryCloner"
            ) as mock_cloner_class,
            mock.patch(
                "ca_bhfuil.cli.async_bridge.with_progress"
            ) as mock_with_progress,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_repository_config.return_value = None

            # Mock the configuration object with non-async repos attribute
            mock_config = mock.Mock()
            mock_config.repos = []  # Use a real list to avoid async mock issues
            # Use side_effect to ensure the mock object is returned directly
            mock_manager.load_configuration = mock.AsyncMock(return_value=mock_config)
            mock_manager.save_configuration = mock.AsyncMock(return_value=None)

            # Mock with_progress to return the awaited result directly
            async def mock_with_progress_func(coro, *args):
                if hasattr(coro, "__await__"):
                    return await coro
                return coro

            mock_with_progress.side_effect = mock_with_progress_func

            mock_cloner = mock.AsyncMock()
            mock_cloner_class.return_value = mock_cloner
            mock_cloner.clone_repository.return_value = mock.Mock()
            mock_cloner.clone_repository.return_value.success = True

            result = cli_runner.invoke(
                main.app, ["repo", "add", "https://github.com/test/repo.git"]
            )
            assert result.exit_code == 0
            assert "Repository added to configuration" in result.stdout

    def test_repo_add_force(self, cli_runner, temp_config_dir):
        """Test repository addition with force flag."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
            mock.patch(
                "ca_bhfuil.core.git.clone.AsyncRepositoryCloner"
            ) as mock_cloner_class,
            mock.patch(
                "ca_bhfuil.cli.async_bridge.with_progress"
            ) as mock_with_progress,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_repository_config.return_value = None

            # Mock the configuration object with non-async repos attribute
            mock_config = mock.Mock()
            mock_config.repos = []  # Use a real list to avoid async mock issues
            # Use side_effect to ensure the mock object is returned directly
            mock_manager.load_configuration = mock.AsyncMock(return_value=mock_config)
            mock_manager.save_configuration = mock.AsyncMock(return_value=None)

            # Mock with_progress to return the awaited result directly
            async def mock_with_progress_func(coro, *args):
                if hasattr(coro, "__await__"):
                    return await coro
                return coro

            mock_with_progress.side_effect = mock_with_progress_func

            mock_cloner = mock.AsyncMock()
            mock_cloner_class.return_value = mock_cloner
            mock_cloner.clone_repository.return_value = mock.Mock()
            mock_cloner.clone_repository.return_value.success = True

            result = cli_runner.invoke(
                main.app, ["repo", "add", "--force", "https://github.com/test/repo.git"]
            )
            assert result.exit_code == 0
            assert "Repository added to configuration" in result.stdout


class TestMainCommands:
    """Test main application commands."""

    def test_version_callback(self, cli_runner):
        """Test version callback."""
        result = cli_runner.invoke(main.app, ["--version"])

        assert result.exit_code == 0
        assert "ca-bhfuil" in result.stdout

    def test_help_display(self, cli_runner):
        """Test help display."""
        result = cli_runner.invoke(main.app, ["--help"])

        assert result.exit_code == 0
        assert "Git repository analysis tool" in result.stdout

    def test_config_help(self, cli_runner):
        """Test config command help."""
        result = cli_runner.invoke(main.app, ["config", "--help"])

        assert result.exit_code == 0
        assert "Configuration management commands" in result.stdout

    def test_repo_help(self, cli_runner):
        """Test repo command help."""
        result = cli_runner.invoke(main.app, ["repo", "--help"])

        assert result.exit_code == 0
        assert "Repository management commands" in result.stdout

    def test_install_completion(self, cli_runner):
        """Test completion installation."""
        result = cli_runner.invoke(main.app, ["install-completion", "bash"])

        assert result.exit_code == 0
        assert "Bash completion installed" in result.stdout

    def test_search_command(self, cli_runner, temp_config_dir):
        """Test search command."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_repository.AsyncRepositoryManager"
            ) as mock_repo_manager_class,
        ):
            mock_repo_manager = mock.AsyncMock()
            mock_repo_manager_class.return_value = mock_repo_manager
            # Make shutdown a regular mock (not async) to avoid warnings
            mock_repo_manager.shutdown = mock.Mock(return_value=None)

            # Mock the repository detection
            mock_repo_manager.detect_repository.return_value = mock.AsyncMock(
                success=True, result={"repository_path": str(temp_config_dir)}
            )

            # Mock the search results
            mock_repo_manager.search_commits.return_value = mock.AsyncMock(
                success=True, matches=[]
            )

            result = cli_runner.invoke(main.app, ["search", "test"])
            assert result.exit_code == 0
            assert "No commits found matching 'test'" in result.stdout

    def test_search_command_with_repo_name(self, cli_runner, temp_config_dir):
        """Test search command with repository name."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_repository.AsyncRepositoryManager"
            ) as mock_repo_manager_class,
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_config_manager_class,
        ):
            mock_repo_manager = mock.AsyncMock()
            mock_repo_manager_class.return_value = mock_repo_manager
            # Make shutdown a regular mock (not async) to avoid warnings
            mock_repo_manager.shutdown = mock.Mock(return_value=None)

            mock_config_manager = mock.AsyncMock()
            mock_config_manager_class.return_value = mock_config_manager

            # Mock repository config lookup
            mock_repo_config = mock.AsyncMock()
            mock_repo_config.repo_path = temp_config_dir / "test-repo"
            mock_config_manager.get_repository_config_by_name.return_value = (
                mock_repo_config
            )

            # Mock the repository detection
            mock_repo_manager.detect_repository.return_value = mock.AsyncMock(
                success=True, result={"repository_path": str(temp_config_dir)}
            )

            # Mock the search results
            mock_repo_manager.search_commits.return_value = mock.AsyncMock(
                success=True, matches=[]
            )

            result = cli_runner.invoke(
                main.app, ["search", "test", "--repo", "test-repo"]
            )
            assert result.exit_code == 0
            assert "No commits found matching 'test'" in result.stdout

    def test_search_command_repo_not_found(self, cli_runner, temp_config_dir):
        """Test search command with non-existent repository name."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_repository.AsyncRepositoryManager"
            ) as mock_repo_manager_class,
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_config_manager_class,
        ):
            mock_repo_manager = mock.AsyncMock()
            mock_repo_manager_class.return_value = mock_repo_manager
            # Make shutdown a regular mock (not async) to avoid warnings
            mock_repo_manager.shutdown = mock.Mock(return_value=None)

            mock_config_manager = mock.AsyncMock()
            mock_config_manager_class.return_value = mock_config_manager

            # Mock repository config lookup returning None (not found)
            mock_config_manager.get_repository_config_by_name.return_value = None

            result = cli_runner.invoke(
                main.app, ["search", "test", "--repo", "nonexistent"]
            )
            assert result.exit_code == 1
            assert (
                "Repository 'nonexistent' not found in configuration" in result.stdout
            )

    def test_search_command_multi_word(self, cli_runner, temp_config_dir):
        """Test search command with multiple words (no quotes needed)."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_repository.AsyncRepositoryManager"
            ) as mock_repo_manager_class,
        ):
            mock_repo_manager = mock.AsyncMock()
            mock_repo_manager_class.return_value = mock_repo_manager
            # Make shutdown a regular mock (not async) to avoid warnings
            mock_repo_manager.shutdown = mock.Mock(return_value=None)

            # Mock the repository detection
            mock_repo_manager.detect_repository.return_value = mock.AsyncMock(
                success=True, result={"repository_path": str(temp_config_dir)}
            )

            # Mock the search results
            mock_repo_manager.search_commits.return_value = mock.AsyncMock(
                success=True, matches=[]
            )

            # Test multi-word search without quotes
            result = cli_runner.invoke(main.app, ["search", "fix", "memory", "leak"])
            assert result.exit_code == 0
            assert "No commits found matching 'fix memory leak'" in result.stdout

            # Verify the search was called with joined words
            mock_repo_manager.search_commits.assert_called_once()
            call_args = mock_repo_manager.search_commits.call_args
            # The second argument should be the joined query string
            assert call_args[0][1] == "fix memory leak"

    def test_status_command(self, cli_runner, temp_config_dir):
        """Test status command."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_configuration.return_value = mock.AsyncMock()
            mock_manager.load_configuration.return_value.repos = []

            result = cli_runner.invoke(main.app, ["status"])
            assert result.exit_code == 0
            assert "Ca-Bhfuil System Status" in result.stdout


class TestErrorHandling:
    """Test CLI error handling."""

    def test_config_validate_error(self, cli_runner, temp_config_dir):
        """Test configuration validation error handling."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.validate_configuration.side_effect = Exception("Config error")

            result = cli_runner.invoke(main.app, ["config", "validate"])
            assert result.exit_code != 0
            assert "Configuration validation failed" in result.stdout

    def test_repo_add_error(self, cli_runner, temp_config_dir):
        """Test repository addition error handling."""
        with (
            mock.patch(
                "ca_bhfuil.core.config.get_config_dir", return_value=temp_config_dir
            ),
            mock.patch(
                "ca_bhfuil.core.async_config.AsyncConfigManager"
            ) as mock_manager_class,
            mock.patch(
                "ca_bhfuil.core.git.clone.AsyncRepositoryCloner"
            ) as mock_cloner_class,
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_repository_config.return_value = None

            mock_cloner = mock.AsyncMock()
            mock_cloner_class.return_value = mock_cloner
            mock_cloner.clone_repository.side_effect = Exception("Clone error")

            result = cli_runner.invoke(
                main.app, ["repo", "add", "https://github.com/test/repo.git"]
            )
            assert result.exit_code != 0
            assert "Clone error" in result.stdout
