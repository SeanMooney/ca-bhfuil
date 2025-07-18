"""Integration tests for CLI commands using the manager layer."""

import asyncio
import pathlib
import tempfile
import unittest.mock

import pytest
import typer.testing

from ca_bhfuil.cli import main as cli_main
from ca_bhfuil.core.managers import factory as manager_factory
from tests.fixtures import alembic


class TestCLIManagerIntegration:
    """Test CLI commands properly use manager layer."""

    @pytest.fixture
    def cli_runner(self):
        """Provide CLI test runner."""
        return typer.testing.CliRunner()

    @pytest.fixture
    def mock_factory(self, tmp_path):
        """Provide a mock manager factory."""
        # Create test database
        db_path = tmp_path / "test.db"
        asyncio.run(alembic.create_test_database(db_path))

        # Patch the factory function to use test database
        original_get_manager_factory = manager_factory.get_manager_factory

        async def mock_get_factory(*args, **kwargs):
            return await original_get_manager_factory(db_path, *args, **kwargs)

        with unittest.mock.patch(
            "ca_bhfuil.core.managers.factory.get_manager_factory",
            side_effect=mock_get_factory,
        ):
            yield

        # Clean up global factory
        asyncio.run(manager_factory.close_global_factory())

    def test_search_command_uses_manager_factory(self, cli_runner, mock_factory):
        """Test that search command uses manager factory instead of direct git access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock the manager factory function
            with unittest.mock.patch(
                "ca_bhfuil.core.managers.factory.get_repository_manager",
                new_callable=unittest.mock.AsyncMock,
            ) as mock_get_repo_manager:
                mock_manager = unittest.mock.AsyncMock()
                mock_manager.search_commits.return_value = unittest.mock.MagicMock(
                    success=True, commits=[], total_count=0
                )
                mock_get_repo_manager.return_value = mock_manager

                # Mock config manager for repository lookup
                with unittest.mock.patch(
                    "ca_bhfuil.core.async_config.get_async_config_manager",
                    new_callable=unittest.mock.AsyncMock,
                ) as mock_get_config_manager:
                    mock_config = unittest.mock.AsyncMock()
                    mock_config.get_repository_config_by_name.return_value = None
                    mock_get_config_manager.return_value = mock_config

                    # Run search command with async bridge
                    result = cli_runner.invoke(
                        cli_main.app, ["search", "test", "--repo", str(repo_path)]
                    )

                    # Should not have errors and should use manager
                    assert result.exit_code == 0
                    mock_get_repo_manager.assert_called_once()
                    mock_manager.search_commits.assert_called_once()

    def test_status_command_uses_manager_factory(self, cli_runner, mock_factory):
        """Test that status command uses manager factory for repository analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = pathlib.Path(temp_dir)

            # Mock the manager factory function
            with unittest.mock.patch(
                "ca_bhfuil.core.managers.factory.get_repository_manager"
            ) as mock_get_repo_manager:
                mock_manager = unittest.mock.MagicMock()
                mock_analysis_result = unittest.mock.MagicMock()
                mock_analysis_result.success = True
                mock_analysis_result.commit_count = 5
                mock_analysis_result.branch_count = 2
                mock_analysis_result.authors = ["test-author"]
                mock_analysis_result.high_impact_commits = []
                mock_analysis_result.recent_commits = []
                mock_analysis_result.date_range = {}
                mock_manager.analyze_repository.return_value = mock_analysis_result
                mock_get_repo_manager.return_value = mock_manager

                # Mock config manager for repository lookup
                with unittest.mock.patch(
                    "ca_bhfuil.core.async_config.get_async_config_manager"
                ) as mock_config_manager:
                    mock_config = unittest.mock.MagicMock()
                    mock_config.get_repository_config_by_name.return_value = None
                    mock_config_manager.return_value = mock_config

                    # Run status command with async bridge
                    result = cli_runner.invoke(
                        cli_main.app, ["status", "--repo", str(repo_path)]
                    )

                    # Should not have errors and should use manager
                    assert result.exit_code == 0
                    mock_get_repo_manager.assert_called_once()
                    mock_manager.analyze_repository.assert_called_once()

    def test_search_no_direct_git_imports(self):
        """Test that search command doesn't import git modules directly."""
        # This is a static analysis test - check the CLI source doesn't import
        # git modules that would bypass the manager layer

        # Read the CLI main module
        cli_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "ca_bhfuil"
            / "cli"
            / "main.py"
        )
        with cli_path.open() as f:
            cli_content = f.read()

        # Should import manager factory
        assert (
            "from ca_bhfuil.core.managers import factory as manager_factory"
            in cli_content
        )

        # Should NOT directly import repository or database modules in search command
        # The search command should only use manager_factory functions
        search_function_start = cli_content.find("async def search(")
        search_function_end = cli_content.find("async def ", search_function_start + 1)
        if search_function_end == -1:
            search_function_end = len(cli_content)

        search_function = cli_content[search_function_start:search_function_end]

        # Should use manager factory
        assert "manager_factory.get_repository_manager" in search_function

        # Should NOT use direct git or database access
        assert "async_repository.AsyncRepositoryManager()" not in search_function
        assert "Repository(" not in search_function
        assert "SQLModelDatabaseManager" not in search_function

    def test_status_no_direct_git_imports(self):
        """Test that status command doesn't import git modules directly."""
        # Read the CLI main module
        cli_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "ca_bhfuil"
            / "cli"
            / "main.py"
        )
        with cli_path.open() as f:
            cli_content = f.read()

        # Find status function
        status_function_start = cli_content.find("async def status(")
        status_function_end = cli_content.find(
            "@repo_app.command", status_function_start + 1
        )
        if status_function_end == -1:
            status_function_end = len(cli_content)

        status_function = cli_content[status_function_start:status_function_end]

        # Should use manager factory
        assert "manager_factory.get_repository_manager" in status_function

        # Should NOT use direct git or database access
        assert "async_repository.AsyncRepositoryManager()" not in status_function
        assert "Repository(" not in status_function
        assert "SQLModelDatabaseManager" not in status_function


class TestManagerArchitectureCompliance:
    """Test that CLI follows Manager + Rich Models architecture patterns."""

    def test_business_logic_in_managers_not_cli(self):
        """Test that business logic is in managers, not CLI."""
        # Read the CLI main module
        cli_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "ca_bhfuil"
            / "cli"
            / "main.py"
        )
        with cli_path.open() as f:
            cli_content = f.read()

        # Should NOT contain business logic patterns that should be in managers

        # Pattern matching should be delegated to managers
        assert (
            "matches_pattern" not in cli_content
            or "commit.matches_pattern" in cli_content
        )

        # Impact scoring should be delegated to managers
        assert (
            "calculate_impact_score" not in cli_content
            or "commit.calculate_impact_score" in cli_content
        )

        # Database operations should go through managers
        assert "get_by_sha" not in cli_content
        assert "create_commit" not in cli_content
        assert "CommitCreate" not in cli_content

    def test_cli_uses_result_models(self):
        """Test that CLI uses result models from manager operations."""
        # Read the CLI main module
        cli_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "ca_bhfuil"
            / "cli"
            / "main.py"
        )
        with cli_path.open() as f:
            cli_content = f.read()

        # Should use result objects from managers
        search_function_start = cli_content.find("async def search(")
        search_function_end = cli_content.find("async def ", search_function_start + 1)
        if search_function_end == -1:
            search_function_end = len(cli_content)

        search_function = cli_content[search_function_start:search_function_end]

        # Should access result properties properly
        assert "search_result.success" in search_function
        assert "search_result.commits" in search_function

    def test_error_handling_uses_manager_results(self):
        """Test that error handling uses manager result patterns."""
        # Read the CLI main module
        cli_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "ca_bhfuil"
            / "cli"
            / "main.py"
        )
        with cli_path.open() as f:
            cli_content = f.read()

        # Should check .success attribute on results
        assert ".success" in cli_content

        # Should access .error attribute for error messages
        assert ".error" in cli_content
