import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import QuizQuestion, Quiz
from ..database.db import save_active_quiz, get_active_quiz
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


FALLBACK_QUIZZES: Dict[str, List[Dict[str, Any]]] = {
    "default": [
        {
            "id": 1,
            "question": "What does a Python function allow you to do?",
            "options": [
                "A) Store data permanently on disk",
                "B) Reuse a block of code and encapsulate logic",
                "C) Compile Python code to assembly",
                "D) Install third-party packages"
            ],
            "correct_option": "B",
            "explanation": "Functions encapsulate reusable logic that can be executed repeatedly.",
            "question_type": "multiple_choice"
        },
        {
            "id": 2,
            "question": "Which keyword defines a named function in Python?",
            "options": [
                "A) function",
                "B) func",
                "C) def",
                "D) define"
            ],
            "correct_option": "C",
            "explanation": "'def' is the Python keyword for function definitions.",
            "question_type": "multiple_choice"
        },
        {
            "id": 3,
            "question": "What value is returned by a Python function that does not have an explicit return statement?",
            "options": [
                "A) 0",
                "B) None",
                "C) False",
                "D) An empty string"
            ],
            "correct_option": "B",
            "explanation": "Python functions implicitly return None if no return statement executes.",
            "question_type": "multiple_choice"
        },
        {
            "id": 4,
            "question": "In Python, arguments passed to functions are passed by object reference (assignment).",
            "options": [
                "A) True",
                "B) False"
            ],
            "correct_option": "A",
            "explanation": "Python evaluates arguments using pass-by-object-reference semantics.",
            "question_type": "true_false"
        },
        {
            "id": 5,
            "question": "What is the average time complexity of looking up a key in a Python dictionary?",
            "options": [
                "A) O(1)",
                "B) O(n)",
                "C) O(log n)",
                "D) O(n^2)"
            ],
            "correct_option": "A",
            "explanation": "Dictionaries use hash tables yielding O(1) average lookup time.",
            "question_type": "multiple_choice"
        }
    ]
}


def quiz_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 4: Quiz Agent
    Role: Generates calibrated diagnostic multi-questions (3-5 questions) targeting the current topic and level
    to test the student's active conceptual comprehension.
    """
    student_id = state.get("student_id", "student_default")
    topic = state.get("current_topic", "Python Fundamentals & Data Structures")
    level = state.get("assessed_level", "beginner")
    context_list = state.get("retrieved_context", [])
    context_str = "\n".join(context_list)
    history = list(state.get("workflow_history", []))
    history.append("Quiz")

    # If student is submitting answers, grade against the active quiz they were answering
    if state.get("student_quiz_answers") or state.get("student_quiz_answer"):
        active_q = get_active_quiz(student_id)
        if active_q and active_q.get("questions"):
            first_q = active_q["questions"][0] if active_q["questions"] else None
            return {
                "quiz": first_q,
                "quiz_multi": active_q,
                "workflow_history": history,
                "status": "quizzed"
            }

    llm = get_llm()
    prompt = f"""You are StudyMate's Quiz Agent.
Topic: "{topic}"
Level: {level}
Context: {context_str[:600]}

Generate 5 high-quality questions (4 multiple-choice with A/B/C/D, 1 true/false) testing:
1. Syntax and basic concepts
2. Parameters and return values
3. Common pitfalls or edge-cases
4. Time complexity or memory behavior
5. Practical scenario usage

Output valid JSON matching this schema:
{{
  "questions": [
    {{
      "id": 1,
      "question": "What does a Python function allow you to do?",
      "options": ["A) Store data permanently", "B) Reuse a block of code", "C) Create a database", "D) Install Python"],
      "correct_option": "B",
      "explanation": "Functions encapsulate reusable logic.",
      "question_type": "multiple_choice"
    }},
    {{
      "id": 2,
      "question": "Which keyword defines a function?",
      "options": ["A) class", "B) def", "C) function", "D) func"],
      "correct_option": "B",
      "explanation": "The 'def' keyword is standard.",
      "question_type": "multiple_choice"
    }},
    {{
      "id": 3,
      "question": "What is returned if no return statement is specified?",
      "options": ["A) None", "B) 0", "C) False", "D) Error"],
      "correct_option": "A",
      "explanation": "Functions implicitly return None.",
      "question_type": "multiple_choice"
    }},
    {{
      "id": 4,
      "question": "Arguments are passed by object reference in Python.",
      "options": ["A) True", "B) False"],
      "correct_option": "A",
      "explanation": "Python passes object references.",
      "question_type": "true_false"
    }},
    {{
      "id": 5,
      "question": "Average dictionary key lookup time complexity?",
      "options": ["A) O(1)", "B) O(n)", "C) O(log n)", "D) O(n^2)"],
      "correct_option": "A",
      "explanation": "Hash tables provide O(1) lookups.",
      "question_type": "multiple_choice"
    }}
  ]
}}"""

    questions_list = []
    try:
        response = llm.invoke([
            SystemMessage(content="You are a strict, precise examiner. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
        if data and "questions" in data and isinstance(data["questions"], list) and len(data["questions"]) >= 3:
            questions_list = data["questions"]
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        questions_list = []

    if not questions_list:
        questions_list = FALLBACK_QUIZZES["default"]

    quiz_questions = []
    for idx, q in enumerate(questions_list, start=1):
        quiz_questions.append(QuizQuestion(
            id=q.get("id", idx),
            question=q.get("question", f"Question {idx} on {topic}"),
            options=q.get("options", ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"]),
            correct_option=q.get("correct_option", "A"),
            explanation=q.get("explanation", "Correct mechanism."),
            question_type=q.get("question_type", "multiple_choice")
        ))

    quiz_obj = Quiz(topic=topic, questions=quiz_questions)
    first_q = quiz_questions[0]
    save_active_quiz(student_id, quiz_obj.model_dump())

    return {
        "quiz": first_q.model_dump(),
        "quiz_multi": quiz_obj.model_dump(),
        "workflow_history": history,
        "status": "quizzed"
    }
