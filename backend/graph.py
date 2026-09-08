from typing import Literal
from langgraph.graph import StateGraph, START, END
from .state import StudyState
from .agents import (
    assessment_agent_node,
    learning_planner_agent_node,
    tutor_agent_node,
    quiz_agent_node,
    practice_agent_node,
    evaluation_agent_node,
    performance_agent_node,
    planner_update_agent_node,
    advance_task_node,
    reinforce_task_node,
    finalizer_node,
)


def route_performance(state: StudyState) -> Literal["advance", "reinforce", "replan", "finish"]:
    """
    Conditional Router:
    Inspects the Performance Agent's decision and bounded cycle count.
    - If cycle limit reached -> routes to 'finish' (finalizer)
    - If decision is ADVANCE -> routes to 'advance' node
    - If decision is REINFORCE -> routes to 'reinforce' node
    - If decision is FULL_REPLAN -> routes to 'replan' (planner_update) node
    """
    cycle_count = state.get("cycle_count", 0)
    max_cycles = state.get("max_cycles", 3)

    if cycle_count >= max_cycles:
        return "finish"

    decision = state.get("routing_decision", "ADVANCE").upper()

    if decision == "ADVANCE":
        roadmap = state.get("roadmap", [])
        idx = state.get("current_topic_index", 0)
        # If student just finished the very last topic
        if idx >= len(roadmap) - 1 and state.get("evaluation", {}).get("passed", False):
            return "advance"
        return "advance"
    elif decision == "REINFORCE":
        return "reinforce"
    elif decision == "FULL_REPLAN":
        return "replan"
    else:
        return "advance"


def route_after_advance(state: StudyState) -> Literal["tutor", "finish"]:
    """
    Determines whether to cycle back to Tutor for the next learning task
    or terminate at Finalizer if the roadmap is complete or max cycles reached.
    """
    cycle_count = state.get("cycle_count", 0)
    max_cycles = state.get("max_cycles", 3)
    status = state.get("status")

    if cycle_count >= max_cycles or status == "roadmap_completed":
        return "finish"
    return "tutor"


def route_after_reinforce(state: StudyState) -> Literal["tutor", "finish"]:
    """
    Cycles back to Tutor for targeted reteaching and practice,
    guarded by max cycle limit.
    """
    cycle_count = state.get("cycle_count", 0)
    max_cycles = state.get("max_cycles", 3)

    if cycle_count >= max_cycles:
        return "finish"
    return "tutor"


def route_after_replan(state: StudyState) -> Literal["tutor", "finish"]:
    """
    Cycles back to Tutor with the freshly reorganized roadmap module,
    guarded by max cycle limit.
    """
    cycle_count = state.get("cycle_count", 0)
    max_cycles = state.get("max_cycles", 3)

    if cycle_count >= max_cycles:
        return "finish"
    return "tutor"


def create_studymate_graph():
    """
    Builds and compiles the full 8-Agent StudyMate LangGraph with real cyclic topology
    and 3-way conditional routing (ADVANCE vs REINFORCE vs FULL REPLAN).
    """
    builder = StateGraph(StudyState)

    # 1. Register All 8 Core Agents + Action Nodes
    builder.add_node("assessment", assessment_agent_node)
    builder.add_node("learning_planner", learning_planner_agent_node)
    builder.add_node("tutor", tutor_agent_node)
    builder.add_node("quiz", quiz_agent_node)
    builder.add_node("practice", practice_agent_node)
    builder.add_node("evaluation", evaluation_agent_node)
    builder.add_node("performance", performance_agent_node)
    builder.add_node("advance", advance_task_node)
    builder.add_node("reinforce", reinforce_task_node)
    builder.add_node("planner_update", planner_update_agent_node)
    builder.add_node("finalizer", finalizer_node)

    # 2. Linear Pedagogical Sequence
    builder.add_edge(START, "assessment")
    builder.add_edge("assessment", "learning_planner")
    builder.add_edge("learning_planner", "tutor")
    builder.add_edge("tutor", "quiz")
    builder.add_edge("quiz", "practice")
    builder.add_edge("practice", "evaluation")
    builder.add_edge("evaluation", "performance")

    # 3. Conditional Routing From Performance Agent
    builder.add_conditional_edges(
        "performance",
        route_performance,
        {
            "advance": "advance",
            "reinforce": "reinforce",
            "replan": "planner_update",
            "finish": "finalizer"
        }
    )

    # 4. Cyclic Loop Edges (Loop back to Tutor or exit to Finalizer)
    builder.add_conditional_edges(
        "advance",
        route_after_advance,
        {
            "tutor": "tutor",
            "finish": "finalizer"
        }
    )

    builder.add_conditional_edges(
        "reinforce",
        route_after_reinforce,
        {
            "tutor": "tutor",
            "finish": "finalizer"
        }
    )

    builder.add_conditional_edges(
        "planner_update",
        route_after_replan,
        {
            "tutor": "tutor",
            "finish": "finalizer"
        }
    )

    # 5. Finalizer Terminates at END
    builder.add_edge("finalizer", END)

    return builder.compile()


# Pre-compiled graph instance
study_graph = create_studymate_graph()
