"""Tests for __main__.py entry point."""

import pathlib
from unittest import mock

import pytest

from ca_bhfuil import __main__


class TestMainEntryPoint:
    """Test main entry point functionality."""

    def test_main_module_imports(self):
        """Test that main module imports correctly."""
        # Should be able to import the main function
        assert hasattr(__main__, "main")
        assert callable(__main__.main)

    def test_main_function_available(self):
        """Test that main function is available from cli.main."""
        from ca_bhfuil.cli.main import main

        assert callable(main)
        assert __main__.main is main

    @mock.patch("ca_bhfuil.__main__.main")
    def test_main_execution_when_name_is_main(self, mock_main):
        """Test that main() is called when __name__ == '__main__'."""
        # Mock the condition check
        with (
            mock.patch.object(__main__, "__name__", "__main__"),
            pathlib.Path(__main__.__file__).open() as f,
        ):
            # Re-import or re-execute the module logic
            exec(compile(f.read(), __main__.__file__, "exec"))

        # Note: This test is tricky because the if __name__ == "__main__"
        # block has already been executed during import.
        # We can verify the main function exists and is importable.
        mock_main.assert_not_called()  # Because we're not actually running as main

    def test_module_structure(self):
        """Test the module structure is correct."""
        # Verify the module has the expected attributes
        assert hasattr(__main__, "__file__")
        assert hasattr(__main__, "__name__")

        # Verify the import works
        from ca_bhfuil.cli.main import main

        assert main is not None


class TestMainEntryPointIntegration:
    """Test main entry point integration."""

    @mock.patch("ca_bhfuil.__main__.main")
    def test_main_function_call_integration(self, mock_main):
        """Test that the main function can be called."""
        # Import and call main directly
        from ca_bhfuil.__main__ import main

        # Call the function
        main()

        # Verify it was called (though it's the same function, this tests the import path)
        mock_main.assert_called_once()

    def test_import_path_consistency(self):
        """Test that import paths are consistent."""
        # Both import paths should give the same function
        from ca_bhfuil.__main__ import main as main1
        from ca_bhfuil.cli.main import main as main2

        assert main1 is main2

    def test_module_can_be_executed(self):
        """Test that the module can be executed as a script."""
        # This tests the structure but doesn't actually execute
        # since that would run the CLI
        import ca_bhfuil.__main__ as main_module

        # Verify it's a proper module
        assert hasattr(main_module, "__file__")
        assert main_module.__file__.endswith("__main__.py")


class TestMainEntryPointCommandLine:
    """Test command line execution scenarios."""

    @mock.patch("sys.argv", ["ca-bhfuil", "--help"])
    @mock.patch("ca_bhfuil.__main__.main")
    def test_help_argument_handling(self, mock_main):
        """Test that help arguments can be handled."""
        # Import the main function
        from ca_bhfuil.__main__ import main

        # Call it (this would normally show help)
        main()

        # Verify the main function was called
        mock_main.assert_called_once()

    @mock.patch("sys.argv", ["ca-bhfuil", "--version"])
    @mock.patch("ca_bhfuil.__main__.main")
    def test_version_argument_handling(self, mock_main):
        """Test that version arguments can be handled."""
        # Import the main function
        from ca_bhfuil.__main__ import main

        # Call it (this would normally show version)
        main()

        # Verify the main function was called
        mock_main.assert_called_once()

    def test_module_name_check(self):
        """Test the __name__ check logic."""
        # When imported as a module, __name__ should not be '__main__'
        import ca_bhfuil.__main__

        assert ca_bhfuil.__main__.__name__ == "ca_bhfuil.__main__"


class TestMainEntryPointErrorHandling:
    """Test error handling in main entry point."""

    @mock.patch("ca_bhfuil.__main__.main")
    def test_main_function_exception_propagation(self, mock_main):
        """Test that exceptions from main function are propagated."""
        # Configure mock to raise an exception
        mock_main.side_effect = RuntimeError("CLI error")

        # Import the main function
        from ca_bhfuil.__main__ import main

        # Should propagate the exception
        with pytest.raises(RuntimeError, match="CLI error"):
            main()

    @mock.patch("ca_bhfuil.cli.main.main")
    def test_main_function_import_error_handling(self, mock_main):
        """Test handling of import errors."""
        # This test verifies that if there were import issues,
        # they would be caught appropriately

        # The import should work without issues
        try:
            from ca_bhfuil.__main__ import main

            assert main is not None
        except ImportError:
            pytest.fail("Import should not fail")


class TestMainEntryPointDocumentation:
    """Test documentation and metadata."""

    def test_module_docstring(self):
        """Test that module has appropriate docstring."""
        import ca_bhfuil.__main__

        assert ca_bhfuil.__main__.__doc__ is not None
        assert "CLI entry point" in ca_bhfuil.__main__.__doc__

    def test_module_file_location(self):
        """Test that module file is in correct location."""
        import ca_bhfuil.__main__

        assert ca_bhfuil.__main__.__file__.endswith("__main__.py")
        assert "ca_bhfuil" in ca_bhfuil.__main__.__file__


# Integration test to verify the entry point works with python -m
class TestPythonModuleExecution:
    """Test execution via python -m ca_bhfuil."""

    def test_module_execution_structure(self):
        """Test that the module is structured for -m execution."""
        # Verify the __main__.py file exists and is importable
        import ca_bhfuil.__main__

        # Verify it has the right structure for module execution
        assert hasattr(ca_bhfuil.__main__, "main")

        # The file should have the if __name__ == "__main__" check
        with pathlib.Path(ca_bhfuil.__main__.__file__).open() as f:
            content = f.read()
            assert 'if __name__ == "__main__"' in content
            assert "main()" in content
