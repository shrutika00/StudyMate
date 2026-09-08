from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.llm import set_test_llm
from .conftest import DeterministicMockLLM

client = TestClient(app)


def test_api_study_endpoint_success():
    """Verify POST /study returns a complete structured StudyResponse for 8 agents."""
    set_test_llm(DeterministicMockLLM(eval_score=88, eval_passed=True))

    payload = {
        "student_id": "test_api_student",
        "learning_goal": "I want to learn Python for backend development in 30 days",
        "target_days": 30,
        "action": "start"
    }
    response = client.post("/study", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["student_id"] == "test_api_student"
    assert data["learning_goal"] == "I want to learn Python for backend development in 30 days"
    assert data["assessed_level"] in ["beginner", "intermediate", "advanced"]
    assert len(data["roadmap"]) >= 3
    assert data["teaching"] is not None
    assert data["quiz"] is not None
    assert data["practice"] is not None
    assert data["evaluation"] is not None
    assert data["performance"] is not None
    assert data["routing_decision"] in ["ADVANCE", "REINFORCE", "FULL_REPLAN"]
    assert "Assessment" in data["workflow_history"]
    assert "Tutor" in data["workflow_history"]


def test_api_progress_and_history_endpoints():
    """Verify GET /progress and GET /history endpoints return student data."""
    # Progress check
    res_prog = client.get("/progress?student_id=test_api_student")
    assert res_prog.status_code == 200
    prog_data = res_prog.json()
    assert prog_data["student_id"] == "test_api_student"
    assert "roadmap" in prog_data

    # History check
    res_hist = client.get("/history?student_id=test_api_student")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert isinstance(hist_data, list)
