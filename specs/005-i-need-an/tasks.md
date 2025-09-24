# Tasks: Script Upload Option

**Input**: Design documents from `/code/contentizer/specs/005-i-need-an/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+/FastAPI (backend), TypeScript 5+/React 18+ (frontend)
   → Libraries: SQLAlchemy, Redis, Celery, Vite
   → Structure: Web app (backend/ + frontend/)
2. Load design documents:
   → data-model.md: UploadedScript, WorkflowState entities
   → contracts/: Script upload API, workflow mode API, frontend components
   → quickstart.md: File upload, text input, error handling scenarios
3. Generated tasks by category:
   → Setup: Dependencies, database migrations
   → Tests: Contract tests, integration tests
   → Core: Models, services, API endpoints, frontend components
   → Integration: Workflow integration, validation
   → Polish: Error handling, performance, documentation
4. Applied task rules:
   → Different files = marked [P] for parallel
   → Tests before implementation (TDD)
   → Dependencies ordered properly
5. Tasks numbered T001-T029
6. Parallel execution examples provided
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- Paths reflect web application structure from implementation plan

## Phase 3.1: Setup
- [x] T001 Create database migration for uploaded_scripts table in backend/src/migrations/add_script_upload_tables.py
- [x] T002 Extend workflows table schema in backend/src/migrations/extend_workflow_tables.py
- [x] T003 [P] Add multipart/form-data support validation in backend/requirements.txt (if needed)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test POST /api/v1/scripts/upload in backend/tests/contract/test_script_upload_api.py
- [x] T005 [P] Contract test GET /api/v1/scripts/{script_id} in backend/tests/contract/test_script_retrieval_api.py
- [x] T006 [P] Contract test DELETE /api/v1/scripts/{script_id} in backend/tests/contract/test_script_deletion_api.py
- [x] T007 [P] Contract test PUT /api/v1/workflows/{workflow_id}/mode in backend/tests/contract/test_workflow_mode_api.py
- [x] T008 [P] Integration test file upload workflow in backend/tests/integration/test_file_upload_workflow.py
- [x] T009 [P] Integration test text input workflow in backend/tests/integration/test_text_input_workflow.py
- [x] T010 [P] Integration test error handling scenarios in backend/tests/integration/test_upload_error_handling.py
- [x] T011 [P] Frontend component test ScriptUploadComponent in frontend/tests/components/ScriptUploadComponent.test.tsx
- [x] T012 [P] Frontend component test WorkflowModeSelector in frontend/tests/components/WorkflowModeSelector.test.tsx
- [x] T013 [P] Frontend component test ScriptValidationStatus in frontend/tests/components/ScriptValidationStatus.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)
### Backend Models & Services
- [x] T014 [P] UploadedScript model in backend/src/models/uploaded_script.py
- [x] T015 [P] WorkflowState model extensions in backend/src/models/workflow.py
- [x] T016 [P] ScriptUploadService in backend/src/services/script_upload_service.py
- [x] T017 [P] WorkflowModeService in backend/src/services/workflow_mode_service.py
- [x] T018 [P] ScriptValidationService in backend/src/services/script_validation_service.py

### Backend API Endpoints
- [x] T019 POST /api/v1/scripts/upload endpoint in backend/src/api/script_upload.py
- [x] T020 GET /api/v1/scripts/{script_id} endpoint in backend/src/api/script_upload.py
- [x] T021 DELETE /api/v1/scripts/{script_id} endpoint in backend/src/api/script_upload.py
- [x] T022 PUT /api/v1/workflows/{workflow_id}/mode endpoint in backend/src/api/workflow.py

### Frontend Components
- [x] T023 [P] ScriptUploadComponent in frontend/src/components/ScriptUpload/ScriptUploadComponent.tsx
- [x] T024 [P] WorkflowModeSelector in frontend/src/components/Workflow/WorkflowModeSelector.tsx
- [x] T025 [P] ScriptValidationStatus in frontend/src/components/ScriptUpload/ScriptValidationStatus.tsx
- [x] T026 [P] Upload service API client in frontend/src/services/scriptUploadService.ts

## Phase 3.4: Integration
- [x] T027 Integrate script upload with existing workflow engine in backend/src/services/workflow_engine.py
- [x] T028 Add workflow mode routing logic in backend/src/api/middleware/workflow_routing.py
- [x] T029 Connect frontend components to workflow pages in frontend/src/pages/WorkflowPage.tsx

## Phase 3.5: Polish
- [x] T030 [P] Input validation and sanitization in backend/src/utils/script_validators.py
- [x] T031 [P] Error handling and user feedback in frontend/src/hooks/useScriptUpload.ts
- [x] T032 [P] Performance optimization for large file uploads in backend/src/middleware/upload_middleware.py
- [x] T033 End-to-end workflow testing following quickstart scenarios
- [x] T034 [P] Update API documentation in docs/api/script-upload.md

## Dependencies
- Setup (T001-T003) before all other phases
- Tests (T004-T013) before implementation (T014-T029)
- Models (T014-T015) before services (T016-T018)
- Services (T016-T018) before API endpoints (T019-T022)
- Backend API (T019-T022) before frontend services (T026)
- Components (T023-T025) can run parallel with backend development
- Integration (T027-T029) requires core implementation complete
- Polish (T030-T034) after integration complete

## Parallel Example
```
# Launch contract tests together (Phase 3.2):
Task: "Contract test POST /api/v1/scripts/upload in backend/tests/contract/test_script_upload_api.py"
Task: "Contract test GET /api/v1/scripts/{script_id} in backend/tests/contract/test_script_retrieval_api.py"
Task: "Contract test DELETE /api/v1/scripts/{script_id} in backend/tests/contract/test_script_deletion_api.py"
Task: "Contract test PUT /api/v1/workflows/{workflow_id}/mode in backend/tests/contract/test_workflow_mode_api.py"

# Launch model creation together (Phase 3.3):
Task: "UploadedScript model in backend/src/models/uploaded_script.py"
Task: "ScriptUploadService in backend/src/services/script_upload_service.py"
Task: "WorkflowModeService in backend/src/services/workflow_mode_service.py"

# Launch frontend components together (Phase 3.3):
Task: "ScriptUploadComponent in frontend/src/components/ScriptUpload/ScriptUploadComponent.tsx"
Task: "WorkflowModeSelector in frontend/src/components/Workflow/WorkflowModeSelector.tsx"
Task: "ScriptValidationStatus in frontend/src/components/ScriptUpload/ScriptValidationStatus.tsx"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing (TDD requirement)
- Database migrations (T001-T002) must run before any model/service work
- Frontend components can develop in parallel with backend API
- Integration phase connects all pieces together
- Follow existing codebase patterns for FastAPI/React integration

## Task Generation Rules Applied
1. **From Contracts**: Each API endpoint → contract test + implementation task
2. **From Data Model**: Each entity → model task, relationships → service tasks
3. **From Frontend Components**: Each component → test + implementation task
4. **From User Stories**: Each quickstart scenario → integration test task
5. **Ordering**: Setup → Tests → Models → Services → Endpoints → Components → Integration → Polish

## Validation Checklist
- [x] All contract endpoints have corresponding tests (T004-T007)
- [x] All entities have model tasks (T014-T015)
- [x] All tests come before implementation (T004-T013 before T014+)
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Frontend and backend tasks properly separated
- [x] Database migrations come first (T001-T002)
- [x] Integration tests cover all quickstart scenarios