import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import Evaluation
from .llm import get_llm, extract_text_content


def extract_json(text: str) -> Dict[str, Any]:
    """Helper to extract JSON object from markdown code blocks or text."""
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


def evaluator_node(state: StudyState) -> Dict[str, Any]:
    """
    Evaluator Agent:
    Rigorously assesses whether the teacher's explanation is sufficient,
    accurate, level-appropriate, and accompanied by practical examples.
    Produces structured Evaluation schema: score, is_sufficient, missing_points, feedback.
    """
    question = state.get("user_question", "")
    level = state.get("level", "beginner")
    explanation = state.get("explanation", "")
    key_points = state.get("key_points", [])
    examples = state.get("examples", [])
    follow_up = state.get("follow_up_question", "")

    history = list(state.get("workflow_history", []))
    history.append("Evaluate")

    llm = get_llm()

    prompt = f"""You are StudyMate's educational evaluator and quality auditor.
Evaluate this teaching response critically.

Question: {question}
Target Level: {level}

Proposed Explanation:
{explanation}

Key Points:
{key_points}

Examples:
{examples}

Follow-up Question:
{follow_up}

Rubric:
1. Did it directly and accurately answer the student's question?
2. Is the tone and complexity calibrated to '{level}' level?
3. Does it offer a clear concrete example?
4. Is the explanation self-contained and clear?

Scoring rules:
- Score 1-10.
- is_sufficient MUST be true ONLY if score >= 7 and no critical concept is omitted.
- If score < 7, list specific missing_points and constructive feedback explaining what to fix.

Output valid JSON matching this schema exactly:
{{
  "score": 8,
  "is_sufficient": true,
  "missing_points": [],
  "feedback": "Clear explanation well suited for beginner level."
}}"""

    response = llm.invoke([
        SystemMessage(content="You are a strict, constructive academic tutor evaluating educational content. Always return valid JSON."),
        HumanMessage(content=prompt)
    ])

    raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
    data = extract_json(raw_text)

    score = data.get("score")
    if score is None:
        score = 8
    score = max(1, min(10, int(score)))

    is_sufficient = data.get("is_sufficient")
    if is_sufficient is None:
        is_sufficient = (score >= 7)
    else:
        is_sufficient = bool(is_sufficient)

    missing_points = data.get("missing_points", [])
    if not isinstance(missing_points, list):
        missing_points = [str(missing_points)] if missing_points else []

    feedback = data.get("feedback") or ("Explanation is satisfactory." if is_sufficient else "Needs more depth and clearer examples.")

    evaluation_obj = Evaluation(
        score=score,
        is_sufficient=is_sufficient,
        missing_points=missing_points,
        feedback=feedback
    )

    return {
        "evaluation": evaluation_obj.model_dump(),
        "status": "evaluated",
        "workflow_history": history
    }
