import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
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


def teacher_node(state: StudyState) -> Dict[str, Any]:
    """
    Teaching Agent:
    Uses Gemini to compose an intuitive, pedagogical explanation tailored to the
    requested difficulty level (Beginner / Intermediate / Advanced).
    If entering from a revision cycle, incorporates evaluator feedback to fix deficiencies.
    """
    question = state.get("user_question", "")
    level = state.get("level", "beginner")
    context_list = state.get("context", [])
    context_text = "\n\n".join(context_list)
    feedback_history = state.get("feedback_history", [])
    latest_feedback = feedback_history[-1] if feedback_history else ""
    evaluation = state.get("evaluation") or {}
    missing_points = evaluation.get("missing_points", [])

    history = list(state.get("workflow_history", []))
    history.append("Teach")

    llm = get_llm()

    revision_instruction = ""
    if latest_feedback:
        missing_str = "\n".join(f"- {p}" for p in missing_points) if missing_points else "None specific"
        revision_instruction = f"""
IMPORTANT - THIS IS A REVISION (Cycle {state.get('revision_count', 1)}):
The previous explanation was evaluated and deemed INSUFFICIENT.
Evaluator Feedback:
{latest_feedback}

Specific Missing Points to Address:
{missing_str}

Ensure your new explanation thoroughly resolves these points!
"""

    prompt = f"""You are StudyMate's master teacher agent.
Topic/Question: {question}
Target Level: {level}

Reference Context:
{context_text}
{revision_instruction}

Instructions:
1. Provide an engaging, level-appropriate explanation ({level}):
   - Beginner: use intuitive analogies, everyday language, and zero intimidating jargon.
   - Intermediate: explain mechanics, control flow, and practical patterns.
   - Advanced: delve into performance characteristics, edge cases, and architectural design.
2. Provide 3-4 bullet Key Points.
3. Provide 1-2 concrete code or real-world practical examples.
4. Provide 1 follow-up comprehension question for the student to test their learning.

Output MUST be a valid JSON object matching this exact structure:
{{
  "explanation": "Thorough, clear explanation here...",
  "key_points": ["First key takeaway", "Second key takeaway", "Third key takeaway"],
  "examples": ["Concrete example or code demonstration here"],
  "follow_up_question": "A stimulating question to verify the student understood"
}}"""

    response = llm.invoke([
        SystemMessage(content="You are an empathetic, world-class computer science and STEM educator. Always output valid JSON."),
        HumanMessage(content=prompt)
    ])

    raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
    data = extract_json(raw_text)

    explanation = data.get("explanation")
    key_points = data.get("key_points") or []
    examples = data.get("examples") or []
    follow_up_question = data.get("follow_up_question")

    if not explanation:
        explanation = raw_text.strip()
    if not key_points:
        key_points = [
            f"Core principle of {question}",
            f"Key application suited for {level} level",
            "Fundamental design best practice"
        ]
    if not examples:
        examples = [f"Standard implementation example for {question}"]
    if not follow_up_question:
        follow_up_question = f"How would you explain the fundamental mechanism of {question} in your own words?"

    return {
        "explanation": explanation,
        "key_points": key_points,
        "examples": examples,
        "follow_up_question": follow_up_question,
        "status": "taught",
        "workflow_history": history
    }
