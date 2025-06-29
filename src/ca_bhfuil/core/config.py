"""Configuration management for ca-bhfuil with XDG Base Directory compliance."""

import os
import pathlib
import re
import typing  # Any

import pydantic  # BaseModel, Field, field_validator
import yaml

from ..utils import paths


# XDG Base Directory utilities
def get_config_dir() -> pathlib.Path:
    """Get XDG_CONFIG_HOME compliant config directory."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return pathlib.Path(xdg_config) / "ca-bhfuil"
    return pathlib.Path.home() / ".config" / "ca-bhfuil"


def get_state_dir() -> pathlib.Path:
    """Get XDG_STATE_HOME compliant state directory."""
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return pathlib.Path(xdg_state) / "ca-bhfuil"
    return pathlib.Path.home() / ".local" / "state" / "ca-bhfuil"


def get_cache_dir() -> pathlib.Path:
    """Get XDG_CACHE_HOME compliant cache directory."""
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return pathlib.Path(xdg_cache) / "ca-bhfuil"
    return pathlib.Path.home() / ".cache" / "ca-bhfuil"


def setup_secure_directories() -> None:
    """Set up directories with appropriate permissions."""
    config_dir = get_config_dir()
    state_dir = get_state_dir()
    cache_dir = get_cache_dir()

    # Create directories with secure permissions
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    cache_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    # Secure auth file if it exists
    auth_file = config_dir / "auth.yaml"
    if auth_file.exists():
        auth_file.chmod(0o600)


# Repository configuration models
class RemoteConfig(pydantic.BaseModel):
    """Configuration for a git remote."""

    name: str
    url: str
    fetch_refs: list[str] = pydantic.Field(default_factory=lambda: ["refs/heads/*"])


class AuthMethod(pydantic.BaseModel):
    """Authentication method for git operations."""

    type: str = "ssh_key"  # ssh_key, token, credential_helper
    ssh_key_path: str | None = None
    ssh_key_passphrase_env: str | None = None
    token_env: str | None = None
    username_env: str | None = None
    credential_helper: str | None = None


class BranchConfig(pydantic.BaseModel):
    """Branch filtering configuration."""

    patterns: list[str] = pydantic.Field(default_factory=lambda: ["*"])
    exclude_patterns: list[str] = pydantic.Field(default_factory=list)
    max_branches: int = 100

    @pydantic.field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate glob patterns."""
        for pattern in v:
            try:
                # Convert glob to regex for validation
                re.compile(pattern.replace("*", ".*"))
            except re.error as e:
                raise ValueError(f"Invalid pattern: {pattern}") from e
        return v


class SyncConfig(pydantic.BaseModel):
    """Repository synchronization configuration."""

    strategy: str = "fetch_all"  # fetch_all, fetch_recent, manual
    interval: str = "6h"  # 1h, 30m, 1d format
    recent_days: int | None = None
    prune_deleted: bool = True


class StorageConfig(pydantic.BaseModel):
    """Repository storage configuration."""

    type: str = "bare"  # bare, full
    max_size: str | None = None  # "5GB", "1TB" format
    retention_days: int = 365


class RepositoryConfig(pydantic.BaseModel):
    """Configuration for a single repository."""

    name: str
    source: dict[str, typing.Any]  # URL, type
    remotes: list[RemoteConfig] = pydantic.Field(default_factory=list)
    branches: BranchConfig = pydantic.Field(default_factory=BranchConfig)
    sync: SyncConfig = pydantic.Field(default_factory=SyncConfig)
    storage: StorageConfig = pydantic.Field(default_factory=StorageConfig)
    auth_key: str | None = None  # Reference to auth.yaml entry

    @property
    def url_path(self) -> str:
        """Generate URL-based path from source URL."""
        return paths.url_to_path(self.source["url"])

    @property
    def repo_path(self) -> pathlib.Path:
        """Get full path to git repository (cache)."""
        return get_cache_dir() / "repos" / self.url_path

    @property
    def state_path(self) -> pathlib.Path:
        """Get full path to state directory."""
        return get_state_dir() / self.url_path


class GlobalConfig(pydantic.BaseModel):
    """Global repository configuration."""

    version: str = "1.0"
    repos: list[RepositoryConfig] = pydantic.Field(default_factory=list)
    settings: dict[str, typing.Any] = pydantic.Field(default_factory=dict)


class ConfigManager:
    """Manages repository configuration loading and validation."""

    def __init__(self, config_dir: pathlib.Path | None = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or get_config_dir()
        self.repositories_file = self.config_dir / "repos.yaml"
        self.global_settings_file = self.config_dir / "global.yaml"
        self.auth_file = self.config_dir / "auth.yaml"

        # Ensure directories exist
        setup_secure_directories()

    def load_configuration(self) -> GlobalConfig:
        """Load and validate all configuration files."""
        if not self.repositories_file.exists():
            return GlobalConfig()

        try:
            with self.repositories_file.open(encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            return GlobalConfig(**config_data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.repositories_file}: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}") from e

    def get_repository_config(self, url_path: str) -> RepositoryConfig | None:
        """Get configuration for specific repository by URL path."""
        config = self.load_configuration()
        for repo in config.repos:
            if repo.url_path == url_path:
                return repo
        return None

    def get_repository_config_by_url(self, url: str) -> RepositoryConfig | None:
        """Get configuration for specific repository by source URL."""
        config = self.load_configuration()
        for repo in config.repos:
            if repo.source.get("url") == url:
                return repo
        return None

    def get_repository_config_by_name(self, name: str) -> RepositoryConfig | None:
        """Get configuration for specific repository by name."""
        config = self.load_configuration()
        for repo in config.repos:
            if repo.name == name:
                return repo
        return None

    def validate_configuration(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        try:
            config = self.load_configuration()

            # Check for duplicate repository names
            names = [repo.name for repo in config.repos]
            if len(names) != len(set(names)):
                errors.append("Duplicate repository names found")

            # Check for duplicate URLs
            urls = [repo.source.get("url") for repo in config.repos]
            if len(urls) != len(set(urls)):
                errors.append("Duplicate repository URLs found")

            # Validate auth references
            auth_config = self.load_auth_config()
            for repo in config.repos:
                if repo.auth_key and repo.auth_key not in auth_config:
                    errors.append(
                        f"Repository '{repo.name}' references unknown auth key '{repo.auth_key}'"
                    )

        except Exception as e:
            errors.append(f"Configuration loading error: {e}")

        return errors

    def generate_default_config(self) -> None:
        """Generate default configuration files."""
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
            with self.repositories_file.open("w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)

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
            with self.global_settings_file.open("w", encoding="utf-8") as f:
                yaml.dump(default_global, f, default_flow_style=False, indent=2)

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
            with self.auth_file.open("w", encoding="utf-8") as f:
                yaml.dump(auth_template, f, default_flow_style=False, indent=2)
            self.auth_file.chmod(0o600)  # Secure permissions

    def load_auth_config(self) -> dict[str, AuthMethod]:
        """Load authentication configuration from auth.yaml."""
        if not self.auth_file.exists():
            return {}

        try:
            with self.auth_file.open(encoding="utf-8") as f:
                auth_data = yaml.safe_load(f) or {}

            auth_methods = {}
            for key, method_data in auth_data.get("auth_methods", {}).items():
                auth_methods[key] = AuthMethod(**method_data)

            return auth_methods
        except Exception as e:
            raise ValueError(f"Error loading auth configuration: {e}") from e

    def get_auth_method(self, auth_key: str) -> AuthMethod | None:
        """Get authentication method by key."""
        auth_config = self.load_auth_config()
        return auth_config.get(auth_key)

    def validate_auth_config(self) -> list[str]:
        """Validate authentication configuration."""
        errors = []

        try:
            self.load_auth_config()
        except Exception as e:
            errors.append(f"Auth configuration error: {e}")

        return errors


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
