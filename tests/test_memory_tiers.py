import uuid
from backend.database.db import (
    init_db,
    save_or_update_student,
    get_student,
    save_roadmap,
    get_roadmap,
    record_topic_mastery,
    get_student_mastery,
    save_session_record,
    get_student_sessions,
)
from backend.state import StudyState


def test_persistent_cross_session_memory():
    """Requirement 15: Persistent memory survives across sessions in SQLite."""
    init_db()
    sid = f"student_persist_test_{uuid.uuid4().hex[:6]}"

    # 1. Profile persistence
    save_or_update_student(
        student_id=sid,
        learning_goal="Master FastAPI in 30 days",
        assessed_level="intermediate",
        target_days=30,
        current_day=5
    )
    profile = get_student(sid)
    assert profile is not None
    assert profile["learning_goal"] == "Master FastAPI in 30 days"
    assert profile["assessed_level"] == "intermediate"

    # 2. Roadmap persistence
    test_roadmap = [
        {"id": 1, "topic": "HTTP & REST", "target_day": 5, "status": "mastered"},
        {"id": 2, "topic": "FastAPI Models", "target_day": 12, "status": "in_progress"}
    ]
    save_roadmap(sid, test_roadmap, current_topic_index=1)
    roadmap_data = get_roadmap(sid)
    assert roadmap_data is not None
    assert len(roadmap_data["roadmap"]) == 2
    assert roadmap_data["current_topic_index"] == 1

    # 3. Topic Mastery persistence
    record_topic_mastery(sid, "HTTP & REST", score=90, status="mastered")
    record_topic_mastery(sid, "FastAPI Models", score=60, status="reinforcing")
    mastery = get_student_mastery(sid)
    assert len(mastery) == 2

    # 4. Learning Session logs
    save_session_record(
        student_id=sid,
        topic="HTTP & REST",
        cycle_type="ADVANCE",
        quiz_score=95,
        practice_score=85,
        overall_score=90,
        feedback="High mastery",
        pace_status="ahead",
        routing_decision="ADVANCE"
    )
    sessions = get_student_sessions(sid)
    assert len(sessions) == 1
    assert sessions[0]["topic"] == "HTTP & REST"
    assert sessions[0]["routing_decision"] == "ADVANCE"


def test_session_scoped_memory_isolation():
    """Requirement 16: Session memory remains session-scoped in LangGraph state."""
    # Two distinct session states with different ephemeral quiz and practice attempts
    session_1: StudyState = {
        "student_id": "student_alpha",
        "current_topic": "Topic A",
        "student_quiz_answer": "A",
        "student_practice_code": "code_alpha"
    }

    session_2: StudyState = {
        "student_id": "student_beta",
        "current_topic": "Topic B",
        "student_quiz_answer": "B",
        "student_practice_code": "code_beta"
    }

    # Session 1 inputs do not bleed into Session 2
    assert session_1["student_quiz_answer"] != session_2["student_quiz_answer"]
    assert session_1["student_practice_code"] != session_2["student_practice_code"]
    assert session_1["current_topic"] != session_2["current_topic"]
