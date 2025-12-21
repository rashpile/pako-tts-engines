# Data Model: TTS API Service

**Feature**: 001-tts-api
**Date**: 2025-12-21

## Domain Entities

### Engine

Represents a TTS backend (e.g., Coqui, Silero).

```python
@dataclass
class Engine:
    """A TTS engine backend."""
    name: str                      # Unique identifier (e.g., "coqui", "silero")
    type: EngineType               # Enum: COQUI, SILERO
    models: list[Model]            # Available models for this engine
    is_available: bool             # Runtime availability status
    error_message: str | None      # If unavailable, reason why
```

**Validation Rules**:
- `name` must be unique across all engines
- `name` must be lowercase alphanumeric with hyphens only
- At least one model must be configured per engine

### Model

Represents a specific voice/model within an engine.

```python
@dataclass
class Model:
    """A TTS model/voice configuration."""
    id: str                        # Unique identifier (e.g., "coqui-english")
    name: str                      # Human-readable name
    engine_type: EngineType        # Parent engine type
    model_path: str                # Model identifier (e.g., "tts_models/en/ljspeech/vits")
    languages: list[str]           # Supported language codes (e.g., ["en-US", "en-GB"])
    default_language: str          # Default if not specified in request
    parameters: ParameterSchema    # Adjustable parameters
    is_default: bool               # Is this the default model?
    sample_rate: int               # Output audio sample rate (Hz)
    speaker: str | None            # Speaker ID for multi-speaker models
```

**Validation Rules**:
- `id` must be unique across all models
- `languages` must contain at least one valid BCP-47 language code
- `default_language` must be in `languages` list
- Only one model can have `is_default=True` globally

### ParameterSchema

Defines adjustable parameters for a model.

```python
@dataclass
class ParameterSchema:
    """Schema for model-specific parameters."""
    parameters: list[ParameterDefinition]

@dataclass
class ParameterDefinition:
    """Definition of a single adjustable parameter."""
    name: str                      # Parameter name (e.g., "speed")
    type: ParameterType            # Enum: FLOAT, INT, STRING, BOOL
    description: str               # Human-readable description
    default: Any                   # Default value
    min_value: float | None        # Minimum (for numeric types)
    max_value: float | None        # Maximum (for numeric types)
    allowed_values: list[Any] | None  # Enum values (for STRING type)
```

**Standard Parameters by Engine**:
| Engine | Parameter | Type | Range | Default |
|--------|-----------|------|-------|---------|
| Coqui | speed | float | 0.5-2.0 | 1.0 |
| Silero | speaker | string | model-specific | varies |
| Silero | sample_rate | int | [8000, 24000, 48000] | 48000 |

### SynthesisRequest

Input for TTS synthesis.

```python
@dataclass
class SynthesisRequest:
    """Request to synthesize text to speech."""
    text: str                      # Text to synthesize (1-5000 chars)
    model_id: str | None           # Model to use (default if not specified)
    language: str | None           # Language code (model default if not specified)
    output_format: OutputFormat    # Enum: WAV, MP3 (default: WAV)
    parameters: dict[str, Any] | None  # Model-specific parameters
```

**Validation Rules**:
- `text` must be 1-5000 characters
- `text` must not be empty or whitespace-only
- `model_id` if provided, must exist and be available
- `language` if provided, must be supported by the selected model
- `parameters` must conform to model's parameter schema

### SynthesisResponse

Output from TTS synthesis (metadata, audio returned separately).

```python
@dataclass
class SynthesisResponse:
    """Metadata about synthesized audio."""
    model_id: str                  # Model used
    language: str                  # Language used
    output_format: OutputFormat    # Audio format
    sample_rate: int               # Audio sample rate (Hz)
    duration_ms: int               # Audio duration in milliseconds
    audio_size_bytes: int          # Audio file size
```

### EngineConfig

Configuration for an engine from config.yaml.

```python
@dataclass
class EngineConfig:
    """Configuration for a TTS engine."""
    name: str                      # Model identifier
    type: str                      # Engine type: "coqui" or "silero"
    model: str                     # Model path or identifier
    languages: list[str]           # Supported languages
    default: bool                  # Is this the default model?
    speaker: str | None            # Speaker ID (for multi-speaker models)
    parameters: dict[str, Any] | None  # Default parameter values
```

### ServiceConfig

Root configuration from config.yaml.

```python
@dataclass
class ServiceConfig:
    """Root service configuration."""
    server: ServerConfig
    engines: list[EngineConfig]
    logging: LoggingConfig

@dataclass
class ServerConfig:
    """Server configuration."""
    host: str                      # Bind address (default: "0.0.0.0")
    port: int                      # Listen port (default: 8000)
    max_queue_size: int            # Request queue limit (default: 100)
    max_text_length: int           # Max text chars (default: 5000)
    synthesis_timeout: int         # Timeout in seconds (default: 30)

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str                     # Log level: debug, info, warning, error
    format: str                    # Log format: json, text
```

## Entity Relationships

```
ServiceConfig
├── ServerConfig (1:1)
├── LoggingConfig (1:1)
└── EngineConfig (1:N)
    └── maps to → Engine
        └── Model (1:N)
            └── ParameterSchema (1:1)
                └── ParameterDefinition (1:N)

SynthesisRequest
├── references → Model (via model_id)
└── contains → parameters (validated against Model.parameters)

SynthesisResponse
└── references → Model (via model_id)
```

## State Transitions

### Engine Availability State

```
[LOADING] → [AVAILABLE] (model loaded successfully)
    ↓
[UNAVAILABLE] (model file not found, load error)
    ↓
[DISABLED] (admin disabled via config)
```

### Request Processing State

```
[RECEIVED] → [QUEUED] (if queue not full)
    ↓           ↓
[REJECTED]  [PROCESSING] → [COMPLETED] (audio returned)
(queue full)     ↓
            [FAILED] (synthesis error)
```

## Enums

```python
class EngineType(str, Enum):
    COQUI = "coqui"
    SILERO = "silero"

class OutputFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"

class ParameterType(str, Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"

class EngineStatus(str, Enum):
    LOADING = "loading"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `TEXT_TOO_LONG` | 413 | Text exceeds maximum length |
| `TEXT_EMPTY` | 422 | Text is empty or whitespace |
| `MODEL_NOT_FOUND` | 404 | Requested model does not exist |
| `MODEL_UNAVAILABLE` | 503 | Model exists but is not available |
| `LANGUAGE_NOT_SUPPORTED` | 422 | Language not supported by model |
| `INVALID_PARAMETER` | 422 | Parameter value out of range |
| `SYNTHESIS_FAILED` | 500 | Engine failed during synthesis |
| `SERVICE_BUSY` | 503 | Request queue is full |
| `SYNTHESIS_TIMEOUT` | 504 | Synthesis exceeded timeout |