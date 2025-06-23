#!/bin/bash
# Comprehensive style checking script for ca-bhfuil
# Usage: ./scripts/style-check.sh [--fix]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SRC_DIRS="src tests"
FIX_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--fix]"
            echo "  --fix    Automatically fix style issues where possible"
            echo "  --help   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_step() {
    echo -e "${BLUE}==> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "Must be run from the project root directory"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    print_error "uv is required but not installed"
    exit 1
fi

print_step "Running comprehensive style checks for ca-bhfuil"
echo

# Track overall success
OVERALL_SUCCESS=true

# 1. Ruff formatting check
print_step "Checking code formatting with Ruff"
if $FIX_MODE; then
    if uv run ruff format $SRC_DIRS; then
        print_success "Code formatting applied"
    else
        print_error "Code formatting failed"
        OVERALL_SUCCESS=false
    fi
else
    if uv run ruff format --check --diff $SRC_DIRS; then
        print_success "Code formatting is consistent"
    else
        print_warning "Code formatting issues found. Run with --fix to apply fixes."
        OVERALL_SUCCESS=false
    fi
fi
echo

# 2. Ruff linting
print_step "Running Ruff linter"
if $FIX_MODE; then
    if uv run ruff check --fix $SRC_DIRS; then
        print_success "Linting issues fixed"
    else
        print_error "Linting failed"
        OVERALL_SUCCESS=false
    fi
else
    if uv run ruff check $SRC_DIRS; then
        print_success "No linting issues found"
    else
        print_warning "Linting issues found. Run with --fix to apply auto-fixes."
        OVERALL_SUCCESS=false
    fi
fi
echo

# 3. Type checking with MyPy (only for src, not tests)
print_step "Running type checking with MyPy"
if uv run mypy src/; then
    print_success "Type checking passed"
else
    print_error "Type checking failed"
    OVERALL_SUCCESS=false
fi
echo

# 4. Security check with Bandit (only if not fixing)
if ! $FIX_MODE; then
    print_step "Running security check with Bandit"
    if uv run bandit -r src/ -c pyproject.toml; then
        print_success "Security check passed"
    else
        print_error "Security issues found"
        OVERALL_SUCCESS=false
    fi
    echo
fi

# 5. Test syntax and imports
print_step "Checking Python syntax and imports"
if python -m py_compile src/ca_bhfuil/**/*.py; then
    print_success "Python syntax is valid"
else
    print_error "Python syntax errors found"
    OVERALL_SUCCESS=false
fi
echo

# 6. Check for common issues
print_step "Checking for common code issues"

# Check for TODO/FIXME comments
if grep -r "TODO\|FIXME" $SRC_DIRS --include="*.py" | head -5; then
    print_warning "Found TODO/FIXME comments (not an error, just FYI)"
else
    print_success "No TODO/FIXME comments found"
fi

# Check for print statements in main code (not tests)
if grep -r "print(" src/ --include="*.py" | grep -v "__main__.py" | grep -v "cli/" | head -5; then
    print_warning "Found print() statements in non-CLI code. Consider using logger instead."
    OVERALL_SUCCESS=false
else
    print_success "No inappropriate print() statements found"
fi

# Check for missing type hints in new functions
if grep -r "def .*:" src/ --include="*.py" | grep -v "__init__" | head -5; then
    print_warning "Found functions without type hints. Consider adding them."
else
    print_success "All functions appear to have type hints"
fi
echo

# Summary
print_step "Style check summary"
if $OVERALL_SUCCESS; then
    print_success "All style checks passed! ✨"
    exit 0
else
    print_error "Some style checks failed."
    if ! $FIX_MODE; then
        echo -e "${YELLOW}Try running with --fix to automatically resolve fixable issues.${NC}"
    fi
    exit 1
fi
