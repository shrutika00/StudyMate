from typing import Dict, Any, List
from ..state import StudyState
from ..models.schemas import PlannerUpdate, RoadmapItem, RoadmapItemStatus
from ..database.db import save_roadmap


def planner_update_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 8: Planner Update Agent
    Role: Modifies the REMAINING study roadmap based on actual student performance.
    Reorganizes modules, injects targeted remediation labs, or fast-tracks mastery,
    making StudyMate a continuously replanning intelligent learning system.
    """
    student_id = state.get("student_id", "student_default")
    current_topic = state.get("current_topic", "")
    current_idx = state.get("current_topic_index", 0)
    roadmap = list(state.get("roadmap", []))
    perf_data = state.get("performance") or {}
    weak_topics = perf_data.get("weak_topics", [])
    pace_status = perf_data.get("pace_status", "on_track")

    history = list(state.get("workflow_history", []))
    history.append("PlannerUpdate")

    # Reorganize Remaining Roadmap
    updated_roadmap: List[Dict[str, Any]] = []

    # Keep completed topics up to current_idx
    for i in range(min(current_idx, len(roadmap))):
        updated_roadmap.append(roadmap[i])

    # Inject targeted reinforcement module directly into roadmap for struggling area
    remedy_id = len(roadmap) + 100
    remedial_module = {
        "id": remedy_id,
        "topic": f"Foundational Remediation: Core Primitives for {current_topic}",
        "description": "Deep-dive diagnostic review addressing syntax errors, edge-cases, and memory patterns.",
        "target_day": roadmap[current_idx]["target_day"] if current_idx < len(roadmap) else 15,
        "status": RoadmapItemStatus.in_progress.value
    }
    updated_roadmap.append(remedial_module)

    # Re-index remaining topics with adjusted target days
    for i in range(current_idx, len(roadmap)):
        item = dict(roadmap[i])
        item["target_day"] = item.get("target_day", 10) + 3  # Stretch timeline slightly
        item["status"] = RoadmapItemStatus.pending.value
        updated_roadmap.append(item)

    reason = f"Performance score triggered FULL_REPLAN. Identified weakness on '{current_topic}' with pace '{pace_status}'."
    changes_summary = f"Injected '{remedial_module['topic']}' and recalibrated remaining deadlines to ensure mastery."

    planner_update_obj = PlannerUpdate(
        reason=reason,
        changes_summary=changes_summary,
        updated_roadmap=[RoadmapItem(**m) for m in updated_roadmap]
    )

    # Persist the reorganized roadmap to Tier 2 SQLite Memory
    save_roadmap(student_id, updated_roadmap, current_topic_index=current_idx)

    # Point current topic to the new remediation module
    new_topic = remedial_module["topic"]

    # Increment cycle count
    cycle = state.get("cycle_count", 0) + 1

    return {
        "roadmap": updated_roadmap,
        "current_topic": new_topic,
        "planner_update": planner_update_obj.model_dump(),
        "workflow_history": history,
        "cycle_count": cycle,
        "status": "replanned"
    }
