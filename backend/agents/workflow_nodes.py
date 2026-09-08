from typing import Dict, Any, List
from ..state import StudyState
from ..models.schemas import (
    StudyResponse,
    RoadmapItem,
    RoadmapItemStatus,
    RoutingDecision,
    AssessmentResult,
    QuizQuestion,
    Quiz,
    QuizResult,
    TeachingContent,
    PracticeExercise,
    EvaluationResult,
    PerformanceAnalysis,
    PlannerUpdate
)
from ..database.db import save_roadmap


def advance_task_node(state: StudyState) -> Dict[str, Any]:
    """
    Workflow Node: Advance Task
    Triggered when routing decision is ADVANCE.
    Marks current topic as mastered, increments to next roadmap module,
    and prepares the next cycle.
    """
    student_id = state.get("student_id", "student_default")
    current_idx = state.get("current_topic_index", 0)
    roadmap = [dict(m) for m in state.get("roadmap", [])]
    history = list(state.get("workflow_history", []))
    history.append("Advance")

    if current_idx < len(roadmap):
        roadmap[current_idx]["status"] = RoadmapItemStatus.mastered.value

    next_idx = current_idx + 1
    new_day = state.get("current_day", 1) + 4
    cycle = state.get("cycle_count", 0) + 1

    if next_idx < len(roadmap):
        roadmap[next_idx]["status"] = RoadmapItemStatus.in_progress.value
        next_topic = roadmap[next_idx]["topic"]
        status = "advancing"
    else:
        next_topic = roadmap[-1]["topic"] if roadmap else "Completed"
        status = "roadmap_completed"

    save_roadmap(student_id, roadmap, current_topic_index=next_idx)

    return {
        "roadmap": roadmap,
        "current_topic_index": next_idx,
        "current_topic": next_topic,
        "current_day": new_day,
        "cycle_count": cycle,
        "workflow_history": history,
        "status": status
    }


def reinforce_task_node(state: StudyState) -> Dict[str, Any]:
    """
    Workflow Node: Reinforce Task
    Triggered when routing decision is REINFORCE.
    Retains current topic, marks status as reinforcing, and preps targeted reteaching.
    """
    student_id = state.get("student_id", "student_default")
    current_idx = state.get("current_topic_index", 0)
    roadmap = [dict(m) for m in state.get("roadmap", [])]
    history = list(state.get("workflow_history", []))
    history.append("Reinforce")

    if current_idx < len(roadmap):
        roadmap[current_idx]["status"] = RoadmapItemStatus.reinforcing.value

    cycle = state.get("cycle_count", 0) + 1
    save_roadmap(student_id, roadmap, current_topic_index=current_idx)

    return {
        "roadmap": roadmap,
        "cycle_count": cycle,
        "workflow_history": history,
        "status": "reinforcing"
    }


def finalizer_node(state: StudyState) -> Dict[str, Any]:
    """
    Workflow Node: Finalizer
    Compiles the comprehensive, structured StudyResponse after a completed cycle.
    """
    history = list(state.get("workflow_history", []))
    if "Final" not in history[-1:]:
        history.append("Final")

    roadmap_items = [RoadmapItem(**m) for m in state.get("roadmap", [])]

    study_resp = StudyResponse(
        student_id=state.get("student_id", "student_default"),
        learning_goal=state.get("learning_goal", ""),
        assessed_level=state.get("assessed_level", "beginner"),
        current_topic=state.get("current_topic", ""),
        current_day=state.get("current_day", 1),
        target_days=state.get("target_days", 30),
        roadmap=roadmap_items,
        assessment=state.get("assessment"),
        teaching=state.get("teaching"),
        quiz=state.get("quiz"),
        quiz_multi=state.get("quiz_multi"),
        quiz_result=state.get("quiz_result"),
        practice=state.get("practice"),
        evaluation=state.get("evaluation"),
        performance=state.get("performance"),
        planner_update=state.get("planner_update"),
        routing_decision=state.get("routing_decision", RoutingDecision.advance.value),
        workflow_history=history,
        cycle_count=state.get("cycle_count", 0),
        status=state.get("status", "completed")
    )

    return {
        "workflow_history": history,
        "final_answer": study_resp.model_dump(),
        "status": "completed"
    }
