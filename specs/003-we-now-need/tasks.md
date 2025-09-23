# Tasks: Frontend Components & Redis Scaling

**Input**: Design documents from `/specs/003-we-now-need/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

## Phase 3.1: Setup & Dependencies
- [x] T001 Add Redis dependencies to backend (redis>=4.5.0, celery>=5.3.0, python-jose>=3.3.0)
- [x] T002 Add frontend UI dependencies (tailwindcss>=3.3.0, @headlessui/react, react-hook-form>=7.45.0)
- [x] T003 [P] Configure Tailwind CSS in frontend/tailwind.config.js
- [x] T004 [P] Configure Celery worker in backend/celery_worker.py
- [x] T005 [P] Configure Redis connection in backend/src/lib/redis.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [x] T006 [P] Contract test WebSocket /ws/progress/{session_id} in backend/tests/contract/test_websocket_api.py
- [x] T007 [P] Contract test POST /api/sessions in backend/tests/contract/test_session_api.py
- [x] T008 [P] Contract test GET /api/sessions/{session_id} in backend/tests/contract/test_session_api.py
- [x] T009 [P] Contract test PUT /api/sessions/{session_id} in backend/tests/contract/test_session_api.py
- [x] T010 [P] Contract test DELETE /api/sessions/{session_id} in backend/tests/contract/test_session_api.py
- [x] T011 [P] Contract test GET /api/sessions/{session_id}/workflow-state in backend/tests/contract/test_session_api.py
- [x] T012 [P] Contract test PUT /api/sessions/{session_id}/workflow-state in backend/tests/contract/test_session_api.py
- [x] T013 [P] Contract test GET /api/sessions/{session_id}/ui-state/{component_name} in backend/tests/contract/test_session_api.py
- [x] T014 [P] Contract test PUT /api/sessions/{session_id}/ui-state/{component_name} in backend/tests/contract/test_session_api.py
- [x] T015 [P] Contract test GET /api/tasks in backend/tests/contract/test_task_queue_api.py
- [x] T016 [P] Contract test GET /api/tasks/{task_id} in backend/tests/contract/test_task_queue_api.py
- [x] T017 [P] Contract test DELETE /api/tasks/{task_id} in backend/tests/contract/test_task_queue_api.py
- [x] T018 [P] Contract test POST /api/tasks/{task_id}/retry in backend/tests/contract/test_task_queue_api.py
- [x] T019 [P] Contract test POST /api/tasks/submit/{task_type} in backend/tests/contract/test_task_queue_api.py

### Integration Tests
- [x] T020 [P] Integration test complete workflow with UI components in backend/tests/integration/test_complete_workflow_ui.py
- [x] T021 [P] Integration test session persistence and recovery in backend/tests/integration/test_session_persistence.py
- [x] T022 [P] Integration test concurrent user processing in backend/tests/integration/test_concurrent_users.py
- [x] T023 [P] Integration test error handling and recovery in backend/tests/integration/test_error_handling.py

## Phase 3.3: Backend Core Implementation (ONLY after tests are failing)

### Redis Services
- [x] T024 [P] UserSession Redis service in backend/src/services/session_service.py
- [x] T025 [P] TaskQueue Redis service in backend/src/services/task_queue_service.py
- [x] T026 [P] ProgressEvent Redis service in backend/src/services/progress_service.py
- [x] T027 [P] UIComponentState Redis service in backend/src/services/ui_state_service.py

### API Endpoints
- [x] T028 Session management endpoints in backend/src/api/sessions.py
- [x] T029 Task queue management endpoints in backend/src/api/tasks.py
- [x] T030 WebSocket progress endpoint in backend/src/api/websocket.py

### Enhanced Models
- [x] T031 [P] Extend VideoProject model with UI fields in backend/src/models/video_project.py
- [x] T032 [P] Extend MediaAsset model with progress fields in backend/src/models/media_asset.py

### Celery Tasks
- [x] T033 [P] Celery task wrapper for trending analysis in backend/src/tasks/trending_tasks.py
- [x] T034 [P] Celery task wrapper for script generation in backend/src/tasks/script_tasks.py
- [x] T035 [P] Celery task wrapper for media generation in backend/src/tasks/media_tasks.py
- [x] T036 [P] Celery task wrapper for video composition in backend/src/tasks/video_tasks.py
- [x] T037 [P] Celery task wrapper for YouTube upload in backend/src/tasks/upload_tasks.py

## Phase 3.4: Frontend Core Implementation

### React Components
- [x] T038 [P] TrendingAnalysis component in frontend/src/components/TrendingAnalysis.tsx
- [x] T039 [P] ScriptGenerator component in frontend/src/components/ScriptGenerator.tsx
- [x] T040 [P] MediaGenerator component in frontend/src/components/MediaGenerator.tsx
- [x] T041 [P] VideoComposer component in frontend/src/components/VideoComposer.tsx
- [x] T042 [P] YouTubeUploader component in frontend/src/components/YouTubeUploader.tsx

### State Management & Hooks
- [x] T043 [P] Session context and provider in frontend/src/contexts/SessionContext.tsx
- [x] T044 [P] Workflow state management hook in frontend/src/hooks/useWorkflowState.ts
- [x] T045 [P] WebSocket connection hook in frontend/src/hooks/useWebSocket.ts
- [x] T046 [P] Auto-save form hook in frontend/src/hooks/useAutoSave.ts

### Services & API Integration
- [x] T047 Extend API client with session endpoints in frontend/src/services/api.ts
- [x] T048 Extend API client with task queue endpoints in frontend/src/services/api.ts
- [x] T049 [P] WebSocket service for progress updates in frontend/src/services/websocket.ts

### UI Components & Layout
- [x] T050 [P] Workflow progress indicator component in frontend/src/components/ProgressIndicator.tsx
- [x] T051 [P] Settings panel for API keys in frontend/src/components/SettingsPanel.tsx
- [x] T052 Main workflow page layout in frontend/src/pages/WorkflowPage.tsx

## Phase 3.5: Integration & Configuration

### Backend Integration
- [x] T053 Update FastAPI main app to include new routes in backend/main.py
- [x] T054 Add Redis health check to backend health endpoint in backend/src/api/health.py
- [x] T055 Configure WebSocket middleware and CORS in backend/src/lib/middleware.py
- [x] T056 Add Celery worker startup/shutdown in backend/main.py

### Frontend Integration
- [x] T057 Update main App component to include SessionProvider in frontend/src/App.tsx
- [x] T058 Add WebSocket connection to main layout in frontend/src/App.tsx
- [x] T059 Configure routing for new workflow page in frontend/src/App.tsx

### Environment Configuration
- [x] T060 Add Redis configuration to backend environment in backend/.env.example
- [x] T061 Update backend startup script with Redis checks in backend/main.py
- [x] T062 Update frontend package.json scripts for new dependencies in frontend/package.json

## Phase 3.6: Polish & Testing

### Unit Tests
- [ ] T063 [P] Unit tests for session service in backend/tests/unit/test_session_service.py
- [ ] T064 [P] Unit tests for task queue service in backend/tests/unit/test_task_queue_service.py
- [ ] T065 [P] Unit tests for progress service in backend/tests/unit/test_progress_service.py
- [ ] T066 [P] Unit tests for WebSocket connection hook in frontend/tests/hooks/test_useWebSocket.test.tsx
- [ ] T067 [P] Unit tests for workflow state hook in frontend/tests/hooks/test_useWorkflowState.test.tsx
- [ ] T068 [P] Unit tests for auto-save hook in frontend/tests/hooks/test_useAutoSave.test.tsx

### Component Tests
- [ ] T069 [P] Component tests for TrendingAnalysis in frontend/tests/components/TrendingAnalysis.test.tsx
- [ ] T070 [P] Component tests for ScriptGenerator in frontend/tests/components/ScriptGenerator.test.tsx
- [ ] T071 [P] Component tests for MediaGenerator in frontend/tests/components/MediaGenerator.test.tsx
- [ ] T072 [P] Component tests for VideoComposer in frontend/tests/components/VideoComposer.test.tsx
- [ ] T073 [P] Component tests for YouTubeUploader in frontend/tests/components/YouTubeUploader.test.tsx

### Performance & Reliability
- [ ] T074 [P] Load testing scripts for WebSocket connections in scripts/websocket-load-test.js
- [ ] T075 [P] Load testing scripts for Redis task queue in scripts/redis-queue-test.py
- [ ] T076 Memory leak testing and optimization in frontend components
- [ ] T077 Redis memory usage monitoring and TTL optimization
- [ ] T078 Execute quickstart.md validation scenarios

## Dependencies

### Setup Dependencies
- T001-T005 must complete before any other tasks
- T003, T004, T005 can run in parallel (different files)

### Test Dependencies
- T006-T023 must complete before T024-T062 (TDD requirement)
- All contract tests (T006-T019) can run in parallel
- All integration tests (T020-T023) can run in parallel

### Implementation Dependencies
- **Redis Services (T024-T027)** before **API Endpoints (T028-T030)**
- **Models (T031-T032)** before **Celery Tasks (T033-T037)**
- **Backend APIs (T028-T030)** before **Frontend API Integration (T047-T048)**
- **State Management (T043-T046)** before **React Components (T038-T042)**
- **Components (T038-T042)** before **Layout (T052)**
- **Core Implementation (T024-T052)** before **Integration (T053-T062)**
- **Implementation (T024-T062)** before **Polish (T063-T078)**

## Parallel Execution Examples

### Phase 3.1 (Setup)
```bash
# T003, T004, T005 can run together:
Task: "Configure Tailwind CSS in frontend/tailwind.config.js"
Task: "Configure Celery worker in backend/celery_worker.py"
Task: "Configure Redis connection in backend/src/lib/redis.py"
```

### Phase 3.2 (Contract Tests)
```bash
# T006-T019 can run together:
Task: "Contract test WebSocket /ws/progress/{session_id} in backend/tests/contract/test_websocket_api.py"
Task: "Contract test POST /api/sessions in backend/tests/contract/test_session_api.py"
Task: "Contract test GET /api/sessions/{session_id} in backend/tests/contract/test_session_api.py"
Task: "Contract test PUT /api/sessions/{session_id} in backend/tests/contract/test_session_api.py"
Task: "Contract test DELETE /api/sessions/{session_id} in backend/tests/contract/test_session_api.py"
Task: "Contract test GET /api/sessions/{session_id}/workflow-state in backend/tests/contract/test_session_api.py"
Task: "Contract test PUT /api/sessions/{session_id}/workflow-state in backend/tests/contract/test_session_api.py"
Task: "Contract test GET /api/sessions/{session_id}/ui-state/{component_name} in backend/tests/contract/test_session_api.py"
Task: "Contract test PUT /api/sessions/{session_id}/ui-state/{component_name} in backend/tests/contract/test_session_api.py"
Task: "Contract test GET /api/tasks in backend/tests/contract/test_task_queue_api.py"
Task: "Contract test GET /api/tasks/{task_id} in backend/tests/contract/test_task_queue_api.py"
Task: "Contract test DELETE /api/tasks/{task_id} in backend/tests/contract/test_task_queue_api.py"
Task: "Contract test POST /api/tasks/{task_id}/retry in backend/tests/contract/test_task_queue_api.py"
Task: "Contract test POST /api/tasks/submit/{task_type} in backend/tests/contract/test_task_queue_api.py"
```

### Phase 3.3 (Redis Services)
```bash
# T024-T027 can run together:
Task: "UserSession Redis service in backend/src/services/session_service.py"
Task: "TaskQueue Redis service in backend/src/services/task_queue_service.py"
Task: "ProgressEvent Redis service in backend/src/services/progress_service.py"
Task: "UIComponentState Redis service in backend/src/services/ui_state_service.py"
```

### Phase 3.4 (React Components)
```bash
# T038-T042 can run together:
Task: "TrendingAnalysis component in frontend/src/components/TrendingAnalysis.tsx"
Task: "ScriptGenerator component in frontend/src/components/ScriptGenerator.tsx"
Task: "MediaGenerator component in frontend/src/components/MediaGenerator.tsx"
Task: "VideoComposer component in frontend/src/components/VideoComposer.tsx"
Task: "YouTubeUploader component in frontend/src/components/YouTubeUploader.tsx"
```

## Notes
- [P] tasks = different files, no dependencies between them
- Verify contract tests fail before implementing endpoints
- Integration tests validate complete workflows from quickstart.md
- All file paths are relative to repository root
- Redis services must handle connection failures gracefully
- WebSocket connections need automatic reconnection logic
- Form auto-save should be debounced to avoid excessive Redis writes
- Component tests should use React Testing Library patterns
- Load tests validate concurrent user scenarios from quickstart.md