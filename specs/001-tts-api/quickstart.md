# Quickstart: TTS API Service

**Feature**: 001-tts-api
**Date**: 2025-12-21

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- ~5GB disk space for TTS models (downloaded on first use)

## Installation

```bash
# Clone and enter the repository
cd pako-tts-engines

# Install dependencies
make dev

# Verify installation
make check
```

## Configuration

Create `config.yaml` in the project root:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  max_queue_size: 100
  max_text_length: 5000
  synthesis_timeout: 30

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

## Running the Service

```bash
# Start the server
make run

# Or directly with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Usage

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "engines": [
    {"name": "coqui", "status": "available", "models_count": 2},
    {"name": "silero", "status": "available", "models_count": 1}
  ],
  "version": "1.0.0"
}
```

### List Available Models

```bash
curl http://localhost:8000/api/v1/models
```

Response:
```json
{
  "models": [
    {
      "id": "coqui-english",
      "name": "Coqui English (LJSpeech)",
      "engine": "coqui",
      "languages": ["en-US", "en-GB"],
      "is_available": true,
      "is_default": true
    },
    {
      "id": "coqui-romanian",
      "name": "Coqui Romanian",
      "engine": "coqui",
      "languages": ["ro-RO"],
      "is_available": true,
      "is_default": false
    }
  ],
  "default_model_id": "coqui-english"
}
```

### Get Model Details

```bash
curl http://localhost:8000/api/v1/models/coqui-english
```

Response:
```json
{
  "id": "coqui-english",
  "name": "Coqui English (LJSpeech)",
  "engine": "coqui",
  "languages": ["en-US", "en-GB"],
  "default_language": "en-US",
  "sample_rate": 22050,
  "parameters": [
    {
      "name": "speed",
      "type": "float",
      "description": "Speech rate multiplier",
      "default": 1.0,
      "min_value": 0.5,
      "max_value": 2.0
    }
  ],
  "is_available": true,
  "is_default": true
}
```

### Synthesize Speech

```bash
# Basic synthesis (uses default model)
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}' \
  --output hello.wav

# Specify model and language
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bună ziua, aceasta este un test.",
    "model_id": "coqui-romanian",
    "language": "ro-RO"
  }' \
  --output romanian.wav

# With custom parameters
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Speaking at a faster rate.",
    "model_id": "coqui-english",
    "parameters": {"speed": 1.5}
  }' \
  --output fast.wav
```

Response headers include metadata:
```
X-Model-Id: coqui-english
X-Language: en-US
X-Duration-Ms: 2340
X-Sample-Rate: 22050
```

## Error Handling

All errors return JSON with a consistent structure:

```json
{
  "error": {
    "code": "TEXT_TOO_LONG",
    "message": "Text exceeds maximum length of 5000 characters",
    "details": {
      "max_length": 5000,
      "actual_length": 6234
    }
  }
}
```

Common error codes:
- `VALIDATION_ERROR` (422): Request validation failed
- `TEXT_TOO_LONG` (413): Text exceeds limit
- `MODEL_NOT_FOUND` (404): Model doesn't exist
- `MODEL_UNAVAILABLE` (503): Model not loaded
- `SERVICE_BUSY` (503): Queue is full

## Development

```bash
# Run tests
make test

# Run with coverage
make test-coverage

# Lint and format
make check

# Type checking only
make typecheck
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Troubleshooting

### Models not loading
Models are downloaded on first use. Ensure you have:
- Internet connection for initial download
- ~5GB disk space
- Write permissions to model cache directory

### Slow first request
First synthesis request triggers model loading. Subsequent requests will be faster.

### Out of memory
Reduce number of loaded models in `config.yaml` or use a machine with more RAM.

### GPU not detected
Coqui TTS and Silero will use CPU if CUDA is not available. For GPU acceleration:
- Install PyTorch with CUDA support
- Set `CUDA_VISIBLE_DEVICES` environment variable
