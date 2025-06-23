"""Bash completion support for ca-bhfuil CLI."""

import pathlib

import typer


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


def install_completion(shell: str = "bash") -> None:
    """Install shell completion for ca-bhfuil."""
    if shell == "bash":
        completion_script = _generate_bash_completion()
        completion_file = pathlib.Path.home() / ".bash_completion.d" / "ca-bhfuil"

        # Create completion directory if it doesn't exist
        completion_file.parent.mkdir(exist_ok=True)

        # Write completion script
        with open(completion_file, "w") as f:
            f.write(completion_script)

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
    local commands="config search status"

    # Config subcommands
    local config_commands="init validate status show"

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
        search)
            case "$prev" in
                --repo|-r)
                    # Complete directory paths
                    COMPREPLY=($(compgen -d -- "$cur"))
                    ;;
                *)
                    # If we have a query already, only offer options
                    if [ ${#words[@]} -gt 2 ] && [[ "${words[2]}" != --* ]]; then
                        COMPREPLY=($(compgen -W "--repo --verbose --help" -- "$cur"))
                    else
                        # No query yet, don't offer specific completions
                        COMPREPLY=($(compgen -W "--repo --verbose --help" -- "$cur"))
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
    with open(bash_script, "w") as f:
        f.write(_generate_bash_completion())

    typer.echo(f"Generated bash completion script: {bash_script}")


if __name__ == "__main__":
    # Generate completion scripts when run directly
    generate_completion_scripts()
