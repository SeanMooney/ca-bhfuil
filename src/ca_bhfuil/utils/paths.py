"""URL-to-path conversion utilities with cross-platform safety."""

import hashlib
import pathlib
import re
from urllib import parse

from ca_bhfuil.core import config


def url_to_path(url: str) -> str:
    """Convert repository URL to filesystem path.

    Args:
        url: Repository URL (SSH or HTTPS format)

    Returns:
        URL-based path (e.g., "github.com/torvalds/linux")

    Examples:
        >>> url_to_path("git@github.com:torvalds/linux.git")
        'github.com/torvalds/linux'
        >>> url_to_path("https://github.com/django/django.git")
        'github.com/django/django'
    """
    # Handle SSH format: git@github.com:owner/repo.git
    if url.startswith("git@"):
        match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
        if match:
            host, path = match.groups()
            return f"{host}/{path}"
    else:
        # Handle HTTP/HTTPS format
        parsed = parse.urlparse(url)
        if parsed.scheme in ("http", "https"):
            # Remove leading slash and .git suffix
            path = parsed.path.lstrip("/").removesuffix(".git")
            return f"{parsed.netloc}/{path}"

    raise ValueError(f"Unsupported URL format: {url}")


def sanitize_path_component(component: str) -> str:
    """Sanitize a single path component for filesystem safety.

    Args:
        component: pathlib.Path component to sanitize

    Returns:
        Sanitized path component safe for all filesystems
    """
    # Replace invalid characters with safe alternatives
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        component = component.replace(char, "_")

    # Handle reserved Windows names
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if component.upper() in reserved:
        component = f"{component}_"

    # Remove leading/trailing dots and spaces
    component = component.strip(". ")

    # Ensure component is not empty
    if not component:
        component = "_"

    return component


def ensure_path_length(path: pathlib.Path, max_length: int = 260) -> pathlib.Path:
    """Ensure path doesn't exceed maximum length limits.

    Args:
        path: pathlib.Path to check and potentially truncate
        max_length: Maximum allowed path length (Windows default: 260)

    Returns:
        Path that fits within length limits
    """
    path_str = str(path)
    if len(path_str) <= max_length:
        return path

    # Truncate path components while preserving structure
    parts = path.parts
    truncated_parts = []

    for part in parts:
        if len(part) > 50:  # Truncate long components
            truncated_parts.append(part[:47] + "...")
        else:
            truncated_parts.append(part)

    truncated_path = pathlib.Path(*truncated_parts)

    # If still too long, use hash-based truncation
    if len(str(truncated_path)) > max_length:
        path_hash = hashlib.sha256(path_str.encode()).hexdigest()[:8]
        # Keep the last component and add hash
        last_part = parts[-1] if parts else "repo"
        if len(last_part) > 20:
            last_part = last_part[:17] + "..."
        truncated_path = pathlib.Path(f"_truncated_{path_hash}") / last_part

    return truncated_path


def get_repo_paths(
    url: str,
    cache_dir: pathlib.Path | None = None,
    state_dir: pathlib.Path | None = None,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Get both repository and state paths for a URL (XDG compliant).

    Args:
        url: Repository URL
        cache_dir: Cache directory (uses XDG default if None)
        state_dir: State directory (uses XDG default if None)

    Returns:
        Tuple of (repo_path, state_path)
    """
    url_path = url_to_path(url)

    # Sanitize path components
    sanitized_parts = [sanitize_path_component(part) for part in url_path.split("/")]
    sanitized_path = "/".join(sanitized_parts)

    # Use provided directories or XDG defaults
    if cache_dir is None:
        cache_dir = config.get_cache_dir()
    if state_dir is None:
        state_dir = config.get_state_dir()

    repo_path = cache_dir / "repos" / sanitized_path
    state_path = state_dir / sanitized_path

    # Ensure path length limits
    repo_path = ensure_path_length(repo_path)
    state_path = ensure_path_length(state_path)

    return repo_path, state_path


def is_valid_url(url: str) -> bool:
    """Check if URL is a valid git repository URL.

    Args:
        url: URL to validate

    Returns:
        True if URL appears to be a valid git repository URL
    """
    if not url or not isinstance(url, str):
        return False

    try:
        # First check if it can be parsed as a URL
        url_to_path(url)

        # Additional checks for git-like URLs
        if url.startswith("git@"):
            # SSH format should have colon after host
            return ":" in url and "/" in url
        if url.startswith(("http://", "https://")):
            # HTTP/HTTPS should have a path component
            parsed = parse.urlparse(url)
            path = parsed.path.strip("/")
            # Should have at least host/repo format or end with .git
            return "/" in path or path.endswith(".git") or url.endswith(".git")

        return False
    except ValueError:
        return False


def normalize_url(url: str) -> str:
    """Normalize URL to a canonical format.

    Args:
        url: Repository URL to normalize

    Returns:
        Normalized URL (HTTPS format preferred)
    """
    try:
        # Convert SSH to HTTPS format for consistency
        if url.startswith("git@"):
            match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
            if match:
                host, path = match.groups()
                return f"https://{host}/{path}.git"

        # Ensure HTTPS URLs have .git suffix
        parsed = parse.urlparse(url)
        if parsed.scheme in ("http", "https"):
            path = parsed.path.rstrip("/")
            if not path.endswith(".git"):
                path += ".git"
            return f"https://{parsed.netloc}{path}"

        return url
    except Exception:
        return url
