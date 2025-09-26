# Complete Development Environment Quickstart

This guide provides step-by-step instructions for setting up the complete Content Creator Workbench development environment with all validation steps.

## Phase 1: Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+
- Git configured
- 4GB+ RAM, 5GB+ disk space

### Install Package Managers
```bash
# Install uv for Python
pip install uv

# Verify installations
python3 --version
node --version
npm --version
uv --version
```

## Phase 2: Redis Installation

Choose your platform:

### Ubuntu/Debian
```bash
# Use installation script
./scripts/install/install-redis-ubuntu.sh

# Verify installation
redis-cli ping  # Should return PONG
```

### macOS
```bash
# Use installation script
./scripts/install/install-redis-macos.sh

# Verify installation
redis-cli ping  # Should return PONG
```

### Docker
```bash
# Use Docker script
./scripts/install/install-redis-docker.sh

# Verify container
docker ps | grep contentizer-redis
```

## Phase 3: Project Setup

### Backend Dependencies
```bash
cd backend
uv sync
uv run python --version  # Should be 3.11+
```

### Frontend Dependencies
```bash
cd frontend
npm install
npm run build  # Test build process
```

## Phase 4: Environment Configuration

### Generate Environment Template
```bash
# Generate local development template
python3 scripts/config/generate-env-template.py --type local --output backend/.env

# Edit with your API keys
nano backend/.env
```

### Required API Keys
1. **YouTube Data API v3**: Get from [Google Cloud Console](https://console.cloud.google.com/)
2. **Gemini API**: Get from [Google AI Studio](https://aistudio.google.com/)

### Gemini Model Configuration
The system uses Google's latest **Gemini 2.5 Flash Image** model for all image and video generation:

- **GEMINI_IMAGE_MODEL**: Set to `gemini-2.5-flash-image` (default)
- **Fallback**: Can be changed to `gemini-pro` if needed
- **Requirements**: Requires Google Gemini API access

This ensures optimal performance and quality for visual content generation.

### Validate Configuration
```bash
python3 scripts/config/validate-env.py --env-file backend/.env
```

## Phase 5: Service Startup

### Terminal 1: Backend
```bash
cd backend
uv run python main.py
# Should start on http://localhost:8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
# Should start on http://localhost:3000
```

## Phase 6: Validation & Testing

### Service Health Check
```bash
python3 scripts/validate/check-services.py
# Should show all services as healthy
```

### Contract Tests
```bash
python3 scripts/test/run-contract-tests.py
# Should pass all API contract validations
```

### Integration Tests
```bash
python3 scripts/test/run-integration-tests.py
# Should validate Redis and service integration
```

### End-to-End Workflow
```bash
python3 scripts/validate/e2e-workflow.py
# Should complete full workflow validation
```

## Phase 7: Verification

### Manual Verification Checklist
- [ ] Redis responds to `redis-cli ping`
- [ ] Backend health: `curl http://localhost:8000/health`
- [ ] Frontend loads: Open http://localhost:3000
- [ ] API docs: Visit http://localhost:8000/docs
- [ ] WebSocket: Test via browser dev tools

### Expected Responses
```bash
# Redis test
$ redis-cli ping
PONG

# Backend health
$ curl http://localhost:8000/health
{"status":"healthy"...}

# Setup API health
$ curl http://localhost:8000/setup/health
{"overall_status":"healthy"...}
```

## Success Confirmation

When setup is complete, you should have:
- ✅ Redis server running on localhost:6379
- ✅ Backend API on localhost:8000 with /health returning healthy
- ✅ Frontend dev server on localhost:3000
- ✅ All contract tests passing
- ✅ All integration tests passing
- ✅ End-to-end workflow completing successfully

## Next Steps

Your development environment is ready! You can now:
1. Explore API documentation at http://localhost:8000/docs
2. Start developing new features
3. Use the setup validation endpoints for testing
4. Monitor services with the health check tools

## Troubleshooting

If you encounter issues, see `troubleshooting.md` for common problems and solutions.