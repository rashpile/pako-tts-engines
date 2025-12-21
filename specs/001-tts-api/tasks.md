# Tasks: TTS API Service

**Input**: Design documents from `/specs/001-tts-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included as constitution requires "Test for Safety" (write tests before or alongside implementation).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create directory structure per implementation plan: src/app/{api/handlers,api/middleware,engines,models,services}
- [ ] T002 Update pyproject.toml with runtime dependencies (fastapi, uvicorn, pydantic, pyyaml, structlog, TTS, torch, torchaudio)
- [ ] T003 [P] Update pyproject.toml with dev dependencies (pytest, pytest-asyncio, pytest-cov, httpx, mypy, ruff)
- [ ] T004 [P] Create tests directory structure: tests/{contract,integration,unit}
- [ ] T005 [P] Create config.yaml template with example engine configurations at project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Define enums (EngineType, OutputFormat, ParameterType, EngineStatus) in src/app/models/engine.py
- [ ] T007 [P] Define error codes and APIError class in src/app/models/errors.py
- [ ] T008 [P] Define ServiceConfig, ServerConfig, LoggingConfig, EngineConfig models in src/app/models/config.py
- [ ] T009 Implement configuration loading from config.yaml in src/app/config.py
- [ ] T010 Define TTSEngine protocol/interface in src/app/engines/base.py
- [ ] T011 [P] Implement EngineRegistry class in src/app/engines/registry.py
- [ ] T012 [P] Implement error handling middleware in src/app/api/middleware/error.py
- [ ] T013 [P] Implement request logging middleware with structlog in src/app/api/middleware/logging.py
- [ ] T014 Create FastAPI application factory in src/app/main.py
- [ ] T015 Implement API route registration in src/app/api/routes.py
- [ ] T016 Create shared test fixtures in tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Speech Synthesis (Priority: P1) 🎯 MVP

**Goal**: Send text to TTS API and receive synthesized audio

**Independent Test**: Send "Hello world" via POST /api/v1/tts, receive playable WAV audio

### Tests for User Story 1

- [ ] T017 [P] [US1] Write contract test for POST /api/v1/tts in tests/contract/test_api.py
- [ ] T018 [P] [US1] Write contract test for GET /api/v1/health in tests/contract/test_api.py
- [ ] T019 [P] [US1] Write unit test for Coqui engine adapter in tests/unit/test_engines.py

### Implementation for User Story 1

- [ ] T020 [P] [US1] Define SynthesisRequest model in src/app/models/request.py
- [ ] T021 [P] [US1] Define SynthesisResponse and HealthResponse models in src/app/models/response.py
- [ ] T022 [US1] Implement CoquiEngine adapter in src/app/engines/coqui.py
- [ ] T023 [US1] Implement SynthesisService in src/app/services/synthesis.py
- [ ] T024 [US1] Implement RequestQueue with bounded asyncio.Queue in src/app/services/queue.py
- [ ] T025 [US1] Implement POST /api/v1/tts handler in src/app/api/handlers/tts.py
- [ ] T026 [US1] Implement GET /api/v1/health handler in src/app/api/handlers/health.py
- [ ] T027 [US1] Add text validation (empty, too long) with appropriate error codes
- [ ] T028 [US1] Write integration test for synthesis flow in tests/integration/test_synthesis.py

**Checkpoint**: User Story 1 complete - basic TTS synthesis works with single default model

---

## Phase 4: User Story 2 - Model and Language Selection (Priority: P2)

**Goal**: List available models and select specific model/language for synthesis

**Independent Test**: GET /api/v1/models returns list, synthesize with specific model_id and language

### Tests for User Story 2

- [ ] T029 [P] [US2] Write contract test for GET /api/v1/models in tests/contract/test_api.py
- [ ] T030 [P] [US2] Write contract test for GET /api/v1/models/{id} in tests/contract/test_api.py

### Implementation for User Story 2

- [ ] T031 [P] [US2] Define ModelSummary and ModelsListResponse in src/app/models/response.py
- [ ] T032 [P] [US2] Define ModelDetailResponse in src/app/models/response.py
- [ ] T033 [US2] Add list_models() and get_model() methods to EngineRegistry in src/app/engines/registry.py
- [ ] T034 [US2] Implement GET /api/v1/models handler in src/app/api/handlers/models.py
- [ ] T035 [US2] Implement GET /api/v1/models/{model_id} handler in src/app/api/handlers/models.py
- [ ] T036 [US2] Update POST /api/v1/tts to accept model_id and language parameters
- [ ] T037 [US2] Add validation for unsupported model/language with appropriate error codes

**Checkpoint**: User Story 2 complete - users can list and select models

---

## Phase 5: User Story 3 - Model-Specific Parameters (Priority: P3)

**Goal**: Adjust model-specific parameters like speed, pitch, speaker

**Independent Test**: Request parameter schema, synthesize with speed=1.5, verify audio is faster

### Tests for User Story 3

- [ ] T038 [P] [US3] Write unit test for parameter validation in tests/unit/test_engines.py
- [ ] T039 [P] [US3] Write unit test for Silero engine adapter in tests/unit/test_engines.py

### Implementation for User Story 3

- [ ] T040 [P] [US3] Define ParameterSchema and ParameterDefinition models in src/app/models/engine.py
- [ ] T041 [US3] Add parameter schema to Coqui engine (speed parameter) in src/app/engines/coqui.py
- [ ] T042 [US3] Implement SileroEngine adapter with speaker parameter in src/app/engines/silero.py
- [ ] T043 [US3] Add parameter validation service in src/app/services/synthesis.py
- [ ] T044 [US3] Update POST /api/v1/tts to accept and validate parameters
- [ ] T045 [US3] Add INVALID_PARAMETER error handling for out-of-range values

**Checkpoint**: User Story 3 complete - users can customize synthesis parameters

---

## Phase 6: User Story 4 - Configuration Management (Priority: P4)

**Goal**: Configure TTS engines through config.yaml with validation and graceful degradation

**Independent Test**: Modify config.yaml, restart service, verify changes reflected

### Tests for User Story 4

- [ ] T046 [P] [US4] Write unit test for config validation in tests/unit/test_config.py
- [ ] T047 [P] [US4] Write unit test for graceful degradation (unavailable engine) in tests/unit/test_config.py

### Implementation for User Story 4

- [ ] T048 [US4] Add comprehensive config validation with clear error messages in src/app/config.py
- [ ] T049 [US4] Implement engine availability checking on startup in src/app/engines/registry.py
- [ ] T050 [US4] Add graceful degradation: log warning, disable unavailable engines, continue with remaining
- [ ] T051 [US4] Update health endpoint to show engine availability status
- [ ] T052 [US4] Add startup logging showing loaded engines and any warnings

**Checkpoint**: User Story 4 complete - administrators can configure service via YAML

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Implement GET /openapi.json handler to serve OpenAPI spec in src/app/api/handlers/openapi.py
- [ ] T054 [P] Add metrics tracking (request count, latency, errors) in src/app/api/middleware/logging.py
- [ ] T055 [P] Run mypy --strict and fix any type errors
- [ ] T056 [P] Run ruff check and fix any linting issues
- [ ] T057 Update README.md with setup and usage instructions
- [ ] T058 Validate quickstart.md scenarios work end-to-end
- [ ] T059 Run full test suite with coverage report

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3 → P4)
  - Or in parallel if staffed appropriately
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 - Extends US1 TTS handler, independently testable
- **US3 (P3)**: Can start after Phase 2 - Extends US2 model details, independently testable
- **US4 (P4)**: Can start after Phase 2 - Extends config validation, independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before handlers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T001 → then parallel: T002, T003, T004, T005
```

**Phase 2 (Foundational)**:
```
T006 → then parallel: T007, T008
T008 → T009
T010 → parallel: T011
Parallel: T012, T013
T006, T009, T010, T011, T012, T013 → T014 → T015
T016 (parallel with all above)
```

**Phase 3 (US1)**:
```
Parallel tests: T017, T018, T019
Parallel models: T020, T021
T010, T020, T021 → T022
T022 → T023
T023 → T024
T023 → T025, T026
T025 → T027
All above → T028
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test basic synthesis works
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP - basic TTS works!)
3. Add User Story 2 → Test → Deploy (model selection)
4. Add User Story 3 → Test → Deploy (custom parameters)
5. Add User Story 4 → Test → Deploy (production config)
6. Polish → Final release

---

## Summary

| Phase | Story | Tasks | Parallel | Purpose |
|-------|-------|-------|----------|---------|
| 1 | Setup | 5 | 4 | Project initialization |
| 2 | Foundational | 11 | 6 | Core infrastructure |
| 3 | US1 (P1) | 12 | 5 | Basic synthesis (MVP) |
| 4 | US2 (P2) | 9 | 4 | Model selection |
| 5 | US3 (P3) | 8 | 3 | Custom parameters |
| 6 | US4 (P4) | 7 | 2 | Configuration management |
| 7 | Polish | 7 | 4 | Cross-cutting concerns |
| **Total** | | **59** | **28** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently