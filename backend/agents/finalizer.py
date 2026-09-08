from typing import Dict, Any
from ..state import StudyState
from ..models.schemas import StudyResponse, Evaluation


def finalizer_node(state: StudyState) -> Dict[str, Any]:
    """
    Finalizer Agent:
    Compiles the comprehensive, structured StudyResponse after either
    satisfying evaluation criteria or reaching the maximum revision limit.
    """
    history = list(state.get("workflow_history", []))
    history.append("Final")

    eval_dict = state.get("evaluation")
    evaluation = Evaluation(**eval_dict) if eval_dict else None

    is_sufficient = evaluation.is_sufficient if evaluation else True
    rev_count = state.get("revision_count", 0)
    max_rev = state.get("max_revisions", 2)

    if is_sufficient:
        status = "completed"
    elif rev_count >= max_rev:
        status = "max_revisions_reached"
    else:
        status = "completed"

    response = StudyResponse(
        question=state.get("user_question", ""),
        level=state.get("level", "beginner"),
        plan=state.get("plan", []),
        explanation=state.get("explanation", ""),
        key_points=state.get("key_points", []),
        examples=state.get("examples", []),
        follow_up_question=state.get("follow_up_question", ""),
        revision_count=rev_count,
        status=status,
        evaluation=evaluation,
        workflow_history=history
    )

    return {
        "final_answer": response.model_dump(),
        "status": status,
        "workflow_history": history
    }
