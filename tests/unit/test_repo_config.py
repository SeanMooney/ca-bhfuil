"""Tests for repository configuration management."""

import pathlib
import tempfile
from unittest import mock

import pytest
import yaml

from ca_bhfuil.core import config


class TestRepositoryConfig:
    """Test repository configuration model."""

    def test_basic_repository_config(self):
        """Test basic repository configuration creation."""
        repo_config = config.RepositoryConfig(
            name="test-repo",
            source={"url": "https://github.com/test/repo.git", "type": "git"},
        )

        assert repo_config.name == "test-repo"
        assert repo_config.source["url"] == "https://github.com/test/repo.git"
        assert repo_config.url_path == "github.com/test/repo"
        assert isinstance(repo_config.branches, config.BranchConfig)

    def test_repository_paths(self):
        """Test repository path generation."""
        repo_config = config.RepositoryConfig(
            name="test-repo",
            source={"url": "git@github.com:torvalds/linux.git", "type": "git"},
        )

        assert repo_config.url_path == "github.com/torvalds/linux"
        assert str(repo_config.repo_path).endswith(
            "cache/ca-bhfuil/repos/github.com/torvalds/linux"
        )
        assert str(repo_config.state_path).endswith(
            "state/ca-bhfuil/github.com/torvalds/linux"
        )

    def test_ssh_url_conversion(self):
        """Test SSH URL to path conversion."""
        repo_config = config.RepositoryConfig(
            name="ssh-repo",
            source={"url": "git@gitlab.example.com:group/project.git", "type": "git"},
        )

        assert repo_config.url_path == "gitlab.example.com/group/project"

    def test_complex_repository_config(self):
        """Test repository configuration with all options."""
        repo_config = config.RepositoryConfig(
            name="complex-repo",
            source={"url": "https://github.com/complex/repo.git", "type": "git"},
            auth_key="github-token",
            branches=config.BranchConfig(
                patterns=["main", "stable/*"],
                exclude_patterns=["experimental/*"],
                max_branches=50,
            ),
        )

        assert repo_config.auth_key == "github-token"
        assert repo_config.branches.patterns == ["main", "stable/*"]
        assert repo_config.branches.exclude_patterns == ["experimental/*"]
        assert repo_config.branches.max_branches == 50


class TestBranchConfig:
    """Test branch configuration validation."""

    def test_valid_patterns(self):
        """Test valid glob patterns."""
        branch_config = config.BranchConfig(patterns=["main", "stable/*", "feature-*"])
        assert branch_config.patterns == ["main", "stable/*", "feature-*"]

    def test_default_patterns(self):
        """Test default pattern behavior."""
        branch_config = config.BranchConfig()
        assert branch_config.patterns == ["*"]
        assert branch_config.exclude_patterns == []
        assert branch_config.max_branches == 100

    def test_invalid_patterns(self):
        """Test invalid pattern validation."""
        with pytest.raises(ValueError, match="Invalid pattern"):
            config.BranchConfig(patterns=["[invalid"])


class TestAuthMethod:
    """Test authentication method configuration."""

    def test_ssh_key_auth(self):
        """Test SSH key authentication configuration."""
        auth = config.AuthMethod(
            type="ssh_key",
            ssh_key_path="~/.ssh/id_ed25519",
            ssh_key_passphrase_env="SSH_PASSPHRASE",
        )

        assert auth.type == "ssh_key"
        assert auth.ssh_key_path == "~/.ssh/id_ed25519"
        assert auth.ssh_key_passphrase_env == "SSH_PASSPHRASE"

    def test_token_auth(self):
        """Test token authentication configuration."""
        auth = config.AuthMethod(
            type="token",
            token_env="GITHUB_TOKEN",
            username_env="GITHUB_USERNAME",
        )

        assert auth.type == "token"
        assert auth.token_env == "GITHUB_TOKEN"
        assert auth.username_env == "GITHUB_USERNAME"

    def test_default_auth_method(self):
        """Test default authentication method."""
        auth = config.AuthMethod()
        assert auth.type == "ssh_key"
        assert auth.ssh_key_path is None
        assert auth.token_env is None


class TestConfigManager:
    """Test configuration manager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Provide temporary configuration directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield pathlib.Path(tmp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Provide configuration manager with temp directory."""
        return config.ConfigManager(config_dir=temp_config_dir)

    def test_config_manager_initialization(self, config_manager, temp_config_dir):
        """Test configuration manager initialization."""
        assert config_manager.config_dir == temp_config_dir
        assert config_manager.repositories_file == temp_config_dir / "repos.yaml"
        assert config_manager.auth_file == temp_config_dir / "auth.yaml"

    def test_empty_configuration(self, config_manager):
        """Test loading empty configuration."""
        global_config = config_manager.load_configuration()
        assert isinstance(global_config, config.GlobalConfig)
        assert global_config.repos == []
        assert global_config.version == "1.0"

    def test_generate_default_config(self, config_manager):
        """Test default configuration generation."""
        config_manager.generate_default_config()

        # Check that files were created
        assert config_manager.repositories_file.exists()
        assert config_manager.global_settings_file.exists()
        assert config_manager.auth_file.exists()

        # Check auth file permissions
        assert oct(config_manager.auth_file.stat().st_mode)[-3:] == "600"

    def test_load_repository_configuration(self, config_manager):
        """Test loading repository configuration from file."""
        # Create test configuration
        test_config = {
            "version": "1.0",
            "repos": [
                {
                    "name": "test-repo",
                    "source": {
                        "url": "https://github.com/test/repo.git",
                        "type": "git",
                    },
                    "auth_key": "github-default",
                },
                {
                    "name": "another-repo",
                    "source": {"url": "git@gitlab.com:user/project.git", "type": "git"},
                },
            ],
        }

        with config_manager.repositories_file.open("w") as f:
            yaml.dump(test_config, f)

        # Load and validate
        global_config = config_manager.load_configuration()
        assert len(global_config.repos) == 2
        assert global_config.repos[0].name == "test-repo"
        assert global_config.repos[1].name == "another-repo"

    def test_get_repository_by_url_path(self, config_manager):
        """Test getting repository configuration by URL path."""
        # Create test configuration
        test_config = {
            "version": "1.0",
            "repos": [
                {
                    "name": "linux-kernel",
                    "source": {
                        "url": "git@github.com:torvalds/linux.git",
                        "type": "git",
                    },
                }
            ],
        }

        with config_manager.repositories_file.open("w") as f:
            yaml.dump(test_config, f)

        # Test retrieval by URL path
        repo_config = config_manager.get_repository_config("github.com/torvalds/linux")
        assert repo_config is not None
        assert repo_config.name == "linux-kernel"

    def test_get_repository_by_url(self, config_manager):
        """Test getting repository configuration by source URL."""
        # Create test configuration
        test_config = {
            "version": "1.0",
            "repos": [
                {
                    "name": "os-vif",
                    "source": {
                        "url": "https://opendev.org/openstack/os-vif.git",
                        "type": "git",
                    },
                }
            ],
        }

        with config_manager.repositories_file.open("w") as f:
            yaml.dump(test_config, f)

        # Test retrieval by source URL
        repo_config = config_manager.get_repository_config_by_url(
            "https://opendev.org/openstack/os-vif.git"
        )
        assert repo_config is not None
        assert repo_config.name == "os-vif"

    def test_configuration_validation(self, config_manager):
        """Test configuration validation."""
        # Create configuration with errors
        test_config = {
            "version": "1.0",
            "repos": [
                {
                    "name": "duplicate-name",
                    "source": {
                        "url": "https://github.com/test/repo1.git",
                        "type": "git",
                    },
                },
                {
                    "name": "duplicate-name",  # Duplicate name
                    "source": {
                        "url": "https://github.com/test/repo2.git",
                        "type": "git",
                    },
                },
                {
                    "name": "missing-auth",
                    "source": {
                        "url": "https://github.com/test/repo3.git",
                        "type": "git",
                    },
                    "auth_key": "nonexistent-key",  # Missing auth key
                },
            ],
        }

        with config_manager.repositories_file.open("w") as f:
            yaml.dump(test_config, f)

        errors = config_manager.validate_configuration()
        assert len(errors) >= 2  # At least duplicate names and missing auth
        assert any("duplicate" in error.lower() for error in errors)
        assert any("unknown auth key" in error.lower() for error in errors)

    def test_auth_configuration(self, config_manager):
        """Test authentication configuration loading."""
        # Create auth configuration
        auth_config = {
            "version": "1.0",
            "auth_methods": {
                "github-ssh": {
                    "type": "ssh_key",
                    "ssh_key_path": "~/.ssh/github_ed25519",
                },
                "gitlab-token": {
                    "type": "token",
                    "token_env": "GITLAB_TOKEN",
                },
            },
        }

        with config_manager.auth_file.open("w") as f:
            yaml.dump(auth_config, f)

        # Load and validate
        auth_methods = config_manager.load_auth_config()
        assert len(auth_methods) == 2
        assert "github-ssh" in auth_methods
        assert "gitlab-token" in auth_methods
        assert auth_methods["github-ssh"].type == "ssh_key"
        assert auth_methods["gitlab-token"].type == "token"

    def test_get_auth_method(self, config_manager):
        """Test getting specific authentication method."""
        # Create auth configuration
        auth_config = {
            "version": "1.0",
            "auth_methods": {
                "test-auth": {
                    "type": "ssh_key",
                    "ssh_key_path": "~/.ssh/test_key",
                }
            },
        }

        with config_manager.auth_file.open("w") as f:
            yaml.dump(auth_config, f)

        # Test retrieval
        auth_method = config_manager.get_auth_method("test-auth")
        assert auth_method is not None
        assert auth_method.type == "ssh_key"
        assert auth_method.ssh_key_path == "~/.ssh/test_key"

        # Test non-existent key
        assert config_manager.get_auth_method("nonexistent") is None


class TestXDGDirectories:
    """Test XDG Base Directory compliance."""

    def test_default_directories(self):
        """Test default XDG directory paths."""
        config_dir = config.get_config_dir()
        state_dir = config.get_state_dir()
        cache_dir = config.get_cache_dir()

        assert str(config_dir).endswith(".config/ca-bhfuil")
        assert str(state_dir).endswith(".local/state/ca-bhfuil")
        assert str(cache_dir).endswith(".cache/ca-bhfuil")

    @mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": "/custom/config"})
    def test_custom_xdg_config(self):
        """Test custom XDG_CONFIG_HOME."""
        config_dir = config.get_config_dir()
        assert str(config_dir) == "/custom/config/ca-bhfuil"

    @mock.patch.dict("os.environ", {"XDG_STATE_HOME": "/custom/state"})
    def test_custom_xdg_state(self):
        """Test custom XDG_STATE_HOME."""
        state_dir = config.get_state_dir()
        assert str(state_dir) == "/custom/state/ca-bhfuil"

    @mock.patch.dict("os.environ", {"XDG_CACHE_HOME": "/custom/cache"})
    def test_custom_xdg_cache(self):
        """Test custom XDG_CACHE_HOME."""
        cache_dir = config.get_cache_dir()
        assert str(cache_dir) == "/custom/cache/ca-bhfuil"


class TestRealWorldConfiguration:
    """Test configuration with real-world repository examples."""

    @pytest.fixture
    def real_world_config(self, tmp_path):
        """Create configuration with real-world repositories."""
        config_manager = config.ConfigManager(config_dir=tmp_path)

        # Create realistic configuration
        test_config = {
            "version": "1.0",
            "settings": {
                "max_total_size": "10GB",
                "default_sync_interval": "12h",
            },
            "repos": [
                {
                    "name": "os-vif",
                    "source": {
                        "url": "https://opendev.org/openstack/os-vif",
                        "type": "git",
                    },
                    "branches": {
                        "patterns": ["master", "stable/*"],
                        "exclude_patterns": ["experimental/*"],
                        "max_branches": 20,
                    },
                    "sync": {
                        "strategy": "fetch_recent",
                        "recent_days": 90,
                    },
                },
                {
                    "name": "hello-world",
                    "source": {
                        "url": "https://github.com/octocat/Hello-World",
                        "type": "git",
                    },
                    "auth_key": "github-default",
                },
            ],
        }

        with config_manager.repositories_file.open("w") as f:
            yaml.dump(test_config, f)

        # Create auth configuration
        auth_config = {
            "version": "1.0",
            "auth_methods": {
                "github-default": {
                    "type": "ssh_key",
                    "ssh_key_path": "~/.ssh/id_ed25519",
                }
            },
        }

        with config_manager.auth_file.open("w") as f:
            yaml.dump(auth_config, f)

        return config_manager

    def test_os_vif_repository_config(self, real_world_config):
        """Test os-vif repository configuration."""
        repo_config = real_world_config.get_repository_config_by_url(
            "https://opendev.org/openstack/os-vif"
        )

        assert repo_config is not None
        assert repo_config.name == "os-vif"
        assert repo_config.url_path == "opendev.org/openstack/os-vif"
        assert repo_config.branches.patterns == ["master", "stable/*"]
        assert repo_config.sync.strategy == "fetch_recent"
        assert repo_config.sync.recent_days == 90

    def test_hello_world_repository_config(self, real_world_config):
        """Test hello-world repository configuration."""
        repo_config = real_world_config.get_repository_config_by_url(
            "https://github.com/octocat/Hello-World"
        )

        assert repo_config is not None
        assert repo_config.name == "hello-world"
        assert repo_config.url_path == "github.com/octocat/Hello-World"
        assert repo_config.auth_key == "github-default"

    def test_configuration_validation_passes(self, real_world_config):
        """Test that real-world configuration validates successfully."""
        errors = real_world_config.validate_configuration()
        assert len(errors) == 0

    def test_repository_paths_generation(self, real_world_config):
        """Test repository path generation for real URLs."""
        global_config = real_world_config.load_configuration()

        for repo in global_config.repos:
            # Test that paths are generated correctly
            assert repo.url_path is not None
            assert "/" in repo.url_path  # Should have host/path format

            # Test that paths exist as properties
            repo_path = repo.repo_path
            state_path = repo.state_path

            assert "cache" in str(repo_path)
            assert "state" in str(state_path)
            assert repo.url_path in str(repo_path)
            assert repo.url_path in str(state_path)
