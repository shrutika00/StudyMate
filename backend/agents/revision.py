from typing import Dict, Any, List
from ..state import StudyState
from ..tools.registry import tool_registry


def revision_node(state: StudyState) -> Dict[str, Any]:
    """
    Revision Agent:
    Triggered when the evaluator determines the explanation is insufficient.
    Increments revision_count, records evaluator feedback into history,
    and optionally pulls supplementary reference context via tool_registry
    to empower the teacher agent to fix identified gaps.
    """
    curr_rev = state.get("revision_count", 0) + 1
    eval_data = state.get("evaluation") or {}
    feedback = eval_data.get("feedback", "Explanation needs improvement.")
    missing_points: List[str] = eval_data.get("missing_points", [])

    feedback_hist = list(state.get("feedback_history", []))
    feedback_hist.append(f"Cycle {curr_rev} feedback: {feedback}")

    history = list(state.get("workflow_history", []))
    history.append("Revise")

    context = list(state.get("context", []))

    # Query tool registry for supplementary information if missing points exist
    if missing_points:
        for missing in missing_points[:2]:
            supplementary = tool_registry.execute("learning_tool", missing)
            if supplementary and "None listed" not in supplementary:
                context.append(f"[Supplementary Reference on '{missing}']\n{supplementary}")

    return {
        "revision_count": curr_rev,
        "feedback_history": feedback_hist,
        "context": context,
        "status": "revising",
        "workflow_history": history
    }
