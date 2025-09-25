# Tasks: Real Video Generation Implementation

**Input**: Design documents from `/code/contentizer/specs/006-implement-the-real/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+, FastAPI, Celery, Redis, SQLAlchemy, ffmpeg-python
   → Structure: Web application (backend + frontend)
2. Load design documents:
   → data-model.md: GeneratedVideo, MediaAsset, VideoGenerationJob, MediaStorage
   → contracts/: Video generation API endpoints
   → quickstart.md: Test scenarios for validation
3. Generate tasks by category:
   → Setup: Media directory structure, FFmpeg integration
   → Tests: Contract tests for 7 API endpoints, integration tests
   → Core: 4 database models, video processing services
   → Integration: File storage, video serving, Celery task updates
   → Polish: Error handling, cleanup, performance validation
4. Apply task rules: Different files marked [P], same file sequential
5. Number tasks T001-T031
6. TDD order: Tests before implementation
7. Dependencies: Models → Services → Endpoints → Integration
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Exact file paths included in task descriptions
- Web app structure: `backend/src/`, `frontend/src/`

## Phase 3.1: Setup & Environment

- [x] T001 Create media directory structure in `media/videos/`, `media/assets/images/`, `media/assets/audio/`, `media/assets/temp/`, `media/stock/`
- [x] T002 Verify FFmpeg installation and add wrapper utilities in `backend/src/lib/ffmpeg_utils.py`
- [x] T003 [P] Add ffmpeg-python dependency validation in `backend/src/lib/system_check.py`

## Phase 3.2: Database Models (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [x] T004 [P] Contract test POST /api/videos/generate in `tests/contract/test_video_generation_generate.py`
- [x] T005 [P] Contract test GET /api/videos/{video_id} in `tests/contract/test_video_generation_get.py`
- [x] T006 [P] Contract test GET /api/videos/{video_id}/download in `tests/contract/test_video_download.py`
- [x] T007 [P] Contract test GET /api/videos/{video_id}/stream in `tests/contract/test_video_streaming.py`
- [x] T008 [P] Contract test GET /api/videos/jobs/{job_id}/status in `tests/contract/test_job_status.py`
- [x] T009 [P] Contract test POST /api/videos/jobs/{job_id}/cancel in `tests/contract/test_job_cancel.py`
- [x] T010 [P] Contract test GET /api/media/assets/{asset_id} in `tests/contract/test_media_assets.py`
- [x] T011 [P] Integration test full video generation workflow in `tests/integration/test_video_generation_workflow.py`
- [x] T012 [P] Integration test video file cleanup on failure in `tests/integration/test_cleanup_on_failure.py`

## Phase 3.3: Data Models (ONLY after tests are failing)

- [x] T013 [P] GeneratedVideo model in `backend/src/models/generated_video.py`
- [x] T014 [P] MediaAsset model in `backend/src/models/media_asset.py`
- [x] T015 [P] VideoGenerationJob model in `backend/src/models/video_generation_job.py`
- [x] T016 [P] MediaStorage model in `backend/src/models/media_storage.py`
- [x] T017 Database migration for new video generation tables in `backend/migrations/`

## Phase 3.4: Core Services

- [x] T018 [P] MediaAssetGenerator service in `backend/src/services/media_asset_generator.py`
- [x] T019 [P] VideoComposer service using FFmpeg in `backend/src/services/video_composer.py`
- [x] T020 [P] StorageManager service for file organization in `backend/src/services/storage_manager.py`
- [x] T021 VideoGenerationService orchestrator in `backend/src/services/video_generation_service.py`

## Phase 3.5: Celery Task Implementation

- [x] T022 Replace mock media generation in `backend/src/tasks/media_tasks.py::generate_media_from_script`
- [x] T023 Replace mock video composition in `backend/src/tasks/media_tasks.py::compose_video`
- [x] T024 Add file cleanup task in `backend/src/tasks/cleanup_tasks.py`

## Phase 3.6: API Endpoints

- [x] T025 POST /api/videos/generate endpoint in `backend/src/api/video_generation.py`
- [x] T026 GET /api/videos/{video_id} endpoint in `backend/src/api/video_generation.py`
- [x] T027 GET /api/videos/{video_id}/download endpoint in `backend/src/api/video_serving.py`
- [x] T028 GET /api/videos/{video_id}/stream endpoint in `backend/src/api/video_serving.py`
- [x] T029 GET /api/videos/jobs/{job_id}/status endpoint in `backend/src/api/job_management.py`
- [x] T030 POST /api/videos/jobs/{job_id}/cancel endpoint in `backend/src/api/job_management.py`
- [x] T031 GET /api/media/assets/{asset_id} endpoint in `backend/src/api/media_assets.py`

## Phase 3.7: Integration & Configuration

- [x] T032 Update FastAPI app to include new video generation routes in `backend/src/main.py`
- [x] T033 Configure static file serving for media files in `backend/src/config/static_files.py`
- [x] T034 Add video generation progress WebSocket events in `backend/src/services/progress_service.py`
- [x] T035 Implement storage quota and cleanup policies in `backend/src/services/storage_manager.py`

## Phase 3.8: Error Handling & Validation

- [ ] T036 [P] Add video file validation utilities in `backend/src/lib/video_validator.py`
- [ ] T037 [P] Add comprehensive error handling for FFmpeg failures in `backend/src/lib/error_handlers.py`
- [ ] T038 Add graceful degradation for missing assets in `backend/src/services/video_generation_service.py`

## Phase 3.9: Frontend Integration

- [ ] T039 [P] Add video player component in `frontend/src/components/VideoPlayer.tsx`
- [ ] T040 [P] Add download progress indicator in `frontend/src/components/DownloadProgress.tsx`
- [ ] T041 Update video generation UI to handle real videos in `frontend/src/pages/VideoGeneration.tsx`

## Phase 3.10: Polish & Performance

- [ ] T042 [P] Unit tests for video validation in `tests/unit/test_video_validator.py`
- [ ] T043 [P] Unit tests for storage management in `tests/unit/test_storage_manager.py`
- [ ] T044 [P] Performance tests for video generation speed in `tests/performance/test_generation_speed.py`
- [ ] T045 Execute quickstart validation scenario from `specs/006-implement-the-real/quickstart.md`
- [ ] T046 [P] Add monitoring for disk usage and performance metrics in `backend/src/lib/monitoring.py`
- [ ] T047 Document video generation API in `docs/api/video-generation.md`

## Dependencies

**Strict Order Requirements:**
- Setup (T001-T003) before everything else
- Contract tests (T004-T012) before ANY implementation
- Models (T013-T017) before services (T018-T021)
- Services before endpoints (T025-T031)
- Endpoints before integration (T032-T035)

**Blocking Dependencies:**
- T013-T016 block T018-T021 (models before services)
- T018-T021 block T022-T024 (services before Celery tasks)
- T022-T024 block T025-T031 (Celery tasks before endpoints)
- T025-T031 block T032-T035 (endpoints before integration)
- All implementation blocks polish (T042-T047)

## Parallel Execution Examples

### Phase 3.2: Contract Tests (can run simultaneously)
```bash
# Launch all contract tests together:
Task: "Contract test POST /api/videos/generate in tests/contract/test_video_generation_generate.py"
Task: "Contract test GET /api/videos/{video_id} in tests/contract/test_video_generation_get.py"
Task: "Contract test GET /api/videos/{video_id}/download in tests/contract/test_video_download.py"
Task: "Contract test GET /api/videos/{video_id}/stream in tests/contract/test_video_streaming.py"
Task: "Contract test GET /api/videos/jobs/{job_id}/status in tests/contract/test_job_status.py"
Task: "Contract test POST /api/videos/jobs/{job_id}/cancel in tests/contract/test_job_cancel.py"
Task: "Contract test GET /api/media/assets/{asset_id} in tests/contract/test_media_assets.py"
```

### Phase 3.3: Data Models (can run simultaneously)
```bash
# Launch all model creation together:
Task: "GeneratedVideo model in backend/src/models/generated_video.py"
Task: "MediaAsset model in backend/src/models/media_asset.py"
Task: "VideoGenerationJob model in backend/src/models/video_generation_job.py"
Task: "MediaStorage model in backend/src/models/media_storage.py"
```

### Phase 3.4: Core Services (can run simultaneously)
```bash
# Launch service implementations together:
Task: "MediaAssetGenerator service in backend/src/services/media_asset_generator.py"
Task: "VideoComposer service using FFmpeg in backend/src/services/video_composer.py"
Task: "StorageManager service for file organization in backend/src/services/storage_manager.py"
```

### Phase 3.9: Frontend Components (can run simultaneously)
```bash
# Launch frontend work together:
Task: "Add video player component in frontend/src/components/VideoPlayer.tsx"
Task: "Add download progress indicator in frontend/src/components/DownloadProgress.tsx"
```

## Implementation Notes

### File Modification Conflicts
- T022-T023: Both modify `backend/src/tasks/media_tasks.py` → Sequential execution required
- T025-T026: Both modify `backend/src/api/video_generation.py` → Sequential execution required
- T027-T028: Both modify `backend/src/api/video_serving.py` → Sequential execution required
- T029-T030: Both modify `backend/src/api/job_management.py` → Sequential execution required
- T034, T035, T038: All modify different services → Can be parallel

### Technology Integration Points
- FFmpeg integration requires system-level validation (T002)
- File serving requires FastAPI static file configuration (T033)
- Progress tracking extends existing WebSocket infrastructure (T034)
- Database models require migration before service implementation (T017)

### Validation Requirements
- All video files must pass format validation (T036)
- Storage quotas must be enforced to prevent disk exhaustion (T035)
- Error cleanup must prevent orphaned files (T024, T037)
- Performance must meet <60 second generation target (T044)

## Success Criteria

**Technical Validation:**
1. All contract tests pass with real implementations
2. Video files are physically created and accessible
3. FFmpeg integration works without system errors
4. File cleanup prevents storage bloat
5. Progress tracking reflects actual generation stages

**Performance Validation:**
1. 30-second video generates in <60 seconds
2. No memory leaks during generation process
3. Concurrent generation doesn't crash system
4. Database queries remain performant under load

**Integration Validation:**
1. Frontend can play generated videos
2. Download and streaming work correctly
3. WebSocket progress updates are accurate
4. Error handling provides useful feedback

## Task Generation Rules Applied

1. **From Contracts**: 7 contract files → 7 contract test tasks [P] (T004-T010)
2. **From Data Model**: 4 entities → 4 model tasks [P] (T013-T016)
3. **From User Stories**: Full workflow → 2 integration tests [P] (T011-T012)
4. **Ordering**: Setup → Tests → Models → Services → Endpoints → Polish
5. **Parallel Marking**: Different files marked [P], same file sequential
6. **TDD Enforcement**: All tests before any implementation

## Validation Checklist

- [x] All 7 contracts have corresponding test tasks
- [x] All 4 entities have model creation tasks
- [x] All tests (T004-T012) come before implementation (T013+)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task conflicts with another [P] task on same file