#!/bin/bash
# Redis Installation Script for Ubuntu/Debian
# Installs Redis server with proper configuration for development

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    log_info "Checking system requirements..."

    # Check if running on Ubuntu/Debian
    if ! command -v apt &> /dev/null; then
        log_error "This script requires apt package manager (Ubuntu/Debian)"
        exit 1
    fi

    # Check sudo privileges
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges"
        exit 1
    fi
}

install_redis() {
    log_info "Installing Redis server..."

    # Update package list
    sudo apt update

    # Install Redis
    sudo apt install -y redis-server

    if [ $? -eq 0 ]; then
        log_info "Redis server installed successfully"
    else
        log_error "Failed to install Redis server"
        exit 1
    fi
}

configure_redis() {
    log_info "Configuring Redis for development..."

    # Backup original config
    sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

    # Enable Redis service
    sudo systemctl enable redis-server

    # Start Redis service
    sudo systemctl start redis-server

    log_info "Redis service started and enabled"
}

verify_installation() {
    log_info "Verifying Redis installation..."

    # Wait for Redis to start
    sleep 2

    # Test Redis connection
    if redis-cli ping | grep -q "PONG"; then
        log_info "✅ Redis is running and responding to ping"

        # Show Redis info
        echo ""
        log_info "Redis Server Information:"
        redis-cli info server | grep -E "redis_version|os|arch"

        return 0
    else
        log_error "❌ Redis is not responding"
        return 1
    fi
}

main() {
    echo "========================================="
    echo "Redis Installation Script for Ubuntu/Debian"
    echo "========================================="

    check_requirements
    install_redis
    configure_redis

    if verify_installation; then
        echo ""
        log_info "🎉 Redis installation completed successfully!"
        log_info "Redis is running on localhost:6379"
        log_info "To test: redis-cli ping"
    else
        echo ""
        log_error "Installation completed but Redis is not responding"
        log_error "Check status: sudo systemctl status redis-server"
        exit 1
    fi
}

main "$@"