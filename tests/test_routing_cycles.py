import pytest
from backend.graph import study_graph, route_performance
from backend.state import StudyState
from backend.agents.llm import set_test_llm
from .conftest import DeterministicMockLLM


def test_conditional_router_decisions():
    """Verify route_performance router accurately branches for ADVANCE, REINFORCE, and FULL_REPLAN."""
    # 1. ADVANCE
    state_advance: StudyState = {
        "routing_decision": "ADVANCE",
        "cycle_count": 0,
        "max_cycles": 3
    }
    assert route_performance(state_advance) == "advance"

    # 2. REINFORCE
    state_reinforce: StudyState = {
        "routing_decision": "REINFORCE",
        "cycle_count": 0,
        "max_cycles": 3
    }
    assert route_performance(state_reinforce) == "reinforce"

    # 3. FULL_REPLAN
    state_replan: StudyState = {
        "routing_decision": "FULL_REPLAN",
        "cycle_count": 0,
        "max_cycles": 3
    }
    assert route_performance(state_replan) == "replan"

    # 4. Cycle boundary termination
    state_limit: StudyState = {
        "routing_decision": "REINFORCE",
        "cycle_count": 3,
        "max_cycles": 3
    }
    assert route_performance(state_limit) == "finish"


def test_requirement_11_advance_routing():
    """Requirement 11: ADVANCE routing executes when mastery is demonstrated."""
    set_test_llm(DeterministicMockLLM(eval_score=90, eval_passed=True))

    initial_state: StudyState = {
        "student_id": "test_student_adv",
        "learning_goal": "Learn Python in 30 days",
        "target_days": 30,
        "cycle_count": 0,
        "max_cycles": 1,
        "workflow_history": []
    }

    final_state = study_graph.invoke(initial_state)

    assert final_state["routing_decision"] == "ADVANCE"
    assert "Advance" in final_state["workflow_history"]
    # Current topic index incremented
    assert final_state["current_topic_index"] == 1


def test_requirement_12_reinforce_routing():
    """Requirement 12: REINFORCE routing executes when partial understanding is shown."""
    # Score 65 triggers REINFORCE
    set_test_llm(DeterministicMockLLM(eval_score=65, eval_passed=False))

    initial_state: StudyState = {
        "student_id": "test_student_reinf",
        "learning_goal": "Learn Python in 30 days",
        "target_days": 30,
        "cycle_count": 0,
        "max_cycles": 1,
        "workflow_history": []
    }

    final_state = study_graph.invoke(initial_state)

    assert final_state["routing_decision"] == "REINFORCE"
    assert "Reinforce" in final_state["workflow_history"]
    # Topic is retained for targeted reteaching
    assert final_state["current_topic_index"] == 0


def test_requirement_13_full_replan_routing():
    """Requirement 13: FULL REPLAN routing executes on significant difficulty (< 50%)."""
    # Score 40 triggers FULL_REPLAN
    set_test_llm(DeterministicMockLLM(eval_score=40, eval_passed=False))

    initial_state: StudyState = {
        "student_id": "test_student_full_replan",
        "learning_goal": "Learn Python in 30 days",
        "target_days": 30,
        "cycle_count": 0,
        "max_cycles": 1,
        "workflow_history": []
    }

    final_state = study_graph.invoke(initial_state)

    assert final_state["routing_decision"] == "FULL_REPLAN"
    assert "PlannerUpdate" in final_state["workflow_history"]
    # Remediation module injected into roadmap
    remedials = [m for m in final_state["roadmap"] if "Foundational Remediation" in m["topic"]]
    assert len(remedials) == 1


def test_requirement_14_real_cyclic_execution():
    """
    Requirement 14: REAL CYCLIC EXECUTION:
    Poor result -> REINFORCE -> teaching/practice -> evaluation -> improved result -> ADVANCE.
    """
    class TwoPassMockLLM(DeterministicMockLLM):
        def __init__(self):
            super().__init__()
            self.eval_invocations = 0

        def invoke(self, messages, **kwargs):
            prompt_text = "\n".join(getattr(m, 'content', '') for m in messages)
            if "Evaluation Agent" in prompt_text:
                self.eval_invocations += 1
                if self.eval_invocations == 1:
                    # Pass 1: Score 60% -> REINFORCE
                    return DeterministicMockLLM(eval_score=60, eval_passed=False).invoke(messages)
                else:
                    # Pass 2: Score 92% -> ADVANCE
                    return DeterministicMockLLM(eval_score=92, eval_passed=True).invoke(messages)
            return super().invoke(messages, **kwargs)

    set_test_llm(TwoPassMockLLM())

    initial_state: StudyState = {
        "student_id": "test_student_cycle_proof",
        "learning_goal": "Learn Python in 30 days",
        "target_days": 30,
        "cycle_count": 0,
        "max_cycles": 2,
        "workflow_history": []
    }

    final_state = study_graph.invoke(initial_state)

    history = final_state["workflow_history"]
    # The LangGraph cycle must visibly show:
    # 1. First Pass: Assessment -> Plan -> Tutor -> Quiz -> Practice -> Evaluation -> Performance -> Reinforce
    # 2. Cyclic Loop: -> Tutor -> Quiz -> Practice -> Evaluation -> Performance -> Advance -> Final
    assert "Reinforce" in history
    assert "Advance" in history

    # Tutor must have been invoked twice (once initially, and once after the cyclic Reinforce edge)
    tutor_count = history.count("Tutor")
    assert tutor_count >= 2

    # Verification of transition from Reinforce to Advance
    assert final_state["routing_decision"] == "ADVANCE"
    assert final_state["current_topic_index"] == 1
