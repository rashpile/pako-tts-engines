# pako-tts-engines

API service for local Text-to-Speech synthesis with multiple engine backends (Coqui TTS, Silero).

## Prerequisites

- Python 3.11 (< 3.12, required by TTS package)
- [uv](https://docs.astral.sh/uv/) package manager
- ~5GB disk space for TTS models (downloaded on first use)

## Getting Started

```bash
# Install dependencies
make dev

# Create config.yaml (see Configuration section)

# Run the application
make run
```

The API will be available at `http://localhost:8000`.

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

## API Usage

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### List Models

```bash
curl http://localhost:8000/api/v1/models
```

### Synthesize Speech

```bash
# Basic synthesis (uses default model)
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}' \
  --output hello.wav

# With specific model and parameters
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Speaking at a faster rate.",
    "model_id": "coqui-english",
    "parameters": {"speed": 1.5}
  }' \
  --output fast.wav
```

## Development

```bash
# Run tests
make test

# Run tests with coverage
make test-coverage

# Run linter and formatter
make check

# Type checking
make typecheck
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
