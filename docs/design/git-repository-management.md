# Git Repository Management Design

## Overview

This document defines the git repository management system for Ca-Bhfuil, focusing on local repository storage, remote synchronization, branch management, and configuration-driven automation.

**Core Requirements**:
- Clone and manage multiple git repositories locally
- Configure remote sources and additional remotes per repository  
- Define branch patterns for selective processing
- Efficient storage and synchronization strategies
- Performance-optimized for large repositories (10k+ commits)

## Architecture Design

### Repository Management Philosophy

**Local-First Storage**: All repositories are cloned locally for maximum performance and offline capability
- Primary analysis works on local clones
- Periodic synchronization with remotes
- Configurable sync strategies per repository
- Disk space management with cleanup policies

**Configuration-Driven**: Declarative YAML configuration defines all repository management
- Repository sources and remotes
- Branch selection patterns  
- Storage locations and policies
- Sync schedules and strategies

### Storage Architecture

#### Directory Structure (XDG Base Directory Compliant)

```
# Configuration (XDG_CONFIG_HOME)
~/.config/ca-bhfuil/
├── repositories.yaml               # Repository configuration (git-safe)
├── global-settings.yaml            # Global management settings (git-safe)
└── auth.yaml                        # Authentication configuration (git-ignored)

# Persistent State (XDG_STATE_HOME)
~/.local/state/ca-bhfuil/
├── github.com/
│   ├── torvalds/
│   │   └── linux/                  # State for torvalds/linux
│   │       ├── analysis.db          # SQLite: commit analysis state
│   │       ├── sync-log.db          # SQLite: sync history and status
│   │       ├── embeddings.db        # SQLite: RAG vectors (when AI enabled)
│   │       ├── trackers.db          # SQLite: issue tracker state
│   │       ├── repo-config.yaml     # Repository-specific overrides
│   │       ├── stats.json           # Quick access statistics
│   │       └── .locks/              # Process locks for concurrent access
│   │           ├── sync.lock
│   │           └── analysis.lock
│   ├── django/
│   │   └── django/                  # State for django/django
│   └── kubernetes/
│       └── kubernetes/              # State for kubernetes/kubernetes
└── global/
    ├── repo-registry.db             # SQLite: global repository metadata
    └── sync-scheduler.db            # SQLite: sync job management

# Cache (XDG_CACHE_HOME)
~/.cache/ca-bhfuil/
├── repos/                           # Git repositories (cache data)
│   ├── github.com/
│   │   ├── torvalds/
│   │   │   └── linux/              # Git repository (bare or regular)
│   │   ├── django/
│   │   │   └── django/             # Git repository
│   │   └── kubernetes/
│   │       └── kubernetes/         # Git repository  
│   ├── git.kernel.org/
│   │   └── torvalds/
│   │       └── linux/              # Git repository from kernel.org
│   └── gitlab.com/
│       └── {org}/
│           └── {project}/          # GitLab repositories
└── temp/
    └── clone-staging/               # Temporary space for clone operations
```

#### URL-to-Path Conversion
Convert repository URLs to filesystem paths preserving URL structure:
```
https://github.com/torvalds/linux.git → repos/github.com/torvalds/linux
git@github.com:django/django.git → repos/github.com/django/django
https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git → repos/git.kernel.org/torvalds/linux
https://gitlab.com/fdroid/fdroidserver.git → repos/gitlab.com/fdroid/fdroidserver
```

**Benefits of XDG-Compliant Structure**:
- **Standards compliant**: Follows freedesktop.org XDG Base Directory Specification
- **Proper data separation**: Config, state, and cache clearly separated
- **Backup friendly**: Users can backup config and state separately from cache
- **Respects user preferences**: Honors XDG environment variables
- **No slug collisions**: Each URL maps to unique path
- **Intuitive navigation**: Follows familiar URL structure
- **Multi-source support**: Same project from different sources naturally separated
- **Cross-platform safe**: Handles path sanitization and length limits

#### XDG Environment Variable Support

| Variable | Default | Purpose | Ca-Bhfuil Usage |
|----------|---------|---------|------------------|
| `XDG_CONFIG_HOME` | `~/.config` | User configuration | `repositories.yaml`, `global-settings.yaml`, `auth.yaml` |
| `XDG_STATE_HOME` | `~/.local/state` | Persistent state | SQLite databases, stats, locks |
| `XDG_CACHE_HOME` | `~/.cache` | Cache data | Git repositories, temp files |

```bash
# Example: Custom XDG paths
export XDG_CONFIG_HOME="/opt/configs"
export XDG_STATE_HOME="/var/lib/ca-bhfuil" 
export XDG_CACHE_HOME="/tmp/cache"

# Ca-Bhfuil will automatically use:
# Config: /opt/configs/ca-bhfuil/
# State:  /var/lib/ca-bhfuil/
# Cache:  /tmp/cache/ca-bhfuil/
```

### Configuration System

#### Repository Configuration (`repositories.yaml`)

```yaml
# Global repository management configuration
version: "1.0"
settings:
  # Storage follows XDG Base Directory Specification
  cache_directory: "~/.cache/ca-bhfuil"       # Git repositories
  state_directory: "~/.local/state/ca-bhfuil" # Persistent metadata
  
  # Resource limits
  max_total_size: "50GB"
  default_sync_interval: "6h"
  clone_timeout: "30m"
  parallel_clones: 3

repositories:
  - name: "linux-kernel"
    source:
      url: "git@github.com:torvalds/linux.git"  # Prefer SSH over HTTPS
      type: "github"  # github, gitlab, generic
    
    remotes:
      - name: "stable"
        url: "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
        fetch_refs: ["refs/heads/linux-*", "refs/tags/v*"]
      - name: "security"  
        url: "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
        fetch_refs: ["refs/heads/master"]
    
    branches:
      patterns:
        - "master"                    # Exact branch name
        - "linux-*"                   # Glob pattern
        - "stable/*"                  # Stable branches
        - "!linux-2.6.*"             # Exclusion pattern
      max_branches: 50               # Limit for performance
      
    sync:
      strategy: "fetch_all"          # fetch_all, fetch_recent, manual
      interval: "4h"                 # Override global default
      prune_deleted: true            # Remove deleted remote branches
      
    storage:
      type: "bare"                   # bare, full (bare for analysis only)
      max_size: "5GB"                # Per-repository limit
      retention_days: 365            # Keep sync history
      
  - name: "django"
    source:
      url: "git@github.com:django/django.git"  # SSH preferred
      type: "github"
      
    branches:
      patterns:
        - "main"
        - "stable/*"
        - "security/*"
      
    sync:
      strategy: "fetch_recent"
      recent_days: 90                # Only sync recent commits
      
  - name: "kubernetes"
    source:
      url: "git@github.com:kubernetes/kubernetes.git"  # SSH preferred
      type: "github"
    auth_key: "github-default"       # Reference to auth.yaml
        
    remotes:
      - name: "release"
        url: "git@github.com:kubernetes/release.git"  # SSH preferred
        
    branches:
      patterns:
        - "master"
        - "release-*"
      exclude_patterns:
        - "release-0.*"              # Exclude very old releases
        
    sync:
      strategy: "manual"             # No automatic sync
```

#### Authentication Configuration (`auth.yaml`)

**Separate file for security - should NOT be committed to git**:

```yaml
# Authentication configuration (DO NOT COMMIT TO GIT)
version: "1.0"

# Default authentication methods
defaults:
  github:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"  # Preferred over RSA
  gitlab:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"
  generic:
    type: "credential_helper"
    credential_helper: "system"

# Repository-specific authentication
auth_methods:
  github-default:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_ed25519"
    ssh_key_passphrase_env: "SSH_KEY_PASSPHRASE"  # Optional
    
  github-token:
    type: "token"
    token_env: "GITHUB_TOKEN"
    username_env: "GITHUB_USERNAME"
    
  corporate-gitlab:
    type: "ssh_key"
    ssh_key_path: "~/.ssh/id_rsa_corp"
    ssh_key_passphrase_env: "CORP_SSH_PASSPHRASE"
    
  generic-https:
    type: "credential_helper"
    credential_helper: "store"  # or "cache", "system"
```

**Security Notes**:
- SSH keys are preferred over tokens for better security
- ED25519 keys are preferred over RSA for better performance
- Passphrases stored in environment variables, not config files
- Auth file should be in `.gitignore`

#### Global Settings (`global-settings.yaml`)

```yaml
version: "1.0"

# Storage Management
storage:
  # XDG Base Directory compliant paths
  config_directory: "~/.config/ca-bhfuil"     # XDG_CONFIG_HOME
  state_directory: "~/.local/state/ca-bhfuil" # XDG_STATE_HOME  
  cache_directory: "~/.cache/ca-bhfuil"       # XDG_CACHE_HOME
  
  # Size limits
  max_total_size: "100GB"
  max_cache_size: "80GB"           # Git repositories (can be re-cloned)
  max_state_size: "20GB"           # Persistent state (important to preserve)
  
  # Cleanup policies
  cleanup_policy: "lru"             # lru, fifo, manual
  cleanup_threshold: 0.9            # Clean when 90% full
  
  # Cross-platform compatibility
  path_max_length: 260              # Windows path length limit
  sanitize_paths: true              # Clean invalid filesystem characters
  
# Sync Management  
sync:
  max_parallel_jobs: 3
  default_timeout: "30m"
  retry_attempts: 3
  retry_backoff: "exponential"      # linear, exponential
  
# Network Configuration
network:
  max_connections_per_host: 2
  connection_timeout: "30s"
  read_timeout: "5m"
  user_agent: "ca-bhfuil/0.1.0"
  
# Performance Tuning
performance:
  git_clone_depth: null            # null for full clone, number for shallow
  git_clone_single_branch: false   # Clone all branches by default  
  git_clone_bare: true             # Bare clones for analysis
  pygit2_cache_size: "100MB"       # LibGit2 object cache
  
# Authentication
auth:
  github_token_env: "GITHUB_TOKEN"
  gitlab_token_env: "GITLAB_TOKEN"
  git_credential_helper: "system"   # system, store, cache, none
```

## Core Components

### 1. Repository Registry (`core/git/registry.py`)

**Purpose**: Central registry for all managed repositories

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import sqlite3

@dataclass
class RepositoryEntry:
    url_path: str                    # URL-based path (e.g., "github.com/torvalds/linux")
    name: str
    source_url: str
    repo_path: Path                  # Path to git repository
    memory_path: Path                # Path to metadata directory
    last_sync: Optional[datetime]
    sync_status: str                 # active, paused, error, not_synced
    repo_size: int                   # Git repository size in bytes
    memory_size: int                 # Metadata size in bytes
    branch_count: int
    commit_count: int
    created_at: datetime
    config_hash: str                 # Hash of configuration for change detection

class RepositoryRegistry:
    """Manages the registry of all local repositories"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
    
    def register_repository(self, config: RepositoryConfig) -> RepositoryEntry:
        """Register a new repository in the registry"""
        
    def get_repository(self, url_path: str) -> Optional[RepositoryEntry]:
        """Get repository entry by URL path"""
        
    def get_repository_by_url(self, url: str) -> Optional[RepositoryEntry]:
        """Get repository entry by source URL"""
        
    def list_repositories(self, 
                         status_filter: Optional[str] = None) -> List[RepositoryEntry]:
        """List all registered repositories with optional status filter"""
        
    def update_sync_status(self, url_path: str, status: str, 
                          last_sync: datetime, stats: Dict[str, Any]):
        """Update repository sync status and statistics"""
        
    def cleanup_orphaned(self) -> List[str]:
        """Find and clean up repositories not in current config"""
```

### 2. Configuration Manager (`core/git/config.py`)

**Purpose**: Load, validate, and manage repository configurations

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import List, Optional, Dict, Pattern
import re

class RemoteConfig(BaseModel):
    name: str
    url: str
    fetch_refs: List[str] = Field(default_factory=lambda: ["refs/heads/*"])
    
class AuthMethod(BaseModel):
    """Authentication method for git operations"""
    type: str = "ssh_key"             # ssh_key, token, credential_helper
    ssh_key_path: Optional[str] = None # Path to SSH private key
    ssh_key_passphrase_env: Optional[str] = None
    token_env: Optional[str] = None   # Environment variable for token
    username_env: Optional[str] = None
    credential_helper: Optional[str] = None  # Git credential helper

class BranchConfig(BaseModel):
    patterns: List[str] = Field(default_factory=lambda: ["*"])
    exclude_patterns: List[str] = Field(default_factory=list)
    max_branches: int = 100
    
    @validator('patterns')
    def validate_patterns(cls, v):
        # Validate glob patterns
        for pattern in v:
            try:
                re.compile(pattern.replace('*', '.*'))
            except re.error:
                raise ValueError(f"Invalid pattern: {pattern}")
        return v

class SyncConfig(BaseModel):
    strategy: str = "fetch_all"  # fetch_all, fetch_recent, manual
    interval: str = "6h"         # 1h, 30m, 1d format
    recent_days: Optional[int] = None
    prune_deleted: bool = True
    
class StorageConfig(BaseModel):
    type: str = "bare"           # bare, full
    max_size: Optional[str] = None  # "5GB", "1TB" format
    retention_days: int = 365
    
class RepositoryConfig(BaseModel):
    name: str
    source: Dict[str, Any]       # URL, type (no auth here)
    remotes: List[RemoteConfig] = Field(default_factory=list)
    branches: BranchConfig = Field(default_factory=BranchConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    auth_key: Optional[str] = None  # Reference to auth.yaml entry
    
    @property
    def url_path(self) -> str:
        """Generate URL-based path from source URL"""
        return url_to_path(self.source['url'])
    
    @property 
    def repo_path(self) -> Path:
        """Get full path to git repository (cache)"""
        from ..config import get_cache_dir
        return get_cache_dir() / "repos" / self.url_path
        
    @property
    def state_path(self) -> Path:
        """Get full path to state directory"""
        from ..config import get_state_dir
        return get_state_dir() / self.url_path

class GlobalConfig(BaseModel):
    version: str = "1.0"
    repositories: List[RepositoryConfig]
    settings: Dict[str, Any] = Field(default_factory=dict)

class ConfigManager:
    """Manages repository configuration loading and validation"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        # XDG Base Directory compliant paths
        self.config_dir = config_dir or self._get_config_dir()
        self.repositories_file = self.config_dir / "repositories.yaml"
        self.global_settings_file = self.config_dir / "global-settings.yaml"
        self.auth_file = self.config_dir / "auth.yaml"
        
    def _get_config_dir(self) -> Path:
        """Get XDG_CONFIG_HOME compliant config directory"""
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            return Path(xdg_config) / "ca-bhfuil"
        return Path.home() / ".config" / "ca-bhfuil"
    
    def load_configuration(self) -> GlobalConfig:
        """Load and validate all configuration files"""
        
    def get_repository_config(self, url_path: str) -> Optional[RepositoryConfig]:
        """Get configuration for specific repository by URL path"""
        
    def get_repository_config_by_url(self, url: str) -> Optional[RepositoryConfig]:
        """Get configuration for specific repository by source URL"""
        
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of errors"""
        
    def generate_default_config(self) -> None:
        """Generate default configuration files"""
        
    def load_auth_config(self) -> Dict[str, AuthMethod]:
        """Load authentication configuration from auth.yaml"""
        
    def get_auth_method(self, auth_key: str) -> Optional[AuthMethod]:
        """Get authentication method by key"""
        
    def validate_auth_config(self) -> List[str]:
        """Validate authentication configuration"""
```

### 3. Repository Manager (`core/git/manager.py`)

**Purpose**: High-level repository management operations

```python
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio

class RepositoryManager:
    """High-level repository management operations"""
    
    def __init__(self, 
                 config_manager: ConfigManager,
                 registry: RepositoryRegistry,
                 storage_root: Path):
        self.config_manager = config_manager
        self.registry = registry
        self.storage_root = storage_root
        self.cloner = RepositoryCloner(storage_root)
        self.syncer = RepositorySyncer()
    
    async def initialize_repositories(self) -> Dict[str, Any]:
        """Initialize all repositories from configuration"""
        
    async def sync_repository(self, url_path: str, 
                             force: bool = False) -> Dict[str, Any]:
        """Sync a specific repository with its remotes"""
        
    async def sync_repository_by_url(self, url: str,
                                    force: bool = False) -> Dict[str, Any]:
        """Sync a specific repository by source URL"""
        
    async def sync_all_repositories(self, 
                                   parallel: bool = True) -> Dict[str, List[Any]]:
        """Sync all configured repositories"""
        
    def get_repository_status(self, url_path: str) -> Dict[str, Any]:
        """Get detailed status of a repository"""
        
    def cleanup_repositories(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up repositories based on retention policies"""
        
    def add_repository(self, config: RepositoryConfig) -> str:
        """Add a new repository to management"""
        
    def remove_repository(self, url_path: str, 
                         delete_local: bool = False) -> bool:
        """Remove repository from management"""
```

### 4. Repository Cloner (`core/git/cloner.py`)

**Purpose**: Handle initial repository cloning with optimization

```python
import pygit2
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import asyncio

class CloneProgress:
    """Track cloning progress"""
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.total_objects = 0
        self.received_objects = 0
        self.received_bytes = 0
        
    def __call__(self, stats):
        self.total_objects = stats.total_objects
        self.received_objects = stats.received_objects
        self.received_bytes = stats.received_bytes
        if self.callback:
            self.callback(self)

class RepositoryCloner:
    """Handles repository cloning operations"""
    
    def __init__(self, cache_dir: Optional[Path] = None, state_dir: Optional[Path] = None):
        # XDG Base Directory compliant paths
        self.cache_dir = cache_dir or self._get_cache_dir()
        self.state_dir = state_dir or self._get_state_dir()
        
        self.repos_dir = self.cache_dir / "repos"
        self.temp_dir = self.cache_dir / "temp" / "clone-staging"
        
        # Create directory structure
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_dir(self) -> Path:
        """Get XDG_CACHE_HOME compliant cache directory"""
        xdg_cache = os.environ.get('XDG_CACHE_HOME')
        if xdg_cache:
            return Path(xdg_cache) / "ca-bhfuil"
        return Path.home() / ".cache" / "ca-bhfuil"
        
    def _get_state_dir(self) -> Path:
        """Get XDG_STATE_HOME compliant state directory"""
        xdg_state = os.environ.get('XDG_STATE_HOME')
        if xdg_state:
            return Path(xdg_state) / "ca-bhfuil"
        return Path.home() / ".local" / "state" / "ca-bhfuil"
    
    async def clone_repository(self, 
                              config: RepositoryConfig,
                              progress_callback: Optional[Callable] = None) -> Path:
        """Clone repository with progress tracking"""
        
    def _prepare_clone_options(self, config: RepositoryConfig) -> Dict[str, Any]:
        """Prepare pygit2 clone options from configuration"""
        
    def _setup_authentication(self, config: RepositoryConfig) -> Optional[Any]:
        """Setup authentication for cloning"""
        
    async def _clone_with_timeout(self, 
                                 url: str, 
                                 path: Path,
                                 options: Dict[str, Any],
                                 timeout: int = 1800) -> None:
        """Clone with timeout and error handling"""
```

### 5. Repository Syncer (`core/git/syncer.py`)

**Purpose**: Handle ongoing synchronization with remotes

```python
import pygit2
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SyncResult:
    """Results from a sync operation"""
    def __init__(self):
        self.success = False
        self.updated_refs: List[str] = []
        self.new_commits = 0
        self.deleted_refs: List[str] = []
        self.errors: List[str] = []
        self.duration: float = 0.0

class RepositorySyncer:
    """Handles repository synchronization"""
    
    def __init__(self):
        pass
    
    async def sync_repository(self, 
                             repo_path: Path,
                             config: RepositoryConfig) -> SyncResult:
        """Sync repository based on its configuration"""
        
    def _sync_fetch_all(self, repo: pygit2.Repository, 
                       config: RepositoryConfig) -> SyncResult:
        """Fetch all refs from all remotes"""
        
    def _sync_fetch_recent(self, repo: pygit2.Repository,
                          config: RepositoryConfig) -> SyncResult:
        """Fetch only recent commits"""
        
    def _filter_branches(self, branches: List[str], 
                        config: BranchConfig) -> List[str]:
        """Filter branches based on patterns"""
        
    def _update_remotes(self, repo: pygit2.Repository,
                       remotes: List[RemoteConfig]) -> None:
        """Update remote configurations"""
```

## Implementation Tasks

### Phase 1: Configuration System (Priority 1)
**Timeline**: 1-2 weeks

- [ ] **Task 1.1**: Implement configuration models with Pydantic
  - Repository, Remote, Branch, Sync, Storage configurations
  - Validation and error handling
  - YAML loading and parsing

- [ ] **Task 1.2**: Create ConfigManager class
  - Load and validate configurations
  - Generate default configurations
  - Configuration change detection

- [ ] **Task 1.3**: Add configuration CLI commands
  - `ca-bhfuil config init` - Generate default config
  - `ca-bhfuil config validate` - Validate current config
  - `ca-bhfuil config show` - Show current configuration

### Phase 2: Repository Registry (Priority 1)
**Timeline**: 1 week

- [ ] **Task 2.1**: Implement SQLite-based repository registry
  - Database schema for repository metadata
  - CRUD operations for repository entries
  - Status tracking and statistics

- [ ] **Task 2.2**: Create RepositoryRegistry class
  - Register/unregister repositories
  - Query and list operations
  - Orphan detection and cleanup

### Phase 3: Repository Cloning (Priority 2)
**Timeline**: 2 weeks

- [ ] **Task 3.1**: Implement RepositoryCloner
  - pygit2-based cloning with progress tracking
  - Authentication handling (token, SSH key)
  - Timeout and error handling

- [ ] **Task 3.2**: Add clone optimization
  - Bare repository cloning for analysis
  - Shallow cloning options
  - Parallel cloning support

- [ ] **Task 3.3**: Create clone CLI commands
  - `ca-bhfuil repo clone <url>` - Clone specific repository by URL
  - `ca-bhfuil repo clone <name>` - Clone specific repository by name
  - `ca-bhfuil repo clone-all` - Clone all configured repositories

### Phase 4: Repository Synchronization (Priority 2)  
**Timeline**: 2-3 weeks

- [ ] **Task 4.1**: Implement RepositorySyncer
  - Fetch strategies (all, recent, manual)
  - Remote management and updates
  - Branch filtering and pruning

- [ ] **Task 4.2**: Add sync scheduling
  - Periodic sync based on intervals
  - Background sync processes
  - Conflict detection and resolution

- [ ] **Task 4.3**: Create sync CLI commands
  - `ca-bhfuil repo sync <url>` - Sync specific repository by URL
  - `ca-bhfuil repo sync <name>` - Sync specific repository by name  
  - `ca-bhfuil repo sync-all` - Sync all repositories
  - `ca-bhfuil repo status <name|url>` - Show sync status for specific repo
  - `ca-bhfuil repo status` - Show status for all repositories

### Phase 5: Repository Management (Priority 3)
**Timeline**: 1-2 weeks

- [ ] **Task 5.1**: Implement high-level RepositoryManager
  - Repository lifecycle management
  - Bulk operations and status reporting
  - Storage cleanup and maintenance

- [ ] **Task 5.2**: Add management CLI commands
  - `ca-bhfuil repo add <url>` - Add new repository
  - `ca-bhfuil repo remove <name|url>` - Remove repository  
  - `ca-bhfuil repo list` - List all repositories
  - `ca-bhfuil repo info <name|url>` - Show detailed repository information
  - `ca-bhfuil repo cleanup` - Clean up storage
  - `ca-bhfuil repo paths <name|url>` - Show repository and metadata paths

### Phase 6: Integration & Testing (Priority 3)
**Timeline**: 1 week

- [ ] **Task 6.1**: Integration with existing codebase
  - Update CommitInfo models for repository context
  - Integrate with cache and storage systems
  - Update CLI framework

- [ ] **Task 6.2**: Comprehensive testing
  - Unit tests for all components
  - Integration tests with real repositories
  - Performance testing with large repositories

## Success Criteria

### Functional Requirements
- [ ] Clone multiple repositories from configuration
- [ ] Sync repositories with configurable strategies
- [ ] Filter branches based on patterns
- [ ] Manage authentication for private repositories
- [ ] Track repository status and statistics
- [ ] Clean up storage based on retention policies

### Performance Requirements
- [ ] Clone Linux kernel repository in <10 minutes
- [ ] Sync 10 repositories in parallel efficiently
- [ ] Handle repositories with 100k+ commits
- [ ] Disk usage stays within configured limits

### Usability Requirements
- [ ] Simple YAML configuration format
- [ ] Clear CLI commands for all operations
- [ ] Progress reporting for long operations
- [ ] Helpful error messages and validation

## Risk Mitigation

### Storage Management
- **Risk**: Unlimited disk usage growth
- **Mitigation**: Size limits, cleanup policies, monitoring

### Network Dependencies
- **Risk**: Sync failures due to network issues
- **Mitigation**: Retry logic, timeout handling, offline operation

### Authentication Complexity
- **Risk**: Complex credential management
- **Mitigation**: Standard environment variables, system credential helpers

### Performance Degradation
- **Risk**: Slow operations on large repositories  
- **Mitigation**: pygit2 optimization, parallel operations, progress tracking

## URL-to-Path Conversion Utilities

The new design requires robust URL parsing and path conversion utilities:

```python
import re
from urllib.parse import urlparse
from pathlib import Path
from typing import Tuple

def url_to_path(url: str) -> str:
    """Convert repository URL to filesystem path"""
    # Handle different URL formats
    if url.startswith('git@'):
        # SSH format: git@github.com:owner/repo.git
        match = re.match(r'git@([^:]+):(.+?)(?:\.git)?$', url)
        if match:
            host, path = match.groups()
            return f"{host}/{path}"
    else:
        # HTTP/HTTPS format
        parsed = urlparse(url)
        if parsed.scheme in ('http', 'https'):
            # Remove leading slash and .git suffix
            path = parsed.path.lstrip('/').removesuffix('.git')
            return f"{parsed.netloc}/{path}"
    
    raise ValueError(f"Unsupported URL format: {url}")

def sanitize_path_component(component: str) -> str:
    """Sanitize a single path component for filesystem safety"""
    # Replace invalid characters with safe alternatives
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        component = component.replace(char, '_')
    
    # Handle reserved Windows names
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    if component.upper() in reserved:
        component = f"{component}_"
    
    return component

def ensure_path_length(path: Path, max_length: int = 260) -> Path:
    """Ensure path doesn't exceed maximum length limits"""
    if len(str(path)) <= max_length:
        return path
    
    # Truncate path components while preserving structure
    parts = path.parts
    truncated_parts = []
    
    for part in parts:
        if len(part) > 50:  # Truncate long components
            truncated_parts.append(part[:47] + "...")
        else:
            truncated_parts.append(part)
    
    return Path(*truncated_parts)

def get_repo_paths(url: str, cache_dir: Optional[Path] = None, state_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """Get both repository and state paths for a URL (XDG compliant)"""
    url_path = url_to_path(url)
    
    # Sanitize path components
    sanitized_parts = [sanitize_path_component(part) for part in url_path.split('/')]
    sanitized_path = '/'.join(sanitized_parts)
    
    # XDG Base Directory compliant paths
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    if state_dir is None:
        state_dir = _get_state_dir()
    
    repo_path = cache_dir / "repos" / sanitized_path
    state_path = state_dir / sanitized_path
    
    # Ensure path length limits
    repo_path = ensure_path_length(repo_path)
    state_path = ensure_path_length(state_path)
    
    return repo_path, state_path

def _get_cache_dir() -> Path:
    """Get XDG_CACHE_HOME compliant cache directory"""
    xdg_cache = os.environ.get('XDG_CACHE_HOME')
    if xdg_cache:
        return Path(xdg_cache) / "ca-bhfuil"
    return Path.home() / ".cache" / "ca-bhfuil"

def _get_state_dir() -> Path:
    """Get XDG_STATE_HOME compliant state directory"""
    xdg_state = os.environ.get('XDG_STATE_HOME')
    if xdg_state:
        return Path(xdg_state) / "ca-bhfuil"
    return Path.home() / ".local" / "state" / "ca-bhfuil"

def _get_config_dir() -> Path:
    """Get XDG_CONFIG_HOME compliant config directory"""
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return Path(xdg_config) / "ca-bhfuil"
    return Path.home() / ".config" / "ca-bhfuil"
```

## Benefits of the Refined Design

### Simplified Architecture
- **No slug generation complexity**: Direct URL-to-path mapping
- **Intuitive organization**: Follows familiar URL hierarchy
- **Collision-free**: Each unique URL gets unique path
- **Multi-source friendly**: Same project from different hosts naturally separated

### Better Separation of Concerns
- **Clean data separation**: Git repositories vs. metadata clearly divided
- **Independent backup**: Can backup/sync repos and metadata separately
- **Selective cleanup**: Can clean metadata without affecting git repos
- **Cross-platform compatibility**: Handles Windows path limitations

### Enhanced Usability
- **Predictable paths**: Users can find repositories by URL structure
- **Better CLI experience**: Can use URLs or names interchangeably
- **Improved debugging**: Clear relationship between configuration and storage
- **Future-proof**: Easily extensible for new git hosting platforms

## Lock File Management

To handle concurrent operations safely, each repository metadata directory includes lock files:

```python
from pathlib import Path
import fcntl
import time
from contextlib import contextmanager
from typing import Generator

class RepositoryLock:
    """Manages lock files for repository operations"""
    
    def __init__(self, repo_memory_path: Path):
        self.lock_dir = repo_memory_path / ".locks"
        self.lock_dir.mkdir(exist_ok=True)
        
    @contextmanager
    def sync_lock(self, timeout: int = 300) -> Generator[None, None, None]:
        """Acquire sync lock with timeout"""
        lock_file = self.lock_dir / "sync.lock"
        self._acquire_lock(lock_file, timeout)
        try:
            yield
        finally:
            self._release_lock(lock_file)
    
    @contextmanager
    def analysis_lock(self, timeout: int = 60) -> Generator[None, None, None]:
        """Acquire analysis lock with timeout"""
        lock_file = self.lock_dir / "analysis.lock"
        self._acquire_lock(lock_file, timeout)
        try:
            yield
        finally:
            self._release_lock(lock_file)
            
    def _acquire_lock(self, lock_file: Path, timeout: int) -> None:
        """Acquire file lock with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                fd = open(lock_file, 'w')
                fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fd.write(f"{os.getpid()}\n{time.time()}\n")
                fd.flush()
                return fd
            except (IOError, OSError):
                time.sleep(0.1)
        raise TimeoutError(f"Could not acquire lock {lock_file} within {timeout}s")
        
    def _release_lock(self, fd) -> None:
        """Release file lock"""
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        fd.close()
```

## SQLite Schema Versioning

All SQLite databases include schema versioning for future migrations:

```python
import sqlite3
from pathlib import Path
from typing import Dict, Any

class SchemaManager:
    """Manages SQLite schema versioning and migrations"""
    
    CURRENT_VERSION = 1
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        
    def initialize_schema(self) -> None:
        """Initialize database with schema versioning"""
        with sqlite3.connect(self.db_path) as conn:
            # Create schema_info table first
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_info (
                    version INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ca_bhfuil_version TEXT NOT NULL,
                    migration_log TEXT
                )
            """)
            
            # Check current schema version
            cursor = conn.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
            current_version = cursor.fetchone()
            
            if not current_version:
                # Fresh database
                self._create_initial_schema(conn)
                conn.execute("""
                    INSERT INTO schema_info (version, ca_bhfuil_version) 
                    VALUES (?, ?)
                """, (self.CURRENT_VERSION, "0.1.0"))
            elif current_version[0] < self.CURRENT_VERSION:
                # Need migration
                self._migrate_schema(conn, current_version[0])
                
    def _create_initial_schema(self, conn: sqlite3.Connection) -> None:
        """Create initial database schema"""
        # Repository-specific schema creation
        pass
        
    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int) -> None:
        """Migrate schema from old version to current"""
        migrations = {
            # version: migration_function
        }
        
        for version in range(from_version + 1, self.CURRENT_VERSION + 1):
            if version in migrations:
                migrations[version](conn)
                conn.execute("""
                    INSERT INTO schema_info (version, ca_bhfuil_version, migration_log) 
                    VALUES (?, ?, ?)
                """, (version, "0.1.0", f"Migrated from {version-1} to {version}"))
```

## Updated CLI Commands

Final CLI pattern following `ca-bhfuil <resource> <operation> [--options] [args]`:

```bash
# Repository Management
ca-bhfuil repo clone <name|url>              # Clone specific repository
ca-bhfuil repo clone --all                   # Clone all configured repositories
ca-bhfuil repo sync <name|url>               # Sync specific repository  
ca-bhfuil repo sync --all                    # Sync all repositories
ca-bhfuil repo add <url> [--name=<name>]     # Add new repository
ca-bhfuil repo remove <name|url>             # Remove repository
ca-bhfuil repo list [--status=<filter>]      # List repositories
ca-bhfuil repo status [<name|url>]           # Show sync status
ca-bhfuil repo info <name|url>               # Detailed repository info
ca-bhfuil repo cleanup [--dry-run]           # Clean up storage
ca-bhfuil repo paths <name|url>              # Show file paths

# Configuration Management  
ca-bhfuil config init                        # Initialize default config
ca-bhfuil config validate                    # Validate current config
ca-bhfuil config show [--section=<name>]     # Show configuration
ca-bhfuil config auth init                   # Initialize auth.yaml template
ca-bhfuil config auth validate               # Validate auth configuration

# Search and Analysis (Future)
ca-bhfuil search <pattern> [--repo=<name>]   # Search commits
ca-bhfuil analyze <sha> [--context]          # Analyze specific commit

# System Operations
ca-bhfuil health check                       # System health check
ca-bhfuil health repair                      # Attempt automatic repairs
ca-bhfuil version                            # Show version information
```

## Security Best Practices

### Git Configuration
Recommended `.gitignore` additions for ca-bhfuil projects:

```gitignore
# Ca-Bhfuil Authentication (if config is in project directory)
auth.yaml
auth.yml

# Ca-Bhfuil Local Overrides
.ca-bhfuil-local.yaml
.ca-bhfuil-override.yaml

# Lock files (if using project-local state)
*.lock
.locks/

# Local development
.env.local
.ca-bhfuil.env
```

### SSH Key Management
1. **Generate ED25519 keys** (preferred over RSA):
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   ```

2. **Use SSH agent** for passphrase management:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

3. **Configure SSH for multiple keys**:
   ```ssh-config
   # ~/.ssh/config
   Host github.com
     HostName github.com
     User git
     IdentityFile ~/.ssh/id_ed25519
     
   Host corp-gitlab
     HostName gitlab.corp.com
     User git
     IdentityFile ~/.ssh/id_rsa_corp
   ```

## Linux Best Practices Compliance

### File Permissions and Security

```python
# Recommended file permissions for ca-bhfuil directories
PERMISSIONS = {
    'config_dir': 0o700,        # rwx------ (user only)
    'auth_file': 0o600,         # rw------- (user only, contains secrets)
    'config_files': 0o644,      # rw-r--r-- (readable by others)
    'state_dir': 0o700,         # rwx------ (user only)
    'cache_dir': 0o755,         # rwxr-xr-x (others can read)
    'lock_files': 0o644,        # rw-r--r-- (readable for monitoring)
}

def setup_secure_directories():
    """Set up directories with appropriate permissions"""
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
```

### Systemd Integration (Optional)

For users wanting systemd integration:

```ini
# ~/.config/systemd/user/ca-bhfuil-sync.service
[Unit]
Description=Ca-Bhfuil Repository Sync
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ca-bhfuil repo sync --all
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/state/ca-bhfuil %h/.cache/ca-bhfuil

[Install]
WantedBy=default.target
```

```ini
# ~/.config/systemd/user/ca-bhfuil-sync.timer
[Unit]
Description=Ca-Bhfuil Repository Sync Timer
Requires=ca-bhfuil-sync.service

[Timer]
OnBootSec=15min
OnUnitActiveSec=6h
Persistent=true

[Install]
WantedBy=timers.target
```

### AppArmor Profile (Optional)

For enhanced security on Ubuntu/Debian systems:

```apparmor
# /etc/apparmor.d/usr.local.bin.ca-bhfuil
#include <tunables/global>

/usr/local/bin/ca-bhfuil {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/ssl_certs>
  
  # Network access for git operations
  network inet stream,
  network inet6 stream,
  
  # Git binary access
  /usr/bin/git ix,
  
  # SSH access for git operations
  /usr/bin/ssh ix,
  owner @{HOME}/.ssh/ r,
  owner @{HOME}/.ssh/* r,
  
  # Ca-Bhfuil directories
  owner @{HOME}/.config/ca-bhfuil/ rw,
  owner @{HOME}/.config/ca-bhfuil/** rw,
  owner @{HOME}/.local/state/ca-bhfuil/ rw,
  owner @{HOME}/.local/state/ca-bhfuil/** rw,
  owner @{HOME}/.cache/ca-bhfuil/ rw,
  owner @{HOME}/.cache/ca-bhfuil/** rw,
  
  # Temporary files
  /tmp/ r,
  /tmp/ca-bhfuil-*/ rw,
  /tmp/ca-bhfuil-*/** rw,
}
```

### Environment Variables

Recommended environment variables for ca-bhfuil:

```bash
# ~/.profile or ~/.bashrc

# XDG Base Directory compliance
export XDG_CONFIG_HOME="${HOME}/.config"
export XDG_STATE_HOME="${HOME}/.local/state" 
export XDG_CACHE_HOME="${HOME}/.cache"

# Ca-Bhfuil specific
export CA_BHFUIL_LOG_LEVEL="INFO"          # DEBUG, INFO, WARNING, ERROR
export CA_BHFUIL_MAX_PARALLEL_SYNC="3"     # Override config default
export CA_BHFUIL_SSH_KEY_PATH="${HOME}/.ssh/id_ed25519"  # Default SSH key

# Git configuration for ca-bhfuil
export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new"
export GIT_TERMINAL_PROMPT="0"             # Disable interactive prompts
```

### Logging and Monitoring

Integration with system logging:

```python
import syslog
from loguru import logger

# Configure loguru to send to syslog for system integration
def setup_system_logging():
    """Configure logging for system integration"""
    
    # Remove default handler
    logger.remove()
    
    # Add file handler (user logs)
    log_file = get_state_dir() / "ca-bhfuil.log"
    logger.add(log_file, rotation="10 MB", retention="30 days", level="INFO")
    
    # Add syslog handler for system integration
    logger.add(
        lambda msg: syslog.syslog(syslog.LOG_INFO, msg),
        format="ca-bhfuil: {message}",
        level="WARNING"
    )
    
    # Add console handler for interactive use
    logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | {message}")
```

### Resource Limits

Respect system resource limits:

```python
import resource

def check_system_resources():
    """Check and respect system resource limits"""
    
    # Check available disk space
    cache_dir = get_cache_dir()
    state_dir = get_state_dir()
    
    cache_stat = os.statvfs(cache_dir)
    cache_free = cache_stat.f_bavail * cache_stat.f_frsize
    
    state_stat = os.statvfs(state_dir) 
    state_free = state_stat.f_bavail * state_stat.f_frsize
    
    # Warn if low on space
    if cache_free < 1_000_000_000:  # Less than 1GB
        logger.warning(f"Low cache disk space: {cache_free / 1_000_000_000:.1f}GB")
        
    if state_free < 100_000_000:    # Less than 100MB
        logger.warning(f"Low state disk space: {state_free / 1_000_000:.1f}MB")
    
    # Respect memory limits
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)
    if soft_limit != resource.RLIM_INFINITY:
        logger.info(f"Memory limit: {soft_limit / 1_000_000:.0f}MB")
```

This XDG-compliant design provides a more intuitive and maintainable foundation for managing multiple git repositories locally while maintaining performance, security, and flexibility for Ca-Bhfuil's analysis needs. It follows Linux best practices and integrates well with system tools and security frameworks.
