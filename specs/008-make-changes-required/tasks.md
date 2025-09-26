# Tasks: Frontend Gemini Model Integration

**Input**: Design documents from `/specs/008-make-changes-required/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Focus on frontend React components and TypeScript interfaces
- All paths relative to repository root

## Phase 3.1: Setup
- [x] T001 Install additional frontend dependencies for Gemini integration in frontend/package.json
- [x] T002 [P] Configure TypeScript interfaces for Gemini models in frontend/src/types/gemini.ts
- [x] T003 [P] Set up Jest test configuration for React components in frontend/jest.config.js

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test GET /api/health/models in frontend/src/tests/contract/test_health_models_get.ts
- [x] T005 [P] Contract test POST /api/media/generate with model selection in frontend/src/tests/contract/test_media_generation_post.ts
- [x] T006 [P] Contract test GET /api/media/assets/{id} with model metadata in frontend/src/tests/contract/test_media_assets_get.ts
- [x] T007 [P] Contract test GET /api/jobs/{id}/status in frontend/src/tests/contract/test_job_status_get.ts
- [ ] T008 [P] Component test ModelSelector component in frontend/src/tests/components/test_model_selector.tsx
- [ ] T009 [P] Component test HealthStatusDisplay component in frontend/src/tests/components/test_health_status_display.tsx
- [ ] T010 [P] Component test AssetMetadataView component in frontend/src/tests/components/test_asset_metadata_view.tsx
- [ ] T011 [P] Integration test model selection workflow in frontend/src/tests/integration/test_model_selection_workflow.ts
- [ ] T012 [P] Integration test health monitoring updates in frontend/src/tests/integration/test_health_monitoring.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T013 [P] Update MediaGenerateRequest interface in frontend/src/services/api.ts
- [ ] T014 [P] Update MediaGenerateResponse interface in frontend/src/services/api.ts
- [ ] T015 [P] Add ModelHealthStatus interfaces in frontend/src/types/health.ts
- [ ] T016 [P] Add SystemModelHealth interface in frontend/src/types/health.ts
- [ ] T017 [P] Enhanced AssetMetadata interface in frontend/src/types/assets.ts
- [ ] T018 [P] Create ModelSelector React component in frontend/src/components/ModelSelector.tsx
- [ ] T019 [P] Create HealthStatusDisplay React component in frontend/src/components/HealthStatusDisplay.tsx
- [ ] T020 [P] Create AssetMetadataView React component in frontend/src/components/AssetMetadataView.tsx
- [ ] T021 [P] Create useModelHealth custom hook in frontend/src/hooks/useModelHealth.ts
- [ ] T022 [P] Create useModelSelection custom hook in frontend/src/hooks/useModelSelection.ts
- [ ] T023 Update media generation API methods in frontend/src/services/api.ts
- [ ] T024 Update asset detail API methods in frontend/src/services/api.ts
- [ ] T025 Add model health API methods in frontend/src/services/api.ts

## Phase 3.4: Integration
- [ ] T026 Integrate ModelSelector into media generation form in frontend/src/pages/MediaGeneration.tsx
- [ ] T027 Integrate HealthStatusDisplay into dashboard in frontend/src/pages/Dashboard.tsx
- [ ] T028 Integrate AssetMetadataView into asset detail pages in frontend/src/pages/AssetDetail.tsx
- [ ] T029 Add model selection to workflow forms in frontend/src/components/WorkflowForm.tsx
- [ ] T030 Update job status tracking with model info in frontend/src/components/JobStatusTracker.tsx
- [ ] T031 Add error handling for model unavailability in frontend/src/services/errorHandler.ts
- [ ] T032 Implement user preferences storage for model selection in frontend/src/utils/preferences.ts

## Phase 3.5: Polish
- [ ] T033 [P] Unit tests for ModelSelector component in frontend/src/tests/unit/test_model_selector.tsx
- [ ] T034 [P] Unit tests for health monitoring hooks in frontend/src/tests/unit/test_health_hooks.ts
- [ ] T035 [P] Unit tests for API service updates in frontend/src/tests/unit/test_api_service.ts
- [ ] T036 [P] Performance tests for component rendering in frontend/src/tests/performance/test_component_performance.ts
- [ ] T037 [P] Accessibility tests for model selection UI in frontend/src/tests/accessibility/test_model_selection_a11y.ts
- [ ] T038 [P] Update Storybook stories for new components in frontend/src/stories/
- [ ] T039 Bundle size analysis and optimization for new features
- [ ] T040 Cross-browser compatibility testing per quickstart.md
- [ ] T041 Run complete quickstart validation scenarios

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T012) before implementation (T013-T032)
- Interface updates (T013-T017) before component implementation (T018-T020)
- Components (T018-T020) before integration (T026-T032)
- Core implementation (T013-T032) before polish (T033-T041)

## Parallel Execution Groups

### Group 1: Setup (can run together)
```bash
# T001-T003 can run in parallel
Task: "Install additional frontend dependencies for Gemini integration in frontend/package.json"
Task: "Configure TypeScript interfaces for Gemini models in frontend/src/types/gemini.ts"
Task: "Set up Jest test configuration for React components in frontend/jest.config.js"
```

### Group 2: Contract Tests (can run together)
```bash
# T004-T007 can run in parallel
Task: "Contract test GET /api/health/models in frontend/src/tests/contract/test_health_models_get.ts"
Task: "Contract test POST /api/media/generate with model selection in frontend/src/tests/contract/test_media_generation_post.ts"
Task: "Contract test GET /api/media/assets/{id} with model metadata in frontend/src/tests/contract/test_media_assets_get.ts"
Task: "Contract test GET /api/jobs/{id}/status in frontend/src/tests/contract/test_job_status_get.ts"
```

### Group 3: Component Tests (can run together)
```bash
# T008-T010 can run in parallel
Task: "Component test ModelSelector component in frontend/src/tests/components/test_model_selector.tsx"
Task: "Component test HealthStatusDisplay component in frontend/src/tests/components/test_health_status_display.tsx"
Task: "Component test AssetMetadataView component in frontend/src/tests/components/test_asset_metadata_view.tsx"
```

### Group 4: Integration Tests (can run together)
```bash
# T011-T012 can run in parallel
Task: "Integration test model selection workflow in frontend/src/tests/integration/test_model_selection_workflow.ts"
Task: "Integration test health monitoring updates in frontend/src/tests/integration/test_health_monitoring.ts"
```

### Group 5: Interface Updates (can run together)
```bash
# T013-T017 can run in parallel
Task: "Update MediaGenerateRequest interface in frontend/src/services/api.ts"
Task: "Update MediaGenerateResponse interface in frontend/src/services/api.ts"
Task: "Add ModelHealthStatus interfaces in frontend/src/types/health.ts"
Task: "Add SystemModelHealth interface in frontend/src/types/health.ts"
Task: "Enhanced AssetMetadata interface in frontend/src/types/assets.ts"
```

### Group 6: React Components (can run together)
```bash
# T018-T022 can run in parallel
Task: "Create ModelSelector React component in frontend/src/components/ModelSelector.tsx"
Task: "Create HealthStatusDisplay React component in frontend/src/components/HealthStatusDisplay.tsx"
Task: "Create AssetMetadataView React component in frontend/src/components/AssetMetadataView.tsx"
Task: "Create useModelHealth custom hook in frontend/src/hooks/useModelHealth.ts"
Task: "Create useModelSelection custom hook in frontend/src/hooks/useModelSelection.ts"
```

### Group 7: Polish Tasks (can run together)
```bash
# T033-T038 can run in parallel
Task: "Unit tests for ModelSelector component in frontend/src/tests/unit/test_model_selector.tsx"
Task: "Unit tests for health monitoring hooks in frontend/src/tests/unit/test_health_hooks.ts"
Task: "Unit tests for API service updates in frontend/src/tests/unit/test_api_service.ts"
Task: "Performance tests for component rendering in frontend/src/tests/performance/test_component_performance.ts"
Task: "Accessibility tests for model selection UI in frontend/src/tests/accessibility/test_model_selection_a11y.ts"
Task: "Update Storybook stories for new components in frontend/src/stories/"
```

## Implementation Notes
- Focus on React TypeScript components and hooks
- Maintain backward compatibility with existing API contracts
- Use existing Tailwind CSS classes for consistent styling
- Follow established patterns from existing components
- Implement proper error boundaries for model unavailability
- Add loading states for async operations
- Ensure accessibility compliance for all new UI elements
- Test across target browsers per technical requirements

## Validation Checklist
- [ ] All contract tests validate new API endpoints
- [ ] React components render correctly with different model states
- [ ] Health monitoring updates in real-time
- [ ] Model selection persists across user sessions
- [ ] Asset metadata displays model information correctly
- [ ] Error handling works for model unavailability scenarios
- [ ] Performance meets defined benchmarks (<100ms UI response)
- [ ] Bundle size impact stays within acceptable limits
- [ ] Accessibility standards maintained for new components
- [ ] Cross-browser compatibility validated per quickstart.md

## Success Criteria
**Implementation Complete** ✅ when:
- All tests pass (contract, component, integration, unit)
- Quickstart scenarios validate successfully
- Performance benchmarks met
- No breaking changes to existing functionality
- Model selection and health monitoring work as specified
- Asset metadata enhancement displays correctly