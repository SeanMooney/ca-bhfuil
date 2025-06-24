"""Repository cloning functionality using pygit2."""

import collections.abc
import dataclasses
import os
import pathlib
import time
import typing

from loguru import logger
import pygit2

from .. import config


@dataclasses.dataclass
class CloneProgress:
    """Clone progress information."""

    received_objects: int = 0
    total_objects: int = 0
    received_bytes: int = 0
    local_objects: int = 0
    indexed_objects: int = 0
    total_deltas: int = 0
    indexed_deltas: int = 0

    @property
    def objects_progress(self) -> float:
        """Get objects progress as percentage."""
        if self.total_objects == 0:
            return 0.0
        return (self.received_objects / self.total_objects) * 100.0

    @property
    def deltas_progress(self) -> float:
        """Get deltas progress as percentage."""
        if self.total_deltas == 0:
            return 0.0
        return (self.indexed_deltas / self.total_deltas) * 100.0

    @property
    def overall_progress(self) -> float:
        """Get overall progress as percentage."""
        if self.total_objects == 0:
            return 0.0

        # Weight objects more heavily than deltas
        objects_weight = 0.8
        deltas_weight = 0.2

        return (
            objects_weight * self.objects_progress
            + deltas_weight * self.deltas_progress
        )


@dataclasses.dataclass
class CloneResult:
    """Result of a clone operation."""

    success: bool
    repo_path: pathlib.Path
    state_path: pathlib.Path
    duration: float
    objects_count: int = 0
    refs_count: int = 0
    error: str | None = None
    clone_progress: CloneProgress | None = None


class CloneLockManager:
    """Manages clone operation locks to prevent concurrent cloning."""

    def __init__(self, repo_path: pathlib.Path):
        """Initialize lock manager."""
        self.repo_path = repo_path
        self.lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
        self.acquired = False

    def __enter__(self) -> "CloneLockManager":
        """Acquire lock."""
        if self.lock_file.exists():
            raise RuntimeError(f"Clone already in progress for {self.repo_path}")

        # Create parent directory if needed
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Create lock file with process info
        lock_info = f"pid:{os.getpid()}\ntime:{time.time()}\n"
        self.lock_file.write_text(lock_info)
        self.acquired = True

        logger.debug(f"Acquired clone lock for {self.repo_path}")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: typing.Any,
    ) -> None:
        """Release lock."""
        if self.acquired and self.lock_file.exists():
            self.lock_file.unlink()
            logger.debug(f"Released clone lock for {self.repo_path}")


class RepositoryCloner:
    """Handles git repository cloning operations."""

    def __init__(self, config_manager: config.ConfigManager | None = None):
        """Initialize repository cloner."""
        self.config_manager = config_manager or config.ConfigManager()

    def clone_repository(
        self,
        repo_config: config.RepositoryConfig,
        progress_callback: collections.abc.Callable[[CloneProgress], None]
        | None = None,
        force: bool = False,
    ) -> CloneResult:
        """Clone a repository using configuration.

        Args:
            repo_config: Repository configuration
            progress_callback: Optional progress callback function
            force: Force clone even if repository exists

        Returns:
            CloneResult with operation details
        """
        start_time = time.time()
        repo_path = repo_config.repo_path
        state_path = repo_config.state_path
        url = repo_config.source["url"]

        logger.info(f"Starting clone of {url} to {repo_path}")

        # Check if repository already exists
        if repo_path.exists() and not force:
            if self._is_valid_repository(repo_path):
                logger.info(f"Repository already exists at {repo_path}")
                return CloneResult(
                    success=True,
                    repo_path=repo_path,
                    state_path=state_path,
                    duration=time.time() - start_time,
                )
            logger.warning(f"Invalid repository exists at {repo_path}, removing")
            import shutil

            shutil.rmtree(repo_path)

        try:
            with CloneLockManager(repo_path):
                return self._perform_clone(repo_config, progress_callback, start_time)
        except Exception as e:
            logger.error(f"Clone failed for {url}: {e}")
            return CloneResult(
                success=False,
                repo_path=repo_path,
                state_path=state_path,
                duration=time.time() - start_time,
                error=str(e),
            )

    def _perform_clone(
        self,
        repo_config: config.RepositoryConfig,
        progress_callback: collections.abc.Callable[[CloneProgress], None] | None,
        start_time: float,
    ) -> CloneResult:
        """Perform the actual clone operation."""
        repo_path = repo_config.repo_path
        state_path = repo_config.state_path
        url = repo_config.source["url"]

        # Ensure parent directories exist
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.mkdir(parents=True, exist_ok=True)

        # Set up progress tracking
        current_progress = CloneProgress()

        def _progress_callback(stats: typing.Any) -> None:
            """Internal progress callback that updates our progress object."""
            current_progress.received_objects = stats.received_objects
            current_progress.total_objects = stats.total_objects
            current_progress.received_bytes = stats.received_bytes
            current_progress.local_objects = stats.local_objects
            current_progress.indexed_objects = stats.indexed_objects
            current_progress.total_deltas = stats.total_deltas
            current_progress.indexed_deltas = stats.indexed_deltas

            if progress_callback:
                progress_callback(current_progress)

        # Set up authentication
        auth_callbacks = self._setup_authentication(repo_config)

        # Clone the repository
        logger.debug(f"Cloning {url} to {repo_path}")

        bare = repo_config.storage.type == "bare"
        checkout_branch: str | None = None  # Clone all branches

        # Set up remote callbacks
        remote_callbacks = pygit2.RemoteCallbacks()  # type: ignore[attr-defined, no-untyped-call]

        # Set progress callback (method, not constructor parameter)
        if hasattr(remote_callbacks, "progress"):
            remote_callbacks.progress = _progress_callback

        # Add authentication if available
        if auth_callbacks:
            for key, value in auth_callbacks.items():
                setattr(remote_callbacks, key, value)

        try:
            repository = pygit2.clone_repository(
                url,
                str(repo_path),
                bare=bare,
                checkout_branch=checkout_branch,
                callbacks=remote_callbacks,
            )

            # Gather statistics
            if hasattr(repository, "references"):
                refs_count = len(list(repository.references))
            else:
                refs_count = 0

            # For bare repositories, count objects directly
            if repository.is_bare:
                try:
                    # Count objects in the object database
                    objects_count = len(list(repository.odb))
                except Exception:
                    objects_count = current_progress.received_objects or 0
            else:
                objects_count = current_progress.received_objects or 0

            logger.info(
                f"Successfully cloned {url} ({objects_count} objects, {refs_count} refs)"
            )

            return CloneResult(
                success=True,
                repo_path=repo_path,
                state_path=state_path,
                duration=time.time() - start_time,
                objects_count=objects_count,
                refs_count=refs_count,
                clone_progress=current_progress,
            )

        except pygit2.GitError as e:
            error_msg = f"Git error during clone: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _setup_authentication(
        self, repo_config: config.RepositoryConfig
    ) -> dict[str, typing.Any]:
        """Set up authentication for cloning."""
        auth_callbacks: dict[str, typing.Any] = {}

        if not repo_config.auth_key:
            return auth_callbacks

        auth_method = self.config_manager.get_auth_method(repo_config.auth_key)
        if not auth_method:
            logger.warning(f"Auth method '{repo_config.auth_key}' not found")
            return auth_callbacks

        if auth_method.type == "ssh_key":
            auth_callbacks.update(self._setup_ssh_auth(auth_method))
        elif auth_method.type == "token":
            auth_callbacks.update(self._setup_token_auth(auth_method))
        else:
            logger.warning(f"Unsupported auth method type: {auth_method.type}")

        return auth_callbacks

    def _setup_ssh_auth(self, auth_method: config.AuthMethod) -> dict[str, typing.Any]:
        """Set up SSH key authentication."""
        if not auth_method.ssh_key_path:
            return {}

        ssh_key_path = pathlib.Path(auth_method.ssh_key_path).expanduser()
        if not ssh_key_path.exists():
            logger.error(f"SSH key not found: {ssh_key_path}")
            return {}

        # Get passphrase from environment if specified
        passphrase = None
        if auth_method.ssh_key_passphrase_env:
            passphrase = os.environ.get(auth_method.ssh_key_passphrase_env)

        def credentials_callback(
            url: str, username_from_url: str, allowed_types: int
        ) -> pygit2.Keypair | None:
            """SSH key credentials callback."""
            # Parameters required by callback interface but not all used
            del url, username_from_url
            if (
                hasattr(pygit2, "credentials")
                and hasattr(pygit2.credentials, "GIT_CREDENTIAL_SSH_KEY")
                and allowed_types & pygit2.credentials.GIT_CREDENTIAL_SSH_KEY
            ):
                return pygit2.Keypair(
                    "git",
                    str(ssh_key_path) + ".pub",
                    str(ssh_key_path),
                    passphrase or "",
                )
            return None

        return {"credentials": credentials_callback}

    def _setup_token_auth(
        self, auth_method: config.AuthMethod
    ) -> dict[str, typing.Any]:
        """Set up token-based authentication."""
        if not auth_method.token_env:
            return {}

        token = os.environ.get(auth_method.token_env)
        if not token:
            logger.error(f"Token not found in environment: {auth_method.token_env}")
            return {}

        username = "token"
        if auth_method.username_env:
            username = os.environ.get(auth_method.username_env, "token")

        def credentials_callback(
            url: str, username_from_url: str, allowed_types: int
        ) -> pygit2.UserPass | None:
            """Token credentials callback."""
            # Parameters required by callback interface but not all used
            del url, username_from_url
            if (
                hasattr(pygit2, "credentials")
                and hasattr(pygit2.credentials, "GIT_CREDENTIAL_USERPASS_PLAINTEXT")
                and allowed_types & pygit2.credentials.GIT_CREDENTIAL_USERPASS_PLAINTEXT
            ):
                return pygit2.UserPass(username, token)
            return None

        return {"credentials": credentials_callback}

    def _is_valid_repository(self, repo_path: pathlib.Path) -> bool:
        """Check if path contains a valid git repository."""
        try:
            pygit2.Repository(str(repo_path))
            return True
        except (pygit2.GitError, OSError):
            return False

    def validate_clone(self, repo_path: pathlib.Path) -> dict[str, typing.Any]:
        """Validate a cloned repository.

        Args:
            repo_path: pathlib.Path to repository

        Returns:
            Dictionary with validation results
        """
        checks = {
            "path_exists": repo_path.exists(),
            "is_git_repo": False,
            "is_bare": False,
            "has_refs": False,
            "has_objects": False,
            "refs_count": 0,
            "healthy": False,
        }

        if not checks["path_exists"]:
            return checks

        try:
            repository = pygit2.Repository(str(repo_path))
            checks["is_git_repo"] = True
            checks["is_bare"] = repository.is_bare

            # Check for refs
            if hasattr(repository, "references"):
                refs = list(repository.references)
                checks["has_refs"] = len(refs) > 0
                checks["refs_count"] = len(refs)
            else:
                checks["has_refs"] = False
                checks["refs_count"] = 0

            # Check for objects
            try:
                checks["has_objects"] = len(list(repository.odb)) > 0
            except Exception:
                # Fallback check for objects directory
                objects_dir = repo_path / "objects"
                checks["has_objects"] = objects_dir.exists() and any(
                    objects_dir.iterdir()
                )

            checks["healthy"] = checks["has_refs"] and checks["has_objects"]

        except (pygit2.GitError, OSError) as e:
            logger.debug(f"Repository validation failed for {repo_path}: {e}")

        return checks

    def remove_repository(self, repo_config: config.RepositoryConfig) -> bool:
        """Remove a cloned repository and its state.

        Args:
            repo_config: Repository configuration

        Returns:
            True if successfully removed
        """
        repo_path = repo_config.repo_path
        state_path = repo_config.state_path

        try:
            # Check for lock file
            lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"
            if lock_file.exists():
                logger.error(
                    f"Cannot remove repository, clone in progress: {repo_path}"
                )
                return False

            # Remove repository
            if repo_path.exists():
                import shutil

                shutil.rmtree(repo_path)
                logger.info(f"Removed repository: {repo_path}")

            # Remove state directory
            if state_path.exists():
                import shutil

                shutil.rmtree(state_path)
                logger.info(f"Removed state: {state_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to remove repository {repo_path}: {e}")
            return False


# Convenience functions
def clone_repository_by_url(
    url: str,
    name: str | None = None,
    progress_callback: collections.abc.Callable[[CloneProgress], None] | None = None,
) -> CloneResult:
    """Clone a repository by URL with minimal configuration.

    Args:
        url: Repository URL
        name: Optional repository name (derived from URL if not provided)
        progress_callback: Optional progress callback

    Returns:
        CloneResult with operation details
    """
    from ...utils import paths

    if not name:
        name = paths.url_to_path(url).split("/")[-1]

    repo_config = config.RepositoryConfig(
        name=name,
        source={"url": url, "type": "git"},
    )

    cloner = RepositoryCloner()
    return cloner.clone_repository(repo_config, progress_callback)


def validate_repository_by_path(repo_path: pathlib.Path) -> dict[str, typing.Any]:
    """Validate repository by path.

    Args:
        repo_path: pathlib.Path to repository

    Returns:
        Validation results
    """
    cloner = RepositoryCloner()
    return cloner.validate_clone(repo_path)
