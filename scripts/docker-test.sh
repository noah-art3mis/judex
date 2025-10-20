#!/bin/bash
# Docker testing script for judex across different environments

set -e

echo "🐳 judex Docker Testing Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_warning "docker-compose not found. Using 'docker compose' instead."
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
}

# Build all images
build_images() {
    print_status "Building Docker images..."
    
    # Build main image
    print_status "Building main image (Python 3.10)..."
    docker build -t judex:latest .
    
    # Build Python 3.9 image
    print_status "Building Python 3.9 image..."
    docker build -f Dockerfile.python39 -t judex:python39 .
    
    # Build Python 3.11 image
    print_status "Building Python 3.11 image..."
    docker build -f Dockerfile.python311 -t judex:python311 .
    
    print_success "All images built successfully!"
}

# Run tests on different Python versions
test_python_versions() {
    print_status "Testing across Python versions..."
    
    # Test Python 3.9
    print_status "Testing Python 3.9..."
    if docker run --rm -v "$(pwd):/app" judex:python39; then
        print_success "Python 3.9 tests passed!"
    else
        print_error "Python 3.9 tests failed!"
        return 1
    fi
    
    # Test Python 3.10
    print_status "Testing Python 3.10..."
    if docker run --rm -v "$(pwd):/app" judex:latest; then
        print_success "Python 3.10 tests passed!"
    else
        print_error "Python 3.10 tests failed!"
        return 1
    fi
    
    # Test Python 3.11
    print_status "Testing Python 3.11..."
    if docker run --rm -v "$(pwd):/app" judex:python311; then
        print_success "Python 3.11 tests passed!"
    else
        print_error "Python 3.11 tests failed!"
        return 1
    fi
}

# Run tests with docker-compose
test_with_compose() {
    print_status "Running tests with docker-compose..."
    
    # Start services
    $COMPOSE_CMD up --build -d
    
    # Wait for services to be ready
    sleep 5
    
    # Run tests
    $COMPOSE_CMD exec judex-linux uv run python -m pytest tests/ -v
    
    # Cleanup
    $COMPOSE_CMD down
    
    print_success "Docker-compose tests completed!"
}

# Run specific test suites
test_specific() {
    local test_suite="$1"
    
    case "$test_suite" in
        "models")
            print_status "Running model tests..."
            docker run --rm -v "$(pwd):/app" judex:latest uv run python -m pytest tests/test_models.py -v
            ;;
        "database")
            print_status "Running database tests..."
            docker run --rm -v "$(pwd):/app" judex:latest uv run python -m pytest tests/test_database_standalone.py -v
            ;;
        "pipeline")
            print_status "Running pipeline tests..."
            docker run --rm -v "$(pwd):/app" judex:latest uv run python -m pytest tests/test_pydantic_pipeline.py -v
            ;;
        "spider")
            print_status "Running spider tests..."
            docker run --rm -v "$(pwd):/app" judex:latest uv run python -m pytest tests/test_spider_integration.py -v
            ;;
        *)
            print_error "Unknown test suite: $test_suite"
            print_status "Available test suites: models, database, pipeline, spider"
            exit 1
            ;;
    esac
}

# Clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Remove containers
    docker container prune -f
    
    # Remove images
    docker image prune -f
    
    # Remove volumes
    docker volume prune -f
    
    print_success "Cleanup completed!"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build          Build all Docker images"
    echo "  test           Run tests across Python versions"
    echo "  test-compose   Run tests with docker-compose"
    echo "  test-models    Run model tests only"
    echo "  test-database  Run database tests only"
    echo "  test-pipeline  Run pipeline tests only"
    echo "  test-spider    Run spider tests only"
    echo "  cleanup        Clean up Docker resources"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 test"
    echo "  $0 test-models"
    echo "  $0 cleanup"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        "build")
            build_images
            ;;
        "test")
            test_python_versions
            ;;
        "test-compose")
            test_with_compose
            ;;
        "test-models")
            test_specific "models"
            ;;
        "test-database")
            test_specific "database"
            ;;
        "test-pipeline")
            test_specific "pipeline"
            ;;
        "test-spider")
            test_specific "spider"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
