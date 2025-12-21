# Research: TTS API Service

**Feature**: 001-tts-api
**Date**: 2025-12-21

## Technology Decisions

### 1. Web Framework: FastAPI

**Decision**: Use FastAPI as the web framework

**Rationale**:
- Native async support for handling concurrent synthesis requests
- Built-in OpenAPI/Swagger documentation generation
- Pydantic v2 integration for request/response validation
- Excellent Python type hints support (aligns with mypy --strict)
- Proven performance for I/O-bound workloads

**Alternatives Considered**:
- Flask: Simpler but lacks native async and OpenAPI generation
- Django REST Framework: Too heavyweight for a single-purpose API service
- Starlette: Lower-level, FastAPI provides better DX on top of it

### 2. TTS Engine: Coqui TTS + Silero

**Decision**: Use Coqui TTS as primary engine, Silero for Russian language

**Rationale**:
- Coqui TTS (via `TTS` package) provides high-quality VITS models
- Proven in ro-tts POC with Romanian, English support
- Silero provides superior Russian language support via torch.hub
- Both are offline-capable with local model caching
- No API keys or external service dependencies

**Alternatives Considered**:
- eSpeak: Lower quality output, better for accessibility than production TTS
- Piper: Similar to Coqui but less mature ecosystem
- OpenAI TTS API: Requires network, not local, has cost

**Engine Capabilities from ro-tts POC**:
| Engine | Languages | Model | Sample Rate | Voice |
|--------|-----------|-------|-------------|-------|
| Coqui | ro | tts_models/ro/cv/vits | 22050 Hz | Female |
| Coqui | en | tts_models/en/ljspeech/vits | 22050 Hz | Female |
| Silero | ru | snakers4/silero-models v4 | 48000 Hz | xenia (Female) |

### 3. Configuration: PyYAML + Pydantic

**Decision**: YAML configuration with Pydantic validation

**Rationale**:
- YAML is human-readable and supports comments
- Matches spec requirement for single config.yaml file
- Pydantic provides runtime validation with clear error messages
- Type safety for configuration at load time

**Configuration Schema**:
```yaml
# config.yaml structure
server:
  host: "0.0.0.0"
  port: 8000
  max_queue_size: 100
  max_text_length: 5000

engines:
  - name: coqui-english
    type: coqui
    model: tts_models/en/ljspeech/vits
    languages: [en-US, en-GB]
    default: true

  - name: coqui-romanian
    type: coqui
    model: tts_models/ro/cv/vits
    languages: [ro-RO]

  - name: silero-russian
    type: silero
    model: v4_ru
    speaker: xenia
    languages: [ru-RU]

logging:
  level: info
  format: json
```

### 4. API Design: ElevenLabs-Compatible

**Decision**: Model API after ElevenLabs patterns from pako-tts

**Rationale**:
- User explicitly requested ElevenLabs-similar API
- pako-tts provides proven patterns for TTS APIs
- Enables potential future drop-in replacement scenarios
- Well-documented, industry-standard approach

**Key API Patterns Adopted**:
1. `POST /api/v1/tts` - Synchronous synthesis (returns audio)
2. `GET /api/v1/models` - List available models/voices
3. `GET /api/v1/models/{model_id}` - Get model details with parameter schema
4. `GET /api/v1/health` - Service health check

**Request/Response Patterns**:
```python
# Synthesis Request
{
    "text": "Hello world",
    "model_id": "coqui-english",
    "language": "en-US",  # optional, uses model default
    "output_format": "wav",  # wav, mp3
    "parameters": {  # model-specific, optional
        "speed": 1.0
    }
}

# Synthesis Response
Content-Type: audio/wav
[Binary audio data]

# Error Response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Text exceeds maximum length",
        "details": {"max_length": 5000, "actual_length": 6000}
    }
}
```

### 5. Structured Logging: structlog

**Decision**: Use structlog for JSON logging

**Rationale**:
- Native JSON output for log aggregation
- Contextual logging with request correlation
- Integrates well with FastAPI middleware
- Aligns with FR-012 requirement for structured logs

**Log Events**:
- `synthesis.started`: model_id, text_length, language
- `synthesis.completed`: model_id, duration_ms, audio_bytes
- `synthesis.failed`: model_id, error_code, error_message
- `request.received`: method, path, client_ip
- `config.loaded`: engines_count, models_count

### 6. Queue Management: asyncio.Queue

**Decision**: Use Python's built-in asyncio.Queue for request queuing

**Rationale**:
- Simple, no external dependencies
- Sufficient for single-instance deployment
- Bounded queue with configurable size
- Native async integration

**Alternatives Considered**:
- Redis Queue: Overkill for single-instance, adds operational complexity
- Celery: Too heavyweight for synchronous synthesis
- In-memory threading.Queue: Less integration with async handlers

### 7. Audio Output: WAV + Optional MP3

**Decision**: WAV as primary format, MP3 as optional

**Rationale**:
- WAV is native output from Coqui/Silero (no transcoding)
- MP3 requires ffmpeg or pydub for conversion
- WAV meets FR-008 requirement
- MP3 can be added later without architecture changes

## Engine Interface Design

**TTSEngine Protocol**:
```python
from typing import Protocol

class TTSEngine(Protocol):
    """Interface for TTS engine adapters."""

    @property
    def name(self) -> str: ...

    @property
    def supported_languages(self) -> list[str]: ...

    @property
    def parameter_schema(self) -> dict[str, Any]: ...

    def synthesize(
        self,
        text: str,
        language: str,
        parameters: dict[str, Any] | None = None,
    ) -> bytes: ...

    def is_available(self) -> bool: ...
```

**Engine Registry Pattern**:
```python
class EngineRegistry:
    """Manages available TTS engines."""

    def register(self, engine: TTSEngine) -> None: ...
    def get(self, name: str) -> TTSEngine | None: ...
    def list_available(self) -> list[EngineInfo]: ...
    def get_default(self) -> TTSEngine | None: ...
```

## Performance Considerations

1. **Model Caching**: Load models once at startup, reuse across requests
2. **Bounded Queue**: Prevent memory exhaustion with configurable limit
3. **Timeout Handling**: Synthesis timeout per request (default 30s)
4. **Graceful Degradation**: Disable unavailable engines, continue with others

## Security Considerations

1. **Input Validation**: Text length limits, character filtering
2. **No Shell Execution**: Engine calls through Python libraries only
3. **File Path Sanitization**: Audio cache paths validated
4. **Rate Limiting**: Deferred to v2 (external proxy recommended)

## Dependencies Summary

**Runtime Dependencies**:
```toml
[project.dependencies]
fastapi = ">=0.109"
uvicorn = { version = ">=0.27", extras = ["standard"] }
pydantic = ">=2.0"
pyyaml = ">=6.0"
structlog = ">=24.0"
TTS = ">=0.22"
torch = ">=2.0"
torchaudio = ">=2.0"
```

**Development Dependencies**:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "httpx>=0.27",  # async test client
    "mypy>=1.8",
    "ruff>=0.3",
]
```