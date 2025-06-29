"""Repository wrapper class for pygit2 operations."""

import datetime
import pathlib
import typing

from loguru import logger
import pygit2

from ca_bhfuil.core.models import commit as commit_models


class Repository:
    """Wrapper around pygit2.Repository with enhanced operations."""

    def __init__(self, repo_path: pathlib.Path | str):
        """Initialize repository wrapper.

        Args:
            repo_path: Path to the git repository.

        Raises:
            pygit2.GitError: If the path is not a valid git repository.
        """
        self.path = pathlib.Path(repo_path)
        self._repo = pygit2.Repository(str(self.path))

    @property
    def is_bare(self) -> bool:
        """Check if repository is bare."""
        return self._repo.is_bare

    @property
    def head_is_unborn(self) -> bool:
        """Check if HEAD is unborn (empty repository)."""
        return self._repo.head_is_unborn

    @property
    def head_branch(self) -> str | None:
        """Get the current HEAD branch name."""
        if self.head_is_unborn:
            return None
        return self._repo.head.shorthand

    @property
    def head_sha(self) -> str | None:
        """Get the current HEAD commit SHA."""
        if self.head_is_unborn:
            return None
        return str(self._repo.head.target)

    def get_commit(self, sha: str) -> commit_models.CommitInfo | None:
        """Get a commit by SHA (full or partial).

        Args:
            sha: Full or partial commit SHA.

        Returns:
            CommitInfo if found, None otherwise.
        """
        try:
            # Try exact match first
            if len(sha) == 40:  # Full SHA
                commit = self._repo[sha]  # type: ignore[index]
            else:
                # Try to resolve partial SHA
                commit = self._repo.revparse_single(sha)

            if not isinstance(commit, pygit2.Commit):
                return None

            return self._commit_to_model(commit)

        except (KeyError, pygit2.GitError) as e:
            logger.debug(f"Commit lookup failed for {sha}: {e}")
            return None

    def get_commits_by_pattern(
        self, pattern: str, max_results: int = 100
    ) -> list[commit_models.CommitInfo]:
        """Find commits by message pattern.

        Args:
            pattern: Pattern to search for in commit messages.
            max_results: Maximum number of results to return.

        Returns:
            List of matching commits.
        """
        matches = []
        pattern_lower = pattern.lower()

        try:
            # Walk through all commits on all branches
            for commit in self._repo.walk(self._repo.head.target):
                if pattern_lower in commit.message.lower():
                    matches.append(self._commit_to_model(commit))
                    if len(matches) >= max_results:
                        break

        except Exception as e:
            logger.error(f"Pattern search failed for '{pattern}': {e}")

        return matches

    def list_branches(self, include_remote: bool = True) -> dict[str, list[str]]:
        """List all branches in the repository.

        Args:
            include_remote: Whether to include remote branches.

        Returns:
            Dictionary with 'local' and 'remote' branch lists.
        """
        result: dict[str, list[str]] = {"local": [], "remote": []}

        try:
            # Get local branches
            for branch in self._repo.branches.local:  # type: ignore[attr-defined]
                result["local"].append(branch)

            # Get remote branches if requested
            if include_remote:
                for branch in self._repo.branches.remote:  # type: ignore[attr-defined]
                    result["remote"].append(branch)

        except Exception as e:
            logger.error(f"Branch listing failed: {e}")

        return result

    def list_remotes(self) -> list[str]:
        """List all remotes in the repository.

        Returns:
            List of remote names.
        """
        try:
            return [remote.name for remote in self._repo.remotes]  # type: ignore[attr-defined]
        except Exception as e:
            logger.error(f"Remote listing failed: {e}")
            return []

    def list_tags(self, limit: int | None = None) -> list[str]:
        """List all tags in the repository.

        Args:
            limit: Maximum number of tags to return.

        Returns:
            List of tag names.
        """
        try:
            tags = []
            for ref_name in self._repo.references:  # type: ignore[attr-defined]
                if ref_name.startswith("refs/tags/"):
                    tag_name = ref_name.replace("refs/tags/", "")
                    tags.append(tag_name)
                    if limit and len(tags) >= limit:
                        break
            return sorted(tags)
        except Exception as e:
            logger.error(f"Tag listing failed: {e}")
            return []

    def get_branch_commits(
        self, branch_name: str, max_commits: int = 100
    ) -> list[commit_models.CommitInfo]:
        """Get recent commits from a specific branch.

        Args:
            branch_name: Name of the branch.
            max_commits: Maximum number of commits to return.

        Returns:
            List of commit information.
        """
        try:
            # Try to get the branch
            branch = None
            if branch_name in self._repo.branches.local:  # type: ignore[attr-defined]
                branch = self._repo.branches.local[branch_name]  # type: ignore[attr-defined]
            elif branch_name in self._repo.branches.remote:  # type: ignore[attr-defined]
                branch = self._repo.branches.remote[branch_name]  # type: ignore[attr-defined]

            if not branch:
                logger.warning(f"Branch not found: {branch_name}")
                return []

            # Walk commits on this branch
            commits = []
            for commit in self._repo.walk(branch.target):
                commits.append(self._commit_to_model(commit))
                if len(commits) >= max_commits:
                    break

            return commits

        except Exception as e:
            logger.error(f"Branch commit listing failed for {branch_name}: {e}")
            return []

    def find_commit_in_branches(self, commit_sha: str) -> list[str]:
        """Find which branches contain a specific commit.

        Args:
            commit_sha: SHA of the commit to search for.

        Returns:
            List of branch names containing the commit.
        """
        try:
            commit_oid = pygit2.Oid(hex=commit_sha)
            containing_branches = []

            # Check all branches
            all_branches = list(self._repo.branches.local) + list(  # type: ignore[attr-defined]
                self._repo.branches.remote  # type: ignore[attr-defined]
            )

            for branch_name in all_branches:
                try:
                    branch = self._repo.branches.local.get(  # type: ignore[attr-defined]
                        branch_name
                    ) or self._repo.branches.remote.get(branch_name)  # type: ignore[attr-defined]
                    if branch:
                        # Check if commit is reachable from branch
                        merge_base = self._repo.merge_base(commit_oid, branch.target)
                        if merge_base == commit_oid:
                            containing_branches.append(branch_name)
                except pygit2.GitError:
                    # Branch might not exist or other error
                    continue

            return containing_branches

        except Exception as e:
            logger.error(f"Commit branch search failed for {commit_sha}: {e}")
            return []

    def get_repository_stats(self) -> dict[str, typing.Any]:
        """Get basic repository statistics.

        Returns:
            Dictionary with repository statistics.
        """
        try:
            local_branches = list(self._repo.branches.local)  # type: ignore[attr-defined]
            remote_branches = list(self._repo.branches.remote)  # type: ignore[attr-defined]
            remotes = [remote.name for remote in self._repo.remotes]  # type: ignore[attr-defined]

            # Count commits (approximate)
            commit_count = 0
            if not self.head_is_unborn:
                try:
                    for _ in self._repo.walk(self._repo.head.target):
                        commit_count += 1
                        # Limit counting to prevent performance issues
                        if commit_count >= 10000:
                            commit_count = 10000  # Mark as 10000+
                            break
                except Exception:
                    commit_count = 0

            return {
                "path": str(self.path),
                "head_branch": self.head_branch,
                "head_sha": self.head_sha,
                "local_branches": len(local_branches),
                "remote_branches": len(remote_branches),
                "total_branches": len(local_branches) + len(remote_branches),
                "remotes": remotes,
                "remote_count": len(remotes),
                "is_bare": self.is_bare,
                "is_empty": self.head_is_unborn,
                "commit_count": commit_count,
                "workdir": str(self._repo.workdir) if self._repo.workdir else None,
            }

        except Exception as e:
            logger.error(f"Repository stats calculation failed: {e}")
            return {"error": str(e)}

    def _commit_to_model(self, commit: pygit2.Commit) -> commit_models.CommitInfo:
        """Convert pygit2.Commit to CommitInfo model.

        Args:
            commit: pygit2 commit object.

        Returns:
            CommitInfo model.
        """
        return commit_models.CommitInfo(
            sha=str(commit.id),
            short_sha=str(commit.id)[:7],
            message=commit.message,
            author_name=commit.author.name,
            author_email=commit.author.email,
            author_date=datetime.datetime.fromtimestamp(
                commit.author.time,
                tz=datetime.timezone(datetime.timedelta(minutes=commit.author.offset)),
            ),
            committer_name=commit.committer.name,
            committer_email=commit.committer.email,
            committer_date=datetime.datetime.fromtimestamp(
                commit.committer.time,
                tz=datetime.timezone(
                    datetime.timedelta(minutes=commit.committer.offset)
                ),
            ),
            parents=[str(parent.id) for parent in commit.parents],
            files_changed=None,  # Could be calculated if needed
            insertions=None,  # Could be calculated if needed
            deletions=None,  # Could be calculated if needed
        )

    @classmethod
    def discover(cls, path: pathlib.Path | str) -> "Repository | None":
        """Discover a git repository starting from a path.

        Args:
            path: Path to start searching from.

        Returns:
            Repository instance if found, None otherwise.
        """
        current_path = pathlib.Path(path).resolve()

        while current_path != current_path.parent:
            git_dir = current_path / ".git"
            if git_dir.exists():
                try:
                    return cls(current_path)
                except pygit2.GitError:
                    return None
            current_path = current_path.parent

        return None

    @classmethod
    def is_repository(cls, path: pathlib.Path | str) -> bool:
        """Check if a path contains a valid git repository.

        Args:
            path: Path to check.

        Returns:
            True if valid repository, False otherwise.
        """
        try:
            pygit2.Repository(str(path))
            return True
        except (pygit2.GitError, KeyError):
            return False
