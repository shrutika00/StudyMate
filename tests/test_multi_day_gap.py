import pytest
from backend.agents.learning_planner import learning_planner_agent_node
from backend.agents.performance import performance_agent_node
from backend.database.db import save_roadmap, get_roadmap, save_or_update_student
from backend.models.schemas import RoadmapItemStatus, RoutingDecision


def test_multi_day_gap_recalibrates_remaining_plan():
    student_id = "test_gap_student_1"
    initial_roadmap = [
        {"id": 1, "topic": "Topic 1", "description": "Desc 1", "target_day": 5, "status": RoadmapItemStatus.mastered.value},
        {"id": 2, "topic": "Topic 2", "description": "Desc 2", "target_day": 10, "status": RoadmapItemStatus.in_progress.value},
        {"id": 3, "topic": "Topic 3", "description": "Desc 3", "target_day": 18, "status": RoadmapItemStatus.pending.value},
        {"id": 4, "topic": "Topic 4", "description": "Desc 4", "target_day": 25, "status": RoadmapItemStatus.pending.value},
        {"id": 5, "topic": "Topic 5", "description": "Desc 5", "target_day": 30, "status": RoadmapItemStatus.pending.value},
    ]
    save_roadmap(student_id, initial_roadmap, current_topic_index=1)
    save_or_update_student(student_id, "Learn Python", "beginner", target_days=30, current_day=1)

    # Student returns on day 15 (5 days behind Topic 2's schedule of day 10)
    state = {
        "student_id": student_id,
        "learning_goal": "Learn Python",
        "assessed_level": "beginner",
        "target_days": 30,
        "current_day": 15,
        "workflow_history": []
    }

    result = learning_planner_agent_node(state)

    assert result["status"] == "recalibrated"
    assert result["current_topic_index"] == 1
    assert "planner_update" in result
    
    updated_roadmap = result["roadmap"]
    assert updated_roadmap[0]["target_day"] == 5
    assert updated_roadmap[1]["target_day"] >= 15
    assert updated_roadmap[-1]["target_day"] <= 30


def test_performance_agent_triggers_full_replan_on_major_deadline_drift():
    student_id = "test_gap_student_2"
    roadmap = [
        {"id": 1, "topic": "Topic 1", "description": "Desc 1", "target_day": 5, "status": RoadmapItemStatus.in_progress.value},
        {"id": 2, "topic": "Topic 2", "description": "Desc 2", "target_day": 10, "status": RoadmapItemStatus.pending.value},
        {"id": 3, "topic": "Topic 3", "description": "Desc 3", "target_day": 20, "status": RoadmapItemStatus.pending.value},
        {"id": 4, "topic": "Topic 4", "description": "Desc 4", "target_day": 30, "status": RoadmapItemStatus.pending.value},
    ]

    # Progress = 1/4 (25%), time = 25/30 (83%), lag > 25% -> triggers FULL_REPLAN even if topic score is 85%
    state = {
        "student_id": student_id,
        "current_topic": "Topic 1",
        "current_topic_index": 0,
        "roadmap": roadmap,
        "target_days": 30,
        "current_day": 25,
        "evaluation": {"score": 85, "passed": True, "feedback": "Good quiz score"},
        "workflow_history": []
    }

    result = performance_agent_node(state)
    assert result["routing_decision"] == RoutingDecision.full_replan.value
    assert "deadline drift" in result["performance"]["summary"].lower()
