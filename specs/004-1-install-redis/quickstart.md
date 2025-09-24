# Development Environment Quickstart Guide

## Overview
This guide walks you through setting up a complete local development environment for the Content Creator Workbench project, including Redis infrastructure, service startup, and validation testing.

## Prerequisites Checklist

### System Requirements
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Git installed and configured
- [ ] 4GB+ RAM available
- [ ] 5GB+ free disk space

### Development Tools
- [ ] `uv` package manager installed (`pip install uv`)
- [ ] `npm` package manager (included with Node.js)
- [ ] Text editor or IDE
- [ ] Terminal/command line access

## Phase 1: Redis Installation

### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Redis server
sudo apt install redis-server

# Start and enable Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping
# Expected output: PONG
```

### macOS (Homebrew)
```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify installation
redis-cli ping
# Expected output: PONG
```

### Alternative: Docker
```bash
# Run Redis in Docker container
docker run -d --name redis-dev \
  -p 6379:6379 \
  redis:alpine

# Verify container is running
docker ps | grep redis-dev

# Test connection
redis-cli -h localhost -p 6379 ping
# Expected output: PONG
```

### Validation Steps
- [ ] Redis server responds to ping
- [ ] Redis is accessible on port 6379
- [ ] No conflicting services using port 6379

## Phase 2: Environment Configuration

### Create Environment File
```bash
# Navigate to project root
cd /path/to/contentizer

# Create backend environment file
cp backend/.env.example backend/.env

# Edit the environment file with your settings
nano backend/.env
```

### Required Environment Variables
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_DB=1
REDIS_TASK_DB=2

# API Keys (obtain from respective services)
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Service URLs (defaults for local development)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
WEBSOCKET_URL=ws://localhost:8000/ws

# Development Settings
ENVIRONMENT=local
DEBUG=true
LOG_LEVEL=INFO
```

### API Key Setup Instructions

#### YouTube Data API v3 Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable YouTube Data API v3
4. Create API credentials (API key)
5. Copy key to `YOUTUBE_API_KEY` in .env file

#### OpenAI API Key
1. Go to [OpenAI API Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new secret key
5. Copy key to `OPENAI_API_KEY` in .env file

### Validation Steps
- [ ] .env file exists in backend directory
- [ ] All required variables are set
- [ ] API keys are valid format (non-empty strings)
- [ ] Redis URL matches your installation

## Phase 3: Service Startup

### Terminal 1: Start Redis (if not running as service)
```bash
# If installed via package manager, Redis should already be running
# If using Docker or need manual start:
redis-server

# Verify Redis is running
redis-cli ping
```

### Terminal 2: Start Backend Service
```bash
# Navigate to backend directory
cd backend

# Install dependencies
uv sync

# Start the backend server
uv run python main.py

# Verify backend is running
curl http://localhost:8000/health
```

### Terminal 3: Start Frontend Service
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### Service Health Check
Visit these URLs to verify services are running:

- **Backend Health**: http://localhost:8000/health
- **Backend API Docs**: http://localhost:8000/docs
- **Frontend App**: http://localhost:3000
- **WebSocket Test**: Use browser dev tools to test `ws://localhost:8000/ws`

### Validation Steps
- [ ] Redis responds to ping command
- [ ] Backend health endpoint returns "healthy" status
- [ ] Frontend loads without errors in browser
- [ ] WebSocket connection can be established
- [ ] No port conflicts reported

## Phase 4: Contract Test Execution

### Run Backend Tests
```bash
# Navigate to backend directory
cd backend

# Run contract tests
uv run pytest tests/contract/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# Run all tests
uv run pytest tests/ -v --tb=short
```

### Run Frontend Tests
```bash
# Navigate to frontend directory
cd frontend

# Run frontend tests
npm test

# Run tests in watch mode (for development)
npm test -- --watch
```

### Expected Test Results
All tests should pass with output similar to:
```
tests/contract/test_session_api.py::test_session_create ✓
tests/contract/test_task_queue_api.py::test_task_submit ✓
tests/contract/test_websocket_api.py::test_websocket_connection ✓
tests/integration/test_complete_workflow_ui.py::test_workflow ✓

=================== 25 passed, 0 failed ===================
```

### Validation Steps
- [ ] All contract tests pass
- [ ] All integration tests pass
- [ ] No test failures or errors
- [ ] Test execution completes within 2 minutes

## Phase 5: End-to-End Workflow Validation

### Scenario 1: User Session Management
1. **Create Session**:
   ```bash
   curl -X POST http://localhost:8000/api/sessions \
     -H "Content-Type: application/json" \
     -d '{"preferences": {"theme": "dark"}}'
   ```

2. **Verify Session**:
   - Note the session_id from response
   - Check Redis storage: `redis-cli GET "session:{session_id}"`
   - Verify session data is encrypted

3. **Test Session Persistence**:
   - Restart backend service
   - Retrieve session: `GET /api/sessions/{session_id}`
   - Verify data persists across restarts

### Scenario 2: Task Queue Processing
1. **Submit Background Task**:
   ```bash
   curl -X POST http://localhost:8000/api/tasks/submit/trending_analysis \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your_session_id",
       "input_data": {"categories": ["Entertainment"]},
       "priority": "normal"
     }'
   ```

2. **Monitor Task Progress**:
   - Open browser to http://localhost:3000
   - Watch real-time progress updates
   - Verify WebSocket messages in browser dev tools

3. **Check Task Completion**:
   - Task should complete successfully
   - Results should be stored and retrievable
   - Progress should show 100% completion

### Scenario 3: Real-Time WebSocket Updates
1. **Open Frontend Application**:
   - Navigate to http://localhost:3000
   - Open browser developer tools (Network tab)
   - Look for WebSocket connection

2. **Test WebSocket Communication**:
   - WebSocket should auto-connect to backend
   - Submit a task via the UI
   - Observe real-time progress updates
   - Verify connection survives page refresh

3. **Test Connection Recovery**:
   - Temporarily stop backend service
   - Restart backend service
   - Verify WebSocket reconnects automatically

### Validation Checklist
- [ ] Sessions created and persist across restarts
- [ ] Tasks execute and show progress updates
- [ ] WebSocket connections work reliably
- [ ] Real-time UI updates display correctly
- [ ] Error handling works for service interruptions

## Troubleshooting Guide

### Common Issues and Solutions

#### Redis Connection Refused
**Symptoms**: Backend fails to start, Redis connection errors
**Solutions**:
1. Check if Redis is running: `redis-cli ping`
2. Verify Redis port 6379 is not blocked
3. Check Redis configuration in .env file
4. Restart Redis service: `sudo systemctl restart redis-server`

#### API Authentication Errors
**Symptoms**: 401 Unauthorized errors, API key invalid messages
**Solutions**:
1. Verify API keys are correctly set in .env file
2. Check for extra spaces or quotes in API key values
3. Test API keys directly with curl commands
4. Regenerate API keys if expired

#### Port Conflicts
**Symptoms**: "Address already in use" errors
**Solutions**:
1. Check what's using the port: `netstat -tulpn | grep :8000`
2. Kill conflicting processes or change port numbers
3. Update port numbers in both backend and frontend configs

#### WebSocket Connection Failed
**Symptoms**: Frontend shows disconnected status, no real-time updates
**Solutions**:
1. Verify backend WebSocket endpoint is accessible
2. Check browser console for WebSocket errors
3. Test WebSocket manually with browser dev tools
4. Ensure firewall allows WebSocket connections

#### Test Failures
**Symptoms**: Contract or integration tests failing
**Solutions**:
1. Ensure all services are running before tests
2. Check test database is clean (no leftover data)
3. Verify environment variables are set correctly
4. Run tests individually to isolate issues

### Getting Help
- Check logs in backend console output
- Review browser developer console for frontend issues
- Use Redis CLI to inspect data: `redis-cli monitor`
- Check service health endpoints for diagnostic information

## Success Confirmation

When setup is complete, you should have:
- ✅ Redis server running and accessible
- ✅ Backend service responding on port 8000
- ✅ Frontend application loading on port 3000
- ✅ All contract tests passing
- ✅ Real-time WebSocket updates working
- ✅ End-to-end workflows completing successfully

## Next Steps

With your development environment ready:
1. Explore the API documentation at http://localhost:8000/docs
2. Try creating content workflows via the frontend
3. Monitor real-time progress and session management
4. Experiment with different task types and priorities
5. Review the codebase to understand the implementation

Your Content Creator Workbench development environment is now fully operational!