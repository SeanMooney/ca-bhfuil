# Ca-Bhfuil CLI Design Patterns

> **Command-line interface design principles and conventions**

## Design Philosophy

### Core Principles

1. **Consistency First**: All commands follow the same patterns and conventions
2. **Composability**: Options can be combined in intuitive ways
3. **Progressive Disclosure**: Basic usage is simple, advanced features are available when needed
4. **Rich Terminal Experience**: Beautiful output with smart formatting and colors
5. **UNIX Philosophy**: Do one thing well, compose with other tools

### User Experience Goals

- **Intuitive**: Common operations should be obvious and memorable
- **Forgiving**: Clear error messages with helpful suggestions
- **Efficient**: Fast for both new users and power users
- **Informative**: Rich feedback without being overwhelming

## Command Structure

### Pattern: `ca-bhfuil <resource> <operation> [options] [arguments]`

This follows the modern CLI pattern established by tools like `git`, `docker`, and `kubectl`.

**Examples:**
```bash
ca-bhfuil config init              # Initialize configuration
ca-bhfuil repo add <url>           # Add repository
ca-bhfuil search <query>           # Search commits
ca-bhfuil status                   # Show system status
```

### Resource-Based Organization

Commands are organized around resources that users work with:

- **`config`**: Configuration management (files, settings, validation)
- **`repo`**: Repository management (add, remove, sync, list)
- **`search`**: Commit and code search operations
- **`status`**: System and repository status information
- **`completion`**: Shell completion installation

### Operation Types

Each resource supports relevant operations:

- **Lifecycle**: `init`, `add`, `remove`, `update`
- **Information**: `show`, `list`, `status`, `validate`
- **Management**: `sync`, `clean`, `export`, `import`

## Option Design Patterns

### Flag-Based Operations

Prefer composable flags over separate subcommands for related operations:

**✅ Good:**
```bash
ca-bhfuil config show --repos --global    # Show multiple configs
ca-bhfuil config show --all               # Show all configs
ca-bhfuil repo list --active --remote     # List with filters
```

**❌ Avoid:**
```bash
ca-bhfuil config show-repos-and-global    # Non-composable
ca-bhfuil config repos                    # Separate commands for related data
```

### Format Options

Support multiple output formats where appropriate:

```bash
ca-bhfuil config show --format json       # Machine-readable
ca-bhfuil config show --format yaml       # Human-readable (default)
ca-bhfuil repo list --format table        # Structured display
```

### Common Option Conventions

Consistent naming for frequently used options:

```bash
--repo, -r          # Repository path
--config, -c        # Configuration file
--format, -f        # Output format
--verbose, -v       # Verbose output
--quiet, -q         # Minimal output
--force             # Override safety checks
--all               # Include all items
```

## Output Design

### Rich Terminal Formatting

Use Rich library for beautiful, informative output:

1. **Tables**: For structured data (repository lists, status information)
2. **Panels**: For grouped information (configuration display)
3. **Progress**: For long-running operations (sync, clone)
4. **Syntax Highlighting**: For configuration files and code
5. **Colors**: For status indicators and emphasis

### Output Levels

Support different verbosity levels:

- **Quiet (`-q`)**: Minimal output, errors only
- **Normal**: Standard informative output
- **Verbose (`-v`)**: Detailed operation information
- **Debug**: Development and troubleshooting information

### Status Indicators

Consistent visual indicators across all commands:

- ✅ Success/exists/active
- ❌ Error/missing/failed
- ⚠️  Warning/attention needed
- 🔄 In progress/syncing
- 📁 Directory/path
- 📄 File
- 🔗 URL/remote
- 🔑 Authentication/security

## Error Handling

### Error Message Structure

```
[CONTEXT] Error message with specific problem
Suggestion: What the user can do to fix it
Example: command --option value
```

**Example:**
```
❌ Configuration file not found: ~/.config/ca-bhfuil/repos.yaml
Suggestion: Initialize configuration first
Example: ca-bhfuil config init
```

### Exit Codes

Follow standard UNIX conventions:

- `0`: Success
- `1`: General error (validation failure, missing files, etc.)
- `2`: Misuse of shell command (invalid arguments)
- `126`: Command invoked cannot execute
- `127`: Command not found
- `128+n`: Fatal error signal "n"

### Error Recovery

Provide actionable suggestions:

- Missing configuration → suggest `config init`
- Invalid repository → suggest `repo add` or `repo list`
- Permission issues → explain file permissions needed
- Network errors → suggest retry or check connectivity

## Autocompletion Design

### Smart Context-Aware Completion

- **Commands**: Complete available subcommands and operations
- **Options**: Complete valid flags for current command
- **Values**: Complete valid values for option (e.g., formats: yaml, json)
- **Paths**: Complete file system paths for --repo, --config options
- **Repository Names**: Complete configured repository names

### Mutually Exclusive Options

Respect option relationships in completion:

```bash
ca-bhfuil config show --all <TAB>    # Only show --format, not other flags
ca-bhfuil config show --repos <TAB>  # Allow additional flags like --global
```

## Validation and Safety

### Input Validation

- **URLs**: Validate repository URLs before operations
- **Paths**: Check file system permissions and existence
- **Configuration**: Validate YAML syntax and schema
- **Dependencies**: Check for required tools (git, ssh)

### Safety Mechanisms

- **Destructive Operations**: Require confirmation or --force flag
- **Overwrite Protection**: Warn when overwriting existing data
- **Backup Creation**: Create backups before destructive changes
- **Dry Run Support**: Preview operations before execution

## Command Implementation Guidelines

### Code Organization

```
cli/
├── main.py           # Main app and top-level commands
├── commands/         # Command implementations
│   ├── config.py     # Config management commands
│   ├── repo.py       # Repository management commands
│   └── search.py     # Search commands
├── completion.py     # Shell completion support
├── formatters.py     # Output formatting utilities
└── validators.py     # Input validation utilities
```

### Command Template

```python
@app.command()
def command_name(
    required_arg: str = typer.Argument(..., help="Description"),
    optional_flag: bool = typer.Option(False, "--flag", help="Description"),
    common_option: str = typer.Option("default", "--option", "-o", help="Description"),
) -> None:
    """Brief command description.

    Longer description with examples and context.
    """
    try:
        # Implementation with proper error handling
        pass
    except SpecificError as e:
        rprint(f"[red]❌ Specific error: {e}[/red]")
        rprint("[yellow]Suggestion: How to fix this[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)
```

## User Workflow Patterns

### Discovery Workflow

```bash
# User discovers available commands
ca-bhfuil --help

# User explores specific resource
ca-bhfuil config --help

# User learns about specific operation
ca-bhfuil config init --help
```

### Progressive Complexity

```bash
# Basic usage - simple and obvious
ca-bhfuil search "CVE-2024-1234"

# Intermediate usage - add common options
ca-bhfuil search "CVE-2024-1234" --repo /path/to/repo

# Advanced usage - multiple options and filters
ca-bhfuil search "CVE-2024-1234" --repo /path/to/repo --format json --ai
```

### Integration Patterns

```bash
# Piping and composition with other tools
ca-bhfuil repo list --format json | jq '.[] | select(.status == "active")'

# Command chaining for workflows
ca-bhfuil repo sync --all && ca-bhfuil search "security fix"

# Shell integration
eval "$(ca-bhfuil completion bash)"
```

## Testing Patterns

### CLI Testing Strategy

- **Unit Tests**: Test command logic and validation
- **Integration Tests**: Test full command execution
- **Completion Tests**: Verify autocompletion behavior
- **Error Tests**: Ensure proper error handling and messages

### Example Test Structure

```python
def test_config_init_success():
    """Test successful config initialization"""
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert "✅ Configuration initialized" in result.stdout

def test_config_init_existing_no_force():
    """Test config init with existing files without force"""
    # Setup existing config
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 1
    assert "already exists" in result.stderr
    assert "Use --force" in result.stderr
```

## Documentation Requirements

Every command must have:

- **Help Text**: Clear, concise description
- **Usage Examples**: Common use cases with examples
- **Option Documentation**: All flags and arguments explained
- **Error Scenarios**: Common errors and solutions

## Cross-References

- **System architecture**: See [architecture-overview.md](architecture-overview.md)
- **Technology choices**: See [technology-decisions.md](technology-decisions.md)
- **Development process**: See [development-workflow.md](development-workflow.md)
- **Storage implementation**: See [data-storage-design.md](data-storage-design.md)

---

These CLI design patterns ensure a consistent, powerful, and user-friendly interface that grows naturally as ca-bhfuil evolves.
