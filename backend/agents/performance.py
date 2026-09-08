from typing import Dict, Any, List
from ..state import StudyState
from ..models.schemas import PerformanceAnalysis, PaceStatus, RoutingDecision
from ..database.db import (
    record_topic_mastery,
    get_student_mastery,
    save_session_record,
    get_roadmap
)


def performance_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 7: Performance Agent
    Role: Aggregates evaluation results across the session and persistent memory.
    Identifies strong and weak topics, evaluates pace vs. deadline, and determines
    the deterministic routing decision: ADVANCE vs REINFORCE vs FULL REPLAN.
    """
    student_id = state.get("student_id", "student_default")
    topic = state.get("current_topic", "Python Fundamentals & Data Structures")
    eval_data = state.get("evaluation") or {}
    score = eval_data.get("score", 75)
    passed = eval_data.get("passed", score >= 70)

    target_days = state.get("target_days", 30)
    current_day = state.get("current_day", 1)
    current_topic_idx = state.get("current_topic_index", 0)
    roadmap = state.get("roadmap", [])
    total_topics = max(1, len(roadmap))

    history = list(state.get("workflow_history", []))
    history.append("Performance")

    # Update persistent topic mastery in Tier 2 SQLite Memory
    status_label = "mastered" if score >= 80 else ("reinforcing" if score >= 50 else "weak")
    record_topic_mastery(student_id, topic, score, status_label)

    # Fetch aggregated mastery history for student
    mastery_records = get_student_mastery(student_id)
    strong_topics: List[str] = []
    weak_topics: List[str] = []
    total_score = 0

    for m in mastery_records:
        t_name = m["topic_name"]
        t_score = m["score"]
        total_score += t_score
        if t_score >= 80:
            strong_topics.append(f"{t_name} ({t_score}%)")
        elif t_score < 70:
            weak_topics.append(f"{t_name} ({t_score}%)")

    mastery_pct = int(total_score / len(mastery_records)) if mastery_records else score

    # Pace vs Deadline Analysis
    # Expectation: progress % vs time %
    progress_pct = (current_topic_idx + 1) / total_topics
    time_pct = current_day / max(1, target_days)

    if progress_pct >= time_pct + 0.1:
        pace_status = PaceStatus.ahead
    elif progress_pct >= time_pct - 0.15:
        pace_status = PaceStatus.on_track
    else:
        pace_status = PaceStatus.behind

    # =========================================================================
    # DETERMINISTIC ROUTING POLICY: ADVANCE vs REINFORCE vs FULL REPLAN
    # =========================================================================
    # 1. ADVANCE: Strong mastery (score >= 80%)
    # 2. REINFORCE: Partial mastery (50% <= score < 80%)
    # 3. FULL REPLAN: Major struggle (score < 50%) or multiple weak topics
    if score >= 80:
        routing_decision = RoutingDecision.advance
        summary = f"Strong mastery demonstrated on '{topic}' ({score}%). Ready to advance to the next learning task."
    elif score >= 50:
        routing_decision = RoutingDecision.reinforce
        summary = f"Partial mastery on '{topic}' ({score}%). System will reinforce key concepts and provide targeted practice."
    else:
        routing_decision = RoutingDecision.full_replan
        summary = f"Substantial knowledge gaps identified on '{topic}' ({score}%). Triggering full roadmap replan and pacing adjustment."

    perf_obj = PerformanceAnalysis(
        strong_topics=strong_topics,
        weak_topics=weak_topics,
        mastery_percentage=mastery_pct,
        current_score=score,
        pace_status=pace_status,
        routing_decision=routing_decision,
        summary=summary
    )

    # Persist session log in Tier 2 SQLite Memory
    save_session_record(
        student_id=student_id,
        topic=topic,
        cycle_type=routing_decision.value,
        quiz_score=score,
        practice_score=score,
        overall_score=score,
        feedback=eval_data.get("feedback", "Completed evaluation"),
        pace_status=pace_status.value,
        routing_decision=routing_decision.value
    )

    return {
        "performance": perf_obj.model_dump(),
        "routing_decision": routing_decision.value,
        "workflow_history": history,
        "status": "evaluated"
    }
