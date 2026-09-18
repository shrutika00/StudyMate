import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import PracticeExercise
from ..knowledge.rag import rag_retriever
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


def practice_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 5: Practice Agent
    Role: Generates relevant hands-on exercises and coding challenges,
    grounded in the retrieved RAG knowledge to give the student practical mastery.
    """
    topic = state.get("current_topic", "Python Fundamentals & Data Structures")
    level = state.get("assessed_level", "beginner")
    context_list = state.get("retrieved_context", [])
    if not context_list:
        retrieved_docs = rag_retriever.retrieve(topic, top_k=2)
        context_str = "\n\n".join(
            f"Document: {d['title']}\nContent:\n{d['content']}" for d in retrieved_docs
        )
    else:
        context_str = "\n".join(context_list)
    history = list(state.get("workflow_history", []))
    history.append("Practice")

    llm = get_llm()
    prompt = f"""You are StudyMate's Practice Agent.
Topic: "{topic}"
Level: {level}
Retrieved Technical Reference:
{context_str[:600]}

Design a realistic, hands-on programming exercise or problem-solving challenge directly relevant to "{topic}".
Provide clear instructions, starter code with a callable test/demonstration at the bottom so the student can immediately click "Run Code" and see the output, and specify the expected output.

Output valid JSON matching this schema:
{{
  "title": "Build a Resilient Memory Cache",
  "problem_statement": "Write a Python function 'get_user_cache(user_ids: list)' that deduplicates IDs and stores lookup counts in a dictionary.",
  "starter_code": "def get_user_cache(user_ids: list) -> dict:\\n    # Your implementation here\\n    pass\\n\\n# Test your solution\\nids = ['u1', 'u2', 'u1', 'u3', 'u2', 'u1']\\nprint('Cache result:', get_user_cache(ids))",
  "expected_output": "Cache result: {{'u1': 3, 'u2': 2, 'u3': 1}}",
  "hints": ["Use dict.get(key, 0) + 1 or collections.Counter"]
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You design pragmatic, industry-relevant programming exercises. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        data = {}

    title = data.get("title") or f"Hands-On Lab: {topic}"
    statement = data.get("problem_statement") or f"Implement a clean Python solution demonstrating core {topic} functionality."
    starter = data.get("starter_code") or f"def solve_challenge():\n    # Implement {topic} logic\n    return True"
    expected = data.get("expected_output") or "Returns valid processed result matching required contract."
    hints = data.get("hints") or [f"Review the grounded {topic} reference principles."]

    practice_obj = PracticeExercise(
        title=title,
        problem_statement=statement,
        starter_code=starter,
        expected_output=expected,
        hints=hints
    )

    return {
        "practice": practice_obj.model_dump(),
        "workflow_history": history,
        "status": "practiced"
    }
