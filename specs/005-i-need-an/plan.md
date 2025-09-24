
# Implementation Plan: Script Upload Option

**Branch**: `005-i-need-an` | **Date**: 2025-09-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/code/contentizer/specs/005-i-need-an/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Add option for users to upload/input existing script content instead of generating it via YouTube research and AI generation. All subsequent workflow steps (optimization, formatting, publishing) remain unchanged. This provides flexibility for users who already have script content and want to skip the research/generation phases.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5+ (frontend)
**Primary Dependencies**: FastAPI, React 18+, Redis, SQLAlchemy, Vite, Celery
**Storage**: SQLite/PostgreSQL (persistent data), Redis (sessions/tasks)
**Testing**: pytest (backend), Jest (frontend)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: web - determines source structure (backend/ + frontend/)
**Performance Goals**: Standard web performance (<3s page load, <500ms API response)
**Constraints**: Must integrate with existing content workflow, maintain data consistency
**Scale/Scope**: Individual content creators, script size up to ~50KB text, single user workflow

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check**: ✅ PASS
- ✅ Feature adds capability to existing workflow without architectural changes
- ✅ Uses existing backend/frontend structure and technologies
- ✅ No new external dependencies required for core functionality
- ✅ Maintains existing data flow patterns
- ✅ Script upload is well-defined, bounded feature scope

**Post-Design Check**: ✅ PASS
- ✅ Data model extends existing entities without breaking changes
- ✅ API contracts follow existing REST patterns
- ✅ Frontend components integrate with existing UI framework
- ✅ Database schema changes are additive only
- ✅ No new complexity introduced - leverages existing patterns
- ✅ Error handling follows established conventions

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 (Web application) - backend/ and frontend/ structure confirmed

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs:
  - data-model.md → database migration + model creation tasks
  - script-upload-api.yaml → API endpoint + contract test tasks
  - frontend-components.md → React component creation tasks
  - quickstart.md → integration test scenarios
- Each contract endpoint → contract test task [P]
- Each data entity → model creation task [P]
- Each frontend component → component implementation task [P]
- Each user scenario → integration test task
- Implementation tasks to make contract tests pass

**Ordering Strategy**:
- TDD order: Contract tests → Models → Services → API → Frontend → Integration tests
- Dependency order: Database schema → Backend models → API endpoints → Frontend components → E2E tests
- Mark [P] for parallel execution within same layer:
  - Database migrations can run in parallel
  - API endpoints are independent [P]
  - Frontend components are independent [P]
  - Contract tests are independent [P]

**Specific Task Categories**:
1. **Database Tasks**: Migration scripts, model extensions
2. **Backend API Tasks**: Script upload endpoints, workflow mode management
3. **Frontend Tasks**: Upload components, mode selector, validation UI
4. **Testing Tasks**: Contract tests, component tests, integration scenarios
5. **Integration Tasks**: End-to-end workflow testing

**Estimated Output**: 28-32 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
