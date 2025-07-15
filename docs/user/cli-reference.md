# CLI Reference

This document provides a comprehensive reference for the ca-bhfuil command-line interface.

## Overview

Ca-bhfuil provides a command-line interface for managing git repository analysis configuration and performing commit searches across stable branches.

```bash
ca-bhfuil [OPTIONS] COMMAND [ARGS]...
```

## User Experience Features

### Progress Display

Long-running operations display progress information to keep you informed:

```bash
# Configuration operations show loading progress
ca-bhfuil config init

# Repository operations show detailed progress
ca-bhfuil repo add https://github.com/user/repo --force

# Search operations with progress tracking
ca-bhfuil search "fix bug" --verbose
```

### Responsive Interface

The CLI remains responsive during operations:

- **Interruptible Operations**: Use Ctrl+C to cancel long-running operations
- **Status Updates**: Real-time progress bars and status messages
- **Non-blocking**: The interface stays responsive during file and network operations

### Error Handling

Operations include built-in error handling and recovery:

- **Clear Error Messages**: User-friendly error descriptions with actionable suggestions
- **Retry Logic**: Automatic retry for transient network issues
- **Graceful Degradation**: Operations continue with partial results when possible

## Global Options

- `--version`: Show version and exit
- `--help`: Show help message and exit

## Commands

### config

Configuration management commands for ca-bhfuil.

```bash
ca-bhfuil config [OPTIONS] COMMAND [ARGS]...
```

#### config init

Initialize default configuration files.

```bash
ca-bhfuil config init [OPTIONS]
```

**Options:**
- `--force`, `-f`: Overwrite existing configuration files

**Description:**
Creates the default configuration files in the XDG-compliant directory structure:
- `~/.config/ca-bhfuil/repos.yaml`: Repository configuration
- `~/.config/ca-bhfuil/global.yaml`: Global settings
- `~/.config/ca-bhfuil/auth.yaml`: Authentication configuration (secure permissions)

**Examples:**
```bash
# Initialize default configuration
ca-bhfuil config init

# Force overwrite existing configuration
ca-bhfuil config init --force
```

#### config validate

Validate current configuration files.

```bash
ca-bhfuil config validate
```

**Description:**
Validates all configuration files for:
- YAML syntax errors
- Schema validation
- Duplicate repository names or URLs
- Invalid authentication references
- Missing required fields

**Examples:**
```bash
# Validate current configuration
ca-bhfuil config validate
```

#### config status

Show configuration system status.

```bash
ca-bhfuil config status
```

**Description:**
Displays comprehensive status information including:
- XDG directory paths and existence
- Configuration file status
- Configured repositories summary

**Examples:**
```bash
# Show configuration status
ca-bhfuil config status
```

#### config show

Display configuration file contents.

```bash
ca-bhfuil config show [OPTIONS]
```

**Options:**
- `--repos`: Show repos configuration (`repos.yaml`)
- `--global`: Show global configuration (`global.yaml`)
- `--auth`: Show auth configuration (`auth.yaml`)
- `--all`: Show all configuration files
- `--format`, `-f`: Output format: `yaml` (default) or `json`

**Description:**
Displays configuration file contents with syntax highlighting. Multiple options can be combined to show multiple files. Defaults to showing global configuration if no options are specified.

**Examples:**
```bash
# Show global configuration (default)
ca-bhfuil config show
ca-bhfuil config show --global

# Show specific configuration files
ca-bhfuil config show --repos
ca-bhfuil config show --auth

# Show multiple configuration files
ca-bhfuil config show --repos --global
ca-bhfuil config show --repos --auth

# Show all configuration files
ca-bhfuil config show --all

# Show configuration in JSON format
ca-bhfuil config show --global --format json
ca-bhfuil config show --all --format json

# Combine multiple files with JSON format
ca-bhfuil config show --repos --auth --format json
```

### search

Search for commits in repositories.

```bash
ca-bhfuil search [OPTIONS] QUERY
```

**Arguments:**
- `QUERY`: Search query (SHA, partial SHA, or commit message pattern)

**Options:**
- `--repo`, `-r`: Path to git repository (defaults to current directory)
- `--verbose`, `-v`: Enable verbose output

**Description:**
Search for commits using various patterns. Currently a placeholder implementation.

**Examples:**
```bash
# Search in current directory
ca-bhfuil search abc123

# Search in specific repository
ca-bhfuil search --repo /path/to/repo "fix bug"

# Verbose search
ca-bhfuil search --verbose abc123
```

### completion

Install shell completion for ca-bhfuil.

```bash
ca-bhfuil completion [SHELL]
```

**Arguments:**
- `SHELL`: Shell type (default: bash). Supported: bash, zsh, fish

**Description:**
Installs shell completion scripts that provide intelligent tab completion for ca-bhfuil commands, options, and file paths.

**Examples:**
```bash
# Install bash completion (default)
ca-bhfuil completion
ca-bhfuil completion bash

# Install for other shells (when supported)
ca-bhfuil completion zsh
ca-bhfuil completion fish
```

### status

Show repository analysis status.

```bash
ca-bhfuil status [OPTIONS]
```

**Options:**
- `--repo`, `-r`: Path to git repository (defaults to current directory)
- `--verbose`, `-v`: Enable verbose output

**Description:**
Displays system status including:
- XDG directory structure
- Configuration loading status
- Repository statistics

**Examples:**
```bash
# Show system status
ca-bhfuil status

# Show status for specific repository
ca-bhfuil status --repo /path/to/repo

# Verbose status output
ca-bhfuil status --verbose
```

### repo

Repository management commands for ca-bhfuil.

```bash
ca-bhfuil repo [OPTIONS] COMMAND [ARGS]...
```

#### repo add

Add a new repository to the configuration.

```bash
ca-bhfuil repo add [OPTIONS] URL
```

**Arguments:**
- `URL`: Repository URL to add

**Options:**
- `--name`, `-n`: Repository name (defaults to inferred from URL)
- `--force`, `-f`: Force clone even if repository exists

**Description:**
Adds a new repository to the configuration and clones it locally. The operation shows progress information during cloning and configuration updates.

**Examples:**
```bash
# Add repository with auto-generated name
ca-bhfuil repo add https://github.com/user/repo

# Add repository with custom name
ca-bhfuil repo add https://github.com/user/repo --name my-project

# Force re-clone existing repository
ca-bhfuil repo add https://github.com/user/repo --force
```

#### repo list

List configured repositories.

```bash
ca-bhfuil repo list [OPTIONS]
```

**Options:**
- `--format`, `-f`: Output format: `table` (default), `json`, or `yaml`
- `--verbose`, `-v`: Show additional repository details

**Description:**
Displays all configured repositories with their status and metadata. Supports multiple output formats and verbose mode for detailed information.

**Examples:**
```bash
# List all repositories (default table format)
ca-bhfuil repo list

# List repositories in JSON format
ca-bhfuil repo list --format json

# List repositories in YAML format
ca-bhfuil repo list --format yaml

# List repositories with verbose details
ca-bhfuil repo list --verbose

# Combine format and verbose options
ca-bhfuil repo list --format json --verbose
```

#### repo update

Update/sync a configured repository with its remote.

```bash
ca-bhfuil repo update [OPTIONS] NAME
```

**Arguments:**
- `NAME`: Repository name to update

**Options:**
- `--force`, `-f`: Force update even if no changes detected
- `--verbose`, `-v`: Show detailed update progress

**Description:**
Updates a single repository by synchronizing it with its remote. Shows progress during the update operation and provides detailed feedback on the changes made.

**Examples:**
```bash
# Update a specific repository
ca-bhfuil repo update my-repo

# Force update even if no changes detected
ca-bhfuil repo update my-repo --force

# Update with verbose progress information
ca-bhfuil repo update my-repo --verbose

# Combine force and verbose options
ca-bhfuil repo update my-repo --force --verbose
```

#### repo remove

Remove a repository from configuration (optionally delete files).

```bash
ca-bhfuil repo remove [OPTIONS] NAME
```

**Arguments:**
- `NAME`: Repository name to remove

**Options:**
- `--force`, `-f`: Skip confirmation prompt
- `--keep-files`: Keep repository files, only remove from config

**Description:**
Removes a repository from the configuration. By default, prompts for confirmation and asks whether to delete the repository files. Can be configured to skip prompts or preserve files.

**Examples:**
```bash
# Remove repository with interactive confirmation
ca-bhfuil repo remove my-repo

# Remove repository without confirmation
ca-bhfuil repo remove my-repo --force

# Remove from config but keep files
ca-bhfuil repo remove my-repo --keep-files

# Remove without confirmation and keep files
ca-bhfuil repo remove my-repo --force --keep-files
```

#### repo sync

Sync all configured repositories or a specific one.

```bash
ca-bhfuil repo sync [OPTIONS] [NAME]
```

**Arguments:**
- `NAME`: Repository name to sync (syncs all if not specified)

**Options:**
- `--force`, `-f`: Force sync even if no changes detected
- `--verbose`, `-v`: Show detailed sync progress

**Description:**
Synchronizes repositories with their remotes. Can sync all repositories at once or target a specific repository. Shows progress information and provides detailed feedback on the sync results.

**Examples:**
```bash
# Sync all repositories
ca-bhfuil repo sync

# Sync a specific repository
ca-bhfuil repo sync my-repo

# Force sync all repositories
ca-bhfuil repo sync --force

# Sync with verbose progress information
ca-bhfuil repo sync --verbose

# Sync specific repository with force and verbose
ca-bhfuil repo sync my-repo --force --verbose
```

## Configuration Files

### repos.yaml

Repository configuration file containing repository definitions and settings.

**Location:** `~/.config/ca-bhfuil/repos.yaml`

**Schema:**
```yaml
version: "1.0"
repos:
  - name: "repository-name"
    source:
      url: "git@github.com:owner/repo.git"
      type: "github"
    auth_key: "github-default"
    branches:
      patterns: ["main", "stable/*"]
      exclude_patterns: ["stable/old-*"]
      max_branches: 50
    sync:
      strategy: "fetch_all"
      interval: "6h"
      prune_deleted: true
    storage:
      type: "bare"
      max_size: "5GB"
      retention_days: 365

settings:
  max_total_size: "50GB"
  default_sync_interval: "6h"
  clone_timeout: "30m"
  parallel_clones: 3
```

### global.yaml

Global system configuration and settings.

**Location:** `~/.config/ca-bhfuil/global.yaml`

**Schema:**
```yaml
version: "1.0"
storage:
  max_total_size: "100GB"
  max_cache_size: "80GB"
  max_state_size: "20GB"
  cleanup_policy: "lru"
  cleanup_threshold: 0.9

sync:
  max_parallel_jobs: 3
  default_timeout: "30m"
  retry_attempts: 3
  retry_backoff: "exponential"

performance:
  git_clone_bare: true
  pygit2_cache_size: "100MB"
```

### auth.yaml

Authentication configuration (secure file with 600 permissions).

**Location:** `~/.config/ca-bhfuil/auth.yaml`

**Schema:**
```yaml
version: "1.0"
defaults:
  github:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"
  gitlab:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"

auth_methods:
  github-default:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"
  github-token:
    type: "token"
    token_env: "GITHUB_TOKEN"
    username_env: "GITHUB_USERNAME"
```

## Directory Structure

Ca-bhfuil follows the XDG Base Directory Specification:

```
~/.config/ca-bhfuil/          # Configuration (XDG_CONFIG_HOME)
├── repos.yaml               # Repository definitions
├── global.yaml              # Global settings  
└── auth.yaml                 # Authentication (git-ignored)

~/.local/state/ca-bhfuil/     # Persistent state (XDG_STATE_HOME)
└── {host}/{org}/{repo}/      # Per-repository metadata
    ├── analysis.db           # Commit analysis
    ├── sync-log.db          # Sync history
    └── .locks/              # Operation locks

~/.cache/ca-bhfuil/          # Cache data (XDG_CACHE_HOME)
└── repos/{host}/{org}/{repo}/ # Git repositories
```

## Environment Variables

- `XDG_CONFIG_HOME`: Override config directory (default: `~/.config`)
- `XDG_STATE_HOME`: Override state directory (default: `~/.local/state`)
- `XDG_CACHE_HOME`: Override cache directory (default: `~/.cache`)
- `CA_BHFUIL_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR)

## Exit Codes

- `0`: Success
- `1`: General error (validation failure, missing files, etc.)

## Examples and Workflows

### Initial Setup

```bash
# Initialize configuration
ca-bhfuil config init

# Check status
ca-bhfuil config status

# Validate configuration
ca-bhfuil config validate

# View configuration
ca-bhfuil config show --all
```

### Configuration Management

```bash
# View current repositories
ca-bhfuil config show --repos

# View global settings
ca-bhfuil config show --global

# View authentication settings
ca-bhfuil config show --auth

# Export configuration as JSON
ca-bhfuil config show --all --format json > config-backup.json

# Compare configurations
ca-bhfuil config show --repos --auth
```

### Development Workflow

```bash
# Check system status
ca-bhfuil status

# Validate configuration after changes
ca-bhfuil config validate

# Reinitialize if needed
ca-bhfuil config init --force

# Search for commits (placeholder)
ca-bhfuil search abc123 --verbose
```

### Repository Management

```bash
# Add a new repository
ca-bhfuil repo add https://github.com/user/project

# Add repository with custom name
ca-bhfuil repo add https://github.com/user/project --name my-project

# List configured repositories
ca-bhfuil repo list

# List repositories in JSON format
ca-bhfuil repo list --format json

# Update a specific repository
ca-bhfuil repo update my-project

# Update with verbose progress
ca-bhfuil repo update my-project --verbose

# Sync all repositories
ca-bhfuil repo sync

# Sync a specific repository
ca-bhfuil repo sync my-project

# Remove a repository (with confirmation)
ca-bhfuil repo remove my-project

# Remove repository without confirmation
ca-bhfuil repo remove my-project --force

# Remove from config but keep files
ca-bhfuil repo remove my-project --keep-files

# Check repository status
ca-bhfuil status --repo /path/to/repo
```

## Troubleshooting

### Common Issues

**Configuration not found:**
```bash
# Initialize default configuration
ca-bhfuil config init
```

**Validation errors:**
```bash
# Check specific validation issues
ca-bhfuil config validate

# View current configuration
ca-bhfuil config show --all
```

**Permission issues:**
```bash
# Check file permissions
ls -la ~/.config/ca-bhfuil/

# Reinitialize with proper permissions
ca-bhfuil config init --force
```

**XDG directory issues:**
```bash
# Check directory status
ca-bhfuil config status

# Use custom directories
export XDG_CONFIG_HOME=/custom/config/path
ca-bhfuil config init
```

## Bash Completion

Bash completion is available for all commands and options, providing smart completion for options, file paths, and format values.

### Installation

Install bash completion using the built-in command:

```bash
# Install bash completion
ca-bhfuil completion bash

# The completion script will be installed to ~/.bash_completion.d/ca-bhfuil
# Source your .bashrc or start a new shell to enable completion
```

### Manual Installation

Alternatively, you can manually source the completion script:

```bash
# Generate completion script
python -m ca_bhfuil.cli.completion

# Source the generated script
source scripts/ca-bhfuil-completion.bash
```

### Features

The bash completion provides:
- Command and subcommand completion (`config`, `repo`, `search`, `status`)
- Config subcommand completion (`init`, `validate`, `status`, `show`)
- Repo subcommand completion (`add`, `list`, `update`, `remove`, `sync`)
- Option flag completion (`--repos`, `--global`, `--auth`, `--format`, `--verbose`, etc.)
- Format completion for `--format` option (`table`, `json`, `yaml`)
- Repository name completion for repo commands (`update`, `remove`, `sync`)
- Directory path completion for `--repo` option
- Smart completion that respects mutually exclusive options
