import os
import pathlib
import shutil
import time
import typing

import aiofiles
from loguru import logger
import pygit2

from ca_bhfuil.core import async_config
from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.models import progress as progress_models
from ca_bhfuil.core.models import results as results_models


class AsyncCloneLockManager:
    """Manages clone operation locks to prevent concurrent cloning."""

    def __init__(self, repo_path: pathlib.Path):
        self.repo_path = repo_path
        self.lock_file = repo_path.parent / f".{repo_path.name}.clone_lock"

    async def __aenter__(self) -> "AsyncCloneLockManager":
        """Acquire lock."""
        if await self._is_locked():
            raise RuntimeError(f"Clone already in progress for {self.repo_path}")

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        lock_info = f"pid:{os.getpid()}\ntime:{time.time()}\n"
        async with aiofiles.open(self.lock_file, "w", encoding="utf-8") as f:
            await f.write(lock_info)

        logger.debug(f"Acquired clone lock for {self.repo_path}")
        return self

    async def __aexit__(
        self, exc_type: typing.Any, exc_val: typing.Any, exc_tb: typing.Any
    ) -> None:
        """Release lock."""
        if await self._is_locked():
            os.remove(self.lock_file)
            logger.debug(f"Released clone lock for {self.repo_path}")

    async def _is_locked(self) -> bool:
        return self.lock_file.exists()


class AsyncRepositoryCloner:
    """Handles git repository cloning operations asynchronously."""

    def __init__(self, git_manager: async_git.AsyncGitManager):
        self.git_manager = git_manager
        self.config_manager = async_config.AsyncConfigManager()

    async def clone_repository(
        self,
        repo_config: config.RepositoryConfig,
        progress_callback: typing.Callable[[progress_models.CloneProgress], None]
        | None = None,
        force: bool = False,
    ) -> results_models.CloneResult:
        """Clone a repository using configuration."""
        start_time = time.time()
        repo_path = repo_config.repo_path
        url = repo_config.source["url"]

        logger.info(f"Starting clone of {url} to {repo_path}")

        if repo_path.exists() and not force:
            is_valid = await self.git_manager.run_in_executor(
                self._is_valid_repository, repo_path
            )
            if is_valid:
                logger.info(f"Repository already exists at {repo_path}")
                return results_models.CloneResult(
                    success=True,
                    duration=time.time() - start_time,
                    repository_path=str(repo_path),
                )
            logger.warning(f"Invalid repository at {repo_path}, removing.")
            await self.git_manager.run_in_executor(shutil.rmtree, repo_path)

        try:
            async with AsyncCloneLockManager(repo_path):
                return await self._perform_clone(
                    repo_config, progress_callback, start_time
                )
        except Exception as e:
            logger.error(f"Clone failed for {url}: {e}")
            return results_models.CloneResult(
                success=False,
                duration=time.time() - start_time,
                error=str(e),
                repository_path=str(repo_path),
            )

    def _is_valid_repository(self, repo_path: pathlib.Path) -> bool:
        try:
            pygit2.Repository(str(repo_path))
            return True
        except (pygit2.GitError, KeyError):
            return False

    async def _perform_clone(
        self,
        repo_config: config.RepositoryConfig,
        progress_callback: typing.Callable[[progress_models.CloneProgress], None]
        | None,
        start_time: float,
    ) -> results_models.CloneResult:
        repo_path = repo_config.repo_path
        url = repo_config.source["url"]

        repo_path.parent.mkdir(parents=True, exist_ok=True)

        callbacks = await self._setup_callbacks(repo_config, progress_callback)

        # Use functools.partial to handle keyword arguments
        import functools

        clone_func = functools.partial(
            pygit2.clone_repository, url, str(repo_path), callbacks=callbacks
        )
        await self.git_manager.run_in_executor(clone_func)

        return results_models.CloneResult(
            success=True,
            duration=time.time() - start_time,
            repository_path=str(repo_path),
        )

    async def _setup_callbacks(
        self,
        repo_config: config.RepositoryConfig,
        progress_callback: typing.Callable[[progress_models.CloneProgress], None]
        | None,
    ) -> typing.Any:
        callbacks = pygit2.RemoteCallbacks()  # type: ignore[attr-defined,no-untyped-call]

        if progress_callback:
            # Use setattr to work around mypy method assignment restrictions
            setattr(
                callbacks,
                "transfer_progress",
                self._create_progress_callback(progress_callback),
            )

        if repo_config.auth_key:
            auth_method = await self.config_manager.get_auth_method(
                repo_config.auth_key
            )
            if auth_method:
                # Use setattr to work around mypy method assignment restrictions
                setattr(
                    callbacks,
                    "credentials",
                    self._create_credentials_callback(auth_method),
                )
            else:
                # Use setattr to work around mypy method assignment restrictions
                setattr(callbacks, "credentials", None)
        else:
            # Use setattr to work around mypy method assignment restrictions
            setattr(callbacks, "credentials", None)

        return callbacks

    def _create_progress_callback(
        self, progress_callback: typing.Callable[[progress_models.CloneProgress], None]
    ) -> typing.Callable[[typing.Any], None]:
        def _callback(stats: typing.Any) -> None:
            progress = progress_models.CloneProgress(
                total=stats.total_objects,
                completed=stats.received_objects,
                status="Cloning...",
                receiving_objects=stats.received_objects,
                indexing_objects=stats.indexed_objects,
                resolving_deltas=stats.total_deltas,
            )
            progress_callback(progress)

        return _callback

    def _create_credentials_callback(
        self, auth_method: config.AuthMethod
    ) -> typing.Callable[[str, str, int], typing.Any]:
        def _callback(
            url: str, username_from_url: str, allowed_types: int
        ) -> typing.Any:
            del url, username_from_url, allowed_types  # Unused arguments
            if auth_method.type == "ssh_key":
                passphrase = ""
                if auth_method.ssh_key_passphrase_env:
                    passphrase = os.environ.get(auth_method.ssh_key_passphrase_env, "")
                if auth_method.ssh_key_path:
                    public_key_path = (
                        str(pathlib.Path(auth_method.ssh_key_path).expanduser())
                        + ".pub"
                    )
                    private_key_path = str(
                        pathlib.Path(auth_method.ssh_key_path).expanduser()
                    )
                    return pygit2.Keypair(
                        "git", public_key_path, private_key_path, passphrase
                    )
                raise ValueError("SSH key path is required for ssh_key authentication")
            if auth_method.type == "token":
                username = "git"
                if auth_method.username_env:
                    username = os.environ.get(auth_method.username_env, "git")
                token = ""
                if auth_method.token_env:
                    token = os.environ.get(auth_method.token_env, "")
                return pygit2.UserPass(username, token)
            raise NotImplementedError(f"Unsupported auth type: {auth_method.type}")

        return _callback
