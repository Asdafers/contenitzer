# Tasks: Development Environment Setup & Testing

**Input**: Design documents from `/code/contentizer/specs/004-1-install-redis/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, TypeScript 5+, FastAPI, Redis, React 18+
   → Structure: Web app (backend/frontend directories)
2. Load design documents:
   → data-model.md: ConfigurationProfile, ServiceStatus, TestExecution, SetupProgress entities
   → contracts/setup-api.yaml: /setup/health, /setup/validate-config, /setup/test-connectivity, /setup/run-tests
   → quickstart.md: 5-phase setup process with validation scenarios
3. Generate tasks by category:
   → Setup: Redis installation scripts, environment configuration
   → Tests: Contract tests for setup API, validation tests
   → Core: Setup validation services, health check endpoints
   → Integration: Service connectivity tests, end-to-end workflows
   → Polish: Documentation, troubleshooting guides
4. Apply TDD ordering: Tests before implementation
5. Mark [P] for parallel execution (different files/independent tasks)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute within repository structure

## Phase 3.1: Setup & Prerequisites
- [x] T001 Create Redis installation scripts for multiple platforms in `scripts/install/`
- [x] T002 Create environment configuration validation script in `scripts/config/validate-env.py`
- [x] T003 [P] Create setup documentation structure in `docs/setup/`

## Phase 3.2: Contract Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test GET /setup/health in `backend/tests/contract/test_setup_health.py`
- [x] T005 [P] Contract test POST /setup/validate-config in `backend/tests/contract/test_setup_validate_config.py`
- [x] T006 [P] Contract test POST /setup/test-connectivity in `backend/tests/contract/test_setup_connectivity.py`
- [x] T007 [P] Contract test POST /setup/run-tests in `backend/tests/contract/test_setup_run_tests.py`
- [x] T008 [P] Integration test Redis installation validation in `backend/tests/integration/test_redis_setup.py`
- [x] T009 [P] Integration test service startup sequence in `backend/tests/integration/test_service_startup.py`
- [x] T010 [P] Integration test end-to-end workflow validation in `backend/tests/integration/test_e2e_setup.py`

## Phase 3.3: Data Models (ONLY after tests are failing)
- [x] T011 [P] ConfigurationProfile model in `backend/src/models/configuration_profile.py`
- [x] T012 [P] ServiceStatus model in `backend/src/models/service_status.py`
- [x] T013 [P] TestExecution model in `backend/src/models/test_execution.py`
- [x] T014 [P] SetupProgress model in `backend/src/models/setup_progress.py`

## Phase 3.4: Setup Services
- [x] T015 Environment validation service in `backend/src/services/environment_service.py`
- [x] T016 Redis connectivity service in `backend/src/services/redis_connectivity_service.py`
- [x] T017 Service health monitoring in `backend/src/services/health_service.py`
- [x] T018 Setup progress tracking service in `backend/src/services/setup_progress_service.py`

## Phase 3.5: API Endpoints
- [x] T019 GET /setup/health endpoint in `backend/src/api/setup.py`
- [x] T020 POST /setup/validate-config endpoint in `backend/src/api/setup.py`
- [x] T021 POST /setup/test-connectivity endpoint in `backend/src/api/setup.py`
- [x] T022 POST /setup/run-tests endpoint in `backend/src/api/setup.py`

## Phase 3.6: Installation Scripts
- [x] T023 [P] Redis installation script for Ubuntu/Debian in `scripts/install/install-redis-ubuntu.sh`
- [x] T024 [P] Redis installation script for macOS in `scripts/install/install-redis-macos.sh`
- [x] T025 [P] Docker Redis setup script in `scripts/install/install-redis-docker.sh`
- [x] T026 [P] Environment file template generator in `scripts/config/generate-env-template.py`

## Phase 3.7: Validation & Testing Tools
- [x] T027 [P] Contract test runner script in `scripts/test/run-contract-tests.py`
- [x] T028 [P] Integration test runner script in `scripts/test/run-integration-tests.py`
- [x] T029 Service startup validation script in `scripts/validate/check-services.py`
- [x] T030 End-to-end workflow test script in `scripts/validate/e2e-workflow.py`

## Phase 3.8: Documentation & Guides
- [x] T031 [P] Complete quickstart implementation guide in `docs/setup/quickstart-complete.md`
- [x] T032 [P] Troubleshooting guide with solutions in `docs/setup/troubleshooting.md`
- [x] T033 [P] Platform-specific setup instructions in `docs/setup/platform-guides/`
- [x] T034 [P] Developer onboarding checklist in `docs/setup/developer-checklist.md`

## Dependencies
- Setup (T001-T003) before everything else
- Contract tests (T004-T010) before any implementation
- Models (T011-T014) before services (T015-T018)
- Services before API endpoints (T019-T022)
- Installation scripts (T023-T026) support validation (T027-T030)
- All implementation before documentation (T031-T034)

## Parallel Execution Examples

### Phase 3.2: All Contract Tests
```bash
# Launch T004-T010 together (different test files):
Task: "Contract test GET /setup/health in backend/tests/contract/test_setup_health.py"
Task: "Contract test POST /setup/validate-config in backend/tests/contract/test_setup_validate_config.py"
Task: "Contract test POST /setup/test-connectivity in backend/tests/contract/test_setup_connectivity.py"
Task: "Contract test POST /setup/run-tests in backend/tests/contract/test_setup_run_tests.py"
Task: "Integration test Redis installation validation in backend/tests/integration/test_redis_setup.py"
Task: "Integration test service startup sequence in backend/tests/integration/test_service_startup.py"
Task: "Integration test end-to-end workflow validation in backend/tests/integration/test_e2e_setup.py"
```

### Phase 3.3: All Model Creation
```bash
# Launch T011-T014 together (different model files):
Task: "ConfigurationProfile model in backend/src/models/configuration_profile.py"
Task: "ServiceStatus model in backend/src/models/service_status.py"
Task: "TestExecution model in backend/src/models/test_execution.py"
Task: "SetupProgress model in backend/src/models/setup_progress.py"
```

### Phase 3.6: Platform Installation Scripts
```bash
# Launch T023-T026 together (different platform scripts):
Task: "Redis installation script for Ubuntu/Debian in scripts/install/install-redis-ubuntu.sh"
Task: "Redis installation script for macOS in scripts/install/install-redis-macos.sh"
Task: "Docker Redis setup script in scripts/install/install-redis-docker.sh"
Task: "Environment file template generator in scripts/config/generate-env-template.py"
```

### Phase 3.8: Documentation Tasks
```bash
# Launch T031-T034 together (different documentation files):
Task: "Complete quickstart implementation guide in docs/setup/quickstart-complete.md"
Task: "Troubleshooting guide with solutions in docs/setup/troubleshooting.md"
Task: "Platform-specific setup instructions in docs/setup/platform-guides/"
Task: "Developer onboarding checklist in docs/setup/developer-checklist.md"
```

## Validation Scenarios
Each task must pass these acceptance criteria:

### Installation Scripts (T023-T025)
- Script executes without errors on target platform
- Redis server starts and responds to ping
- Script provides clear success/failure messages
- Rollback capability if installation fails

### Contract Tests (T004-T007)
- Tests initially FAIL (no implementation exists)
- Tests validate exact OpenAPI schema compliance
- Tests include error scenarios (404, 400, 503)
- Tests are independent and can run in parallel

### Integration Tests (T008-T010)
- Tests validate complete setup workflows
- Tests can run against real services
- Tests clean up after themselves
- Tests provide clear failure diagnostics

### API Endpoints (T019-T022)
- Endpoints match OpenAPI contract exactly
- Endpoints handle all documented error cases
- Endpoints return proper HTTP status codes
- Endpoints include proper logging and monitoring

## Notes
- All [P] tasks operate on different files with no shared dependencies
- Contract tests must fail initially - this validates TDD approach
- Each installation script must be tested on actual platform
- Documentation tasks should include code examples and screenshots
- Validation scripts should provide actionable error messages

## Task Generation Rules Applied

1. **From Contracts** (setup-api.yaml):
   - 4 endpoints → 4 contract test tasks [P] → 4 implementation tasks

2. **From Data Model**:
   - 4 entities → 4 model creation tasks [P]
   - Services derived from entity relationships

3. **From Quickstart Scenarios**:
   - 5 setup phases → integration test tasks [P]
   - Platform variations → platform-specific script tasks [P]

4. **From Research Decisions**:
   - Multiple installation methods → platform-specific scripts [P]
   - Validation approach → test runner scripts [P]

## Validation Checklist

- [x] All contracts have corresponding tests (T004-T007)
- [x] All entities have model tasks (T011-T014)
- [x] All tests come before implementation (Phase 3.2 before 3.3+)
- [x] Parallel tasks truly independent (different files/platforms)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD ordering enforced (tests fail first, then implement)
- [x] Setup and validation tools included (T023-T030)
- [x] Complete documentation coverage (T031-T034)