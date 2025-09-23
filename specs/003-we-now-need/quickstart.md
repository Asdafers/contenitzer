# Quickstart: Frontend Components & Redis Scaling

**Feature**: 003-we-now-need
**Purpose**: Validate implementation through real user scenarios
**Prerequisites**: Backend running with Redis, frontend development server active

## Test Scenarios

### Scenario 1: Complete Workflow with UI Components
**Goal**: Verify all React components work together for end-to-end video creation

#### Steps:
1. **Access Application**
   ```bash
   # Terminal 1: Start backend with Redis
   cd backend
   uv run python main.py

   # Terminal 2: Start Redis (if not running)
   redis-server

   # Terminal 3: Start frontend
   cd frontend
   npm run dev
   ```

2. **Open Browser**
   - Navigate to `http://localhost:3000`
   - Verify main workflow page loads
   - Check that all 5 workflow components are visible:
     - Trending Analysis component
     - Script Generator component
     - Media Generator component
     - Video Composer component
     - YouTube Uploader component

3. **Execute Complete Workflow**
   - **Trending Analysis**: Select categories, click "Analyze Trends"
   - **Verify**: Progress bar appears, WebSocket updates show real-time progress
   - **Script Generation**: Choose theme, click "Generate Script"
   - **Verify**: Script preview loads, form auto-saves on input
   - **Media Generation**: Configure audio/visual settings, click "Generate Media"
   - **Verify**: Preview thumbnails appear as assets are created
   - **Video Composition**: Review timeline, click "Compose Video"
   - **Verify**: Video player shows composed result
   - **YouTube Upload**: Add metadata, click "Upload to YouTube"
   - **Verify**: Upload progress and completion confirmation

#### Expected Results:
- ✅ All components render without errors
- ✅ WebSocket connection established (check browser dev tools Network tab)
- ✅ Real-time progress updates appear during processing
- ✅ Form data persists across page refreshes
- ✅ Complete workflow executes end-to-end
- ✅ Final video uploaded successfully

### Scenario 2: Session Persistence & Recovery
**Goal**: Verify user sessions and workflow state survive interruptions

#### Steps:
1. **Start Workflow**
   - Begin trending analysis
   - Fill out script generation form partially
   - Verify auto-save indicator appears

2. **Simulate Interruption**
   - Close browser tab (do NOT close browser entirely)
   - Wait 10 seconds
   - Open new tab to `http://localhost:3000`

3. **Verify Recovery**
   - Check that workflow resumes at correct step
   - Verify form data is pre-populated
   - Confirm progress from previous steps is preserved

4. **Test Browser Restart**
   - Close entire browser
   - Restart browser and navigate to application
   - Verify session recovery works

#### Expected Results:
- ✅ Session ID maintained across tab close/reopen
- ✅ Form data restored from auto-save
- ✅ Workflow progress preserved
- ✅ Session survives browser restart (24-hour TTL)

### Scenario 3: Concurrent User Processing
**Goal**: Verify Redis task queue handles multiple users simultaneously

#### Steps:
1. **Open Multiple Browser Sessions**
   - Chrome: `http://localhost:3000`
   - Firefox: `http://localhost:3000`
   - Chrome Incognito: `http://localhost:3000`

2. **Submit Concurrent Tasks**
   - In each session, start video processing simultaneously
   - Verify unique session IDs in browser dev tools
   - Monitor Redis task queue: `redis-cli KEYS tasks:*`

3. **Verify Independent Progress**
   - Each session shows its own progress updates
   - No cross-session progress contamination
   - All tasks complete successfully

#### Expected Results:
- ✅ Each session gets unique session ID
- ✅ Tasks queued independently in Redis
- ✅ WebSocket updates isolated per session
- ✅ All concurrent tasks complete successfully
- ✅ No performance degradation with 3 concurrent users

### Scenario 4: Error Handling & Recovery
**Goal**: Verify graceful handling of failures and network issues

#### Steps:
1. **Test API Key Errors**
   - Remove API keys from settings
   - Attempt video generation
   - Verify clear error messages in UI
   - Verify task marked as failed in Redis

2. **Test Network Interruption**
   - Start video processing
   - Disconnect network during processing
   - Reconnect network
   - Verify WebSocket reconnection and task recovery

3. **Test Redis Connection Loss**
   - Stop Redis server during active session
   - Verify graceful degradation to database-only mode
   - Restart Redis, verify normal operation resumes

#### Expected Results:
- ✅ Clear error messages displayed in UI
- ✅ Failed tasks can be retried from UI
- ✅ WebSocket reconnects automatically
- ✅ Application functions without Redis (degraded mode)
- ✅ Full functionality restored when Redis available

## Performance Validation

### Load Testing
```bash
# Test concurrent WebSocket connections
node scripts/websocket-load-test.js --connections=10 --duration=60s

# Test Redis task queue throughput
python scripts/redis-queue-test.py --tasks=50 --workers=5

# Test session creation rate
curl -X POST http://localhost:8000/api/sessions -H "Content-Type: application/json" -d "{}"
```

### Memory Testing
```bash
# Monitor Redis memory usage
redis-cli INFO memory

# Check for memory leaks in frontend
# Chrome Dev Tools -> Memory tab -> Take heap snapshots during workflow
```

### Response Time Validation
- **Session creation**: < 100ms
- **UI state save**: < 50ms
- **WebSocket message latency**: < 10ms
- **Task queue submission**: < 200ms

## Integration Points Validation

### Backend Integration
- **New endpoints** respond correctly: `/api/sessions`, `/api/tasks`, `/ws/progress`
- **Existing endpoints** unmodified and functional: `/api/scripts/generate`, etc.
- **Database + Redis** work together without conflicts

### Frontend Integration
- **API client** handles new session/task endpoints
- **WebSocket service** connects and receives messages
- **React components** integrate with existing routing
- **Build process** includes new dependencies

### Redis Integration
- **Task queue** processes Celery jobs correctly
- **Session storage** persists and expires appropriately
- **Pub/sub** delivers WebSocket messages reliably
- **Memory usage** stays within configured limits

## Success Criteria

**Functional Requirements Met**:
- [x] FR-001: Visual components for YouTube trending analysis ✅
- [x] FR-002: Script generation interface with input options ✅
- [x] FR-003: Media generation progress with previews ✅
- [x] FR-004: Video composition interface with timeline ✅
- [x] FR-005: YouTube upload management with progress ✅
- [x] FR-006: Session state persistence across refreshes ✅
- [x] FR-007: Concurrent user handling without degradation ✅
- [x] FR-008: Real-time progress updates for operations ✅
- [x] FR-009: Settings interface for API key configuration ✅
- [x] FR-010: Project history and management interface ✅
- [x] FR-011: Task queuing for resource-intensive operations ✅
- [x] FR-012: Session persistence across logouts/restarts ✅

**Technical Validation**:
- Redis integration stable and performant
- WebSocket connections reliable with reconnection
- React components render without errors
- Auto-save functionality working correctly
- Error handling graceful and informative

**User Experience Validation**:
- Workflow intuitive and guided
- Progress updates clear and timely
- Error messages actionable
- Performance acceptable for content creators

---

**Completion**: All scenarios pass → Implementation ready for production