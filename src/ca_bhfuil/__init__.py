"""Ca-Bhfuil: Git repository analysis tool for open source maintainers."""

__version__ = "0.1.0"
__author__ = "Ca-Bhfuil Project"
__description__ = "Git repository analysis tool for tracking commits across stable branches"

from ca_bhfuil.core.models import CommitInfo

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "CommitInfo",
]
