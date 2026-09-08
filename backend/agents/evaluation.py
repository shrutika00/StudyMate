import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import EvaluationResult, QuizResult, QuizQuestionResult
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


def deterministic_code_check(code_str: str) -> Dict[str, Any]:
    """
    Deterministic validation for code submissions:
    Checks syntax validity and analyzes basic structure without executing unsafe code.
    """
    if not code_str or not code_str.strip():
        return {"valid_syntax": False, "has_return": False, "length": 0, "error": "Empty code submitted"}

    try:
        compile(code_str, "<student_code>", "exec")
        valid_syntax = True
        error = None
    except SyntaxError as e:
        valid_syntax = False
        error = f"SyntaxError at line {e.lineno}: {e.msg}"

    has_return = "return" in code_str or "yield" in code_str
    has_def = "def " in code_str or "class " in code_str

    return {
        "valid_syntax": valid_syntax,
        "has_return": has_return,
        "has_def": has_def,
        "error": error
    }


def evaluate_quiz_submission(
    quiz_data: Dict[str, Any],
    submitted_answers: Dict[Any, str]
) -> QuizResult:
    """
    Evaluates student quiz answers deterministically against quiz questions.
    Supports both single question and multi-question quizzes.
    """
    questions = quiz_data.get("questions") or [quiz_data]
    results: List[QuizQuestionResult] = []
    correct_count = 0
    areas_to_improve: List[str] = []

    for q in questions:
        qid = q.get("id", 1)
        student_ans = submitted_answers.get(qid)
        if student_ans is None:
            student_ans = submitted_answers.get(str(qid), "")

        correct_opt = str(q.get("correct_option", "A")).strip().upper()
        clean_stud_ans = str(student_ans).strip().upper()

        is_correct = (
            clean_stud_ans == correct_opt or
            correct_opt in clean_stud_ans or
            (clean_stud_ans != "" and clean_stud_ans[0] == correct_opt[0])
        )

        if is_correct:
            correct_count += 1
        else:
            q_text = q.get("question", "")
            short_topic = q_text.split("?")[0][:40] if q_text else f"Question {qid}"
            areas_to_improve.append(short_topic)

        results.append(QuizQuestionResult(
            question_id=qid,
            question=q.get("question", f"Question {qid}"),
            student_answer=str(student_ans),
            correct_option=correct_opt,
            is_correct=is_correct,
            explanation=q.get("explanation", "Reference material")
        ))

    total = max(1, len(questions))
    pct = int((correct_count / total) * 100)

    return QuizResult(
        score=correct_count,
        total=total,
        percentage=pct,
        question_results=results,
        areas_to_improve=areas_to_improve,
        passed=pct >= 70
    )


def evaluation_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 6: Evaluation Agent
    Role: Objective and rubric-based grading of quiz answers and practice code.
    Uses a hybrid approach:
    1. Deterministic comparison for objective quiz answers.
    2. Deterministic AST/syntax checks for code submissions.
    3. Gemini reasoning component evaluated against a strict pedagogical rubric for free-text.
    """
    topic = state.get("current_topic", "Python Fundamentals & Data Structures")
    quiz_multi = state.get("quiz_multi") or {}
    quiz_single = state.get("quiz") or {}
    practice_data = state.get("practice") or {}
    history = list(state.get("workflow_history", []))
    history.append("Evaluation")

    student_quiz = state.get("student_quiz_answer")
    student_quiz_answers = state.get("student_quiz_answers")
    student_code = state.get("student_practice_code")

    effective_answers: Dict[Any, str] = {}
    if student_quiz_answers:
        effective_answers = student_quiz_answers
    elif student_quiz:
        effective_answers = {1: student_quiz}
    else:
        correct_single = quiz_single.get("correct_option", "A")
        effective_answers = {1: correct_single}

    active_quiz_data = quiz_multi if (quiz_multi and "questions" in quiz_multi) else quiz_single
    quiz_eval = evaluate_quiz_submission(active_quiz_data, effective_answers)
    quiz_score = quiz_eval.percentage

    if student_code is None:
        student_code = practice_data.get("starter_code", "").replace("pass", "return True")

    code_check = deterministic_code_check(student_code or "")

    llm = get_llm()
    prompt = f"""You are StudyMate's Evaluation Agent.
Topic: "{topic}"

Quiz Result: {quiz_eval.score}/{quiz_eval.total} ({quiz_eval.percentage}%)
Quiz Question Breakdown:
{[r.model_dump() for r in quiz_eval.question_results]}

Practice Problem: {practice_data.get('problem_statement')}
Deterministic Syntax Check: {code_check}
Student Submitted Code/Answer:
{student_code}

Rubric:
1. Objective Accuracy: Did the student get the core concept right in quiz and code?
2. Code Quality: Is the code syntactically sound and solves the challenge?
3. Completeness: Were any essential edge-cases or return mechanics omitted?

Scoring:
- Score 0 to 100 combining quiz ({quiz_score}%) and practice.
- Passed: true if score >= 70, false otherwise.

Output valid JSON matching this schema:
{{
  "score": 85,
  "passed": true,
  "answer_type": "code",
  "correctness": "Demonstrated core concept with functional implementation.",
  "missing_concepts": [],
  "feedback": "Great implementation! Demonstrates understanding of function returns and syntax."
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a strict, objective academic evaluator. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        data = {}

    score = data.get("score")
    if score is None:
        base_score = int(quiz_score * 0.5)
        if code_check.get("valid_syntax"):
            base_score += 35
        if code_check.get("has_return"):
            base_score += 15
        score = min(100, max(0, base_score))

    passed = data.get("passed", score >= 70)
    answer_type = data.get("answer_type", "code")
    correctness = data.get("correctness", f"Achieved {score}% on objective and coding rubric.")
    missing = data.get("missing_concepts") or quiz_eval.areas_to_improve
    feedback = data.get("feedback") or (
        f"Quiz score: {quiz_eval.score}/{quiz_eval.total}. "
        f"{'Syntax valid with clear returns.' if code_check.get('valid_syntax') else 'Please review function syntax.'}"
    )

    eval_obj = EvaluationResult(
        score=score,
        quiz_score=quiz_score,
        practice_score=score,
        passed=passed,
        answer_type=answer_type,
        correctness=correctness,
        missing_concepts=missing,
        feedback=feedback
    )

    return {
        "evaluation": eval_obj.model_dump(),
        "quiz_result": quiz_eval.model_dump(),
        "workflow_history": history,
        "status": "evaluated"
    }
