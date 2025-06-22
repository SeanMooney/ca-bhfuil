"""Main CLI application for ca-bhfuil."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ca_bhfuil.core.config import (
    get_cache_dir,
    get_config_dir,
    get_config_manager,
    get_state_dir,
)
from ca_bhfuil.cli.completion import (
    complete_format,
    complete_repo_path,
    install_completion,
)

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

console = Console()


@config_app.command("init")
def config_init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
) -> None:
    """Initialize default configuration files."""
    try:
        config_manager = get_config_manager()

        # Check if config already exists
        if not force and config_manager.repositories_file.exists():
            rprint(
                "[yellow]Configuration already exists. Use --force to overwrite.[/yellow]"
            )
            raise typer.Exit(1)

        # Generate default configuration
        config_manager.generate_default_config()

        rprint("[green]✅ Configuration initialized successfully![/green]")
        rprint(f"📁 Config directory: {config_manager.config_dir}")
        rprint("📄 Configuration files:")
        rprint(f"   • {config_manager.repositories_file}")
        rprint(f"   • {config_manager.global_settings_file}")
        rprint(f"   • {config_manager.auth_file} [red](secure permissions)[/red]")

    except Exception as e:
        rprint(f"[red]❌ Error initializing configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("validate")
def config_validate() -> None:
    """Validate current configuration."""
    try:
        config_manager = get_config_manager()

        # Validate main configuration
        config_errors = config_manager.validate_configuration()
        auth_errors = config_manager.validate_auth_config()

        all_errors = config_errors + auth_errors

        if not all_errors:
            rprint("[green]✅ Configuration is valid![/green]")
        else:
            rprint("[red]❌ Configuration validation failed:[/red]")
            for error in all_errors:
                rprint(f"   • {error}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("status")
def config_status() -> None:
    """Show configuration system status."""
    try:
        config_manager = get_config_manager()

        # Show configuration paths
        table = Table(title="Ca-Bhfuil Configuration Status")
        table.add_column("Directory", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Exists", style="yellow")

        config_dir = get_config_dir()
        state_dir = get_state_dir()
        cache_dir = get_cache_dir()

        table.add_row("Config", str(config_dir), "✅" if config_dir.exists() else "❌")
        table.add_row("State", str(state_dir), "✅" if state_dir.exists() else "❌")
        table.add_row("Cache", str(cache_dir), "✅" if cache_dir.exists() else "❌")

        console.print(table)

        # Show configuration files
        files_table = Table(title="Configuration Files")
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

        console.print(files_table)

        # Show repositories if they exist
        config = config_manager.load_configuration()
        if config.repos:
            repos_table = Table(title="Configured Repositories")
            repos_table.add_column("Name", style="cyan")
            repos_table.add_column("URL", style="green")
            repos_table.add_column("Auth", style="yellow")

            for repo in config.repos:
                repos_table.add_row(
                    repo.name,
                    repo.source.get("url", "N/A"),
                    repo.auth_key or "default",
                )

            console.print(repos_table)
        else:
            console.print(
                Panel(
                    "[yellow]No repositories configured[/yellow]",
                    title="Repositories",
                )
            )

    except Exception as e:
        rprint(f"[red]❌ Error showing configuration status: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("show")
def config_show(
    repos: bool = typer.Option(False, "--repos", help="Show repos configuration"),
    global_: bool = typer.Option(False, "--global", help="Show global configuration"),
    auth: bool = typer.Option(False, "--auth", help="Show auth configuration"),
    all_: bool = typer.Option(False, "--all", help="Show all configuration files"),
    format: str = typer.Option(
        "yaml", "--format", "-f", help="Output format: yaml, json", autocompletion=complete_format
    ),
) -> None:
    """Display configuration file contents. Shows global config by default."""
    try:
        config_manager = get_config_manager()
        
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
                rprint(f"[yellow]⚠️  File does not exist: {file_path}[/yellow]")
                continue

            # Add spacing between files if showing multiple
            if i > 0:
                console.print()

            # Read and display file contents
            with open(file_path) as f:
                content = f.read()

            if format == "json":
                # Parse YAML and output as JSON
                import yaml
                import json

                data = yaml.safe_load(content)
                # Add header for multiple files
                if len(files_to_show) > 1:
                    rprint(f"[bold cyan]--- {file_name}.yaml ---[/bold cyan]")
                console.print_json(json.dumps(data, indent=2))
            else:
                # Show raw YAML with syntax highlighting
                from rich.syntax import Syntax

                syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"{file_name}.yaml"))

    except Exception as e:
        rprint(f"[red]❌ Error displaying configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def completion(
    shell: str = typer.Argument("bash", help="Shell type (bash, zsh, fish)"),
) -> None:
    """Install shell completion for ca-bhfuil."""
    try:
        install_completion(shell)
    except Exception as e:
        rprint(f"[red]❌ Error installing completion: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(
        ..., help="Search query (SHA, partial SHA, or commit message pattern)"
    ),
    repo_path: Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)",
        autocompletion=complete_repo_path,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Search for commits in the repository."""
    repo_path = repo_path or Path.cwd()

    rprint(f"🔍 Searching for '{query}' in repository: {repo_path}")
    rprint("[yellow]🚧 Search functionality not yet implemented[/yellow]")


@app.command()
def status(
    repo_path: Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)",
        autocompletion=complete_repo_path,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Show repository analysis status."""
    repo_path = repo_path or Path.cwd()

    # Show XDG directory status
    table = Table(title="Ca-Bhfuil System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Status", style="yellow")

    config_dir = get_config_dir()
    state_dir = get_state_dir()
    cache_dir = get_cache_dir()

    table.add_row(
        "Config Directory", str(config_dir), "✅" if config_dir.exists() else "❌"
    )
    table.add_row(
        "State Directory", str(state_dir), "✅" if state_dir.exists() else "❌"
    )
    table.add_row(
        "Cache Directory", str(cache_dir), "✅" if cache_dir.exists() else "❌"
    )

    console.print(table)

    # Check configuration
    try:
        config_manager = get_config_manager()
        config = config_manager.load_configuration()

        rprint(f"📊 Configured repositories: {len(config.repos)}")
        if config.repos:
            for repo in config.repos[:3]:  # Show first 3
                rprint(f"   • {repo.name}")
            if len(config.repos) > 3:
                rprint(f"   ... and {len(config.repos) - 3} more")

        rprint("[green]✅ Ca-bhfuil configuration loaded successfully![/green]")

    except Exception as e:
        rprint(f"[red]⚠️  Configuration issue: {e}[/red]")


def version_callback(value: bool) -> None:
    """Version callback function."""
    if value:
        rprint("ca-bhfuil 0.1.0")
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
    pass


if __name__ == "__main__":
    app()
