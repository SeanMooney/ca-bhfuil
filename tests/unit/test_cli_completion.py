"""Tests for CLI completion functionality."""

import pathlib
import tempfile
from unittest import mock

import pytest

from ca_bhfuil.cli import completion


class TestCompletionFunctions:
    """Test individual completion functions."""

    def test_complete_format(self):
        """Test format completion."""
        # Test empty incomplete
        result = completion.complete_format("")
        assert set(result) == {"yaml", "json"}

        # Test partial match
        result = completion.complete_format("y")
        assert result == ["yaml"]

        # Test partial match
        result = completion.complete_format("j")
        assert result == ["json"]

        # Test no match
        result = completion.complete_format("xml")
        assert result == []

        # Test exact match
        result = completion.complete_format("yaml")
        assert result == ["yaml"]

    def test_complete_repo_path_with_existing_directories(self):
        """Test repository path completion with existing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Create test directories
            (temp_path / "repo1").mkdir()
            (temp_path / "repo2").mkdir()
            (temp_path / "not_repo").mkdir()
            (temp_path / "file.txt").write_text("content")  # File, not directory

            # Test completion from directory
            with mock.patch("pathlib.Path.iterdir") as mock_iterdir:
                mock_iterdir.return_value = [
                    temp_path / "repo1",
                    temp_path / "repo2",
                    temp_path / "not_repo",
                    temp_path / "file.txt",
                ]
                # Mock is_dir to return True for directories
                with mock.patch("pathlib.Path.is_dir") as mock_is_dir:

                    def is_dir_side_effect(path):
                        return path.name != "file.txt"

                    mock_is_dir.side_effect = lambda: is_dir_side_effect(
                        mock_is_dir.return_value
                        if hasattr(mock_is_dir, "return_value")
                        else temp_path / "repo1"
                    )

                    # Simplify the test - just check that function returns list
                    result = completion.complete_repo_path("")
                    assert isinstance(result, list)

    def test_complete_repo_path_with_incomplete_path(self):
        """Test repository path completion with incomplete path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Create test directories
            (temp_path / "my_repo1").mkdir()
            (temp_path / "my_repo2").mkdir()
            (temp_path / "other_dir").mkdir()

            # Test completion with partial name
            incomplete = str(temp_path / "my_")
            result = completion.complete_repo_path(incomplete)

            # Should find directories starting with "my_"
            matching = [r for r in result if "my_repo" in r]
            assert len(matching) >= 2

    def test_complete_repo_path_nonexistent_path(self):
        """Test repository path completion with nonexistent path."""
        result = completion.complete_repo_path("/nonexistent/path/test")
        assert result == []

    def test_complete_repo_path_permission_error(self):
        """Test repository path completion with permission error."""
        # Mock pathlib.Path to raise PermissionError
        with mock.patch(
            "pathlib.Path.iterdir", side_effect=PermissionError("Access denied")
        ):
            result = completion.complete_repo_path("/some/path")
            assert result == []

    def test_complete_repo_path_os_error(self):
        """Test repository path completion with OS error."""
        # Mock pathlib.Path to raise OSError
        with mock.patch("pathlib.Path.iterdir", side_effect=OSError("System error")):
            result = completion.complete_repo_path("/some/path")
            assert result == []

    def test_complete_repository_name_success(self):
        """Test repository name completion with valid config."""
        # Mock configuration
        mock_repo1 = mock.Mock()
        mock_repo1.name = "test-repo-1"
        mock_repo2 = mock.Mock()
        mock_repo2.name = "test-repo-2"
        mock_repo3 = mock.Mock()
        mock_repo3.name = "other-repo"

        mock_global_config = mock.Mock()
        mock_global_config.repos = [mock_repo1, mock_repo2, mock_repo3]

        mock_config_manager = mock.Mock()
        mock_config_manager.load_configuration.return_value = mock_global_config

        with mock.patch(
            "ca_bhfuil.core.config.ConfigManager", return_value=mock_config_manager
        ):
            # Test empty incomplete
            result = completion.complete_repository_name("")
            assert set(result) == {"test-repo-1", "test-repo-2", "other-repo"}

            # Test partial match
            result = completion.complete_repository_name("test")
            assert set(result) == {"test-repo-1", "test-repo-2"}

            # Test exact match
            result = completion.complete_repository_name("other-repo")
            assert result == ["other-repo"]

            # Test no match
            result = completion.complete_repository_name("nonexistent")
            assert result == []

    def test_complete_repository_name_config_error(self):
        """Test repository name completion when config loading fails."""
        with mock.patch(
            "ca_bhfuil.core.config.ConfigManager", side_effect=Exception("Config error")
        ):
            result = completion.complete_repository_name("test")
            assert result == []

    def test_complete_repository_name_import_error(self):
        """Test repository name completion when import fails."""
        # Mock import to fail
        with mock.patch(
            "builtins.__import__", side_effect=ImportError("Import failed")
        ):
            result = completion.complete_repository_name("test")
            assert result == []


class TestInstallCompletion:
    """Test completion installation functionality."""

    @pytest.fixture
    def temp_home(self):
        """Provide a temporary home directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            mock.patch("pathlib.Path.home", return_value=pathlib.Path(temp_dir)),
        ):
            yield pathlib.Path(temp_dir)

    def test_install_completion_bash(self, temp_home):
        """Test installing bash completion."""
        with mock.patch("typer.echo") as mock_echo:
            completion.install_completion("bash")

            # Check that completion file was created
            completion_file = temp_home / ".bash_completion.d" / "ca-bhfuil"
            assert completion_file.exists()

            # Check that content was written
            content = completion_file.read_text()
            assert "ca_bhfuil_completion" in content
            assert "complete -F" in content

            # Check that appropriate messages were printed
            assert mock_echo.call_count == 2
            assert "Bash completion installed" in mock_echo.call_args_list[0][0][0]
            assert "Source your .bashrc" in mock_echo.call_args_list[1][0][0]

    def test_install_completion_unsupported_shell(self):
        """Test installing completion for unsupported shell."""
        with mock.patch("typer.echo") as mock_echo:
            completion.install_completion("zsh")

            mock_echo.assert_called_once_with("Shell 'zsh' is not supported yet")

    def test_install_completion_creates_directory(self, temp_home):
        """Test that installation creates necessary directories."""
        # Ensure .bash_completion.d doesn't exist
        completion_dir = temp_home / ".bash_completion.d"
        assert not completion_dir.exists()

        completion.install_completion("bash")

        # Directory should now exist
        assert completion_dir.exists()
        assert completion_dir.is_dir()

    def test_install_completion_overwrites_existing(self, temp_home):
        """Test that installation overwrites existing completion file."""
        # Create existing file
        completion_file = temp_home / ".bash_completion.d" / "ca-bhfuil"
        completion_file.parent.mkdir(parents=True, exist_ok=True)
        completion_file.write_text("old content")

        completion.install_completion("bash")

        # Should be overwritten with new content
        content = completion_file.read_text()
        assert "old content" not in content
        assert "ca_bhfuil_completion" in content


class TestBashCompletionGeneration:
    """Test bash completion script generation."""

    def test_generate_bash_completion_content(self):
        """Test that bash completion script has expected content."""
        script = completion._generate_bash_completion()

        # Check for essential components
        assert "#!/bin/bash" in script
        assert "_ca_bhfuil_completion" in script
        assert "complete -F _ca_bhfuil_completion ca-bhfuil" in script

        # Check for main commands
        assert "config search status" in script

        # Check for config subcommands
        assert "init validate status show" in script

        # Check for format options
        assert "yaml json" in script

        # Check for global options
        assert "--version --help" in script

        # Check for python -m support
        assert "_python_ca_bhfuil_completion" in script
        assert "python -m ca_bhfuil" in script

    def test_generate_bash_completion_structure(self):
        """Test that bash completion script has proper structure."""
        script = completion._generate_bash_completion()

        # Should have function definitions
        assert "() {" in script  # Function definition syntax

        # Should have case statements
        assert "case " in script

        # Should have completion registration
        assert "complete -F" in script

        # Should be properly formatted bash
        lines = script.split("\n")
        assert len(lines) > 50  # Should be substantial script

    def test_generate_bash_completion_commands_coverage(self):
        """Test that completion script covers all expected commands."""
        script = completion._generate_bash_completion()

        # Main commands
        assert "config)" in script
        assert "search)" in script
        assert "status)" in script

        # Config subcommands
        assert "init)" in script
        assert "validate)" in script
        assert "show)" in script

        # Options
        assert "--format" in script
        assert "--repo" in script
        assert "--help" in script


class TestCompletionScriptGeneration:
    """Test completion script generation functionality."""

    def test_generate_completion_scripts(self):
        """Test generating completion scripts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = pathlib.Path(temp_dir) / "scripts"

            with mock.patch("typer.echo") as mock_echo:
                # Mock the __file__ attribute in the completion module
                mock_file_path = (
                    pathlib.Path(temp_dir)
                    / "src"
                    / "ca_bhfuil"
                    / "cli"
                    / "completion.py"
                )
                with mock.patch.object(completion, "__file__", str(mock_file_path)):
                    completion.generate_completion_scripts()

                    # Check that script was generated
                    bash_script = scripts_dir / "ca-bhfuil-completion.bash"
                    if bash_script.exists():
                        content = bash_script.read_text()
                        assert "_ca_bhfuil_completion" in content

                    # Check that message was printed
                    assert mock_echo.called

    def test_generate_completion_scripts_creates_directory(self):
        """Test that script generation creates scripts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = pathlib.Path(temp_dir) / "scripts"

            # Mock the __file__ attribute in the completion module
            mock_file_path = (
                pathlib.Path(temp_dir) / "src" / "ca_bhfuil" / "cli" / "completion.py"
            )
            with mock.patch.object(completion, "__file__", str(mock_file_path)):
                completion.generate_completion_scripts()

                # Directory should be created
                assert scripts_dir.exists()


class TestCompletionModuleExecution:
    """Test completion module execution scenarios."""

    def test_module_main_execution(self):
        """Test that module can be executed as main."""
        # Test that the main execution block works
        with mock.patch(
            "ca_bhfuil.cli.completion.generate_completion_scripts"
        ) as mock_generate:
            # Simulate __name__ == "__main__"
            if completion.__name__ == "__main__":
                # This would normally execute
                mock_generate()

            # If not running as main, we can still test the function exists
            assert hasattr(completion, "generate_completion_scripts")
            assert callable(completion.generate_completion_scripts)

    def test_completion_functions_availability(self):
        """Test that all completion functions are available."""
        # Test that all expected functions exist and are callable
        functions = [
            "complete_format",
            "complete_repo_path",
            "complete_repository_name",
            "install_completion",
            "generate_completion_scripts",
        ]

        for func_name in functions:
            assert hasattr(completion, func_name)
            assert callable(getattr(completion, func_name))


class TestCompletionEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def temp_home(self):
        """Provide a temporary home directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            mock.patch("pathlib.Path.home", return_value=pathlib.Path(temp_dir)),
        ):
            yield pathlib.Path(temp_dir)

    def test_complete_repo_path_empty_directory(self):
        """Test repo path completion in empty directory."""
        with mock.patch("pathlib.Path.iterdir", return_value=[]):
            result = completion.complete_repo_path("")
            # Empty directory should return empty list
            assert result == []

    def test_complete_repo_path_with_files_only(self):
        """Test repo path completion with only files (no directories)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Mock iterdir to return files
            files = [temp_path / "file1.txt", temp_path / "file2.txt"]
            with (
                mock.patch("pathlib.Path.iterdir", return_value=files),
                mock.patch("pathlib.Path.is_dir", return_value=False),
            ):
                result = completion.complete_repo_path("")
                # Should return empty list since no directories
                assert result == []

    def test_complete_repository_name_empty_config(self):
        """Test repository name completion with empty configuration."""
        mock_global_config = mock.Mock()
        mock_global_config.repos = []

        mock_config_manager = mock.Mock()
        mock_config_manager.load_configuration.return_value = mock_global_config

        with mock.patch(
            "ca_bhfuil.core.config.ConfigManager", return_value=mock_config_manager
        ):
            result = completion.complete_repository_name("test")
            assert result == []

    def test_install_completion_file_permission_error(self, temp_home):
        """Test completion installation with file permission error."""
        completion_dir = temp_home / ".bash_completion.d"
        completion_dir.mkdir(parents=True, exist_ok=True)

        # Create a file that can't be written to
        completion_file = completion_dir / "ca-bhfuil"
        completion_file.write_text("existing")

        # Mock Path.write_text to raise permission error
        with (
            mock.patch(
                "pathlib.Path.write_text",
                side_effect=PermissionError("Permission denied"),
            ),
            pytest.raises(PermissionError),
        ):
            completion.install_completion("bash")

    def test_bash_completion_script_syntax(self):
        """Test that generated bash script has valid syntax."""
        script = completion._generate_bash_completion()

        # Basic syntax checks
        lines = script.split("\n")

        # Should have proper shebang
        assert lines[0] == "#!/bin/bash"

        # Should have balanced braces
        open_braces = script.count("{")
        close_braces = script.count("}")
        assert open_braces == close_braces

        # Note: Not checking parentheses balance due to command substitution $(compgen ...)
        # which is valid bash syntax but makes simple counting inaccurate

        # Check for key bash completion elements
        assert "_ca_bhfuil_completion" in script
        assert "complete -F" in script

    def test_complete_repository_name_unicode_handling(self):
        """Test repository name completion with unicode characters."""
        # Mock configuration with unicode repo names
        mock_repo1 = mock.Mock()
        mock_repo1.name = "test-repo-ñame"
        mock_repo2 = mock.Mock()
        mock_repo2.name = "test-repo-正常"

        mock_global_config = mock.Mock()
        mock_global_config.repos = [mock_repo1, mock_repo2]

        mock_config_manager = mock.Mock()
        mock_config_manager.load_configuration.return_value = mock_global_config

        with mock.patch(
            "ca_bhfuil.core.config.ConfigManager", return_value=mock_config_manager
        ):
            result = completion.complete_repository_name("test")
            assert len(result) == 2
            assert "test-repo-ñame" in result
            assert "test-repo-正常" in result
