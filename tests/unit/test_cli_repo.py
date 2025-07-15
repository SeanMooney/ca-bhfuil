"""Unit tests for repo sub-command functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest
from typer.testing import CliRunner

from ca_bhfuil.cli import main
from ca_bhfuil.core import config


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Provide a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield pathlib.Path(temp_dir)


@pytest.fixture
def mock_config_manager():
    """Provide a mock config manager."""
    with mock.patch(
        "ca_bhfuil.core.async_config.get_async_config_manager"
    ) as mock_get_manager:
        mock_manager = mock.AsyncMock()
        mock_get_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def mock_with_progress():
    """Provide mock with_progress function."""
    with mock.patch("ca_bhfuil.cli.async_bridge.with_progress") as mock_progress:

        async def mock_with_progress_func(coro, *args):
            if hasattr(coro, "__await__"):
                return await coro
            return coro

        mock_progress.side_effect = mock_with_progress_func
        yield mock_progress


@pytest.fixture
def sample_config():
    """Provide a sample configuration object."""
    return config.GlobalConfig(
        repos=[
            config.RepositoryConfig(
                name="test-repo",
                source={"url": "https://github.com/test/test-repo.git", "type": "git"},
                auth_key="default",
            ),
            config.RepositoryConfig(
                name="another-repo",
                source={
                    "url": "https://github.com/test/another-repo.git",
                    "type": "git",
                },
                auth_key="custom",
            ),
        ],
        settings={},
    )


class TestRepoAdd:
    """Test repo add command."""

    def test_repo_add_missing_url(self, cli_runner):
        """Test repo add without URL argument."""
        result = cli_runner.invoke(main.app, ["repo", "add"])
        assert result.exit_code != 0
        assert "Usage:" in result.stdout or "Usage:" in result.stderr

    def test_repo_add_success(
        self, cli_runner, temp_config_dir, mock_config_manager, mock_with_progress
    ):
        """Test successful repository addition."""
        # Setup mock configuration
        mock_config = mock.Mock()
        mock_config.repos = []
        mock_config_manager.load_configuration.return_value = mock_config
        mock_config_manager.save_configuration.return_value = None

        # Mock git manager and cloner
        with (
            mock.patch(
                "ca_bhfuil.core.git.async_git.AsyncGitManager"
            ) as mock_git_manager_class,
            mock.patch(
                "ca_bhfuil.core.git.clone.AsyncRepositoryCloner"
            ) as mock_cloner_class,
        ):
            mock_git_manager = mock.AsyncMock()
            mock_git_manager_class.return_value = mock_git_manager

            mock_cloner = mock.AsyncMock()
            mock_cloner_class.return_value = mock_cloner

            mock_clone_result = mock.Mock()
            mock_clone_result.success = True
            mock_cloner.clone_repository.return_value = mock_clone_result

            result = cli_runner.invoke(
                main.app, ["repo", "add", "https://github.com/test/test-repo.git"]
            )

            assert result.exit_code == 0
            assert "Successfully cloned test-repo" in result.stdout
            mock_cloner.clone_repository.assert_called_once()
            mock_config_manager.save_configuration.assert_called_once()

    def test_repo_add_with_custom_name(
        self, cli_runner, temp_config_dir, mock_config_manager, mock_with_progress
    ):
        """Test repository addition with custom name."""
        # Setup mock configuration
        mock_config = mock.Mock()
        mock_config.repos = []
        mock_config_manager.load_configuration.return_value = mock_config
        mock_config_manager.save_configuration.return_value = None

        # Mock git manager and cloner
        with (
            mock.patch(
                "ca_bhfuil.core.git.async_git.AsyncGitManager"
            ) as mock_git_manager_class,
            mock.patch(
                "ca_bhfuil.core.git.clone.AsyncRepositoryCloner"
            ) as mock_cloner_class,
        ):
            mock_git_manager = mock.AsyncMock()
            mock_git_manager_class.return_value = mock_git_manager

            mock_cloner = mock.AsyncMock()
            mock_cloner_class.return_value = mock_cloner

            mock_clone_result = mock.Mock()
            mock_clone_result.success = True
            mock_cloner.clone_repository.return_value = mock_clone_result

            result = cli_runner.invoke(
                main.app,
                [
                    "repo",
                    "add",
                    "https://github.com/test/test-repo.git",
                    "--name",
                    "custom-repo",
                ],
            )

            assert result.exit_code == 0
            assert "Successfully cloned custom-repo" in result.stdout


class TestRepoList:
    """Test repo list command."""

    def test_repo_list_no_repos(
        self, cli_runner, mock_config_manager, mock_with_progress
    ):
        """Test listing repositories when none configured."""
        mock_config = mock.Mock()
        mock_config.repos = []
        mock_config_manager.load_configuration.return_value = mock_config

        result = cli_runner.invoke(main.app, ["repo", "list"])

        assert result.exit_code == 0
        assert "No repositories configured" in result.stdout
        assert "Use 'ca-bhfuil repo add <url>' to add repositories" in result.stdout

    def test_repo_list_table_format(
        self, cli_runner, mock_config_manager, mock_with_progress, sample_config
    ):
        """Test listing repositories in table format."""
        mock_config_manager.load_configuration.return_value = sample_config

        result = cli_runner.invoke(main.app, ["repo", "list"])

        assert result.exit_code == 0
        assert "test-repo" in result.stdout
        assert "another-repo" in result.stdout
        assert "github.com/test/test-repo.git" in result.stdout
        assert "Total repositories: 2" in result.stdout

    def test_repo_list_json_format(
        self, cli_runner, mock_config_manager, mock_with_progress, sample_config
    ):
        """Test repo list with JSON format."""
        mock_config_manager.load_configuration.return_value = sample_config

        result = cli_runner.invoke(main.app, ["repo", "list", "--format", "json"])

        assert result.exit_code == 0
        # Check that JSON content is present in output
        assert "test-repo" in result.stdout
        assert "another-repo" in result.stdout
        assert "github.com/test/test-repo.git" in result.stdout
        assert "github.com/test/another-repo.git" in result.stdout


class TestRepoUpdate:
    """Test repo update command."""

    def test_repo_update_missing_name(self, cli_runner):
        """Test repo update without name argument."""
        result = cli_runner.invoke(main.app, ["repo", "update"])
        assert result.exit_code != 0
        assert "Usage:" in result.stdout or "Usage:" in result.stderr

    def test_repo_update_success(
        self,
        cli_runner,
        temp_config_dir,
        mock_config_manager,
        mock_with_progress,
        sample_config,
    ):
        """Test successful repository update."""
        mock_config_manager.load_configuration.return_value = sample_config

        # Mock repository path to exist by patching repo_path property
        repo_path = temp_config_dir / "test-repo"
        repo_path.mkdir()

        with mock.patch.object(
            type(sample_config.repos[0]), "repo_path", new_callable=mock.PropertyMock
        ) as mock_repo_path:
            mock_repo_path.return_value = repo_path

            # Mock AsyncRepositorySynchronizer
            with mock.patch(
                "ca_bhfuil.core.async_sync.AsyncRepositorySynchronizer"
            ) as mock_sync_class:
                mock_synchronizer = mock.AsyncMock()
                mock_sync_class.return_value = mock_synchronizer

                mock_result = mock.Mock()
                mock_result.success = True
                mock_synchronizer.sync_repository.return_value = mock_result

                result = cli_runner.invoke(main.app, ["repo", "update", "test-repo"])

                assert result.exit_code == 0
                assert "Successfully updated test-repo" in result.stdout
                mock_synchronizer.sync_repository.assert_called_once_with("test-repo")

    def test_repo_update_not_found(
        self, cli_runner, mock_config_manager, mock_with_progress, sample_config
    ):
        """Test repository update with non-existent repository."""
        mock_config_manager.load_configuration.return_value = sample_config

        result = cli_runner.invoke(main.app, ["repo", "update", "nonexistent"])

        assert result.exit_code == 1
        assert "Repository 'nonexistent' not found" in result.stdout
        assert (
            "Use 'ca-bhfuil repo list' to see available repositories" in result.stdout
        )


class TestRepoRemove:
    """Test repo remove command."""

    def test_repo_remove_missing_name(self, cli_runner):
        """Test repo remove without name argument."""
        result = cli_runner.invoke(main.app, ["repo", "remove"])
        assert result.exit_code != 0
        assert "Usage:" in result.stdout or "Usage:" in result.stderr

    def test_repo_remove_success_with_confirmation(
        self, cli_runner, temp_config_dir, mock_config_manager, mock_with_progress
    ):
        """Test successful repository removal with confirmation."""
        # Setup mock configuration
        test_repo = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/test-repo.git", "type": "git"},
        )
        mock_config = mock.Mock()
        mock_config.repos = [test_repo]
        mock_config_manager.load_configuration.return_value = mock_config
        mock_config_manager.save_configuration.return_value = None

        # Mock the repository path
        repo_path = temp_config_dir / "test-repo"
        repo_path.mkdir()

        with mock.patch.object(
            type(test_repo), "repo_path", new_callable=mock.PropertyMock
        ) as mock_repo_path:
            mock_repo_path.return_value = repo_path

            # Mock typer.confirm to return True (user confirms)
            with mock.patch("typer.confirm") as mock_confirm:
                mock_confirm.side_effect = [
                    True,  # Confirm removal
                    False,  # Don't delete files
                ]

                result = cli_runner.invoke(main.app, ["repo", "remove", "test-repo"])

                assert result.exit_code == 0
                assert "Removed 'test-repo' from configuration" in result.stdout
                assert len(mock_config.repos) == 0  # Repository should be removed

    def test_repo_remove_not_found(
        self, cli_runner, mock_config_manager, mock_with_progress
    ):
        """Test repository removal with non-existent repository."""
        mock_config = mock.Mock()
        mock_config.repos = []
        mock_config_manager.load_configuration.return_value = mock_config

        result = cli_runner.invoke(main.app, ["repo", "remove", "nonexistent"])

        assert result.exit_code == 1
        assert "Repository 'nonexistent' not found" in result.stdout
        assert (
            "Use 'ca-bhfuil repo list' to see available repositories" in result.stdout
        )


class TestRepoSync:
    """Test repo sync command."""

    def test_repo_sync_no_repos(
        self, cli_runner, mock_config_manager, mock_with_progress
    ):
        """Test syncing with no configured repositories."""
        mock_config = mock.Mock()
        mock_config.repos = []
        mock_config_manager.load_configuration.return_value = mock_config

        result = cli_runner.invoke(main.app, ["repo", "sync"])

        assert result.exit_code == 0
        assert "No repositories configured" in result.stdout
        assert "Use 'ca-bhfuil repo add <url>' to add repositories" in result.stdout

    def test_repo_sync_specific_repo_not_found(
        self, cli_runner, mock_config_manager, mock_with_progress, sample_config
    ):
        """Test syncing a specific repository that doesn't exist."""
        mock_config_manager.load_configuration.return_value = sample_config

        result = cli_runner.invoke(main.app, ["repo", "sync", "nonexistent"])

        assert result.exit_code == 1
        assert "Repository 'nonexistent' not found" in result.stdout
        assert (
            "Use 'ca-bhfuil repo list' to see available repositories" in result.stdout
        )


class TestRepoHelp:
    """Test repo help commands."""

    def test_repo_help(self, cli_runner):
        """Test repo help command."""
        result = cli_runner.invoke(main.app, ["repo", "--help"])
        assert result.exit_code == 0
        assert "Repository management commands" in result.stdout

    def test_repo_add_help(self, cli_runner):
        """Test repo add help command."""
        result = cli_runner.invoke(main.app, ["repo", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a new repository" in result.stdout or "Add" in result.stdout

    def test_repo_list_help(self, cli_runner):
        """Test repo list help command."""
        result = cli_runner.invoke(main.app, ["repo", "list", "--help"])
        assert result.exit_code == 0
        assert "List all configured repositories" in result.stdout

    def test_repo_update_help(self, cli_runner):
        """Test repo update help command."""
        result = cli_runner.invoke(main.app, ["repo", "update", "--help"])
        assert result.exit_code == 0
        assert "Update repository" in result.stdout or "Update" in result.stdout

    def test_repo_remove_help(self, cli_runner):
        """Test repo remove help command."""
        result = cli_runner.invoke(main.app, ["repo", "remove", "--help"])
        assert result.exit_code == 0
        assert "Remove a repository" in result.stdout

    def test_repo_sync_help(self, cli_runner):
        """Test repo sync help command."""
        result = cli_runner.invoke(main.app, ["repo", "sync", "--help"])
        assert result.exit_code == 0
        assert "Sync all configured repositories" in result.stdout
