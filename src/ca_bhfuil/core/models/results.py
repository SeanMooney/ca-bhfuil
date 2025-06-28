"""Models for handling the results of asynchronous operations."""

import typing

import pydantic


class OperationResult(pydantic.BaseModel):
    """Base model for operation results."""

    success: bool
    duration: float
    error: str | None = None
    result: typing.Any = None


class CloneResult(OperationResult):
    """Result of a repository clone operation."""

    repository_path: str | None = None


class AnalysisResult(OperationResult):
    """Result of a repository analysis operation."""

    analysis_data: dict[str, typing.Any] | None = None


class SearchResult(OperationResult):
    """Result of a search operation."""

    matches: list[typing.Any] = []
