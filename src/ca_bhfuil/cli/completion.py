"""Bash completion support for ca-bhfuil CLI."""

import pathlib

import typer

from ca_bhfuil.core import config


def complete_format(incomplete: str) -> list[str]:
    """Complete format options."""
    formats = ["yaml", "json"]
    return [fmt for fmt in formats if fmt.startswith(incomplete)]


def complete_repo_path(incomplete: str) -> list[str]:
    """Complete repository paths (directories)."""
    try:
        if incomplete:
            path = pathlib.Path(incomplete)
            if path.is_dir():
                # Complete subdirectories
                return [
                    str(p)
                    for p in path.iterdir()
                    if p.is_dir() and str(p).startswith(incomplete)
                ]
            # Complete from parent directory
            parent = path.parent
            name = path.name
            if parent.exists():
                return [
                    str(parent / p.name)
                    for p in parent.iterdir()
                    if p.is_dir() and p.name.startswith(name)
                ]
        else:
            # Complete from current directory
            return [str(p) for p in pathlib.Path().iterdir() if p.is_dir()]
    except (OSError, PermissionError):
        return []

    return []


def complete_repository_name(incomplete: str) -> list[str]:
    """Complete configured repository names.

    Note: This uses synchronous config loading as bash completion
    requires immediate response. This is acceptable for CLI completion.
    """
    try:
        # Use sync config manager for bash completion - this is legitimate
        # since bash completion must be synchronous and fast
        config_manager = config.ConfigManager()
        global_config = config_manager.load_configuration()

        repo_names = [repo.name for repo in global_config.repos]
        return [name for name in repo_names if name.startswith(incomplete)]
    except Exception:
        # If we can't load config, return empty list
        return []


def install_completion(shell: str = "bash") -> None:
    """Install shell completion for ca-bhfuil."""
    if shell == "bash":
        completion_script = _generate_bash_completion()
        completion_file = pathlib.Path.home() / ".bash_completion.d" / "ca-bhfuil"

        # Create completion directory if it doesn't exist
        completion_file.parent.mkdir(exist_ok=True)

        # Write completion script
        completion_file.write_text(completion_script, encoding="utf-8")

        typer.echo(f"Bash completion installed to {completion_file}")
        typer.echo("Source your .bashrc or start a new shell to enable completion")
    else:
        typer.echo(f"Shell '{shell}' is not supported yet")


def _generate_bash_completion() -> str:
    """Generate bash completion script."""
    return """#!/bin/bash
# Bash completion for ca-bhfuil CLI

_ca_bhfuil_completion() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="config repo search status"

    # Config subcommands
    local config_commands="init validate status show"

    # Repo subcommands
    local repo_commands="add list update remove sync"

    # Config show options
    local config_show_options="--repos --global --auth --all --format"

    # Format options
    local format_options="yaml json"

    # Global options
    local global_options="--version --help --install-completion --show-completion"

    case "${words[1]}" in
        config)
            case "${words[2]}" in
                init)
                    case "$prev" in
                        *)
                            COMPREPLY=($(compgen -W "--force --help" -- "$cur"))
                            ;;
                    esac
                    ;;
                validate)
                    case "$prev" in
                        *)
                            COMPREPLY=($(compgen -W "--help" -- "$cur"))
                            ;;
                    esac
                    ;;
                status)
                    case "$prev" in
                        *)
                            COMPREPLY=($(compgen -W "--help" -- "$cur"))
                            ;;
                    esac
                    ;;
                show)
                    case "$prev" in
                        --format|-f)
                            COMPREPLY=($(compgen -W "$format_options" -- "$cur"))
                            ;;
                        *)
                            # Check if already have some flags
                            local have_repos=0
                            local have_global=0
                            local have_auth=0
                            local have_all=0

                            for word in "${words[@]}"; do
                                case "$word" in
                                    --repos) have_repos=1 ;;
                                    --global) have_global=1 ;;
                                    --auth) have_auth=1 ;;
                                    --all) have_all=1 ;;
                                esac
                            done

                            # If --all is present, only offer format and help
                            if [ $have_all -eq 1 ]; then
                                COMPREPLY=($(compgen -W "--format --help" -- "$cur"))
                            else
                                COMPREPLY=($(compgen -W "$config_show_options --help" -- "$cur"))
                            fi
                            ;;
                    esac
                    ;;
                *)
                    case "$prev" in
                        config)
                            COMPREPLY=($(compgen -W "$config_commands --help" -- "$cur"))
                            ;;
                        *)
                            COMPREPLY=($(compgen -W "$config_commands --help" -- "$cur"))
                            ;;
                    esac
                    ;;
            esac
            ;;
        repo)
            case "${words[2]}" in
                add)
                    case "$prev" in
                        --name|-n)
                            # No completion for custom names
                            COMPREPLY=()
                            ;;
                        *)
                            # If we already have a URL, only offer options
                            if [ ${#words[@]} -gt 3 ] && [[ "${words[3]}" != --* ]]; then
                                COMPREPLY=($(compgen -W "--name --force --help" -- "$cur"))
                            else
                                COMPREPLY=($(compgen -W "--name --force --help" -- "$cur"))
                            fi
                            ;;
                    esac
                    ;;
                list)
                    case "$prev" in
                        --format|-f)
                            COMPREPLY=($(compgen -W "table json yaml" -- "$cur"))
                            ;;
                        *)
                            COMPREPLY=($(compgen -W "--format --verbose --help" -- "$cur"))
                            ;;
                    esac
                    ;;
                update)
                    case "$prev" in
                        update)
                            # Complete repository names
                            COMPREPLY=($(compgen -W "$(python -c "from ca_bhfuil.cli.completion import complete_repository_name; print(' '.join(complete_repository_name('$cur')))" 2>/dev/null)" -- "$cur"))
                            ;;
                        *)
                            # If we already have a repository name, only offer options
                            if [ ${#words[@]} -gt 3 ] && [[ "${words[3]}" != --* ]]; then
                                COMPREPLY=($(compgen -W "--force --verbose --help" -- "$cur"))
                            else
                                COMPREPLY=($(compgen -W "--force --verbose --help" -- "$cur"))
                            fi
                            ;;
                    esac
                    ;;
                remove)
                    case "$prev" in
                        remove)
                            # Complete repository names
                            COMPREPLY=($(compgen -W "$(python -c "from ca_bhfuil.cli.completion import complete_repository_name; print(' '.join(complete_repository_name('$cur')))" 2>/dev/null)" -- "$cur"))
                            ;;
                        *)
                            # If we already have a repository name, only offer options
                            if [ ${#words[@]} -gt 3 ] && [[ "${words[3]}" != --* ]]; then
                                COMPREPLY=($(compgen -W "--force --keep-files --help" -- "$cur"))
                            else
                                COMPREPLY=($(compgen -W "--force --keep-files --help" -- "$cur"))
                            fi
                            ;;
                    esac
                    ;;
                sync)
                    case "$prev" in
                        sync)
                            # Complete repository names (optional argument)
                            COMPREPLY=($(compgen -W "$(python -c "from ca_bhfuil.cli.completion import complete_repository_name; print(' '.join(complete_repository_name('$cur')))" 2>/dev/null) --force --verbose --help" -- "$cur"))
                            ;;
                        *)
                            # If we already have a repository name, only offer options
                            if [ ${#words[@]} -gt 3 ] && [[ "${words[3]}" != --* ]]; then
                                COMPREPLY=($(compgen -W "--force --verbose --help" -- "$cur"))
                            else
                                COMPREPLY=($(compgen -W "--force --verbose --help" -- "$cur"))
                            fi
                            ;;
                    esac
                    ;;
                *)
                    case "$prev" in
                        repo)
                            COMPREPLY=($(compgen -W "$repo_commands --help" -- "$cur"))
                            ;;
                        *)
                            COMPREPLY=($(compgen -W "$repo_commands --help" -- "$cur"))
                            ;;
                    esac
                    ;;
            esac
            ;;
        search)
            case "$prev" in
                --repo|-r)
                    # Complete repository names (would need custom function)
                    COMPREPLY=($(compgen -W "" -- "$cur"))
                    ;;
                *)
                    # If we have a query already, only offer options
                    if [ ${#words[@]} -gt 2 ] && [[ "${words[2]}" != --* ]]; then
                        COMPREPLY=($(compgen -W "--repo --max --pattern --verbose --help" -- "$cur"))
                    else
                        # No query yet, don't offer specific completions
                        COMPREPLY=($(compgen -W "--repo --max --pattern --verbose --help" -- "$cur"))
                    fi
                    ;;
            esac
            ;;
        status)
            case "$prev" in
                --repo|-r)
                    # Complete directory paths
                    COMPREPLY=($(compgen -d -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--repo --verbose --help" -- "$cur"))
                    ;;
            esac
            ;;
        *)
            case "$prev" in
                ca-bhfuil)
                    COMPREPLY=($(compgen -W "$commands $global_options" -- "$cur"))
                    ;;
                --install-completion)
                    COMPREPLY=($(compgen -W "bash zsh fish" -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "$commands $global_options" -- "$cur"))
                    ;;
            esac
            ;;
    esac
}

# Register completion function
complete -F _ca_bhfuil_completion ca-bhfuil

# Also support completion for python -m ca_bhfuil
_python_ca_bhfuil_completion() {
    local cur prev words cword
    _init_completion || return

    # Check if this is python -m ca_bhfuil
    if [[ "${words[1]}" == "-m" && "${words[2]}" == "ca_bhfuil" ]]; then
        # Shift words to remove "python -m ca_bhfuil" and call main completion
        local shifted_words=("ca-bhfuil" "${words[@]:3}")
        words=("${shifted_words[@]}")
        cword=$((cword - 2))
        _ca_bhfuil_completion
    fi
}

# Register completion for python -m ca_bhfuil
complete -F _python_ca_bhfuil_completion -o bashdefault -o default python
"""


def generate_completion_scripts() -> None:
    """Generate completion scripts for different shells."""
    scripts_dir = pathlib.Path(__file__).parent.parent.parent.parent / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Generate bash completion
    bash_script = scripts_dir / "ca-bhfuil-completion.bash"
    bash_script.write_text(_generate_bash_completion(), encoding="utf-8")

    typer.echo(f"Generated bash completion script: {bash_script}")


if __name__ == "__main__":
    # Generate completion scripts when run directly
    generate_completion_scripts()
