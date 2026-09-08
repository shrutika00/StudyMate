from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    """Requirement 1: Health endpoint returns 200 and registered tools."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "StudyMate"
    assert "tools_registered" in data
    assert "rag_knowledge_tool" in data["tools_registered"]
