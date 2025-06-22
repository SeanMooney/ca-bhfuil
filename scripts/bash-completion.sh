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
    local global_options="--version --help"

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
                            COMPREPLY=($(compgen -W "$config_show_options --help" -- "$cur"))
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
                    COMPREPLY=($(compgen -W "--repo --verbose --help" -- "$cur"))
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
complete -F _ca_bhfuil_completion -o bashdefault -o default python