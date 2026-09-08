import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import RoadmapItem, RoadmapItemStatus, LearningPlan
from ..database.db import save_roadmap, get_roadmap
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


DEFAULT_ROADMAP: List[Dict[str, Any]] = [
    {
        "id": 1,
        "topic": "Python Fundamentals & Data Structures",
        "description": "Master memory primitives, dynamic arrays, dictionaries, and time complexities.",
        "target_day": 5,
        "status": RoadmapItemStatus.in_progress.value
    },
    {
        "id": 2,
        "topic": "Functions, Scope, and Object-Oriented Programming",
        "description": "Construct clean modular abstractions using closures, decorators, and OOP patterns.",
        "target_day": 12,
        "status": RoadmapItemStatus.pending.value
    },
    {
        "id": 3,
        "topic": "REST APIs, HTTP Protocols, and FastAPI Framework",
        "description": "Build high-performance RESTful web services with declarative schema validation.",
        "target_day": 19,
        "status": RoadmapItemStatus.pending.value
    },
    {
        "id": 4,
        "topic": "Relational Databases, SQL, and SQLite Persistence",
        "description": "Design normalized database schemas, enforce ACID transactions, and index queries.",
        "target_day": 25,
        "status": RoadmapItemStatus.pending.value
    },
    {
        "id": 5,
        "topic": "Asynchronous Programming, Event Loops, and AsyncIO",
        "description": "Implement cooperative multitasking and non-blocking I/O using async/await coroutines.",
        "target_day": 30,
        "status": RoadmapItemStatus.pending.value
    }
]


def learning_planner_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 2: Learning Planner Agent
    Role: Creates the personalized, multi-topic study roadmap from the learning goal
    and assessed level. Saves to Persistent Cross-Session Memory.
    """
    student_id = state.get("student_id", "student_default")
    goal = state.get("learning_goal", "I want to learn Python for backend development in 30 days")
    level = state.get("assessed_level", "beginner")
    target_days = state.get("target_days", 30)
    history = list(state.get("workflow_history", []))
    history.append("Plan")

    # Check Tier 2 Persistent Memory for existing roadmap
    saved_plan = get_roadmap(student_id)
    if saved_plan and saved_plan.get("roadmap"):
        roadmap_data = saved_plan["roadmap"]
        idx = saved_plan.get("current_topic_index", 0)
        curr_topic = roadmap_data[idx]["topic"] if idx < len(roadmap_data) else roadmap_data[-1]["topic"]
        return {
            "roadmap": roadmap_data,
            "current_topic_index": idx,
            "current_topic": curr_topic,
            "workflow_history": history,
            "status": "planned"
        }

    llm = get_llm()
    prompt = f"""You are StudyMate's Learning Planner Agent.
Construct a realistic 30-day curriculum roadmap for:
Goal: "{goal}"
Assessed Level: {level}
Total Timeline: {target_days} days

Create a 5-step sequential roadmap.
Output valid JSON matching this schema exactly:
{{
  "roadmap": [
    {{
      "id": 1,
      "topic": "Python Fundamentals & Data Structures",
      "description": "Core types, list comprehensions, and dictionaries",
      "target_day": 5
    }},
    {{
      "id": 2,
      "topic": "Functions, Scope, and Object-Oriented Programming",
      "description": "Decorators, classes, and inheritance",
      "target_day": 12
    }},
    {{
      "id": 3,
      "topic": "REST APIs, HTTP Protocols, and FastAPI Framework",
      "description": "Routing, Pydantic schemas, and endpoints",
      "target_day": 19
    }},
    {{
      "id": 4,
      "topic": "Relational Databases, SQL, and SQLite Persistence",
      "description": "ACID properties, tables, and CRUD queries",
      "target_day": 25
    }},
    {{
      "id": 5,
      "topic": "Asynchronous Programming, Event Loops, and AsyncIO",
      "description": "Async/await, non-blocking I/O, and concurrency",
      "target_day": 30
    }}
  ]
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a master technical curriculum architect. Always output valid JSON."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
        items = data.get("roadmap")
        if not items or len(items) < 3:
            items = DEFAULT_ROADMAP
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        items = DEFAULT_ROADMAP

    formatted_roadmap: List[Dict[str, Any]] = []
    for i, item in enumerate(items):
        status_val = RoadmapItemStatus.in_progress.value if i == 0 else RoadmapItemStatus.pending.value
        formatted_roadmap.append({
            "id": item.get("id", i + 1),
            "topic": item.get("topic", f"Module {i + 1}"),
            "description": item.get("description", "Core domain concepts"),
            "target_day": item.get("target_day", (i + 1) * 6),
            "status": status_val
        })

    # Save initial roadmap in Persistent Memory Tier
    save_roadmap(student_id, formatted_roadmap, current_topic_index=0)

    current_topic = formatted_roadmap[0]["topic"]
    return {
        "roadmap": formatted_roadmap,
        "current_topic_index": 0,
        "current_topic": current_topic,
        "workflow_history": history,
        "status": "planned"
    }
