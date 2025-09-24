#!/bin/bash
# Redis Setup Script using Docker
# Sets up Redis container for development

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CONTAINER_NAME="contentizer-redis"
REDIS_PORT="6379"
REDIS_IMAGE="redis:alpine"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking Docker requirements..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        log_error "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

cleanup_existing() {
    log_info "Checking for existing Redis container..."

    if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Existing Redis container found. Removing..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
}

start_redis_container() {
    log_info "Starting Redis container..."

    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "${REDIS_PORT}:6379" \
        --restart unless-stopped \
        "$REDIS_IMAGE"

    if [ $? -eq 0 ]; then
        log_info "Redis container started successfully"
    else
        log_error "Failed to start Redis container"
        exit 1
    fi
}

verify_installation() {
    log_info "Verifying Redis container..."

    # Wait for container to be ready
    sleep 5

    # Test Redis connection
    if docker exec "$CONTAINER_NAME" redis-cli ping | grep -q "PONG"; then
        log_info "✅ Redis container is running and responding"

        # Show container info
        echo ""
        log_info "Container Information:"
        docker exec "$CONTAINER_NAME" redis-cli info server | grep -E "redis_version|os"

        return 0
    else
        log_error "❌ Redis container is not responding"
        return 1
    fi
}

show_usage() {
    echo ""
    log_info "Docker Redis Commands:"
    echo "  Start:    docker start $CONTAINER_NAME"
    echo "  Stop:     docker stop $CONTAINER_NAME"
    echo "  Restart:  docker restart $CONTAINER_NAME"
    echo "  Remove:   docker rm -f $CONTAINER_NAME"
    echo "  Logs:     docker logs $CONTAINER_NAME"
    echo "  CLI:      docker exec -it $CONTAINER_NAME redis-cli"
}

main() {
    echo "================================"
    echo "Docker Redis Setup Script"
    echo "================================"

    check_requirements
    cleanup_existing
    start_redis_container

    if verify_installation; then
        echo ""
        log_info "🎉 Redis Docker container ready!"
        log_info "Redis is accessible on localhost:$REDIS_PORT"
        show_usage
    else
        echo ""
        log_error "Container started but Redis not responding"
        log_error "Check logs: docker logs $CONTAINER_NAME"
        exit 1
    fi
}

main "$@"