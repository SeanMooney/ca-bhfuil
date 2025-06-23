#!/bin/bash
# Auto-fix script for ca-bhfuil style issues
# Usage: ./scripts/style-fix.sh

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SRC_DIRS="src tests"

# Function to print colored output
print_step() {
    echo -e "${BLUE}==> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "Error: Must be run from the project root directory"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed"
    exit 1
fi

print_step "Auto-fixing style issues for ca-bhfuil"
echo

# 1. Apply Ruff formatting
print_step "Applying Ruff code formatting"
uv run ruff format $SRC_DIRS
print_success "Code formatting applied"
echo

# 2. Apply Ruff auto-fixes
print_step "Applying Ruff auto-fixes"
uv run ruff check --fix $SRC_DIRS
print_success "Ruff auto-fixes applied"
echo

# 3. Sort imports (handled by Ruff)
print_step "Import sorting handled by Ruff"
print_success "Imports organized"
echo

print_success "All auto-fixes applied! 🎉"
echo
echo "Next steps:"
echo "1. Review the changes with: git diff"
echo "2. Run tests: uv run pytest"
echo "3. Run full style check: ./scripts/style-check.sh"
echo "4. Commit if everything looks good"
