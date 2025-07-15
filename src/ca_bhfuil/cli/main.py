"""Main CLI application for ca-bhfuil."""

import asyncio
import contextlib
import json
import pathlib
import shutil
import subprocess
import traceback

import aiofiles
from rich import console
from rich import panel
from rich import syntax
from rich import table
import typer
import yaml

from ca_bhfuil.cli import completion
from ca_bhfuil.cli.async_bridge import async_command
from ca_bhfuil.cli.async_bridge import run_async
from ca_bhfuil.cli.async_bridge import with_progress
from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_registry
from ca_bhfuil.core import async_repository
from ca_bhfuil.core import async_sync
from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.git import clone
from ca_bhfuil.core.models import commit as commit_models


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

# Create repo subcommand group
repo_app = typer.Typer(
    name="repo",
    help="Repository management commands",
    no_args_is_help=True,
)
app.add_typer(repo_app, name="repo")

# Create db subcommand group
db_app = typer.Typer(
    name="db",
    help="Database migration commands",
    no_args_is_help=True,
)
app.add_typer(db_app, name="db")

rich_console = console.Console()


def _build_repo_data(
    repo: config.RepositoryConfig, verbose: bool
) -> dict[str, str | None]:
    """Build a standardized repository data dictionary."""
    repo_dict = {
        "name": repo.name,
        "url": repo.source.get("url", "N/A"),
        "auth_key": repo.auth_key or "default",
        "type": repo.source.get("type", "git"),
    }
    if verbose:
        repo_dict.update(
            {
                "clone_url": repo.source.get("clone_url"),
                "branch": repo.source.get("branch", "main"),
            }
        )
    return repo_dict


@db_app.command("upgrade")
@async_command
async def db_upgrade() -> None:
    """Apply pending database migrations."""
    try:
        rich_console.print("[bold blue]Applying database migrations...[/bold blue]")

        async def _run_alembic_upgrade() -> tuple[int | None, bytes, bytes]:
            process = await asyncio.create_subprocess_shell(
                "uv run alembic upgrade head",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return process.returncode, stdout, stderr

        returncode, stdout, stderr = await with_progress(
            _run_alembic_upgrade(),
            "Running Alembic upgrade...",
        )

        if returncode == 0:
            rich_console.print(
                "[green]✅ Database migration applied successfully![/green]"
            )
        else:
            rich_console.print(
                f"[red]❌ Database migration failed: {stderr.decode().strip()}[/red]"
            )
            raise typer.Exit(1)

    except Exception as e:
        rich_console.print(f"[red]❌ Error during database migration: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("init")
@async_command
async def config_init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
) -> None:
    """Initialize default configuration files."""
    try:
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

    except Exception as e:
        rich_console.print(f"[red]❌ Error initializing configuration: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("validate")
@async_command
async def config_validate() -> None:
    """Validate current configuration."""
    try:
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

    except Exception as e:
        rich_console.print(f"[red]❌ Error validating configuration: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("status")
@async_command
async def config_status() -> None:
    """Show configuration system status."""
    try:
        config_manager = await async_config.get_async_config_manager()

        # Show configuration paths
        status_table = table.Table(title="Ca-Bhfuil Configuration Status")
        status_table.add_column("Directory", style="cyan")
        status_table.add_column("Path", style="green")
        status_table.add_column("Exists", style="yellow")

        config_dir = config.get_config_dir()
        state_dir = config.get_state_dir()
        cache_dir = config.get_cache_dir()

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
        global_config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )
        if global_config.repos:
            repos_table = table.Table(title="Configured Repositories")
            repos_table.add_column("Name", style="cyan")
            repos_table.add_column("URL", style="green")
            repos_table.add_column("Auth", style="yellow")

            for repo in global_config.repos:
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
        raise typer.Exit(1) from e


@config_app.command("show")
@async_command
async def config_show(
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
        config_manager = await async_config.get_async_config_manager()

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

            # Read and display file contents asynchronously
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

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
        raise typer.Exit(1) from e


@app.command()
def install_completion(
    shell: str = typer.Argument("bash", help="Shell type (bash, zsh, fish)"),
) -> None:
    """Install shell completion for ca-bhfuil."""
    try:
        completion.install_completion(shell)
    except Exception as e:
        rich_console.print(f"[red]❌ Error installing completion: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
@async_command
async def search(
    query_words: list[str] = typer.Argument(
        ..., help="Search query words (SHA, partial SHA, or commit message pattern)"
    ),
    repo_name: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository name from configuration (defaults to current directory)",
        autocompletion=completion.complete_repository_name,
    ),
    max_results: int = typer.Option(
        10, "--max", "-m", help="Maximum number of results to return"
    ),
    pattern_search: bool = typer.Option(
        False, "--pattern", "-p", help="Force pattern search in commit messages"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Search for commits in the repository."""
    # Join query words into a single search string
    query = " ".join(query_words)

    try:
        # Initialize repository manager and config manager
        repo_manager = async_repository.AsyncRepositoryManager()
        config_manager = async_config.AsyncConfigManager()

        # Determine the repository path
        if repo_name:
            # Look up repository configuration by name
            repo_config = await config_manager.get_repository_config_by_name(repo_name)
            if not repo_config:
                rich_console.print(
                    f"[red]❌ Repository '{repo_name}' not found in configuration[/red]"
                )
                rich_console.print(
                    "💡 Use 'ca-bhfuil repo list' to see configured repositories"
                )
                raise typer.Exit(1)

            repo_path = repo_config.repo_path
            if verbose:
                rich_console.print(
                    f"📁 Using configured repository '{repo_name}': {repo_path}"
                )
        else:
            # Use current directory
            repo_path = pathlib.Path.cwd()
            if verbose:
                rich_console.print(f"📁 Using current directory: {repo_path}")

        # Detect/validate the repository
        detect_result = await with_progress(
            repo_manager.detect_repository(repo_path),
            f"Detecting git repository at {repo_path}...",
        )

        if not detect_result.success:
            if repo_name:
                rich_console.print(
                    f"[red]❌ Repository '{repo_name}' not found at {repo_path}[/red]"
                )
                rich_console.print(
                    "💡 The repository may not be cloned yet. Use 'ca-bhfuil repo clone' first"
                )
            else:
                rich_console.print(f"[red]❌ {detect_result.error}[/red]")
                rich_console.print(
                    "💡 Make sure you're in a git repository or use --repo to specify a repository name"
                )
            raise typer.Exit(1)

        detected_repo_path = pathlib.Path(detect_result.result["repository_path"])

        # Determine if this looks like a SHA or a pattern
        is_sha_like = (
            len(query) >= 4
            and all(c in "0123456789abcdef" for c in query.lower())
            and not pattern_search
        )

        if is_sha_like:
            # Try SHA lookup first
            rich_console.print(f"🔍 Looking up commit: {query}")
            lookup_result = await with_progress(
                repo_manager.lookup_commit(detected_repo_path, query),
                f"Searching for commit {query}...",
            )

            if lookup_result.success:
                commit = lookup_result.result
                _display_commit_details(commit, verbose)
                return
            rich_console.print(
                f"[yellow]⚠️  No exact SHA match found for '{query}'[/yellow]"
            )
            # Fall through to pattern search

        # Pattern search in commit messages
        rich_console.print(f"🔍 Searching commit messages for: '{query}'")
        search_result = await with_progress(
            repo_manager.search_commits(detected_repo_path, query, max_results),
            "Searching commit messages...",
        )

        if not search_result.success:
            rich_console.print(f"[red]❌ Search failed: {search_result.error}[/red]")
            raise typer.Exit(1)

        matches = search_result.matches

        if not matches:
            rich_console.print(f"[yellow]No commits found matching '{query}'[/yellow]")
            return

        # Display results
        _display_search_results(matches, query, verbose)

        if len(matches) == max_results:
            rich_console.print(
                f"[yellow]💡 Showing first {max_results} results. Use --max to see more.[/yellow]"
            )

    except Exception as e:
        rich_console.print(f"[red]❌ Search error: {e}[/red]")
        if verbose:
            rich_console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1) from e
    finally:
        with contextlib.suppress(Exception):
            repo_manager.shutdown()


def _display_commit_details(
    commit: commit_models.CommitInfo, verbose: bool = False
) -> None:
    """Display detailed information about a single commit."""
    # Create commit details table
    commit_table = table.Table(title=f"Commit {commit.short_sha}")
    commit_table.add_column("Field", style="cyan")
    commit_table.add_column("Value", style="green")

    commit_table.add_row("SHA", commit.sha)
    commit_table.add_row("Short SHA", commit.short_sha)
    commit_table.add_row("Author", f"{commit.author_name} <{commit.author_email}>")
    commit_table.add_row("Date", commit.author_date.strftime("%Y-%m-%d %H:%M:%S %Z"))

    if verbose:
        commit_table.add_row(
            "Committer", f"{commit.committer_name} <{commit.committer_email}>"
        )
        commit_table.add_row(
            "Commit Date", commit.committer_date.strftime("%Y-%m-%d %H:%M:%S %Z")
        )
        if commit.parents:
            commit_table.add_row("Parents", ", ".join(p[:7] for p in commit.parents))

    rich_console.print(commit_table)

    # Display commit message
    rich_console.print(
        panel.Panel(commit.message.strip(), title="Commit Message", border_style="blue")
    )


def _display_search_results(
    matches: list[commit_models.CommitInfo], query: str, verbose: bool = False
) -> None:
    """Display search results in a formatted table."""
    results_table = table.Table(title=f"Search Results for '{query}'")
    results_table.add_column("SHA", style="yellow", width=10)
    results_table.add_column("Author", style="cyan", width=20)
    results_table.add_column("Date", style="blue", width=12)
    results_table.add_column("Message", style="green")

    for commit in matches:
        # Truncate message for table display
        message = commit.message.split("\n")[0]  # First line only
        if len(message) > 60:
            message = message[:57] + "..."

        date_str = commit.author_date.strftime("%Y-%m-%d")
        author_str = commit.author_name
        if len(author_str) > 18:
            author_str = author_str[:15] + "..."

        results_table.add_row(commit.short_sha, author_str, date_str, message)

    rich_console.print(results_table)
    rich_console.print(f"📊 Found {len(matches)} matching commits")

    if verbose and matches:
        rich_console.print("\n[bold]Detailed view of first result:[/bold]")
        _display_commit_details(matches[0], verbose)


@app.command()
@async_command
async def status(
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

    config_dir = config.get_config_dir()
    state_dir = config.get_state_dir()
    cache_dir = config.get_cache_dir()

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
        config_manager = await async_config.get_async_config_manager()
        global_config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )

        rich_console.print(f"📊 Configured repositories: {len(global_config.repos)}")
        if global_config.repos:
            for repo in global_config.repos[:3]:  # Show first 3
                rich_console.print(f"   • {repo.name}")
            if len(global_config.repos) > 3:
                rich_console.print(f"   ... and {len(global_config.repos) - 3} more")

        rich_console.print(
            "[green]✅ Ca-bhfuil configuration loaded successfully![/green]"
        )

    except Exception as e:
        rich_console.print(f"[red]⚠️  Configuration issue: {e}[/red]")


@repo_app.command("add")
@async_command
async def repo_add(
    url: str = typer.Argument(..., help="Repository URL to add"),
    name: str | None = typer.Option(
        None, "--name", "-n", help="Repository name (defaults to inferred from URL)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force clone even if repository exists"
    ),
) -> None:
    """Add a repository to the configuration and clone it."""
    try:
        config_manager = await async_config.get_async_config_manager()
        git_manager = async_git.AsyncGitManager()
        cloner = clone.AsyncRepositoryCloner(git_manager)
        repo_registry = await async_registry.get_async_repository_registry()

        # Load existing configuration
        current_config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )

        # Infer name from URL if not provided
        if not name:
            if url.endswith(".git"):
                name = url.split("/")[-1][:-4]  # Remove .git extension
            else:
                name = url.split("/")[-1]

        # Check if repository already exists in config
        for repo in current_config.repos:
            if repo.source.get("url") == url:
                rich_console.print(
                    f"[yellow]Repository '{url}' already configured[/yellow]"
                )
                raise typer.Exit(1)
            if repo.name == name:
                rich_console.print(
                    f"[yellow]Repository name '{name}' already in use[/yellow]"
                )
                raise typer.Exit(1)

        rich_console.print(f"🔄 Adding repository: {name}")
        rich_console.print(f"📁 URL: {url}")

        # Create a RepositoryConfig object
        new_repo_config = config.RepositoryConfig(
            name=name,
            source={"url": url, "type": "git"},
        )

        # Perform the clone operation
        clone_result = await with_progress(
            cloner.clone_repository(new_repo_config, force=force),
            f"Cloning {name}...",
        )

        if not clone_result.success:
            rich_console.print(
                f"[red]❌ Failed to clone repository: {clone_result.error}[/red]"
            )
            raise typer.Exit(1)

        rich_console.print(
            f"[green]✅ Successfully cloned {name} to {clone_result.repository_path}[/green]"
        )

        # Add the new repository to the configuration and save
        current_config.repos.append(new_repo_config)
        await with_progress(
            config_manager.save_configuration(current_config),
            "Updating configuration...",
        )

        # Register the repository in the database
        await with_progress(
            repo_registry.register_repository(new_repo_config),
            "Registering repository in database...",
        )

        rich_console.print(
            "[green]✅ Repository added to configuration and database![/green]"
        )

    except Exception as e:
        rich_console.print(f"[red]❌ Error adding repository: {e}[/red]")
        raise typer.Exit(1) from e


@repo_app.command("list")
@async_command
async def repo_list(
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, yaml",
        autocompletion=completion.complete_format,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show additional repository details"
    ),
) -> None:
    """List all configured repositories."""
    try:
        config_manager = await async_config.get_async_config_manager()

        config = await with_progress(
            config_manager.load_configuration(), "Loading repositories..."
        )

        if not config.repos:
            rich_console.print("[yellow]No repositories configured[/yellow]")
            rich_console.print("💡 Use 'ca-bhfuil repo add <url>' to add repositories")
            return

        if format == "json":
            repos_data = [_build_repo_data(repo, verbose) for repo in config.repos]
            rich_console.print_json(json.dumps(repos_data, indent=2))
        elif format == "yaml":
            repos_data = [_build_repo_data(repo, verbose) for repo in config.repos]
            yaml_str = yaml.dump(repos_data, default_flow_style=False)
            syntax_obj = syntax.Syntax(yaml_str, "yaml", theme="monokai")
            rich_console.print(syntax_obj)
        else:  # table format
            repos_table = table.Table(title="Configured Repositories")
            repos_table.add_column("Name", style="cyan")
            repos_table.add_column("URL", style="green")
            repos_table.add_column("Auth", style="yellow")
            if verbose:
                repos_table.add_column("Type", style="blue")
                repos_table.add_column("Branch", style="magenta")

            for repo in config.repos:
                row_data = [
                    repo.name,
                    repo.source.get("url", "N/A"),
                    repo.auth_key or "default",
                ]
                if verbose:
                    row_data.extend(
                        [
                            repo.source.get("type", "git"),
                            repo.source.get("branch", "main"),
                        ]
                    )
                repos_table.add_row(*row_data)

            rich_console.print(repos_table)
            rich_console.print(f"📊 Total repositories: {len(config.repos)}")

    except Exception as e:
        rich_console.print(f"[red]❌ Error listing repositories: {e}[/red]")
        raise typer.Exit(1) from e


@repo_app.command("update")
@async_command
async def repo_update(
    name: str = typer.Argument(
        ...,
        help="Repository name to update",
        autocompletion=completion.complete_repository_name,
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force update even if no changes detected"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed update progress"
    ),
) -> None:
    """Update/sync a configured repository with its remote."""
    try:
        config_manager = await async_config.get_async_config_manager()
        synchronizer = async_sync.AsyncRepositorySynchronizer()

        # Load configuration and find the repository
        config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )

        repo_config = None
        for repo in config.repos:
            if repo.name == name:
                repo_config = repo
                break

        if not repo_config:
            rich_console.print(f"[red]❌ Repository '{name}' not found[/red]")
            rich_console.print(
                "💡 Use 'ca-bhfuil repo list' to see available repositories"
            )
            raise typer.Exit(1)

        repo_path = repo_config.repo_path
        if not repo_path.exists():
            rich_console.print(
                f"[red]❌ Repository '{name}' not found at {repo_path}[/red]"
            )
            rich_console.print("💡 The repository may need to be cloned first")
            raise typer.Exit(1)

        rich_console.print(f"🔄 Updating repository: {name}")
        rich_console.print(f"📁 Path: {repo_path}")

        # Perform the update/sync operation
        # Note: force parameter is reserved for future use
        _ = force  # Explicitly acknowledge unused parameter
        update_result = await with_progress(
            synchronizer.sync_repository(name),
            f"Updating {name}...",
        )

        if update_result.success:
            rich_console.print(f"[green]✅ Successfully updated {name}[/green]")
            if verbose and update_result.result:
                changes = update_result.result
                commits_before = changes.get("commits_before", 0)
                commits_after = changes.get("commits_after", 0)
                if commits_before != commits_after:
                    rich_console.print(
                        f"📥 Repository updated: {commits_before} → {commits_after} commits"
                    )
                else:
                    rich_console.print("📊 Repository is up to date")
        else:
            rich_console.print(
                f"[red]❌ Failed to update repository: {update_result.error}[/red]"
            )
            raise typer.Exit(1)

    except Exception as e:
        rich_console.print(f"[red]❌ Error updating repository: {e}[/red]")
        raise typer.Exit(1) from e


@repo_app.command("remove")
@async_command
async def repo_remove(
    name: str = typer.Argument(
        ...,
        help="Repository name to remove",
        autocompletion=completion.complete_repository_name,
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    keep_files: bool = typer.Option(
        False, "--keep-files", help="Keep repository files, only remove from config"
    ),
) -> None:
    """Remove a repository from configuration (optionally delete files)."""
    try:
        config_manager = await async_config.get_async_config_manager()

        # Load configuration and find the repository
        config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )

        repo_config = None
        repo_index = None
        for i, repo in enumerate(config.repos):
            if repo.name == name:
                repo_config = repo
                repo_index = i
                break

        if repo_config is None:
            rich_console.print(f"[red]❌ Repository '{name}' not found[/red]")
            rich_console.print(
                "💡 Use 'ca-bhfuil repo list' to see available repositories"
            )
            raise typer.Exit(1)

        # Show repository details
        rich_console.print(f"🗑️  Removing repository: {name}")
        rich_console.print(f"📁 URL: {repo_config.source.get('url', 'N/A')}")
        rich_console.print(f"📂 Path: {repo_config.repo_path}")

        if not force:
            # Interactive confirmation
            confirm = typer.confirm("Are you sure you want to remove this repository?")
            if not confirm:
                rich_console.print("[yellow]Removal cancelled[/yellow]")
                raise typer.Exit(0)

            if not keep_files:
                confirm_delete = typer.confirm(
                    f"Also delete repository files at {repo_config.repo_path}?"
                )
                keep_files = not confirm_delete

        # Remove from configuration
        removed_repo = config.repos.pop(repo_index)

        await with_progress(
            config_manager.save_configuration(config),
            "Updating configuration...",
        )

        rich_console.print(f"[green]✅ Removed '{name}' from configuration[/green]")

        # Handle file deletion if requested
        if not keep_files:
            repo_path = removed_repo.repo_path
            if repo_path.exists():
                try:
                    await with_progress(
                        asyncio.to_thread(shutil.rmtree, repo_path),
                        f"Deleting files at {repo_path}...",
                    )
                    rich_console.print("[green]✅ Deleted repository files[/green]")
                except Exception as e:
                    rich_console.print(
                        f"[yellow]⚠️  Failed to delete files: {e}[/yellow]"
                    )
                    rich_console.print(f"💡 You can manually delete: {repo_path}")
            else:
                rich_console.print(
                    "[yellow]⚠️  Repository files not found (already deleted)[/yellow]"
                )

    except Exception as e:
        rich_console.print(f"[red]❌ Error removing repository: {e}[/red]")
        raise typer.Exit(1) from e


@repo_app.command("sync")
@async_command
async def repo_sync(
    name: str | None = typer.Argument(
        None,
        help="Repository name to sync (syncs all if not specified)",
        autocompletion=completion.complete_repository_name,
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force sync even if no changes detected"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed sync progress"
    ),
) -> None:
    """Sync all configured repositories or a specific one."""
    try:
        config_manager = await async_config.get_async_config_manager()
        synchronizer = async_sync.AsyncRepositorySynchronizer()

        config = await with_progress(
            config_manager.load_configuration(), "Loading configuration..."
        )

        if not config.repos:
            rich_console.print("[yellow]No repositories configured[/yellow]")
            rich_console.print("💡 Use 'ca-bhfuil repo add <url>' to add repositories")
            return

        # Determine which repositories to sync
        repos_to_sync = []
        if name:
            # Sync specific repository
            for repo in config.repos:
                if repo.name == name:
                    repos_to_sync.append(repo)
                    break
            if not repos_to_sync:
                rich_console.print(f"[red]❌ Repository '{name}' not found[/red]")
                rich_console.print(
                    "💡 Use 'ca-bhfuil repo list' to see available repositories"
                )
                raise typer.Exit(1)
        else:
            # Sync all repositories
            repos_to_sync = config.repos

        rich_console.print(f"🔄 Syncing {len(repos_to_sync)} repository(s)...")

        success_count = 0
        error_count = 0

        for repo in repos_to_sync:
            try:
                repo_path = repo.repo_path
                if not repo_path.exists():
                    rich_console.print(
                        f"[yellow]⚠️  Skipping {repo.name}: repository not found at {repo_path}[/yellow]"
                    )
                    error_count += 1
                    continue

                if verbose:
                    rich_console.print(f"📁 Syncing {repo.name}...")

                # Note: force parameter is reserved for future use
                _ = force  # Explicitly acknowledge unused parameter
                sync_result = await with_progress(
                    synchronizer.sync_repository(repo.name),
                    f"Syncing {repo.name}...",
                )

                if sync_result.success:
                    success_count += 1
                    if verbose:
                        rich_console.print(
                            f"[green]✅ {repo.name} synced successfully[/green]"
                        )
                else:
                    error_count += 1
                    rich_console.print(
                        f"[red]❌ Failed to sync {repo.name}: {sync_result.error}[/red]"
                    )

            except Exception as e:
                error_count += 1
                rich_console.print(f"[red]❌ Error syncing {repo.name}: {e}[/red]")

        # Summary
        rich_console.print(
            f"\n📊 Sync complete: {success_count} successful, {error_count} failed"
        )
        if error_count > 0:
            raise typer.Exit(1)

    except Exception as e:
        rich_console.print(f"[red]❌ Error syncing repositories: {e}[/red]")
        raise typer.Exit(1) from e


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


async def amain() -> None:
    """Async main function to run the typer app."""
    app()


if __name__ == "__main__":
    run_async(amain())
