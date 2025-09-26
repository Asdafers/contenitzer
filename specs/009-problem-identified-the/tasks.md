# Tasks: Real AI-Powered Media Generation

**Input**: Design documents from `/specs/009-problem-identified-the/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Phase 3.1: Setup
- [x] T001 Verify Gemini API environment setup and google-generativeai library version compatibility
- [x] T002 [P] Configure pytest fixtures for Gemini API mocking in backend/tests/conftest.py
- [x] T003 [P] Add AI processing error types to backend/src/lib/exceptions.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test enhanced media generation API in backend/tests/contract/test_enhanced_media_generation.py
- [ ] T005 [P] Integration test AI script analysis workflow in backend/tests/integration/test_ai_script_analysis.py
- [ ] T006 [P] Integration test Gemini image generation in backend/tests/integration/test_gemini_image_generation.py
- [ ] T007 [P] Integration test real AI processing progress tracking in backend/tests/integration/test_ai_progress_tracking.py
- [ ] T008 [P] Integration test error handling without fallbacks in backend/tests/integration/test_ai_error_handling.py

## Phase 3.3: New Services (ONLY after tests are failing)
- [ ] T009 [P] GeminiImageService for AI image generation in backend/src/services/gemini_image_service.py
- [ ] T010 [P] ScriptAnalysisService for AI script theme extraction in backend/src/services/script_analysis_service.py
- [ ] T011 [P] Enhanced progress event types for AI processing stages in backend/src/services/progress_service.py

## Phase 3.4: Enhanced Models & Data
- [ ] T012 [P] Add AI processing fields to MediaAsset model in backend/src/models/media_asset.py
- [ ] T013 [P] Add AI processing job fields to VideoGenerationJob model in backend/src/models/video_generation_job.py
- [ ] T014 [P] Enhanced progress event schemas in backend/src/services/progress_service.py
- [ ] T015 Database migration for new AI processing fields in backend/migrations/

## Phase 3.5: Core AI Integration
- [ ] T016 Replace _generate_background_image with real Gemini calls in backend/src/services/media_asset_generator.py
- [ ] T017 Replace _generate_audio_track with AI-planned audio in backend/src/services/media_asset_generator.py
- [ ] T018 Update media generation progress tracking with real AI stages in backend/src/tasks/media_tasks.py
- [ ] T019 Implement detailed error reporting without fallbacks in backend/src/services/media_asset_generator.py

## Phase 3.6: API Enhancement
- [ ] T020 Update media generation API endpoint to validate AI model parameters in backend/src/api/tasks.py
- [ ] T021 Enhanced WebSocket progress events with AI processing details in backend/src/services/progress_service.py

## Phase 3.7: Frontend Integration
- [ ] T022 [P] Update media generation form to show AI model selection in frontend/src/components/WorkflowPage.tsx
- [ ] T023 [P] Enhanced progress display for AI processing stages in frontend/src/components/ProgressDisplay.tsx
- [ ] T024 [P] Detailed error display with debugging information in frontend/src/components/ErrorDisplay.tsx

## Phase 3.8: Integration & Validation
- [ ] T025 End-to-end test of complete AI media generation workflow in backend/tests/integration/test_complete_ai_workflow.py
- [ ] T026 Performance test to verify realistic AI processing times in backend/tests/integration/test_ai_performance.py
- [ ] T027 Run manual validation using quickstart.md test scenarios

## Phase 3.9: Polish
- [ ] T028 [P] Unit tests for Gemini service error handling in backend/tests/unit/test_gemini_services.py
- [ ] T029 [P] Unit tests for AI progress tracking in backend/tests/unit/test_ai_progress.py
- [ ] T030 [P] Frontend unit tests for AI model selection in frontend/src/tests/AIModelSelection.test.tsx
- [ ] T031 Add AI processing metrics logging for debugging in backend/src/services/gemini_image_service.py
- [ ] T032 Update API documentation with AI processing details in specs/009-problem-identified-the/contracts/

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T008) before implementation (T009-T027)
- T009, T010 block T016, T017 (services before usage)
- T012, T013, T014 block T015 (models before migration)
- T015 blocks T016-T019 (migration before AI integration)
- T016-T019 block T020-T021 (core before API)
- T020-T021 block T022-T024 (API before frontend)
- Core implementation (T009-T024) before validation (T025-T027)
- Everything before polish (T028-T032)

## Parallel Execution Examples

### Setup Phase (can run together):
```
Task: "Configure pytest fixtures for Gemini API mocking in backend/tests/conftest.py"
Task: "Add AI processing error types to backend/src/lib/exceptions.py"
```

### Test Creation Phase (all independent files):
```
Task: "Contract test enhanced media generation API in backend/tests/contract/test_enhanced_media_generation.py"
Task: "Integration test AI script analysis workflow in backend/tests/integration/test_ai_script_analysis.py"
Task: "Integration test Gemini image generation in backend/tests/integration/test_gemini_image_generation.py"
Task: "Integration test real AI processing progress tracking in backend/tests/integration/test_ai_progress_tracking.py"
Task: "Integration test error handling without fallbacks in backend/tests/integration/test_ai_error_handling.py"
```

### New Services Phase (independent files):
```
Task: "GeminiImageService for AI image generation in backend/src/services/gemini_image_service.py"
Task: "ScriptAnalysisService for AI script theme extraction in backend/src/services/script_analysis_service.py"
```

### Model Enhancement Phase (different model files):
```
Task: "Add AI processing fields to MediaAsset model in backend/src/models/media_asset.py"
Task: "Add AI processing job fields to VideoGenerationJob model in backend/src/models/video_generation_job.py"
```

### Frontend Phase (independent components):
```
Task: "Update media generation form to show AI model selection in frontend/src/components/WorkflowPage.tsx"
Task: "Enhanced progress display for AI processing stages in frontend/src/components/ProgressDisplay.tsx"
Task: "Detailed error display with debugging information in frontend/src/components/ErrorDisplay.tsx"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify all tests fail before implementing (TDD requirement)
- No fallback behavior - all AI failures must error with detailed debugging info
- Focus on replacing placeholder generation with real Gemini AI calls
- Maintain realistic processing times (seconds to minutes, not subseconds)
- All progress updates must reflect actual AI processing stages

## Specific Requirements Validation
- **FR-001**: T016, T017 implement real Gemini model usage
- **FR-002**: T010 implements AI script content analysis
- **FR-003**: T016 replaces placeholder images with real AI generation
- **FR-004**: T018, T021 implement realistic progress tracking
- **FR-005**: T020 ensures model parameters are respected
- **FR-006**: T019, T008 implement no-fallback error handling
- **FR-007**: T021, T023 provide detailed AI processing feedback
- **FR-008**: T017 implements AI-planned audio generation
- **FR-009**: T010, T016 ensure contextual relevance

## Task Generation Rules Applied
1. **From Contracts**: T004 (enhanced_media_generation.yaml → contract test)
2. **From Data Model**: T012, T013 (Enhanced entities → model tasks)
3. **From User Stories**: T005-T008, T025 (Quickstart scenarios → integration tests)
4. **From Research**: T009, T010 (New services identified → service creation tasks)

## Validation Checklist ✅
- [x] All contracts have corresponding tests (T004)
- [x] All enhanced entities have model tasks (T012, T013)
- [x] All tests come before implementation (T004-T008 before T009+)
- [x] Parallel tasks truly independent (verified file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task