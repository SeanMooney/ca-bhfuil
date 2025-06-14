"""Configuration management for ca-bhfuil."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseModel):
    """Cache-related configuration."""

    enabled: bool = Field(default=True, description="Enable caching")
    directory: Path = Field(default_factory=lambda: Path.home() / ".ca-bhfuil" / "cache")
    max_size_mb: int = Field(default=1000, description="Maximum cache size in MB")
    default_ttl_hours: int = Field(default=24, description="Default TTL in hours")


class GitSettings(BaseModel):
    """Git-related configuration."""

    default_repo_path: Path | None = Field(default=None, description="Default repository path")
    max_commit_history: int = Field(default=10000, description="Maximum commits to analyze")


class IssueTrackerSettings(BaseModel):
    """Issue tracker integration settings."""

    enabled: bool = Field(default=True, description="Enable issue tracker integration")
    github_token: str | None = Field(default=None, description="GitHub API token")
    jira_base_url: str | None = Field(default=None, description="JIRA base URL")
    jira_username: str | None = Field(default=None, description="JIRA username")
    jira_token: str | None = Field(default=None, description="JIRA API token")
    request_timeout_seconds: int = Field(default=30, description="HTTP request timeout")


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="Log format string"
    )
    file_enabled: bool = Field(default=False, description="Enable file logging")
    file_path: Path | None = Field(default=None, description="Log file path")


class CaBhfuilSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="CA_BHFUIL_",
        env_nested_delimiter="__",
        yaml_file="ca-bhfuil.yaml",
        yaml_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core settings
    debug: bool = Field(default=False, description="Enable debug mode")
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".ca-bhfuil")

    # Component settings
    cache: CacheSettings = Field(default_factory=CacheSettings)
    git: GitSettings = Field(default_factory=GitSettings)
    issue_tracker: IssueTrackerSettings = Field(default_factory=IssueTrackerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and ensure directories exist."""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache.directory.mkdir(parents=True, exist_ok=True)

        if self.logging.file_enabled and self.logging.file_path:
            self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)

    def get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return self.config_dir / "ca-bhfuil.yaml"

    def save_config(self) -> None:
        """Save current configuration to YAML file."""
        import yaml

        config_data = self.model_dump(exclude={"config_dir"})
        config_file = self.get_config_file_path()

        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)


# Global settings instance
_settings: CaBhfuilSettings | None = None


def get_settings() -> CaBhfuilSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = CaBhfuilSettings()
    return _settings


def reload_settings() -> CaBhfuilSettings:
    """Reload settings from configuration sources."""
    global _settings
    _settings = CaBhfuilSettings()
    return _settings
