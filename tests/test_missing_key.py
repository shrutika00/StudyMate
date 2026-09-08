import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import ConfigurationError, check_gemini_key
from backend.agents.llm import reset_test_llm

client = TestClient(app)


def test_check_gemini_key_raises_configuration_error():
    """Verify check_gemini_key raises ConfigurationError when key is empty or dummy."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        with pytest.raises(ConfigurationError) as exc_info:
            check_gemini_key()
        assert "GEMINI_API_KEY is missing" in str(exc_info.value)

    with patch.dict("os.environ", {"GEMINI_API_KEY": "your_gemini_api_key_here"}):
        with pytest.raises(ConfigurationError) as exc_info:
            check_gemini_key()
        assert "GEMINI_API_KEY is missing" in str(exc_info.value)


def test_post_study_missing_key_returns_clear_error():
    """Verify POST /study returns HTTP 503 with clear configuration error when key missing."""
    reset_test_llm()
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        response = client.post("/study", json={"question": "What is an API?", "level": "beginner"})
        assert response.status_code == 503
        data = response.json()
        assert "GEMINI_API_KEY" in data["detail"]
