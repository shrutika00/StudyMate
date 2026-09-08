import pytest
from backend.agents import (
    assessment_agent_node,
    learning_planner_agent_node,
    tutor_agent_node,
    quiz_agent_node,
    practice_agent_node,
    evaluation_agent_node,
    performance_agent_node,
    planner_update_agent_node,
    set_test_llm
)
from backend.state import StudyState
from .conftest import DeterministicMockLLM


def test_agent_1_assessment():
    """Requirement 3: Assessment Agent determines student level."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "student_id": "test_student_assess",
        "learning_goal": "I want to learn Python for backend development in 30 days",
        "target_days": 30,
        "workflow_history": []
    }
    result = assessment_agent_node(state)
    assert "assessment" in result
    assert result["assessed_level"] == "beginner"
    assert "Assessment" in result["workflow_history"]


def test_agent_2_learning_planner():
    """Requirement 4: Learning Planner Agent constructs initial roadmap."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "student_id": "test_student_plan",
        "learning_goal": "I want to learn Python for backend development in 30 days",
        "assessed_level": "beginner",
        "target_days": 30,
        "workflow_history": []
    }
    result = learning_planner_agent_node(state)
    assert "roadmap" in result
    assert len(result["roadmap"]) >= 3
    assert result["current_topic"] != ""
    assert "Plan" in result["workflow_history"]


def test_agent_3_tutor_with_rag():
    """Requirement 5: Tutor retrieves knowledge before teaching."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "assessed_level": "beginner",
        "workflow_history": []
    }
    result = tutor_agent_node(state)
    assert "teaching" in result
    assert "retrieved_context" in result
    assert len(result["retrieved_context"]) > 0
    # Must contain grounded context about Python and data structures
    assert "Python" in result["retrieved_context"][0]
    assert len(result["teaching"]["grounded_sources"]) > 0
    assert "Tutor" in result["workflow_history"]


def test_agent_4_quiz():
    """Requirement 6: Quiz Agent generates structured quiz."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "assessed_level": "beginner",
        "retrieved_context": ["Dictionaries are O(1) hash maps"],
        "workflow_history": []
    }
    result = quiz_agent_node(state)
    assert "quiz" in result
    assert "question" in result["quiz"]
    assert len(result["quiz"]["options"]) == 4
    assert result["quiz"]["correct_option"] != ""
    assert "Quiz" in result["workflow_history"]


def test_agent_5_practice():
    """Requirement 7: Practice Agent generates hands-on exercise."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "assessed_level": "beginner",
        "retrieved_context": ["Lists and dictionaries"],
        "workflow_history": []
    }
    result = practice_agent_node(state)
    assert "practice" in result
    assert "starter_code" in result["practice"]
    assert "problem_statement" in result["practice"]
    assert "Practice" in result["workflow_history"]


def test_agent_6_evaluation_hybrid():
    """Requirement 8: Evaluation Agent evaluates objective and code answers."""
    set_test_llm(DeterministicMockLLM(eval_score=92, eval_passed=True))
    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "quiz": {"question": "Time complexity?", "correct_option": "A"},
        "practice": {"starter_code": "def solve(): pass", "problem_statement": "Implement cache"},
        "student_quiz_answer": "A",
        "student_practice_code": "def solve():\n    return {'user_1': 5}",
        "workflow_history": []
    }
    result = evaluation_agent_node(state)
    assert "evaluation" in result
    assert result["evaluation"]["score"] == 92
    assert result["evaluation"]["passed"] is True
    assert result["evaluation"]["answer_type"] == "code"


def test_agent_7_performance_identifies_weak_topics():
    """Requirement 9: Performance Agent aggregates results and identifies weak topics."""
    state: StudyState = {
        "student_id": "test_student_perf",
        "current_topic": "Async Programming",
        "target_days": 30,
        "current_day": 20,
        "current_topic_index": 2,
        "roadmap": [
            {"topic": "Basics", "status": "mastered"},
            {"topic": "OOP", "status": "mastered"},
            {"topic": "Async Programming", "status": "in_progress"}
        ],
        "evaluation": {
            "score": 45,
            "passed": False,
            "feedback": "Lacks event loop mechanics"
        },
        "workflow_history": []
    }
    result = performance_agent_node(state)
    assert "performance" in result
    perf = result["performance"]
    assert perf["current_score"] == 45
    assert any("Async Programming" in w for w in perf["weak_topics"])
    # With score 45, routing decision must be FULL_REPLAN
    assert result["routing_decision"] == "FULL_REPLAN"


def test_agent_8_planner_update_changes_roadmap():
    """Requirement 10: Planner Update Agent modifies the remaining roadmap."""
    state: StudyState = {
        "student_id": "test_student_replan",
        "current_topic": "Async Programming",
        "current_topic_index": 1,
        "roadmap": [
            {"id": 1, "topic": "Basics", "target_day": 5, "status": "mastered"},
            {"id": 2, "topic": "Async Programming", "target_day": 15, "status": "in_progress"},
            {"id": 3, "topic": "Databases", "target_day": 25, "status": "pending"}
        ],
        "performance": {
            "weak_topics": ["Async Programming (45%)"],
            "pace_status": "behind"
        },
        "workflow_history": []
    }
    result = planner_update_agent_node(state)
    assert "planner_update" in result
    assert "roadmap" in result
    # Must inject remedial module
    remedial_topics = [m["topic"] for m in result["roadmap"] if "Foundational Remediation" in m["topic"]]
    assert len(remedial_topics) == 1
    assert "PlannerUpdate" in result["workflow_history"]
