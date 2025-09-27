# Tasks: Custom Media Selection for Content Planning

**Input**: Design documents from `/code/contentizer/specs/011-i-want-to/`
**Prerequisites**: plan.md (required), spec.md (user requirements)

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.11+/FastAPI (backend), TypeScript 5+/React 18+ (frontend)
   → Structure: Web application (backend/ + frontend/)
2. Load optional design documents:
   → spec.md: Extract user scenarios and functional requirements ✓
   → User clarifications: JPG/PNG/MP4 support, media folder browsing ✓
3. Generate tasks by category:
   → Setup: Backend API structure, frontend components
   → Tests: API contract tests, integration tests
   → Core: File browsing service, media selection UI
   → Integration: Content planning workflow integration
   → Polish: Error handling, performance optimization
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
   → Backend before frontend integration
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph and parallel execution plan
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`
- **Frontend**: `frontend/src/`
- **Tests**: `backend/tests/`, `frontend/tests/`

## Phase 3.1: Setup
- [x] T001 Create media browsing API structure in backend/src/api/media_browsing.py
- [x] T002 [P] Create media selection React components structure in frontend/src/components/MediaSelection/
- [ ] T003 [P] Add media browsing dependencies to backend requirements

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Backend API Contract Tests
- [x] T004 [P] Contract test GET /api/media/browse in backend/tests/contract/test_media_browse_get.py
- [x] T005 [P] Contract test POST /api/content-planning/{id}/custom-media in backend/tests/contract/test_custom_media_post.py
- [x] T006 [P] Contract test DELETE /api/content-planning/{id}/custom-media/{asset_id} in backend/tests/contract/test_custom_media_delete.py
- [x] T007 [P] Contract test PUT /api/content-planning/{id}/custom-media/{asset_id} in backend/tests/contract/test_custom_media_put.py

### Integration Tests
- [x] T008 [P] Integration test media file browsing workflow in backend/tests/integration/test_media_browsing_flow.py
- [x] T009 [P] Integration test custom media selection in content planning in backend/tests/integration/test_content_planning_custom_media.py
- [x] T010 [P] Frontend integration test media selection component in frontend/tests/integration/test_media_selection.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Backend Services
- [x] T011 [P] MediaBrowsingService for file system scanning in backend/src/services/media_browsing_service.py
- [x] T012 [P] CustomMediaService for managing selected assets in backend/src/services/custom_media_service.py
- [x] T013 [P] File validation utilities (JPG/PNG/MP4) in backend/src/lib/file_validators.py

### Backend API Endpoints
- [x] T014 GET /api/media/browse endpoint implementation in backend/src/api/media_browsing.py
- [x] T015 POST /api/content-planning/{id}/custom-media endpoint in backend/src/api/content_planning.py
- [x] T016 [P] PUT /api/content-planning/{id}/custom-media/{asset_id} endpoint in backend/src/api/content_planning.py
- [x] T017 [P] DELETE /api/content-planning/{id}/custom-media/{asset_id} endpoint in backend/src/api/content_planning.py

### Frontend Components
- [ ] T018 [P] MediaBrowser component for file selection in frontend/src/components/MediaSelection/MediaBrowser.tsx
- [ ] T019 [P] MediaFileCard component for displaying files in frontend/src/components/MediaSelection/MediaFileCard.tsx
- [ ] T020 [P] SelectedMediaList component for managing selected assets in frontend/src/components/MediaSelection/SelectedMediaList.tsx
- [ ] T021 [P] MediaSelectionModal component for file browsing dialog in frontend/src/components/MediaSelection/MediaSelectionModal.tsx

### Frontend Services
- [ ] T022 [P] Media browsing API client in frontend/src/services/mediaBrowsingApi.ts
- [ ] T023 [P] Custom media management API client in frontend/src/services/customMediaApi.ts

## Phase 3.4: Integration
- [ ] T024 Integrate MediaSelection components into ContentPlanningPreview.tsx
- [ ] T025 Add "Use Existing Media" section to content planning UI in frontend/src/components/ContentPlanning/ContentPlanningPreview.tsx
- [ ] T026 Update content planning workflow to handle custom media assets in backend/src/services/enhanced_content_planner.py
- [ ] T027 Extend video generation to incorporate custom media files in backend/src/services/media_asset_generator.py

## Phase 3.5: Polish
- [ ] T028 [P] Add error handling for unsupported file formats in backend/src/services/media_browsing_service.py
- [ ] T029 [P] Add file size validation and performance optimization in backend/src/lib/file_validators.py
- [ ] T030 [P] Add loading states and error boundaries to MediaSelection components in frontend/src/components/MediaSelection/
- [ ] T031 [P] Add unit tests for MediaBrowsingService in backend/tests/unit/test_media_browsing_service.py
- [ ] T032 [P] Add unit tests for React components in frontend/tests/unit/MediaSelection/

## Parallel Execution Examples

### Phase 3.2 (All can run in parallel):
```bash
# Run contract tests in parallel
Task agent backend/tests/contract/test_media_browse_get.py &
Task agent backend/tests/contract/test_custom_media_post.py &
Task agent backend/tests/contract/test_custom_media_delete.py &
Task agent backend/tests/contract/test_custom_media_put.py &
Task agent backend/tests/integration/test_media_browsing_flow.py &
Task agent frontend/tests/integration/test_media_selection.test.tsx &
wait
```

### Phase 3.3 (Services and components in parallel):
```bash
# Backend services
Task agent backend/src/services/media_browsing_service.py &
Task agent backend/src/services/custom_media_service.py &
Task agent backend/src/lib/file_validators.py &

# Frontend components
Task agent frontend/src/components/MediaSelection/MediaBrowser.tsx &
Task agent frontend/src/components/MediaSelection/MediaFileCard.tsx &
Task agent frontend/src/components/MediaSelection/SelectedMediaList.tsx &
wait

# API endpoints (sequential - same file)
Task agent backend/src/api/media_browsing.py
Task agent backend/src/api/content_planning.py
```

## Dependencies
- T001-T003 (Setup) → All other tasks
- T004-T010 (Tests) → T011+ (Implementation)
- T011-T013 (Backend Services) → T014-T017 (API Endpoints)
- T018-T021 (Frontend Components) → T024-T025 (Integration)
- T022-T023 (Frontend Services) → T024-T025 (Integration)
- T014-T017 (API Endpoints) → T024-T027 (Integration)
- All Core → T028-T032 (Polish)

## Success Criteria
- [ ] Users can browse JPG/PNG/MP4 files from media folder
- [ ] Users can select custom media files in content planning stage
- [ ] Selected files appear in same format as AI-generated assets
- [ ] Users can edit/delete selected custom media
- [ ] Custom media integrates with video generation workflow
- [ ] "Use Existing Media" section appears below AI-generated content
- [ ] All contract tests pass
- [ ] All integration scenarios work end-to-end