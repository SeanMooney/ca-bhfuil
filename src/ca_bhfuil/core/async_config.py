"""Asynchronous configuration management."""

import asyncio
import pathlib
import typing

import aiofiles
import yaml

from ca_bhfuil.core import config


class AsyncConfigManager:
    """Manages loading configuration files asynchronously."""

    def __init__(self, config_dir: pathlib.Path | None = None):
        """Initialize async configuration manager."""
        self.config_dir = config_dir or config.get_config_dir()
        self.repositories_file = self.config_dir / "repos.yaml"
        self.global_settings_file = self.config_dir / "global.yaml"
        self.auth_file = self.config_dir / "auth.yaml"

        self._config_cache: dict[str, typing.Any] = {}
        self._cache_lock = asyncio.Lock()

        # Ensure directories exist
        config.setup_secure_directories()

    async def load_configuration(self) -> config.GlobalConfig:
        """Load and validate all configuration files asynchronously."""
        if not self.repositories_file.exists():
            return config.GlobalConfig()

        try:
            async with aiofiles.open(self.repositories_file, encoding="utf-8") as f:
                content = await f.read()
                config_data = yaml.safe_load(content) or {}

            return config.GlobalConfig(**config_data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.repositories_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")

    async def get_repository_config(
        self, url_path: str
    ) -> config.RepositoryConfig | None:
        """Get configuration for specific repository by URL path."""
        global_config = await self.load_configuration()
        for repo in global_config.repos:
            if repo.url_path == url_path:
                return repo
        return None

    async def get_repository_config_by_url(
        self, url: str
    ) -> config.RepositoryConfig | None:
        """Get configuration for specific repository by source URL."""
        global_config = await self.load_configuration()
        for repo in global_config.repos:
            if repo.source.get("url") == url:
                return repo
        return None

    async def validate_configuration(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        try:
            global_config = await self.load_configuration()

            # Check for duplicate repository names
            names = [repo.name for repo in global_config.repos]
            if len(names) != len(set(names)):
                errors.append("Duplicate repository names found")

            # Check for duplicate URLs
            urls = [repo.source.get("url") for repo in global_config.repos]
            if len(urls) != len(set(urls)):
                errors.append("Duplicate repository URLs found")

            # Validate auth references
            auth_config = await self.load_auth_config()
            for repo in global_config.repos:
                if repo.auth_key and repo.auth_key not in auth_config:
                    errors.append(
                        f"Repository '{repo.name}' references unknown auth key '{repo.auth_key}'"
                    )

        except Exception as e:
            errors.append(f"Configuration loading error: {e}")

        return errors

    async def generate_default_config(self) -> None:
        """Generate default configuration files asynchronously."""
        # Create default repos.yaml
        default_config = {
            "version": "1.0",
            "settings": {
                "max_total_size": "50GB",
                "default_sync_interval": "6h",
                "clone_timeout": "30m",
                "parallel_clones": 3,
            },
            "repos": [],
        }

        if not self.repositories_file.exists():
            async with aiofiles.open(
                self.repositories_file, "w", encoding="utf-8"
            ) as f:
                await f.write(
                    yaml.dump(default_config, default_flow_style=False, indent=2)
                )

        # Create default global-settings.yaml
        default_global = {
            "version": "1.0",
            "storage": {
                "max_total_size": "100GB",
                "max_cache_size": "80GB",
                "max_state_size": "20GB",
                "cleanup_policy": "lru",
                "cleanup_threshold": 0.9,
            },
            "sync": {
                "max_parallel_jobs": 3,
                "default_timeout": "30m",
                "retry_attempts": 3,
                "retry_backoff": "exponential",
            },
            "performance": {"git_clone_bare": True, "pygit2_cache_size": "100MB"},
        }

        if not self.global_settings_file.exists():
            async with aiofiles.open(
                self.global_settings_file, "w", encoding="utf-8"
            ) as f:
                await f.write(
                    yaml.dump(default_global, default_flow_style=False, indent=2)
                )

        # Create auth.yaml template (with restrictive permissions)
        auth_template = {
            "version": "1.0",
            "defaults": {
                "github": {"type": "ssh_key", "ssh_key_path": "~/.ssh/id_ed25519"},
                "gitlab": {"type": "ssh_key", "ssh_key_path": "~/.ssh/id_ed25519"},
            },
            "auth_methods": {
                "github-default": {
                    "type": "ssh_key",
                    "ssh_key_path": "~/.ssh/id_ed25519",
                }
            },
        }

        if not self.auth_file.exists():
            async with aiofiles.open(self.auth_file, "w", encoding="utf-8") as f:
                await f.write(
                    yaml.dump(auth_template, default_flow_style=False, indent=2)
                )
            self.auth_file.chmod(0o600)  # Secure permissions

    async def load_auth_config(self) -> dict[str, config.AuthMethod]:
        """Load authentication configuration from auth.yaml asynchronously."""
        if not self.auth_file.exists():
            return {}

        try:
            async with aiofiles.open(self.auth_file, encoding="utf-8") as f:
                content = await f.read()
                auth_data = yaml.safe_load(content) or {}

            auth_methods = {}
            for key, method_data in auth_data.get("auth_methods", {}).items():
                auth_methods[key] = config.AuthMethod(**method_data)

            return auth_methods
        except Exception as e:
            raise ValueError(f"Error loading auth configuration: {e}")

    async def get_auth_method(self, auth_key: str) -> config.AuthMethod | None:
        """Get authentication method by key."""
        auth_config = await self.load_auth_config()
        return auth_config.get(auth_key)

    async def validate_auth_config(self) -> list[str]:
        """Validate authentication configuration."""
        errors = []

        try:
            await self.load_auth_config()
        except Exception as e:
            errors.append(f"Auth configuration error: {e}")

        return errors

    async def save_configuration(self, global_config: config.GlobalConfig) -> None:
        """Save configuration to the repositories file asynchronously."""
        config_data = {
            "version": global_config.version,
            "settings": global_config.settings,
            "repos": [
                {
                    "name": repo.name,
                    "source": repo.source,
                    "auth_key": repo.auth_key,
                    "branches": repo.branches.__dict__ if repo.branches else {},
                    "sync": repo.sync.__dict__ if repo.sync else {},
                }
                for repo in global_config.repos
            ],
        }

        async with aiofiles.open(self.repositories_file, "w", encoding="utf-8") as f:
            await f.write(yaml.dump(config_data, default_flow_style=False, indent=2))


# Global async configuration manager instance
_async_config_manager: AsyncConfigManager | None = None


async def get_async_config_manager() -> AsyncConfigManager:
    """Get the global async configuration manager instance."""
    global _async_config_manager
    if _async_config_manager is None:
        _async_config_manager = AsyncConfigManager()
    return _async_config_manager
