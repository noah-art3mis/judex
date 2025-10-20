code quality checks:

```bash
uv run pre-commit run --all-files
```

# Pre-commit Hookws Setup

This project includes non-blocking pre-commit hooks that run code quality checks and tests automatically.

## 🚀 Quick Setup

```bash
# Run the setup script
./scripts/setup-pre-commit.sh
```

## 📋 What the hooks do

The pre-commit hooks run the following checks (non-blocking):

1. **Ruff Check** - Linting and code analysis
2. **Ruff Format** - Code formatting
3. **Black** - Additional code formatting
4. **MyPy** - Type checking
5. **Pytest** - Unit tests

## 🔧 Manual Usage

```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run code-quality-simple

# Skip hooks for a commit
git commit --no-verify -m "your message"
```

## 📁 Files Created

- `.pre-commit-config.yaml` - Main pre-commit configuration
- `.pre-commit-config-simple.yaml` - Alternative simple configuration
- `scripts/pre-commit-hook.sh` - Custom hook script
- `scripts/setup-pre-commit.sh` - Setup automation

## ⚙️ Configuration

The hooks are configured to be **non-blocking**, meaning:
- ✅ Commits will always succeed
- ⚠️ Failed checks are reported but don't stop the commit
- 📊 You get feedback on code quality without workflow interruption

## 🧪 Testing the Setup

```bash
# Test the hook manually
./scripts/pre-commit-hook.sh

# Test with pre-commit
pre-commit run --all-files
```

## 🔄 Disabling Hooks

```bash
# Uninstall hooks
pre-commit uninstall

# Skip hooks for specific commit
git commit --no-verify
```
