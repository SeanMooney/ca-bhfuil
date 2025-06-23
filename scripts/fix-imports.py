#!/usr/bin/env python3
"""Script to systematically fix import styles across the codebase."""

import ast
import pathlib


def get_python_files() -> list[pathlib.Path]:
    """Get all Python files in src/ and tests/."""
    python_files = []
    for pattern in ["src/**/*.py", "tests/**/*.py"]:
        python_files.extend(pathlib.Path().glob(pattern))
    return python_files


def analyze_imports(file_path: pathlib.Path) -> dict[str, list[str]]:
    """Analyze imports in a Python file."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)

        imports = {"stdlib": [], "third_party": [], "local": [], "violations": []}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports["stdlib"].append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                # Check for function/class imports (violations)
                for alias in node.names:
                    if (
                        alias.name[0].isupper()
                        or alias.name.endswith("Error")
                        or alias.name in ["Path", "Optional", "Any", "Dict", "List"]
                    ):
                        imports["violations"].append(
                            f"from {node.module} import {alias.name}"
                        )
                    else:
                        if node.module.startswith("ca_bhfuil"):
                            imports["local"].append(
                                f"from {node.module} import {alias.name}"
                            )
                        else:
                            imports["third_party"].append(
                                f"from {node.module} import {alias.name}"
                            )

        return imports
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {"stdlib": [], "third_party": [], "local": [], "violations": []}


def main():
    """Analyze import violations across the codebase."""
    python_files = get_python_files()

    total_violations = 0
    violations_by_type = {}

    print("🔍 Analyzing import violations across codebase...\n")

    for file_path in python_files:
        imports = analyze_imports(file_path)

        if imports["violations"]:
            print(f"📄 {file_path}")
            for violation in imports["violations"]:
                print(f"   ❌ {violation}")

                # Track violation types
                if "import Path" in violation:
                    violations_by_type.setdefault("Path", []).append(str(file_path))
                elif "import Optional" in violation or "import Any" in violation:
                    violations_by_type.setdefault("typing", []).append(str(file_path))
                elif "Error" in violation:
                    violations_by_type.setdefault("exceptions", []).append(
                        str(file_path)
                    )
                else:
                    violations_by_type.setdefault("other", []).append(str(file_path))

                total_violations += 1
            print()

    print(f"📊 Total violations found: {total_violations}")
    print("\n📈 Violations by type:")
    for vtype, files in violations_by_type.items():
        print(f"   {vtype}: {len(files)} files")

    if total_violations > 0:
        print("\n🔧 To fix these issues:")
        print(
            "1. Replace 'from pathlib import Path' with 'import pathlib' and use 'pathlib.Path'"
        )
        print("2. Replace 'import typing  # X' with 'import typing' and use 'typing.X'")
        print("3. Replace function/class imports with module imports")
        print("4. Run 'uv run ruff check --fix' after manual fixes")


if __name__ == "__main__":
    main()
