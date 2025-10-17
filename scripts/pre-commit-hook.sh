#!/bin/bash
# Non-blocking pre-commit hook for code quality and tests

# Don't use set -e as we want to handle errors gracefully

echo "🔍 Running code quality checks and tests (non-blocking)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run command with error handling
run_check() {
    local name="$1"
    local command="$2"
    
    echo -e "${BLUE}📝 Running $name...${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $name failed (non-blocking)${NC}"
        return 1
    fi
}

# Track overall status
overall_status=0

# Run code quality checks
echo -e "${BLUE}🔧 Code Quality Checks${NC}"
run_check "ruff check" "uv run ruff check ." || overall_status=1
run_check "ruff format" "uv run ruff format ." || overall_status=1
run_check "black" "uv run black ." || overall_status=1
run_check "mypy" "uv run mypy ." || overall_status=1

# Run tests
echo -e "${BLUE}🧪 Running Tests${NC}"
run_check "pytest" "uv run pytest tests/ -v" || overall_status=1

# Summary
echo ""
if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some checks failed, but commit will proceed (non-blocking)${NC}"
fi

echo -e "${BLUE}✅ Pre-commit hook completed${NC}"
exit 0  # Always exit 0 to make it non-blocking
