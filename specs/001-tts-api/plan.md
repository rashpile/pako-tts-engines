# Implementation Plan: TTS API Service

**Branch**: `001-tts-api` | **Date**: 2025-12-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-tts-api/spec.md`

## Summary

Build a Python-based TTS API service that wraps multiple local TTS engines (Coqui TTS, Silero) behind an ElevenLabs-compatible REST API. The service loads engine configuration from a single `config.yaml` file and exposes endpoints for listing models, synthesizing speech, and querying engine capabilities. Based on the pako-tts API patterns and ro-tts engine POC.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, TTS (Coqui), torch, PyYAML, structlog
**Storage**: File-based audio cache (temporary synthesis outputs)
**Testing**: pytest with pytest-asyncio, pytest-cov
**Target Platform**: Linux server (Docker-ready), macOS for development
**Project Type**: Single project (API service)
**Performance Goals**: < 5s synthesis for typical requests (< 500 chars), 10 concurrent requests
**Constraints**: Synchronous audio processing, single-instance deployment initially
**Scale/Scope**: Local deployment, multiple TTS engines, ~5-10 models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Design for Clarity | ✅ PASS | Clear module boundaries: api/, engines/, config/ |
| II. Test for Safety | ✅ PASS | Contract tests for API, integration tests for engines |
| III. Prefer Clarity Over Cleverness | ✅ PASS | Standard FastAPI patterns, no magic |
| IV. Keep Iterations Small | ✅ PASS | 4 user stories with P1-P4 priorities for incremental delivery |
| V. Avoid Unknown Future Requirements | ✅ PASS | No streaming, no auth, no horizontal scaling in v1 |
| VI. Reuse Before Create | ✅ PASS | Reusing Coqui TTS, Silero, FastAPI ecosystem |
| VII. Evolve for Growth | ✅ PASS | Engine interface allows adding new backends |

**Quality Gates:**
- ✅ ruff linting configured in pyproject.toml
- ✅ mypy --strict configured
- ✅ pytest with coverage configured
- ✅ API contracts documented before implementation (OpenAPI)

## Project Structure

### Documentation (this feature)

```text
specs/001-tts-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Configuration loading (config.yaml)
├── api/
│   ├── __init__.py
│   ├── routes.py        # API route registration
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── tts.py       # POST /api/v1/tts - synthesis
│   │   ├── models.py    # GET /api/v1/models - list models
│   │   └── health.py    # GET /api/v1/health
│   └── middleware/
│       ├── __init__.py
│       ├── error.py     # Error handling middleware
│       └── logging.py   # Request logging middleware
├── engines/
│   ├── __init__.py
│   ├── base.py          # TTSEngine protocol/interface
│   ├── registry.py      # Engine registration and discovery
│   ├── coqui.py         # Coqui TTS engine adapter
│   └── silero.py        # Silero TTS engine adapter
├── models/
│   ├── __init__.py
│   ├── config.py        # Configuration models (Pydantic)
│   ├── request.py       # API request models
│   ├── response.py      # API response models
│   └── engine.py        # Engine/Model domain models
└── services/
    ├── __init__.py
    ├── synthesis.py     # Synthesis orchestration
    └── queue.py         # Request queue management

tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── contract/
│   ├── __init__.py
│   └── test_api.py      # API contract tests
├── integration/
│   ├── __init__.py
│   └── test_synthesis.py
└── unit/
    ├── __init__.py
    ├── test_config.py
    └── test_engines.py

config.yaml              # Engine configuration (root)
```

**Structure Decision**: Single project structure with clear separation between API layer (`api/`), engine adapters (`engines/`), domain models (`models/`), and business logic (`services/`). This follows the hexagonal architecture pattern from the pako-tts reference while using Python idioms.

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |