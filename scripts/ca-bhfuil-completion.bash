#!/bin/bash
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
