"""Async CLI operations that can be tested independently."""

from rich import console
import typer

from ca_bhfuil.cli.async_bridge import with_progress
from ca_bhfuil.core import async_config


rich_console = console.Console()


async def config_init_async(force: bool = False) -> None:
    """Initialize default configuration files asynchronously."""
    config_manager = await async_config.get_async_config_manager()

    # Check if config already exists
    if not force and config_manager.repositories_file.exists():
        rich_console.print(
            "[yellow]Configuration already exists. Use --force to overwrite.[/yellow]"
        )
        raise typer.Exit(1)

    # Generate default configuration
    await with_progress(
        config_manager.generate_default_config(),
        "Initializing configuration files...",
    )

    rich_console.print("[green]✅ Configuration initialized successfully![/green]")
    rich_console.print(f"📁 Config directory: {config_manager.config_dir}")
    rich_console.print("📄 Configuration files:")
    rich_console.print(f"   • {config_manager.repositories_file}")
    rich_console.print(f"   • {config_manager.global_settings_file}")
    rich_console.print(
        f"   • {config_manager.auth_file} [red](secure permissions)[/red]"
    )


async def config_validate_async() -> None:
    """Validate current configuration asynchronously."""
    config_manager = await async_config.get_async_config_manager()

    # Validate main configuration
    async def validate_all() -> list[str]:
        config_errors = await config_manager.validate_configuration()
        auth_errors = await config_manager.validate_auth_config()
        return config_errors + auth_errors

    all_errors = await with_progress(validate_all(), "Validating configuration...")

    if not all_errors:
        rich_console.print("[green]✅ Configuration is valid![/green]")
    else:
        rich_console.print("[red]❌ Configuration validation failed:[/red]")
        for error in all_errors:
            rich_console.print(f"   • {error}")
        raise typer.Exit(1)
