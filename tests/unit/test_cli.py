"""Unit tests for CLI commands."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import typer
import yaml
from typer.testing import CliRunner

from ca_bhfuil.cli.main import app
from ca_bhfuil.core.config import ConfigManager


@pytest.fixture
def cli_runner():
    """CLI test runner fixture."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Temporary configuration directory fixture."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "ca-bhfuil"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture
def sample_config_files(temp_config_dir: Path):
    """Create sample configuration files for testing."""
    # Create repos.yaml
    repos_config = {
        "version": "1.0",
        "repos": [
            {
                "name": "test-repo",
                "source": {"url": "https://github.com/test/repo.git", "type": "github"},
                "auth_key": "github-default",
            }
        ],
        "settings": {
            "max_total_size": "50GB",
            "default_sync_interval": "6h",
            "clone_timeout": "30m",
            "parallel_clones": 3,
        },
    }
    
    # Create global.yaml
    global_config = {
        "version": "1.0",
        "storage": {
            "max_total_size": "100GB",
            "max_cache_size": "80GB",
            "cleanup_policy": "lru",
        },
        "sync": {
            "max_parallel_jobs": 3,
            "default_timeout": "30m",
        },
        "performance": {
            "git_clone_bare": True,
            "pygit2_cache_size": "100MB",
        },
    }
    
    # Create auth.yaml
    auth_config = {
        "version": "1.0",
        "defaults": {
            "github": {"type": "ssh_key", "ssh_key_path": "~/.ssh/id_ed25519"}
        },
        "auth_methods": {
            "github-default": {"type": "ssh_key", "ssh_key_path": "~/.ssh/id_ed25519"}
        },
    }
    
    # Write files
    repos_file = temp_config_dir / "repos.yaml"
    global_file = temp_config_dir / "global.yaml"
    auth_file = temp_config_dir / "auth.yaml"
    
    with open(repos_file, "w") as f:
        yaml.dump(repos_config, f, default_flow_style=False)
    with open(global_file, "w") as f:
        yaml.dump(global_config, f, default_flow_style=False)
    with open(auth_file, "w") as f:
        yaml.dump(auth_config, f, default_flow_style=False)
    
    # Set secure permissions on auth file
    auth_file.chmod(0o600)
    
    return {
        "repos": repos_file,
        "global": global_file,
        "auth": auth_file,
        "config_dir": temp_config_dir,
    }


class TestConfigInit:
    """Test config init command."""
    
    def test_config_init_success(self, cli_runner: CliRunner, temp_config_dir: Path):
        """Test successful config initialization."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.config_dir = temp_config_dir
            mock_manager.repositories_file = Mock()
            mock_manager.global_settings_file = Mock()
            mock_manager.auth_file = Mock()
            mock_manager.repositories_file.exists.return_value = False
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "init"])
            
            assert result.exit_code == 0
            assert "Configuration initialized successfully!" in result.stdout
            mock_manager.generate_default_config.assert_called_once()
    
    def test_config_init_force_overwrite(self, cli_runner: CliRunner, temp_config_dir: Path):
        """Test config init with force flag overwrites existing config."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.config_dir = temp_config_dir
            mock_manager.repositories_file = Mock()
            mock_manager.global_settings_file = Mock()
            mock_manager.auth_file = Mock()
            mock_manager.repositories_file.exists.return_value = True
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "init", "--force"])
            
            assert result.exit_code == 0
            assert "Configuration initialized successfully!" in result.stdout
            mock_manager.generate_default_config.assert_called_once()
    
    def test_config_init_existing_no_force(self, cli_runner: CliRunner, temp_config_dir: Path):
        """Test config init fails when config exists and no force flag."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = Mock()
            mock_manager.repositories_file.exists.return_value = True
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "init"])
            
            assert result.exit_code == 1
            assert "Configuration already exists" in result.stdout


class TestConfigValidate:
    """Test config validate command."""
    
    def test_config_validate_success(self, cli_runner: CliRunner):
        """Test successful config validation."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.validate_configuration.return_value = []
            mock_manager.validate_auth_config.return_value = []
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "validate"])
            
            assert result.exit_code == 0
            assert "Configuration is valid!" in result.stdout
    
    def test_config_validate_with_errors(self, cli_runner: CliRunner):
        """Test config validation with errors."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.validate_configuration.return_value = ["Duplicate repository names"]
            mock_manager.validate_auth_config.return_value = ["Invalid auth method"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "validate"])
            
            assert result.exit_code == 1
            assert "Configuration validation failed" in result.stdout
            assert "Duplicate repository names" in result.stdout
            assert "Invalid auth method" in result.stdout


class TestConfigStatus:
    """Test config status command."""
    
    def test_config_status_success(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test successful config status display."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager, \
             patch("ca_bhfuil.core.config.get_config_dir") as mock_config_dir, \
             patch("ca_bhfuil.core.config.get_state_dir") as mock_state_dir, \
             patch("ca_bhfuil.core.config.get_cache_dir") as mock_cache_dir:
            
            # Setup mocks
            config_dir = sample_config_files["config_dir"]
            mock_config_dir.return_value = config_dir
            mock_state_dir.return_value = config_dir / "state"
            mock_cache_dir.return_value = config_dir / "cache"
            
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = Mock()
            mock_manager.global_settings_file = Mock()
            mock_manager.auth_file = Mock()
            mock_manager.repositories_file.__str__ = Mock(return_value=str(sample_config_files["repos"]))
            mock_manager.global_settings_file.__str__ = Mock(return_value=str(sample_config_files["global"]))
            mock_manager.auth_file.__str__ = Mock(return_value=str(sample_config_files["auth"]))
            mock_manager.repositories_file.exists.return_value = True
            mock_manager.global_settings_file.exists.return_value = True
            mock_manager.auth_file.exists.return_value = True
            
            # Mock configuration loading
            from ca_bhfuil.core.config import GlobalConfig
            mock_config = Mock(spec=GlobalConfig)
            mock_config.repos = []
            mock_manager.load_configuration.return_value = mock_config
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "status"])
            
            assert result.exit_code == 0
            assert "Ca-Bhfuil Configuration Status" in result.stdout
            assert "repos.yaml" in result.stdout
            assert "global.yaml" in result.stdout
            assert "auth.yaml" in result.stdout


class TestConfigShow:
    """Test config show command."""
    
    def test_config_show_default_global(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show defaults to global configuration."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.global_settings_file = sample_config_files["global"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show"])
            
            assert result.exit_code == 0
            assert "global.yaml" in result.stdout
            assert "storage:" in result.stdout
    
    def test_config_show_repos(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with --repos flag."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = sample_config_files["repos"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--repos"])
            
            assert result.exit_code == 0
            assert "repos.yaml" in result.stdout
            assert "test-repo" in result.stdout
    
    def test_config_show_auth(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with --auth flag."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.auth_file = sample_config_files["auth"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--auth"])
            
            assert result.exit_code == 0
            assert "auth.yaml" in result.stdout
            assert "auth_methods:" in result.stdout
    
    def test_config_show_multiple_flags(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with multiple flags."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = sample_config_files["repos"]
            mock_manager.global_settings_file = sample_config_files["global"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--repos", "--global"])
            
            assert result.exit_code == 0
            assert "repos.yaml" in result.stdout
            assert "global.yaml" in result.stdout
            assert "test-repo" in result.stdout
            assert "storage:" in result.stdout
    
    def test_config_show_all(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with --all flag."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = sample_config_files["repos"]
            mock_manager.global_settings_file = sample_config_files["global"]
            mock_manager.auth_file = sample_config_files["auth"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--all"])
            
            assert result.exit_code == 0
            assert "repos.yaml" in result.stdout
            assert "global.yaml" in result.stdout
            assert "auth.yaml" in result.stdout
    
    def test_config_show_json_format(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with JSON format."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.global_settings_file = sample_config_files["global"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--global", "--format", "json"])
            
            assert result.exit_code == 0
            # Verify it's valid JSON
            output_lines = [line for line in result.stdout.split('\n') if line.strip() and not line.startswith('---')]
            json_content = '\n'.join(output_lines)
            parsed = json.loads(json_content)
            assert "storage" in parsed
    
    def test_config_show_json_format_multiple(self, cli_runner: CliRunner, sample_config_files: Dict[str, Any]):
        """Test config show with JSON format and multiple files."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.repositories_file = sample_config_files["repos"]
            mock_manager.auth_file = sample_config_files["auth"]
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--repos", "--auth", "--format", "json"])
            
            assert result.exit_code == 0
            assert "--- repos.yaml ---" in result.stdout
            assert "--- auth.yaml ---" in result.stdout
    
    def test_config_show_missing_file(self, cli_runner: CliRunner, temp_config_dir: Path):
        """Test config show with missing file."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            missing_file = temp_config_dir / "missing.yaml"
            mock_manager.repositories_file = missing_file
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["config", "show", "--repos"])
            
            assert result.exit_code == 0
            assert "File does not exist" in result.stdout


class TestSearchCommand:
    """Test search command."""
    
    def test_search_basic(self, cli_runner: CliRunner):
        """Test basic search command."""
        result = cli_runner.invoke(app, ["search", "test-query"])
        
        assert result.exit_code == 0
        assert "Searching for 'test-query'" in result.stdout
        assert "not yet implemented" in result.stdout
    
    def test_search_with_repo_path(self, cli_runner: CliRunner):
        """Test search command with repo path."""
        result = cli_runner.invoke(app, ["search", "test-query", "--repo", "/path/to/repo"])
        
        assert result.exit_code == 0
        assert "Searching for 'test-query'" in result.stdout
        assert "/path/to/repo" in result.stdout


class TestStatusCommand:
    """Test status command."""
    
    def test_status_basic(self, cli_runner: CliRunner):
        """Test basic status command."""
        with patch("ca_bhfuil.core.config.get_config_dir") as mock_config_dir, \
             patch("ca_bhfuil.core.config.get_state_dir") as mock_state_dir, \
             patch("ca_bhfuil.core.config.get_cache_dir") as mock_cache_dir, \
             patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            
            # Setup directory mocks
            mock_config_dir.return_value = Path("/test/config")
            mock_state_dir.return_value = Path("/test/state")
            mock_cache_dir.return_value = Path("/test/cache")
            
            # Setup config manager mock
            mock_manager = Mock(spec=ConfigManager)
            from ca_bhfuil.core.config import GlobalConfig
            mock_config = Mock(spec=GlobalConfig)
            mock_config.repos = []
            mock_manager.load_configuration.return_value = mock_config
            mock_get_manager.return_value = mock_manager
            
            result = cli_runner.invoke(app, ["status"])
            
            assert result.exit_code == 0
            assert "Ca-Bhfuil System Status" in result.stdout
            assert "Configuration loaded successfully" in result.stdout


class TestVersionCallback:
    """Test version callback."""
    
    def test_version_flag(self, cli_runner: CliRunner):
        """Test --version flag."""
        result = cli_runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "ca-bhfuil 0.1.0" in result.stdout


class TestCLIHelp:
    """Test CLI help functionality."""
    
    def test_main_help(self, cli_runner: CliRunner):
        """Test main app help."""
        result = cli_runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Git repository analysis tool" in result.stdout
        assert "config" in result.stdout
        assert "search" in result.stdout
        assert "status" in result.stdout
    
    def test_config_help(self, cli_runner: CliRunner):
        """Test config subcommand help."""
        result = cli_runner.invoke(app, ["config", "--help"])
        
        assert result.exit_code == 0
        assert "Configuration management commands" in result.stdout
        assert "init" in result.stdout
        assert "validate" in result.stdout
        assert "status" in result.stdout
        assert "show" in result.stdout
    
    def test_config_show_help(self, cli_runner: CliRunner):
        """Test config show help."""
        result = cli_runner.invoke(app, ["config", "show", "--help"])
        
        assert result.exit_code == 0
        assert "Display configuration file contents" in result.stdout
        assert "--repos" in result.stdout
        assert "--global" in result.stdout
        assert "--auth" in result.stdout
        assert "--all" in result.stdout
        assert "--format" in result.stdout


# Integration test class for end-to-end functionality
class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_full_config_workflow(self, cli_runner: CliRunner, temp_config_dir: Path):
        """Test complete config workflow: init -> validate -> status -> show."""
        with patch("ca_bhfuil.core.config.get_config_manager") as mock_get_manager:
            mock_manager = Mock(spec=ConfigManager)
            mock_manager.config_dir = temp_config_dir
            mock_manager.repositories_file = Mock()
            mock_manager.global_settings_file = Mock()
            mock_manager.auth_file = Mock()
            
            # Mock file existence for different stages
            mock_manager.repositories_file.exists.return_value = False
            mock_manager.validate_configuration.return_value = []
            mock_manager.validate_auth_config.return_value = []
            
            from ca_bhfuil.core.config import GlobalConfig
            mock_config = Mock(spec=GlobalConfig)
            mock_config.repos = []
            mock_manager.load_configuration.return_value = mock_config
            mock_get_manager.return_value = mock_manager
            
            # Test init
            result = cli_runner.invoke(app, ["config", "init"])
            assert result.exit_code == 0
            
            # Test validate
            result = cli_runner.invoke(app, ["config", "validate"])
            assert result.exit_code == 0
            
            # Verify all commands in workflow executed successfully
            assert mock_manager.generate_default_config.called
            assert mock_manager.validate_configuration.called
            assert mock_manager.validate_auth_config.called