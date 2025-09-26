# Tasks: Upgrade to Gemini 2.5 Flash Image Model

**Input**: Design documents from `/specs/007-https-aistudio-google/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+, FastAPI, Celery, google-generativeai library
   → Structure: Web app (backend/frontend)
2. Load optional design documents:
   → data-model.md: MediaAsset, GeminiModelConfig, ServiceHealth
   → contracts/: media-generation.yml → contract tests
   → quickstart.md: 5 test scenarios → integration tests
3. Generate tasks by category:
   → Setup: Environment configuration, dependencies
   → Tests: Contract tests for API endpoints, integration tests for scenarios
   → Core: GeminiService updates, model configuration, health monitoring
   → Integration: Service integration, error handling
   → Polish: Performance validation, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → GeminiService modifications = sequential (same file)
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. SUCCESS: Tasks ready for execution
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Backend paths: `backend/src/`, `backend/tests/`

## Phase 3.1: Setup
- [x] T001 Add GEMINI_IMAGE_MODEL environment variable to backend configuration
- [x] T002 [P] Update environment templates with new Gemini model settings
- [x] T003 [P] Verify google-generativeai library supports gemini-2.5-flash-image model

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test POST /api/media/generate in backend/tests/contract/test_media_generation_post.py
- [x] T005 [P] Contract test GET /api/media/assets/{asset_id} in backend/tests/contract/test_media_assets_get.py
- [x] T006 [P] Contract test GET /api/health/models in backend/tests/contract/test_health_models_get.py
- [x] T007 [P] Integration test model configuration verification in backend/tests/integration/test_model_configuration.py
- [x] T008 [P] Integration test image generation with new model in backend/tests/integration/test_image_generation.py
- [x] T009 [P] Integration test fallback mechanism in backend/tests/integration/test_model_fallback.py
- [x] T010 [P] Integration test asset metadata tracking in backend/tests/integration/test_asset_metadata.py
- [x] T011 [P] Integration test end-to-end video generation in backend/tests/integration/test_video_generation.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T012 Create GeminiModelConfig class in backend/src/models/gemini_model_config.py
- [x] T013 Enhance MediaAsset model validation in backend/src/models/media_asset.py
- [x] T014 Update ServiceHealth model for model tracking in backend/src/models/service_status.py
- [x] T015 Update GeminiService to support configurable models in backend/src/services/gemini_service.py
- [x] T016 Add model availability checking to GeminiService in backend/src/services/gemini_service.py
- [x] T017 Implement fallback logic in GeminiService in backend/src/services/gemini_service.py
- [x] T018 Add model health monitoring service in backend/src/services/model_health_service.py
- [x] T019 Update media generation endpoints with model selection in backend/src/api/media.py
- [x] T020 Add model health endpoints in backend/src/api/health.py
- [x] T021 Update media asset endpoints with model metadata in backend/src/api/media_assets.py

## Phase 3.4: Integration
- [x] T022 Connect model configuration to environment variables in backend/src/services/gemini_service.py
- [x] T023 Integrate model health monitoring with existing health checks in backend/src/services/health_service.py
- [x] T024 Update Celery tasks to use new model configuration in backend/src/tasks/media_tasks.py
- [x] T025 Add error handling for model unavailability scenarios in backend/src/services/gemini_service.py
- [x] T026 Update progress tracking to include model information in backend/src/services/progress_service.py

## Phase 3.5: Polish
- [x] T027 [P] Unit tests for GeminiModelConfig validation in backend/tests/unit/test_gemini_model_config.py
- [x] T028 [P] Unit tests for model selection logic in backend/tests/unit/test_model_selection.py
- [x] T029 [P] Unit tests for fallback mechanism in backend/tests/unit/test_fallback_logic.py
- [x] T030 Performance tests for model response times in backend/tests/performance/test_model_performance.py
- [x] T031 [P] Update API documentation for new model parameters in backend/docs/api.md
- [x] T032 Run quickstart validation scenarios from quickstart.md
- [x] T033 Load testing with concurrent model requests
- [x] T034 Verify existing functionality still works with model upgrade

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T011) before implementation (T012-T026)
- T012 (GeminiModelConfig) blocks T015-T017 (GeminiService updates)
- T018 (ModelHealthService) blocks T020 (health endpoints)
- T015-T017 (GeminiService) blocks T022, T024-T025 (integrations)
- Implementation before polish (T027-T034)

## Parallel Example
```bash
# Launch T004-T011 together (contract and integration tests):
Task: "Contract test POST /api/media/generate in backend/tests/contract/test_media_generation_post.py"
Task: "Contract test GET /api/media/assets/{asset_id} in backend/tests/contract/test_media_assets_get.py"
Task: "Contract test GET /api/health/models in backend/tests/contract/test_health_models_get.py"
Task: "Integration test model configuration verification in backend/tests/integration/test_model_configuration.py"
Task: "Integration test image generation with new model in backend/tests/integration/test_image_generation.py"

# Launch T012-T014 together (model updates in different files):
Task: "Create GeminiModelConfig class in backend/src/models/gemini_model_config.py"
Task: "Enhance MediaAsset model validation in backend/src/models/media_asset.py"
Task: "Update ServiceHealth model for model tracking in backend/src/models/service_status.py"
```

## Key File Paths
**Models**:
- `backend/src/models/gemini_model_config.py` (new)
- `backend/src/models/media_asset.py` (enhance existing)
- `backend/src/models/service_status.py` (enhance existing)

**Services**:
- `backend/src/services/gemini_service.py` (primary changes)
- `backend/src/services/model_health_service.py` (new)
- `backend/src/services/health_service.py` (integrate)

**APIs**:
- `backend/src/api/media.py` (enhance endpoints)
- `backend/src/api/health.py` (add model health)
- `backend/src/api/media_assets.py` (add model metadata)

**Tasks**:
- `backend/src/tasks/media_tasks.py` (update for new model)

**Tests**:
- `backend/tests/contract/test_media_generation_post.py`
- `backend/tests/contract/test_media_assets_get.py`
- `backend/tests/contract/test_health_models_get.py`
- `backend/tests/integration/test_model_*.py` (5 files)
- `backend/tests/unit/test_*.py` (3 files)

## Notes
- [P] tasks = different files, no dependencies
- GeminiService tasks (T015-T017, T022, T025) are sequential (same file)
- Verify tests fail before implementing
- Commit after each task
- Model fallback must be thoroughly tested
- Performance regression monitoring critical

## Task Generation Rules Applied

1. **From Contracts** (media-generation.yml):
   - POST /api/media/generate → T004 contract test + T019 implementation
   - GET /api/media/assets/{asset_id} → T005 contract test + T021 implementation
   - GET /api/health/models → T006 contract test + T020 implementation

2. **From Data Model**:
   - GeminiModelConfig entity → T012 model creation [P]
   - MediaAsset enhancements → T013 model updates [P]
   - ServiceHealth enhancements → T014 model updates [P]

3. **From Quickstart Scenarios**:
   - Model configuration verification → T007 integration test [P]
   - Image generation with new model → T008 integration test [P]
   - Fallback mechanism testing → T009 integration test [P]
   - Asset metadata tracking → T010 integration test [P]
   - End-to-end video generation → T011 integration test [P]

4. **Ordering Applied**:
   - Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - TDD: All tests (T004-T011) before implementation (T012-T026)

## Validation Checklist
*GATE: Checked before execution*

- [x] All contracts have corresponding tests (T004-T006)
- [x] All entities have model tasks (T012-T014)
- [x] All tests come before implementation
- [x] Parallel tasks truly independent (different file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task