# GEMINI.md - AI Development Companion Guide

> **For Gemini and other AI development assistants working on Ca-Bhfuil**
>
> **Version**: 2.0 | **Last Updated**: 2025-06-27

## 🚨 Important Notice for All AI Assistants

This file provides initial instructions for Gemini. However, to ensure consistency across all AI agents working on this project, the primary source of truth for development workflow, coding standards, and project context is the `CLAUDE.md` file and the shared `ai/memory/` directory.

**You MUST treat `CLAUDE.md` as your primary operational guide.**

## Your Core Responsibilities

1.  **Read the Authoritative Guides**: At the beginning of every session, you MUST read and familiarize yourself with the latest versions of:
    *   `CLAUDE.md`: The master guide for all AI assistants.
    *   All files within the `ai/memory/` directory, especially `ai-style-guide.md`.

2.  **Follow All Instructions**: Adhere strictly to the development workflows, coding standards, quality gates, and session protocols detailed in `CLAUDE.md`.

3.  **Maintain Shared Memory**: When you make progress, decisions, or discover new patterns, you MUST update the relevant files in `ai/memory/` as specified in the `CLAUDE.md` handoff protocol.

## ⭐️ Critical Coding Standards

**All code MUST adhere to `ai/memory/ai-style-guide.md`.** The following rules are non-negotiable:

1.  **Module-Only Imports**:
    *   **NEVER** import classes or functions directly.
    *   **ALWAYS** import the module or submodule.
    *   **CORRECT**: `from rich import console` then `my_console = console.Console()`
    *   **WRONG**: `from rich.console import Console`

2.  **Modern Type Hints**:
    *   **ALWAYS** use modern type hints (`list[str]`, `dict[str, int]`).
    *   **NEVER** use legacy `typing` imports (`List`, `Dict`, `Optional`). Use `| None` for optional types.

3.  **Resource Management**:
    *   **ALWAYS** use `with` statements for resources (files, locks, etc.).
    *   **ALWAYS** specify `encoding="utf-8"` when opening files.

4.  **Quality Gates**:
    *   Before every commit, you **MUST** run and pass all quality checks:
        *   `uv run ruff format .`
        *   `uv run ruff check .`
        *   `uv run mypy .`
        *   `uv run pytest`

## Development Workflow

*   **Follow the Handoff Protocol**: When ending a session, update `ai/memory/current-focus.md` using the template in `CLAUDE.md`.
*   **Document Decisions**: Record all significant architectural decisions in `ai/memory/architecture-decisions.md`.
*   **Update Documentation**: Keep user and contributor docs in `docs/` synchronized with any changes you make.

## Quick Reference

*   **How do I work on this project?** -> Read `CLAUDE.md`
*   **What should I work on now?** -> Read `ai/memory/current-focus.md`
*   **How should I write the code?** -> Read `ai/memory/ai-style-guide.md`
*   **What is the project about?** -> Read `ai/memory/project-context.md`

By following these instructions, you will contribute to the project effectively and consistently alongside other AI assistants.
