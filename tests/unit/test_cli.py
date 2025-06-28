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
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_repository_config.return_value = None

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
        ):
            mock_manager = mock.AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_repository_config.return_value = None

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
                "ca_bhfuil.core.git.async_git.AsyncGitManager"
            ) as mock_git_class,
        ):
            mock_git = mock.AsyncMock()
            mock_git_class.return_value = mock_git
            mock_git.search_repository.return_value = []

            result = cli_runner.invoke(main.app, ["search", "test"])
            assert result.exit_code == 0
            assert "Search functionality not yet implemented" in result.stdout

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
