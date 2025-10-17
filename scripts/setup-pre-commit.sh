#!/bin/bash
# Setup script for pre-commit hooks

set -e

echo "🔧 Setting up pre-commit hooks..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    uv add --dev pre-commit
fi

# Install the hooks
echo "🔗 Installing pre-commit hooks..."
uv run pre-commit install

# Test the hook
echo "🧪 Testing pre-commit hook..."
uv run pre-commit run --all-files

echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "📝 Usage:"
echo "  - Hooks will run automatically on 'git commit'"
echo "  - To run manually: uv run pre-commit run --all-files"
echo "  - To skip hooks: git commit --no-verify"
