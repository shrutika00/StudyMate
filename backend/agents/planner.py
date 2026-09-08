from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from .llm import get_llm, extract_text_content


def planner_node(state: StudyState) -> Dict[str, Any]:
    """
    Planner Agent: Analyzes the student's question and difficulty level,
    synthesizes a concrete learning goal and a structured outline/plan.
    """
    question = state.get("user_question", "").strip()
    level = state.get("level", "beginner")
    history = list(state.get("workflow_history", []))
    history.append("Plan")

    llm = get_llm()
    prompt = f"""You are an educational curriculum planner.
Student Question: {question}
Target Level: {level}

Create a clear 3-step learning plan to guide the student toward understanding this topic.
Format your output as 3 distinct numbered bullet points."""

    try:
        response = llm.invoke([
            SystemMessage(content="You create clear, pedagogical learning roadmaps."),
            HumanMessage(content=prompt)
        ])
        content = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        lines = [
            line.strip().lstrip("- 0123456789.)").strip()
            for line in content.split("\n")
            if line.strip() and (line.strip().startswith(("-", "*")) or (line.strip()[0].isdigit() and "." in line[:3]))
        ]
        plan = lines if len(lines) >= 2 else [
            f"Deconstruct core concept and foundational principles of {question}",
            f"Illustrate with {level}-appropriate concrete real-world analogy and code example",
            "Consolidate knowledge and verify understanding with interactive questions"
        ]
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        plan = [
            f"Deconstruct core concept and foundational principles of {question}",
            f"Illustrate with {level}-appropriate concrete real-world analogy and code example",
            "Consolidate knowledge and verify understanding with interactive questions"
        ]

    learning_goal = f"Achieve {level}-level clarity and mastery of: {question}"
    return {
        "learning_goal": learning_goal,
        "plan": plan,
        "status": "planned",
        "workflow_history": history
    }
