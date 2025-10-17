!# Docker Testing Guide for Lexicon

## 🐳 Overview

This guide covers using Docker for testing Lexicon across different environments (Windows, Mac, Linux) and Python versions.

## 🚀 Quick Start

### Prerequisites

-   Docker installed on your system
-   Docker Compose (optional, for multi-service testing)

### Basic Testing

```bash
# Build and test on Linux with Python 3.10
./scripts/docker-test.sh build
./scripts/docker-test.sh test

# Test with docker-compose
./scripts/docker-test.sh test-compose
```

## 📋 Available Commands

### Build Commands

```bash
# Build all images
./scripts/docker-test.sh build

# Build specific Python version
docker build -f Dockerfile.python39 -t lexicon:python39 .
docker build -f Dockerfile.python311 -t lexicon:python311 .
```

### Testing Commands

```bash
# Test across all Python versions
./scripts/docker-test.sh test

# Test specific components
./scripts/docker-test.sh test-models
./scripts/docker-test.sh test-database
./scripts/docker-test.sh test-pipeline
./scripts/docker-test.sh test-spider

# Test with docker-compose
./scripts/docker-test.sh test-compose
```

### Cleanup Commands

```bash
# Clean up Docker resources
./scripts/docker-test.sh cleanup
```

## 🏗 Docker Images

### Main Image (Python 3.10)

```dockerfile
FROM python:3.10-slim
# Includes Chrome, ChromeDriver, and all dependencies
```

### Python 3.9 Image

```dockerfile
FROM python:3.9-slim
# For testing Python 3.9 compatibility
```

### Python 3.11 Image

```dockerfile
FROM python:3.11-slim
# For testing Python 3.11 compatibility
```

## 🔧 Docker Compose Services

### Services Available

-   **lexicon-linux**: Main testing environment
-   **lexicon-dev**: Development environment with live reload
-   **lexicon-python39**: Python 3.9 testing
-   **lexicon-python311**: Python 3.11 testing

### Using Docker Compose

```bash
# Start all services
docker-compose up --build

# Run tests in specific service
docker-compose exec lexicon-linux uv run python -m pytest tests/ -v

# Stop services
docker-compose down
```

## 🧪 Testing Scenarios

### Cross-Platform Testing

```bash
# Test on different Python versions
docker run --rm -v "$(pwd):/app" lexicon:python39
docker run --rm -v "$(pwd):/app" lexicon:latest
docker run --rm -v "$(pwd):/app" lexicon:python311
```

### Specific Test Suites

```bash
# Model tests
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/test_models.py -v

# Database tests
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/test_database_standalone.py -v

# Pipeline tests
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/test_pydantic_pipeline.py -v

# Spider tests
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/test_spider_integration.py -v
```

## 🛠 Development Environment

### Interactive Development

```bash
# Start development container
docker-compose up lexicon-dev

# Access container shell
docker-compose exec lexicon-dev bash

# Run scraper
docker-compose exec lexicon-dev uv run python -m lexicon.core
```

### Live Development

```bash
# Mount source code for live development
docker run -it --rm \
  -v "$(pwd):/app" \
  -v "$(pwd)/output:/app/output" \
  lexicon:latest bash
```

## 🔍 Debugging

### Container Debugging

```bash
# Run container with debug shell
docker run -it --rm \
  -v "$(pwd):/app" \
  lexicon:latest bash

# Check Chrome installation
docker run --rm lexicon:latest chromium --version
docker run --rm lexicon:latest chromedriver --version
```

### Test Debugging

```bash
# Run tests with verbose output
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/ -v -s

# Run specific test with debugging
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m pytest tests/test_models.py::TestSTFCaseModel::test_minimal_valid_case -v -s
```

## 📊 CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Tests

on: [push, pull_request]

jobs:
    test:
        runs-on: ubuntu-latest
        strategy:
            matrix:
                python-version: [3.9, 3.10, 3.11]

        steps:
            - uses: actions/checkout@v3

            - name: Build Docker image
              run: |
                  docker build -f Dockerfile.python${{ matrix.python-version }} \
                    -t lexicon:python${{ matrix.python-version }} .

            - name: Run tests
              run: |
                  docker run --rm -v "$(pwd):/app" \
                    lexicon:python${{ matrix.python-version }} \
                    uv run python -m pytest tests/ -v
```

### Local CI Simulation

```bash
# Simulate CI environment
docker run --rm \
  -e CI=true \
  -v "$(pwd):/app" \
  lexicon:latest \
  uv run python -m pytest tests/ --cov=lexicon --cov-report=xml
```

## 🚨 Troubleshooting

### Common Issues

1. **Chrome/ChromeDriver Issues**:

    ```bash
    # Check Chrome installation
    docker run --rm lexicon:latest chromium --version

    # Check ChromeDriver
    docker run --rm lexicon:latest chromedriver --version
    ```

2. **Permission Issues**:

    ```bash
    # Fix file permissions
    docker run --rm -v "$(pwd):/app" lexicon:latest \
      chown -R $(id -u):$(id -g) /app
    ```

3. **Memory Issues**:
    ```bash
    # Run with memory limits
    docker run --rm --memory=2g -v "$(pwd):/app" lexicon:latest
    ```

### Performance Optimization

```bash
# Use multi-stage builds for smaller images
docker build --target base -t lexicon:base .

# Use .dockerignore to exclude unnecessary files
# (Already configured in .dockerignore)
```

## 📝 Best Practices

### Development Workflow

1. **Local Development**: Use Docker for consistent environment
2. **Testing**: Test across Python versions before committing
3. **CI/CD**: Use Docker in GitHub Actions for automated testing
4. **Deployment**: Use Docker for production deployment

### Image Management

```bash
# Clean up unused images
docker image prune -f

# Remove specific images
docker rmi lexicon:python39 lexicon:python311

# List all images
docker images | grep lexicon
```

## 🔗 Integration with Publishing

### Pre-Publication Testing

```bash
# Test before publishing to PyPI
./scripts/docker-test.sh test

# Build package in Docker
docker run --rm -v "$(pwd):/app" lexicon:latest \
  uv run python -m build

# Test package installation
docker run --rm -v "$(pwd):/app" lexicon:latest \
  pip install dist/lexicon-*.whl
```

This Docker setup ensures Lexicon works consistently across all platforms and Python versions before publishing to PyPI.
