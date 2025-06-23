"""Main CLI application for ca-bhfuil."""

import json
import pathlib

from rich import console
from rich import panel
from rich import syntax
from rich import table
import typer
import yaml

import ca_bhfuil.cli.completion as completion
import ca_bhfuil.core.config as config_module


# Create the main app and subcommands
app = typer.Typer(
    name="ca-bhfuil",
    help="Git repository analysis tool for tracking commits across stable branches",
    no_args_is_help=True,
)

# Create config subcommand group
config_app = typer.Typer(
    name="config",
    help="Configuration management commands",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

rich_console = console.Console()


@config_app.command("init")
def config_init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
) -> None:
    """Initialize default configuration files."""
    try:
        config_manager = config_module.get_config_manager()

        # Check if config already exists
        if not force and config_manager.repositories_file.exists():
            rich_console.print(
                "[yellow]Configuration already exists. Use --force to overwrite.[/yellow]"
            )
            raise typer.Exit(1)

        # Generate default configuration
        config_manager.generate_default_config()

        rich_console.print("[green]✅ Configuration initialized successfully![/green]")
        rich_console.print(f"📁 Config directory: {config_manager.config_dir}")
        rich_console.print("📄 Configuration files:")
        rich_console.print(f"   • {config_manager.repositories_file}")
        rich_console.print(f"   • {config_manager.global_settings_file}")
        rich_console.print(
            f"   • {config_manager.auth_file} [red](secure permissions)[/red]"
        )

    except Exception as e:
        rich_console.print(f"[red]❌ Error initializing configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("validate")
def config_validate() -> None:
    """Validate current configuration."""
    try:
        config_manager = config_module.get_config_manager()

        # Validate main configuration
        config_errors = config_manager.validate_configuration()
        auth_errors = config_manager.validate_auth_config()

        all_errors = config_errors + auth_errors

        if not all_errors:
            rich_console.print("[green]✅ Configuration is valid![/green]")
        else:
            rich_console.print("[red]❌ Configuration validation failed:[/red]")
            for error in all_errors:
                rich_console.print(f"   • {error}")
            raise typer.Exit(1)

    except Exception as e:
        rich_console.print(f"[red]❌ Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("status")
def config_status() -> None:
    """Show configuration system status."""
    try:
        config_manager = config_module.get_config_manager()

        # Show configuration paths
        status_table = table.Table(title="Ca-Bhfuil Configuration Status")
        status_table.add_column("Directory", style="cyan")
        status_table.add_column("Path", style="green")
        status_table.add_column("Exists", style="yellow")

        config_dir = config_module.get_config_dir()
        state_dir = config_module.get_state_dir()
        cache_dir = config_module.get_cache_dir()

        status_table.add_row(
            "Config", str(config_dir), "✅" if config_dir.exists() else "❌"
        )
        status_table.add_row(
            "State", str(state_dir), "✅" if state_dir.exists() else "❌"
        )
        status_table.add_row(
            "Cache", str(cache_dir), "✅" if cache_dir.exists() else "❌"
        )

        rich_console.print(status_table)

        # Show configuration files
        files_table = table.Table(title="Configuration Files")
        files_table.add_column("File", style="cyan")
        files_table.add_column("Path", style="green")
        files_table.add_column("Exists", style="yellow")

        files_table.add_row(
            "repos.yaml",
            str(config_manager.repositories_file),
            "✅" if config_manager.repositories_file.exists() else "❌",
        )
        files_table.add_row(
            "global.yaml",
            str(config_manager.global_settings_file),
            "✅" if config_manager.global_settings_file.exists() else "❌",
        )
        files_table.add_row(
            "auth.yaml",
            str(config_manager.auth_file),
            "✅" if config_manager.auth_file.exists() else "❌",
        )

        rich_console.print(files_table)

        # Show repositories if they exist
        config = config_manager.load_configuration()
        if config.repos:
            repos_table = table.Table(title="Configured Repositories")
            repos_table.add_column("Name", style="cyan")
            repos_table.add_column("URL", style="green")
            repos_table.add_column("Auth", style="yellow")

            for repo in config.repos:
                repos_table.add_row(
                    repo.name,
                    repo.source.get("url", "N/A"),
                    repo.auth_key or "default",
                )

            rich_console.print(repos_table)
        else:
            rich_console.print(
                panel.Panel(
                    "[yellow]No repositories configured[/yellow]",
                    title="Repositories",
                )
            )

    except Exception as e:
        rich_console.print(f"[red]❌ Error showing configuration status: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("show")
def config_show(
    repos: bool = typer.Option(False, "--repos", help="Show repos configuration"),
    global_: bool = typer.Option(False, "--global", help="Show global configuration"),
    auth: bool = typer.Option(False, "--auth", help="Show auth configuration"),
    all_: bool = typer.Option(False, "--all", help="Show all configuration files"),
    format: str = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Output format: yaml, json",
        autocompletion=completion.complete_format,
    ),
) -> None:
    """Display configuration file contents. Shows global config by default."""
    try:
        config_manager = config_module.get_config_manager()

        # Default to global settings if no flags are set
        if not any([repos, global_, auth, all_]):
            global_ = True

        # If --all is specified, show all configuration files
        if all_:
            files_to_show = [
                (config_manager.repositories_file, "repos"),
                (config_manager.global_settings_file, "global"),
                (config_manager.auth_file, "auth"),
            ]
        else:
            # Build list of files to show based on flags
            files_to_show = []
            if repos:
                files_to_show.append((config_manager.repositories_file, "repos"))
            if global_:
                files_to_show.append((config_manager.global_settings_file, "global"))
            if auth:
                files_to_show.append((config_manager.auth_file, "auth"))

        # Show each requested file
        for i, (file_path, file_name) in enumerate(files_to_show):
            if not file_path.exists():
                rich_console.print(
                    f"[yellow]⚠️  File does not exist: {file_path}[/yellow]"
                )
                continue

            # Add spacing between files if showing multiple
            if i > 0:
                rich_console.print()

            # Read and display file contents
            with open(file_path) as f:
                content = f.read()

            if format == "json":
                # Parse YAML and output as JSON
                data = yaml.safe_load(content)
                # Add header for multiple files
                if len(files_to_show) > 1:
                    rich_console.print(
                        f"[bold cyan]--- {file_name}.yaml ---[/bold cyan]"
                    )
                rich_console.print_json(json.dumps(data, indent=2))
            else:
                # Show raw YAML with syntax highlighting
                syntax_obj = syntax.Syntax(
                    content, "yaml", theme="monokai", line_numbers=True
                )
                rich_console.print(panel.Panel(syntax_obj, title=f"{file_name}.yaml"))

    except Exception as e:
        rich_console.print(f"[red]❌ Error displaying configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def install_completion(
    shell: str = typer.Argument("bash", help="Shell type (bash, zsh, fish)"),
) -> None:
    """Install shell completion for ca-bhfuil."""
    try:
        completion.install_completion(shell)
    except Exception as e:
        rich_console.print(f"[red]❌ Error installing completion: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(
        ..., help="Search query (SHA, partial SHA, or commit message pattern)"
    ),
    repo_path: pathlib.Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)",
        autocompletion=completion.complete_repo_path,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Search for commits in the repository."""
    # TODO: Use verbose parameter when implementing search functionality
    del verbose
    repo_path = repo_path or pathlib.Path.cwd()

    rich_console.print(f"🔍 Searching for '{query}' in repository: {repo_path}")
    rich_console.print("[yellow]🚧 Search functionality not yet implemented[/yellow]")


@app.command()
def status(
    repo_path: pathlib.Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)",
        autocompletion=completion.complete_repo_path,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Show repository analysis status."""
    # TODO: Use verbose parameter when implementing status functionality
    del verbose
    repo_path = repo_path or pathlib.Path.cwd()

    # Show XDG directory status
    system_table = table.Table(title="Ca-Bhfuil System Status")
    system_table.add_column("Component", style="cyan")
    system_table.add_column("Path", style="green")
    system_table.add_column("Status", style="yellow")

    config_dir = config_module.get_config_dir()
    state_dir = config_module.get_state_dir()
    cache_dir = config_module.get_cache_dir()

    system_table.add_row(
        "Config Directory", str(config_dir), "✅" if config_dir.exists() else "❌"
    )
    system_table.add_row(
        "State Directory", str(state_dir), "✅" if state_dir.exists() else "❌"
    )
    system_table.add_row(
        "Cache Directory", str(cache_dir), "✅" if cache_dir.exists() else "❌"
    )

    rich_console.print(system_table)

    # Check configuration
    try:
        config_manager = config_module.get_config_manager()
        config = config_manager.load_configuration()

        rich_console.print(f"📊 Configured repositories: {len(config.repos)}")
        if config.repos:
            for repo in config.repos[:3]:  # Show first 3
                rich_console.print(f"   • {repo.name}")
            if len(config.repos) > 3:
                rich_console.print(f"   ... and {len(config.repos) - 3} more")

        rich_console.print(
            "[green]✅ Ca-bhfuil configuration loaded successfully![/green]"
        )

    except Exception as e:
        rich_console.print(f"[red]⚠️  Configuration issue: {e}[/red]")


def version_callback(value: bool) -> None:
    """Version callback function."""
    if value:
        rich_console.print("ca-bhfuil 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Ca-Bhfuil: Git repository analysis tool for open source maintainers."""


if __name__ == "__main__":
    app()
