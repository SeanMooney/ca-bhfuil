# Cá Bhfuil

> *Irish for "where is" - Git repository analysis tool for open source maintainers*

**Cá Bhfuil** *(pronounced "caw will")* helps open source maintainers track patches, fixes, and features across their stable branches.

[![CI](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/ci.yml/badge.svg)](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/ci.yml)
[![pre-commit.ci](https://results.pre-commit.ci/badge/github/SeanMooney/ca-bhfuil/master.svg)](https://results.pre-commit.ci/latest/github/SeanMooney/ca-bhfuil/master)

## The Problem

- "Did CVE-2024-1234 get backported to all supported stable branches?"
- "Where is the fix for this memory leak across our release branches?"  
- "What fixes are in main but missing from stable/v2.1?"

## The Solution

```bash
ca-bhfuil "CVE-2024-1234"           # Find security fixes across branches
ca-bhfuil abc123def --distribution  # See where this commit landed
ca-bhfuil --missing-from stable/v2.1 # What needs backporting
```

## Key Features

- **🚀 Performance First**: 10x+ faster than GitPython using pygit2
- **🔒 Local-First**: SQLite storage, no external databases
- **🧠 AI-Enhanced**: Local LLM integration with privacy controls
- **🎯 Maintainer-Focused**: Built for real stable branch workflows

## Quick Start

```bash
# Install from PyPI (when available)
pip install ca-bhfuil

# Or run with container
docker run --rm -v $(pwd):/workspace ghcr.io/seanmooney/ca-bhfuil:latest --help
```

## Documentation

### For Users
- **[Container Usage Guide](docs/user/CONTAINER_USAGE.md)** - Complete container usage and security
- **[CLI Reference](docs/user/cli-reference.md)** - Command-line interface documentation

### For Contributors  
- **[Development Setup](docs/contributor/DEVELOPMENT.md)** - Local development environment
- **[Code Style Guide](docs/contributor/code-style.md)** - Coding standards and practices
- **[Design Documents](docs/contributor/design/)** - Technical architecture and decisions

### For AI Assistants
- **[CLAUDE.md](CLAUDE.md)** - AI development setup and project context
- **[AI Memory System](ai/memory/)** - Persistent context across development sessions

## Project Status

**Current Phase**: Core development (CLI, configuration, git operations)  
**License**: MIT  
**Development Model**: Human + AI collaborative development

---

*"Because tracking changes across stable branches shouldn't require a computer science degree."*

**Built by a maintainer, for maintainers who just want to know where their fixes landed.**
