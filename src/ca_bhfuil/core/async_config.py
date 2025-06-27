"""Asynchronous configuration management."""

import asyncio
import typing

import aiofiles
import yaml

from ca_bhfuil.core import config

class AsyncConfigManager:
    """Manages loading configuration files asynchronously."""

    def __init__(self, config_dir: str | None = None):
        self._config_dir = config_dir or str(config.get_config_dir())
        self._config_cache: dict[str, typing.Any] = {}
        self._cache_lock = asyncio.Lock()

    async def get_config(self, config_name: str) -> dict[str, typing.Any]:
        """Load a specific YAML configuration file asynchronously."""
        async with self._cache_lock:
            if config_name in self._config_cache:
                return self._config_cache[config_name]

        config_path = f"{self._config_dir}/{config_name}.yaml"
        try:
            async with aiofiles.open(config_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                config_data = yaml.safe_load(content)
        except FileNotFoundError:
            config_data = {}

        async with self._cache_lock:
            self._config_cache[config_name] = config_data

        return config_data
