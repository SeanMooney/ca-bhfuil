"""Disk cache wrapper for ca-bhfuil."""

import datetime
import json
import pathlib
import typing

import diskcache as dc
from loguru import logger

from ca_bhfuil.core import config


class CacheManager:
    """High-level cache manager using diskcache."""

    def __init__(self, cache_dir: pathlib.Path | None = None) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Optional cache directory override
        """
        cache_directory = config.get_cache_dir()
        self.cache_dir = cache_dir or cache_directory
        self.max_size_bytes = 1024 * 1024 * 1024  # 1GB default
        self.default_ttl = datetime.timedelta(hours=24)  # 24 hours default

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize main cache
        self._cache = dc.Cache(
            directory=str(self.cache_dir),
            size_limit=self.max_size_bytes,
        )

        logger.debug(f"Initialized cache at {self.cache_dir}")

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            return self._cache.get(key, default)
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return default

    def set(
        self, key: str, value: typing.Any, ttl: int | datetime.timedelta | None = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)

        Returns:
            True if successful
        """
        try:
            if isinstance(ttl, int):
                ttl = datetime.timedelta(seconds=ttl)
            elif ttl is None:
                ttl = self.default_ttl

            expire_time = datetime.datetime.now() + ttl
            result = self._cache.set(key, value, expire=expire_time.timestamp())
            return bool(result)
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted
        """
        try:
            result = self._cache.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def stats(self) -> dict[str, typing.Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = self._cache.stats()
            return {
                "size": stats.get("size", 0),
                "count": len(self._cache),
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "directory": str(self.cache_dir),
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"error": str(e)}

    def cache_key(self, *parts: str) -> str:
        """Create a cache key from parts.

        Args:
            parts: Key parts to join

        Returns:
            Formatted cache key
        """
        return ":".join(str(part) for part in parts)

    def close(self) -> None:
        """Close the cache."""
        try:
            self._cache.close()
        except Exception as e:
            logger.warning(f"Cache close error: {e}")

    def __enter__(self) -> "CacheManager":
        """Context manager entry."""
        return self

    def __exit__(
        self, exc_type: typing.Any, exc_val: typing.Any, exc_tb: typing.Any
    ) -> None:
        """Context manager exit."""
        # Parameters are required by context manager protocol but not used
        del exc_type, exc_val, exc_tb
        self.close()


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_git_operation(repo_path: str, operation: str, *args: str) -> str:
    """Generate cache key for git operations.

    Args:
        repo_path: Repository path
        operation: Git operation name
        args: Additional arguments

    Returns:
        Cache key string
    """
    cache_manager = get_cache_manager()
    return cache_manager.cache_key("git", repo_path, operation, *args)


def cache_api_request(url: str, params: dict[str, typing.Any] | None = None) -> str:
    """Generate cache key for API requests.

    Args:
        url: Request URL
        params: Request parameters

    Returns:
        Cache key string
    """
    cache_manager = get_cache_manager()
    parts = ["api", url]
    if params:
        # Sort params for consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        parts.append(param_str)
    return cache_manager.cache_key(*parts)
