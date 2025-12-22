"""Contract tests for API endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /api/v1/health endpoint."""

    def test_health_returns_200(self, test_client: TestClient) -> None:
        """Health endpoint returns 200 OK."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_status(self, test_client: TestClient) -> None:
        """Health endpoint returns status field."""
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_returns_engines(self, test_client: TestClient) -> None:
        """Health endpoint returns engines array."""
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)

    def test_health_engine_has_required_fields(self, test_client: TestClient) -> None:
        """Each engine in health response has required fields."""
        response = test_client.get("/api/v1/health")
        data = response.json()
        for engine in data["engines"]:
            assert "name" in engine
            assert "status" in engine
            assert "models_count" in engine


class TestTTSEndpoint:
    """Tests for POST /api/v1/tts endpoint."""

    def test_tts_returns_audio(self, test_client: TestClient) -> None:
        """TTS endpoint returns audio data."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello world"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_tts_returns_mp3_format(self, test_client: TestClient) -> None:
        """TTS endpoint returns MP3 audio when requested."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello world", "output_format": "mp3"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        # MP3 files start with ID3 tag or MPEG frame sync
        content = response.content
        assert content[:3] == b"ID3" or content[:2] == b"\xff\xfb"

    def test_tts_returns_metadata_headers(self, test_client: TestClient) -> None:
        """TTS endpoint returns metadata in headers."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello world"},
        )
        assert response.status_code == 200
        assert "x-model-id" in response.headers
        assert "x-sample-rate" in response.headers

    def test_tts_empty_text_returns_422(self, test_client: TestClient) -> None:
        """TTS endpoint returns 422 for empty text."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": ""},
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "TEXT_EMPTY"

    def test_tts_text_too_long_returns_413(self, test_client: TestClient) -> None:
        """TTS endpoint returns 413 for text that is too long."""
        # Config has max_text_length = 1000
        long_text = "a" * 1001
        response = test_client.post(
            "/api/v1/tts",
            json={"text": long_text},
        )
        assert response.status_code == 413
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "TEXT_TOO_LONG"

    def test_tts_invalid_model_returns_404(self, test_client: TestClient) -> None:
        """TTS endpoint returns 404 for non-existent model."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello", "model_id": "non-existent-model"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_FOUND"

    def test_tts_missing_text_returns_422(self, test_client: TestClient) -> None:
        """TTS endpoint returns 422 when text is missing."""
        response = test_client.post(
            "/api/v1/tts",
            json={},
        )
        assert response.status_code == 422


class TestModelsEndpoint:
    """Tests for GET /api/v1/models endpoint."""

    def test_list_models_returns_200(self, test_client: TestClient) -> None:
        """Models list endpoint returns 200 OK."""
        response = test_client.get("/api/v1/models")
        assert response.status_code == 200

    def test_list_models_returns_array(self, test_client: TestClient) -> None:
        """Models list endpoint returns models array."""
        response = test_client.get("/api/v1/models")
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

    def test_model_has_required_fields(self, test_client: TestClient) -> None:
        """Each model in list has required fields."""
        response = test_client.get("/api/v1/models")
        data = response.json()
        for model in data["models"]:
            assert "id" in model
            assert "name" in model
            assert "engine" in model
            assert "languages" in model
            assert "is_available" in model


class TestModelDetailEndpoint:
    """Tests for GET /api/v1/models/{model_id} endpoint."""

    def test_get_model_returns_200(self, test_client: TestClient) -> None:
        """Model detail endpoint returns 200 for existing model."""
        response = test_client.get("/api/v1/models/mock-engine")
        assert response.status_code == 200

    def test_get_model_returns_details(self, test_client: TestClient) -> None:
        """Model detail endpoint returns model details."""
        response = test_client.get("/api/v1/models/mock-engine")
        data = response.json()
        assert data["id"] == "mock-engine"
        assert "parameters" in data

    def test_get_model_not_found_returns_404(self, test_client: TestClient) -> None:
        """Model detail endpoint returns 404 for non-existent model."""
        response = test_client.get("/api/v1/models/non-existent")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_FOUND"
