#!/bin/bash
# Redis Installation Script for macOS
# Installs Redis using Homebrew

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
    log_info "Checking macOS requirements..."

    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is for macOS only"
        exit 1
    fi

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_warn "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
}

install_redis() {
    log_info "Installing Redis via Homebrew..."

    # Update Homebrew
    brew update

    # Install Redis
    brew install redis

    if [ $? -eq 0 ]; then
        log_info "Redis installed successfully"
    else
        log_error "Failed to install Redis"
        exit 1
    fi
}

configure_redis() {
    log_info "Starting Redis service..."

    # Start Redis service
    brew services start redis

    if [ $? -eq 0 ]; then
        log_info "Redis service started"
    else
        log_warn "Failed to start Redis service, trying manual start..."
        redis-server &
    fi
}

verify_installation() {
    log_info "Verifying Redis installation..."

    # Wait for Redis to start
    sleep 3

    # Test Redis connection
    if redis-cli ping | grep -q "PONG"; then
        log_info "✅ Redis is running and responding"

        # Show Redis info
        echo ""
        log_info "Redis Information:"
        redis-cli info server | grep -E "redis_version|os|arch"

        return 0
    else
        log_error "❌ Redis is not responding"
        return 1
    fi
}

main() {
    echo "==============================="
    echo "Redis Installation Script for macOS"
    echo "==============================="

    check_requirements
    install_redis
    configure_redis

    if verify_installation; then
        echo ""
        log_info "🎉 Redis installation completed!"
        log_info "Redis is running on localhost:6379"
        log_info "To stop: brew services stop redis"
        log_info "To restart: brew services restart redis"
    else
        echo ""
        log_error "Installation completed but Redis not responding"
        log_error "Try: brew services restart redis"
        exit 1
    fi
}

main "$@"