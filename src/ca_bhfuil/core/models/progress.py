"""Models for tracking asynchronous operation progress."""

from enum import Enum
import time

import pydantic


class TaskStatus(str, Enum):
    """Enum for background task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OperationProgress(pydantic.BaseModel):
    """Generic model for reporting operation progress."""

    total: int = 0
    completed: int = 0
    status: str = "Starting..."
    start_time: float = pydantic.Field(default_factory=time.time)

    @property
    def percent_complete(self) -> float:
        """Return the percentage of completion."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class CloneProgress(OperationProgress):
    """Model for tracking git clone progress."""

    receiving_objects: int = 0
    indexing_objects: int = 0
    resolving_deltas: int = 0


class AnalysisProgress(OperationProgress):
    """Model for tracking repository analysis progress."""

    commits_analyzed: int = 0
    branches_analyzed: int = 0
