# Feature Specification: TTS API Service

**Feature Branch**: `001-tts-api`
**Created**: 2025-12-21
**Status**: Draft
**Input**: User description: "API service for different local tts engines, single config.yaml for configuration, API to select model, language and other parameters depends on model"

## Clarifications

### Session 2025-12-21

- Q: When a TTS engine process fails during synthesis, how should the service respond? → A: Return error immediately, let client decide to retry
- Q: When multiple concurrent requests exceed available engine capacity, how should the service behave? → A: Queue requests up to a limit, reject when queue full
- Q: What level of observability should the service provide? → A: Structured logging (JSON) with key metrics (requests, latency, errors)
- Q: When a configured TTS engine binary or model is not found at runtime, how should the service behave? → A: Start with warning, disable unavailable engines, continue with remaining
- Q: When no model_id and language are provided, how should the service select a model? → A: Auto-detect language using lingua library, then select first available engine supporting that language (config order matters). If no match, use default engine.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Speech Synthesis (Priority: P1)

As a developer, I want to send text to the TTS API and receive synthesized audio so that I can integrate speech capabilities into my application.

**Why this priority**: This is the core functionality—without speech synthesis, the service has no value. Every other feature depends on this working correctly.

**Independent Test**: Can be fully tested by sending a text string via the API and receiving playable audio data back. Delivers immediate value as a working TTS endpoint.

**Acceptance Scenarios**:

1. **Given** a running TTS service with at least one engine configured, **When** I send a synthesis request with text "Hello world", **Then** I receive audio data in a supported format (WAV, MP3, or OGG)
2. **Given** a synthesis request, **When** the request completes successfully, **Then** the response includes metadata about the audio (duration, format, sample rate)
3. **Given** a synthesis request with empty text, **When** the request is processed, **Then** I receive a clear error message indicating text is required

---

### User Story 2 - Model and Language Selection (Priority: P2)

As a developer, I want to select specific TTS models and languages so that I can generate speech appropriate for my use case and audience.

**Why this priority**: Different applications need different voices and languages. This enables the API to serve diverse use cases beyond a single default configuration.

**Independent Test**: Can be tested by listing available models/languages and successfully generating audio with each selectable option.

**Acceptance Scenarios**:

1. **Given** multiple TTS engines configured, **When** I request the list of available models, **Then** I receive a list showing each model's name, supported languages, and available parameters
2. **Given** a model that supports multiple languages, **When** I specify a language code (e.g., "en-US", "de-DE"), **Then** the synthesized speech uses that language
3. **Given** a request with an unsupported model or language, **When** processed, **Then** I receive a clear error indicating what models/languages are available
4. **Given** a synthesis request without model_id or language, **When** I send Russian text "Привет мир", **Then** the service auto-detects Russian and selects the first available engine supporting ru-* languages
5. **Given** multiple engines supporting the same language, **When** auto-detection selects that language, **Then** the first engine in config.yaml order is used
6. **Given** text in a language not supported by any engine, **When** auto-detection runs, **Then** the default engine is used as fallback

---

### User Story 3 - Model-Specific Parameters (Priority: P3)

As a developer, I want to adjust model-specific parameters (like speed, pitch, or voice variants) so that I can fine-tune the audio output for my needs.

**Why this priority**: Customization parameters vary by engine and enhance quality but are not essential for basic functionality.

**Independent Test**: Can be tested by requesting parameter schema for a model, then submitting requests with various parameter values and verifying audio differences.

**Acceptance Scenarios**:

1. **Given** a TTS model with configurable parameters, **When** I request the model's parameter schema, **Then** I receive a description of each parameter (name, type, range, default)
2. **Given** a synthesis request with custom parameters (e.g., speed=1.5), **When** processed, **Then** the audio reflects those parameter adjustments
3. **Given** a parameter value outside the valid range, **When** submitted, **Then** I receive an error specifying the valid range

---

### User Story 4 - Configuration Management (Priority: P4)

As an administrator, I want to configure available TTS engines through a single YAML file so that I can manage the service without code changes.

**Why this priority**: Configuration is essential for deployment but can be handled with reasonable defaults initially. Administrators need this before production use.

**Independent Test**: Can be tested by modifying config.yaml and verifying the service reflects changes on restart.

**Acceptance Scenarios**:

1. **Given** a config.yaml file with engine definitions, **When** the service starts, **Then** it loads and validates the configuration
2. **Given** an invalid configuration (missing required fields, invalid paths), **When** the service starts, **Then** it fails with a clear error message identifying the problem
3. **Given** a configuration change, **When** I restart the service, **Then** the new configuration takes effect

---

### Edge Cases

- When a configured TTS engine binary/model is not found at runtime, service starts with warning, disables that engine, and continues with remaining engines
- Synthesis requests exceeding maximum text length (5000 chars) are rejected with error indicating the limit
- When concurrent requests exceed engine capacity, service queues up to a configurable limit then rejects with "service busy" error
- When an engine process crashes mid-synthesis, the system returns an error immediately with details; client decides whether to retry
- When requested audio format is not supported by the selected engine, error is returned listing the engine's supported formats
- When language detection cannot determine the language (very short or ambiguous text), the default engine is used
- When explicit model_id is provided, language detection is skipped even if language is not specified (engine's default language is used)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an endpoint to synthesize text into audio
- **FR-002**: System MUST support multiple TTS engine backends (e.g., Piper, Coqui, eSpeak)
- **FR-003**: System MUST load engine configuration from a single config.yaml file
- **FR-004**: System MUST provide an endpoint to list available models with their capabilities
- **FR-005**: System MUST allow selection of model, language, and voice per request
- **FR-006**: System MUST expose model-specific parameters dynamically based on engine type
- **FR-007**: System MUST validate synthesis requests against model capabilities
- **FR-008**: System MUST return audio in at least one common format (WAV minimum)
- **FR-009**: System MUST provide meaningful error messages for all failure scenarios
- **FR-010**: System MUST validate configuration on startup and report errors clearly
- **FR-011**: System MUST queue synthesis requests up to a configurable limit and reject with "service busy" when full
- **FR-012**: System MUST emit structured JSON logs for all operations
- **FR-013**: System MUST track and expose key metrics: request count, latency, and error rates
- **FR-014**: System MUST start with available engines if some configured engines are unavailable, logging warnings for missing ones
- **FR-015**: System MUST auto-detect text language using lingua when no model_id and language are provided
- **FR-016**: System MUST select the first available engine (by config order) that supports the detected language
- **FR-017**: System MUST fall back to default engine when detected language is not supported by any engine

### Key Entities

- **Engine**: A TTS backend (e.g., Piper, Coqui). Has name, executable path, supported output formats
- **Model**: A specific voice/model within an engine. Has name, supported languages, parameter schema
- **Language**: A supported language/locale code (e.g., en-US, de-DE). Associated with models
- **Parameter Schema**: Definition of adjustable parameters for a model (name, type, constraints, default)
- **Synthesis Request**: Input for TTS conversion (text, optional model selection, optional language, parameters). When model and language are omitted, language is auto-detected
- **Synthesis Response**: Output containing audio data and metadata (format, duration, sample rate)
- **Language Detector**: Service using lingua library to detect text language. Returns ISO 639-1 codes (e.g., en, ru, ro) which are matched against engine BCP-47 language codes (e.g., en-US, ru-RU)

## Assumptions

- TTS engines are installed locally and accessible via command-line or library interface
- Audio processing happens synchronously (streaming is a future enhancement)
- Authentication/authorization is handled externally or not required for initial version
- Single-instance deployment (horizontal scaling is a future consideration)
- Maximum text length of 5000 characters per request (reasonable for most use cases)
- Language detection uses lingua-language-detector library which supports 75+ languages
- Language matching uses prefix matching: detected ISO code "en" matches any BCP-47 variant (en-US, en-GB, etc.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can synthesize speech from text in under 5 seconds for typical requests (< 500 characters)
- **SC-002**: Service starts successfully within 10 seconds with valid configuration
- **SC-003**: 100% of invalid requests return actionable error messages (not generic 500 errors)
- **SC-004**: Users can discover available models and their capabilities without external documentation
- **SC-005**: Adding a new TTS engine requires only configuration changes, no code modifications
- **SC-006**: Service handles at least 10 concurrent synthesis requests without failures
- **SC-007**: Language detection correctly identifies the text language for major languages (English, Russian, Romanian, German, French, Spanish) with >95% accuracy on sentences of 20+ characters