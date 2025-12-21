"""Integration tests for synthesis flow."""

from fastapi.testclient import TestClient


class TestSynthesisFlow:
    """End-to-end tests for the synthesis flow."""

    def test_basic_synthesis_flow(self, test_client: TestClient) -> None:
        """Test basic text-to-speech synthesis."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello, world!"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert "x-model-id" in response.headers
        assert len(response.content) > 0

    def test_synthesis_with_model_id(self, test_client: TestClient) -> None:
        """Test synthesis with specific model ID."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello", "model_id": "mock-engine"},
        )

        assert response.status_code == 200
        assert response.headers["x-model-id"] == "mock-engine"

    def test_synthesis_returns_wav_audio(self, test_client: TestClient) -> None:
        """Test that synthesis returns valid WAV audio."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Test audio"},
        )

        assert response.status_code == 200

        # Check WAV header
        content = response.content
        assert content[:4] == b"RIFF"
        assert content[8:12] == b"WAVE"

    def test_synthesis_empty_text_rejected(self, test_client: TestClient) -> None:
        """Test that empty text is rejected."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": ""},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "TEXT_EMPTY"

    def test_synthesis_whitespace_text_rejected(self, test_client: TestClient) -> None:
        """Test that whitespace-only text is rejected."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "   \n\t  "},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "TEXT_EMPTY"

    def test_synthesis_long_text_rejected(self, test_client: TestClient) -> None:
        """Test that text exceeding limit is rejected."""
        # Config has max_text_length = 1000
        long_text = "x" * 1001
        response = test_client.post(
            "/api/v1/tts",
            json={"text": long_text},
        )

        assert response.status_code == 413
        data = response.json()
        assert data["error"]["code"] == "TEXT_TOO_LONG"
        assert data["error"]["details"]["max_length"] == 1000

    def test_synthesis_invalid_model_rejected(self, test_client: TestClient) -> None:
        """Test that invalid model ID is rejected."""
        response = test_client.post(
            "/api/v1/tts",
            json={"text": "Hello", "model_id": "invalid-model"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_FOUND"


class TestHealthFlow:
    """End-to-end tests for health check flow."""

    def test_health_check_returns_engine_info(self, test_client: TestClient) -> None:
        """Test that health check returns engine information."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(data["engines"], list)

    def test_health_check_returns_version(self, test_client: TestClient) -> None:
        """Test that health check returns version."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestModelsFlow:
    """End-to-end tests for models listing flow."""

    def test_list_models_returns_array(self, test_client: TestClient) -> None:
        """Test that models endpoint returns array."""
        response = test_client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

    def test_list_models_includes_default(self, test_client: TestClient) -> None:
        """Test that models list includes default model info."""
        response = test_client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "default_model_id" in data

    def test_get_model_detail(self, test_client: TestClient) -> None:
        """Test getting model details."""
        response = test_client.get("/api/v1/models/mock-engine")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mock-engine"
        assert "parameters" in data
        assert "languages" in data

    def test_get_invalid_model_returns_404(self, test_client: TestClient) -> None:
        """Test that invalid model ID returns 404."""
        response = test_client.get("/api/v1/models/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_FOUND"
