"""Tests for CLI operations module."""

import pathlib
import tempfile
from unittest import mock

import pytest
import typer

from ca_bhfuil.cli import operations
from ca_bhfuil.core import async_config


class TestCliOperations:
    """Test CLI operations functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Provide a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield pathlib.Path(temp_dir)

    @pytest.fixture
    def mock_config_manager(self, temp_config_dir):
        """Provide a mock async configuration manager."""
        config_manager = mock.AsyncMock(spec=async_config.AsyncConfigManager)
        config_manager.config_dir = temp_config_dir
        config_manager.repositories_file = temp_config_dir / "repositories.toml"
        config_manager.global_settings_file = temp_config_dir / "global.toml"
        config_manager.auth_file = temp_config_dir / "auth.toml"
        return config_manager

    @pytest.mark.asyncio
    async def test_config_init_async_success(self, mock_config_manager):
        """Test successful configuration initialization."""
        # Mock that config doesn't exist
        mock_config_manager.repositories_file = mock.Mock()
        mock_config_manager.repositories_file.exists.return_value = False
        mock_config_manager.generate_default_config = mock.AsyncMock()

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
        ):
            mock_progress.return_value = None

            await operations.config_init_async(force=False)

            mock_config_manager.generate_default_config.assert_called_once()
            mock_progress.assert_called_once()
            mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_config_init_async_exists_no_force(self, mock_config_manager):
        """Test configuration initialization when config exists and no force."""
        # Mock that config exists
        mock_config_manager.repositories_file = mock.Mock()
        mock_config_manager.repositories_file.exists.return_value = True

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
            pytest.raises(typer.Exit) as exc_info,
        ):
            await operations.config_init_async(force=False)

            assert exc_info.value.exit_code == 1
            mock_console.print.assert_called_with(
                "[yellow]Configuration already exists. Use --force to overwrite.[/yellow]"
            )

    @pytest.mark.asyncio
    async def test_config_init_async_exists_with_force(self, mock_config_manager):
        """Test configuration initialization when config exists but force is used."""
        # Mock that config exists but force is True
        mock_config_manager.repositories_file = mock.Mock()
        mock_config_manager.repositories_file.exists.return_value = True
        mock_config_manager.generate_default_config = mock.AsyncMock()

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
        ):
            mock_progress.return_value = None

            await operations.config_init_async(force=True)

            mock_config_manager.generate_default_config.assert_called_once()
            mock_progress.assert_called_once()
            mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_config_validate_async_success(self, mock_config_manager):
        """Test successful configuration validation."""
        mock_config_manager.validate_configuration = mock.AsyncMock(return_value=[])
        mock_config_manager.validate_auth_config = mock.AsyncMock(return_value=[])

        async def mock_with_progress(coro, description):
            """Mock with_progress that actually awaits the coroutine."""
            return await coro

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch(
                "ca_bhfuil.cli.operations.with_progress", side_effect=mock_with_progress
            ),
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
        ):
            await operations.config_validate_async()

            mock_config_manager.validate_configuration.assert_called_once()
            mock_config_manager.validate_auth_config.assert_called_once()
            mock_console.print.assert_called_with(
                "[green]✅ Configuration is valid![/green]"
            )

    @pytest.mark.asyncio
    async def test_config_validate_async_with_errors(self, mock_config_manager):
        """Test configuration validation with errors."""
        mock_config_manager.validate_configuration.return_value = [
            "Config error 1",
            "Config error 2",
        ]
        mock_config_manager.validate_auth_config.return_value = ["Auth error 1"]

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
            pytest.raises(typer.Exit) as exc_info,
        ):
            mock_progress.return_value = [
                "Config error 1",
                "Config error 2",
                "Auth error 1",
            ]

            await operations.config_validate_async()

            assert exc_info.value.exit_code == 1
            mock_console.print.assert_any_call(
                "[red]❌ Configuration validation failed:[/red]"
            )
            mock_console.print.assert_any_call("   • Config error 1")
            mock_console.print.assert_any_call("   • Config error 2")
            mock_console.print.assert_any_call("   • Auth error 1")

    @pytest.mark.asyncio
    async def test_config_validate_async_config_errors_only(self, mock_config_manager):
        """Test configuration validation with only config errors."""
        mock_config_manager.validate_configuration.return_value = ["Config error"]
        mock_config_manager.validate_auth_config.return_value = []

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
            pytest.raises(typer.Exit) as exc_info,
        ):
            mock_progress.return_value = ["Config error"]

            await operations.config_validate_async()

            assert exc_info.value.exit_code == 1
            mock_console.print.assert_any_call(
                "[red]❌ Configuration validation failed:[/red]"
            )

    @pytest.mark.asyncio
    async def test_config_validate_async_auth_errors_only(self, mock_config_manager):
        """Test configuration validation with only auth errors."""
        mock_config_manager.validate_configuration = mock.AsyncMock(return_value=[])
        mock_config_manager.validate_auth_config.return_value = ["Auth error"]

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console") as mock_console,
            pytest.raises(typer.Exit) as exc_info,
        ):
            mock_progress.return_value = ["Auth error"]

            await operations.config_validate_async()

            assert exc_info.value.exit_code == 1
            mock_console.print.assert_any_call(
                "[red]❌ Configuration validation failed:[/red]"
            )

    def test_rich_console_initialization(self):
        """Test that rich console is properly initialized."""
        assert operations.rich_console is not None
        assert hasattr(operations.rich_console, "print")


class TestCliOperationsIntegration:
    """Test CLI operations integration scenarios."""

    @pytest.mark.asyncio
    async def test_config_init_progress_integration(self):
        """Test that progress integration works correctly."""
        mock_config_manager = mock.AsyncMock()
        mock_config_manager.repositories_file = mock.Mock()
        mock_config_manager.repositories_file.exists.return_value = False
        mock_config_manager.config_dir = pathlib.Path("/test/config")
        mock_config_manager.repositories_file = pathlib.Path(
            "/test/config/repositories.toml"
        )
        mock_config_manager.global_settings_file = pathlib.Path(
            "/test/config/global.toml"
        )
        mock_config_manager.auth_file = pathlib.Path("/test/config/auth.toml")

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console"),
        ):
            mock_progress.return_value = None

            await operations.config_init_async()

            # Verify with_progress was called with correct arguments
            mock_progress.assert_called_once()
            args, kwargs = mock_progress.call_args
            assert len(args) == 2
            assert args[1] == "Initializing configuration files..."

    @pytest.mark.asyncio
    async def test_config_validate_progress_integration(self):
        """Test that validation progress integration works correctly."""
        mock_config_manager = mock.AsyncMock()
        mock_config_manager.validate_configuration = mock.AsyncMock(return_value=[])
        mock_config_manager.validate_auth_config.return_value = []

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
            mock.patch("ca_bhfuil.cli.operations.rich_console"),
        ):
            mock_progress.return_value = []

            await operations.config_validate_async()

            # Verify with_progress was called with correct arguments
            mock_progress.assert_called_once()
            args, kwargs = mock_progress.call_args
            assert len(args) == 2
            assert args[1] == "Validating configuration..."


class TestCliOperationsErrorHandling:
    """Test CLI operations error handling scenarios."""

    @pytest.mark.asyncio
    async def test_config_init_async_exception_handling(self):
        """Test configuration initialization exception handling."""
        mock_config_manager = mock.AsyncMock()
        mock_config_manager.repositories_file = mock.Mock()
        mock_config_manager.repositories_file.exists.return_value = False
        mock_config_manager.generate_default_config.side_effect = Exception(
            "Generation failed"
        )

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
        ):
            mock_progress.side_effect = Exception("Generation failed")

            with pytest.raises(Exception, match="Generation failed"):
                await operations.config_init_async()

    @pytest.mark.asyncio
    async def test_config_validate_async_exception_handling(self):
        """Test configuration validation exception handling."""
        mock_config_manager = mock.AsyncMock()
        mock_config_manager.validate_configuration.side_effect = Exception(
            "Validation failed"
        )

        with (
            mock.patch(
                "ca_bhfuil.core.async_config.get_async_config_manager",
                return_value=mock_config_manager,
            ),
            mock.patch("ca_bhfuil.cli.operations.with_progress") as mock_progress,
        ):
            mock_progress.side_effect = Exception("Validation failed")

            with pytest.raises(Exception, match="Validation failed"):
                await operations.config_validate_async()
