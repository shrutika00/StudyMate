import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import AssessmentResult, DifficultyLevel, AssessmentQuestion
from ..database.db import save_or_update_student, get_student
from .llm import get_llm, extract_text_content


def extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass
    return {}


DIAGNOSTIC_QUESTIONS_BANK = [
    {
        "id": 1,
        "question": "What is a Python function?",
        "options": [
            "A) A reusable block of code designed to perform a specific task",
            "B) A database management system",
            "C) A variable that stores numbers only",
            "D) An operating system program"
        ],
        "correct_option": "A",
        "explanation": "Functions are reusable blocks of code executed when called."
    },
    {
        "id": 2,
        "question": "Which keyword is used in Python to define a function?",
        "options": [
            "A) func",
            "B) def",
            "C) function",
            "D) lambda_func"
        ],
        "correct_option": "B",
        "explanation": "The 'def' keyword is standard in Python for defining named functions."
    },
    {
        "id": 3,
        "question": "What is the average time complexity of looking up a key in a Python dictionary?",
        "options": [
            "A) O(n)",
            "B) O(log n)",
            "C) O(1)",
            "D) O(n^2)"
        ],
        "correct_option": "C",
        "explanation": "Python dictionaries use hash tables, giving O(1) average lookup time."
    }
]

SQL_DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "question": "Which SQL statement is used to retrieve data from a database table?",
        "options": [
            "A) SELECT",
            "B) EXTRACT",
            "C) GET",
            "D) OPEN"
        ],
        "correct_option": "A",
        "explanation": "The SELECT statement is the standard command used to query and fetch records from database tables."
    },
    {
        "id": 2,
        "question": "Which SQL clause is used to filter records based on specified conditions?",
        "options": [
            "A) ORDER BY",
            "B) WHERE",
            "C) GROUP BY",
            "D) LIMIT"
        ],
        "correct_option": "B",
        "explanation": "The WHERE clause filters rows satisfying a boolean condition before grouping or sorting."
    },
    {
        "id": 3,
        "question": "What is the primary difference between INNER JOIN and LEFT JOIN in SQL?",
        "options": [
            "A) INNER JOIN returns only matching rows; LEFT JOIN returns all rows from the left table plus matches",
            "B) INNER JOIN sorts data in ascending order; LEFT JOIN sorts in descending order",
            "C) LEFT JOIN can only be used on primary keys; INNER JOIN works on any column",
            "D) There is no difference between INNER JOIN and LEFT JOIN"
        ],
        "correct_option": "A",
        "explanation": "INNER JOIN requires matches in both tables; LEFT JOIN preserves all left-table rows regardless of matches in the right table."
    }
]

JS_DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "question": "Which keyword declares a block-scoped constant in modern JavaScript?",
        "options": [
            "A) const",
            "B) var",
            "C) let",
            "D) static"
        ],
        "correct_option": "A",
        "explanation": "'const' declares block-scoped constants that cannot be reassigned."
    },
    {
        "id": 2,
        "question": "What does 'typeof null' evaluate to in JavaScript?",
        "options": [
            "A) 'undefined'",
            "B) 'object'",
            "C) 'null'",
            "D) 'boolean'"
        ],
        "correct_option": "B",
        "explanation": "typeof null returns 'object' due to legacy design in JavaScript's type tagging."
    },
    {
        "id": 3,
        "question": "Which array method executes a callback for each element without returning a new array?",
        "options": [
            "A) map()",
            "B) filter()",
            "C) forEach()",
            "D) reduce()"
        ],
        "correct_option": "C",
        "explanation": "forEach() runs a function on each element and always returns undefined."
    }
]


def get_diagnostic_questions_for_goal(goal: str) -> List[Dict[str, Any]]:
    """Return diagnostic assessment questions tailored to the student's learning goal."""
    if not goal:
        return DIAGNOSTIC_QUESTIONS_BANK

    goal_lower = goal.lower()
    if any(k in goal_lower for k in ["sql", "database", "postgres", "mysql", "sqlite", "query", "queries"]):
        return SQL_DIAGNOSTIC_QUESTIONS
    elif any(k in goal_lower for k in ["javascript", "js", "react", "node", "frontend", "typescript"]):
        return JS_DIAGNOSTIC_QUESTIONS
    return DIAGNOSTIC_QUESTIONS_BANK


def assessment_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 1: Assessment Agent
    Role: Analyzes the student's learning goal, diagnostic answers, and background to determine
    the student's current proficiency level and initial knowledge gaps.
    Saves profile to Persistent Cross-Session Memory.
    """
    student_id = state.get("student_id", "student_default")
    goal = state.get("learning_goal", "I want to learn Python for backend development in 30 days")
    target_days = state.get("target_days", 30)
    history = list(state.get("workflow_history", []))
    history.append("Assessment")

    active_questions = get_diagnostic_questions_for_goal(goal)

    diag_answers = state.get("diagnostic_answers") or {}
    score = None
    if diag_answers:
        correct_count = 0
        for q in active_questions:
            qid = str(q["id"])
            user_ans = str(diag_answers.get(qid, "")).strip().upper()
            corr = q["correct_option"].strip().upper()
            if user_ans and (user_ans == corr or corr in user_ans):
                correct_count += 1
        score = int((correct_count / len(active_questions)) * 100)

    existing_profile = get_student(student_id)
    same_goal = bool(
        existing_profile and
        existing_profile.get("learning_goal") and
        existing_profile.get("learning_goal", "").strip().lower() == goal.strip().lower()
    )
    if existing_profile and existing_profile.get("assessed_level") and not diag_answers and same_goal:
        assessed_level_str = existing_profile["assessed_level"]
        assessment_obj = AssessmentResult(
            assessed_level=DifficultyLevel(assessed_level_str),
            strengths=["Returning student with established profile"],
            knowledge_gaps=["Continuing customized roadmap"],
            diagnostic_summary=f"Welcome back! Resuming plan at {assessed_level_str} level.",
            questions=[AssessmentQuestion(**q) for q in active_questions]
        )
        return {
            "assessed_level": assessed_level_str,
            "assessment": assessment_obj.model_dump(),
            "diagnostic_questions": active_questions,
            "workflow_history": history,
            "status": "assessed"
        }

    inferred_level = "beginner"
    if score is not None:
        if score >= 80:
            inferred_level = "advanced"
        elif score >= 50:
            inferred_level = "intermediate"
        else:
            inferred_level = "beginner"

    llm = get_llm()
    prompt = f"""You are the Assessment Agent for StudyMate.
Analyze this student's learning goal:
Goal: "{goal}"
Target Timeline: {target_days} days
Diagnostic Score: {score if score is not None else 'Initial diagnostic pending'}

Evaluate:
1. Assessed Level (must be 'beginner', 'intermediate', or 'advanced').
2. Key strengths implied by goal.
3. Essential knowledge gaps to bridge.
4. Concise diagnostic summary.

Output valid JSON matching this schema exactly:
{{
  "assessed_level": "{inferred_level}",
  "strengths": ["Clear focus on practical backend engineering", "Targeted timeline"],
  "knowledge_gaps": ["Core HTTP/REST mechanics", "Relational persistence", "Asynchronous I/O"],
  "diagnostic_summary": "Student is assessed at {inferred_level} level for 30-day backend target."
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are an expert technical curriculum diagnostician. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        data = {}

    level_val = data.get("assessed_level", inferred_level).lower()
    if level_val not in ["beginner", "intermediate", "advanced"]:
        level_val = inferred_level

    strengths = data.get("strengths") or [
        "Clear technical ambition",
        "Direct backend engineering orientation"
    ]
    gaps = data.get("knowledge_gaps") or [
        "FastAPI routing and Pydantic schemas",
        "SQL relational queries and SQLite",
        "Async event loops and non-blocking I/O"
    ]
    summary = data.get("diagnostic_summary") or f"Assessed at {level_val} level with {target_days}-day timeline."

    assessment_obj = AssessmentResult(
        assessed_level=DifficultyLevel(level_val),
        strengths=strengths,
        knowledge_gaps=gaps,
        diagnostic_summary=summary,
        diagnostic_score=score,
        questions=[AssessmentQuestion(**q) for q in active_questions]
    )

    save_or_update_student(
        student_id=student_id,
        learning_goal=goal,
        assessed_level=level_val,
        target_days=target_days,
        current_day=1
    )

    return {
        "assessed_level": level_val,
        "assessment": assessment_obj.model_dump(),
        "diagnostic_questions": active_questions,
        "workflow_history": history,
        "status": "assessed"
    }
