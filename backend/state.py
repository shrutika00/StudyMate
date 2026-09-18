from typing import TypedDict, List, Optional, Dict, Any


class StudyState(TypedDict, total=False):
    """
    Tier 1 Session-Scoped Memory:
    Ephemeral state passed between LangGraph agent nodes during an active learning cycle.
    Contains the current goal, active assessment, diagnostic questions, current roadmap,
    RAG context, active topic teaching, interactive quiz (3-5 questions), quiz submission/results,
    practice exercise, practice attempt, evaluation, and performance analysis.
    """
    # Student & Goal Metadata
    student_id: str
    learning_goal: str
    goal: Optional[str]
    target_days: int
    current_day: int
    assessed_level: str

    # Agent 1: Assessment Agent Output
    assessment: Optional[Dict[str, Any]]
    diagnostic_questions: Optional[List[Dict[str, Any]]]
    diagnostic_answers: Optional[Dict[str, str]]

    # Agent 2: Learning Planner Agent Output
    roadmap: List[Dict[str, Any]]
    current_topic_index: int
    current_topic: str

    # RAG Knowledge Context
    retrieved_context: List[str]

    # Agent 3: Concept / Tutor Agent Output
    teaching: Optional[Dict[str, Any]]

    # Agent 4: Quiz Agent Output (Supports both single question and 3-5 questions)
    quiz: Optional[Dict[str, Any]]
    quiz_multi: Optional[Dict[str, Any]]

    # Student Inputs for Evaluation
    student_quiz_answer: Optional[str]
    student_quiz_answers: Optional[Dict[int, str]]
    quiz_result: Optional[Dict[str, Any]]

    # Agent 5: Practice Agent Output & Student Practice Attempt
    practice: Optional[Dict[str, Any]]
    student_practice_code: Optional[str]

    # Agent 6: Evaluation Agent Output
    evaluation: Optional[Dict[str, Any]]

    # Agent 7: Performance Agent Output
    performance: Optional[Dict[str, Any]]

    # Agent 8: Planner Update Agent Output
    planner_update: Optional[Dict[str, Any]]

    # Graph Control & Cyclic State
    routing_decision: str  # ADVANCE, REINFORCE, FULL_REPLAN, COMPLETE
    cycle_count: int
    max_cycles: int
    workflow_history: List[str]
    status: str
    errors: List[str]
    final_answer: Optional[Dict[str, Any]]
