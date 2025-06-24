# Cá Bhfuil

> *Irish for "where is" - Git repository analysis tool for open source maintainers*

**Cá Bhfuil** *(pronounced "caw will")* helps open source maintainers track patches, fixes, and features across their stable branches.

[![Continuous Integration](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/ci.yml/badge.svg)](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/ci.yml)
[![Build and Release](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/build-and-release.yml)
[![Dependency Management](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/deps.yml/badge.svg)](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/deps.yml)
[![Release](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/release.yml/badge.svg)](https://github.com/SeanMooney/ca-bhfuil/actions/workflows/release.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/SeanMooney/ca-bhfuil/master.svg)](https://results.pre-commit.ci/latest/github/SeanMooney/ca-bhfuil/master)


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

## Project Status

**Current Phase**: Initial development and repository setup  
**License**: MIT  
**Development Model**: Single developer + AI assistance

## Key Features (Planned)

- **🚀 Performance First**: 10x+ faster than GitPython using pygit2
- **🔒 Local-First**: SQLite storage, no external databases
- **🧠 AI-Enhanced**: Local LLM integration with privacy controls
- **🎯 Maintainer-Focused**: Built for real stable branch workflows

## Documentation

- 📖 **[Project Vision](docs/design/project-vision.md)** - Complete technical vision and roadmap
- 🛠️ **[Technology Stack](docs/design/technology-stack.md)** - Technology decisions and rationale  
- 🏗️ **[Repository Structure](docs/design/repository-structure.md)** - Development organization

## AI-Assisted Development

This project uses **Human + AI collaborative development**:

- **🤖 For AI Assistants**: See [CLAUDE.md](CLAUDE.md) for development setup
- **📁 AI Memory System**: Persistent context in `ai/memory/` directory
- **🔄 Session Continuity**: File-based memory survives development sessions

## Quick Setup for Development

```bash
# Clone repository
git clone https://github.com/SeanMooney/ca-bhfuil.git
cd ca-bhfuil

# For AI development (Claude Code, etc.)
# Read CLAUDE.md and ai/memory/ files for context
```

## Philosophy

*"Because tracking changes across stable branches shouldn't require a computer science degree."*

**A pragmatic tool built by a maintainer, for maintainers who just want to know where their fixes landed.**

---

**License**: MIT  
**Pronunciation**: "caw will" (Irish: where is)  
**Status**: Repository structure and planning complete, ready for development bootstrap
