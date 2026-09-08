import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import TeachingContent
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


def tutor_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 3: Concept / Tutor Agent
    Role: Explains the current learning topic, strictly grounded in material
    retrieved from the local Retrieval-Augmented Knowledge (RAG) layer.
    """
    topic = state.get("current_topic", "Python Fundamentals & Data Structures")
    level = state.get("assessed_level", "beginner")
    history = list(state.get("workflow_history", []))
    history.append("Tutor")

    # Step 1: Retrieve grounded knowledge chunks via RAG Layer
    retrieved_docs = rag_retriever.retrieve(topic, top_k=2)
    grounded_context_str = "\n\n".join(
        f"Document: {d['title']}\nContent:\n{d['content']}" for d in retrieved_docs
    )
    sources = [d["title"] for d in retrieved_docs]

    llm = get_llm()
    prompt = f"""You are StudyMate's Concept / Tutor Agent.
Current Topic: "{topic}"
Student Level: {level}

AUTHORITATIVE RETRIEVED KNOWLEDGE (You MUST ground your teaching in this material):
{grounded_context_str}

Instructions:
1. Explain this topic clearly for a {level} learner.
2. Ground your definitions, mechanisms, and rules directly in the retrieved text.
3. Highlight 3-4 concise Key Points.

Output valid JSON matching this schema:
{{
  "explanation": "Clear, grounded educational explanation...",
  "key_points": [
    "Core takeaway 1",
    "Core takeaway 2",
    "Core takeaway 3"
  ]
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a clear, patient technical educator. Ground all statements in provided context. Output valid JSON."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        data = {}

    explanation = data.get("explanation")
    if not explanation:
        explanation = f"In {topic}, understanding underlying memory patterns, data flow, and runtime guarantees is essential. {grounded_context_str[:250]}..."

    key_points = data.get("key_points") or [
        f"Master foundational mechanisms of {topic}",
        "Understand time and space complexity characteristics",
        "Apply best practices to maintain robust backend systems"
    ]

    teaching_obj = TeachingContent(
        topic=topic,
        explanation=explanation,
        key_points=key_points,
        grounded_sources=sources
    )

    return {
        "teaching": teaching_obj.model_dump(),
        "retrieved_context": [grounded_context_str],
        "workflow_history": history,
        "status": "taught"
    }
