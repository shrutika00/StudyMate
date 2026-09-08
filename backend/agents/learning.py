from typing import Dict, Any, List
from ..state import StudyState
from ..tools.registry import tool_registry


def learning_node(state: StudyState) -> Dict[str, Any]:
    """
    Learning / Research Agent:
    Dynamically discovers and queries registered tools (e.g. learning_tool, web_search_tool)
    to accumulate relevant contextual facts, definitions, pitfalls, and analogies.
    """
    question = state.get("user_question", "")
    history = list(state.get("workflow_history", []))
    history.append("Learn")

    existing_context = list(state.get("context", []))
    new_context: List[str] = []

    available_tools = tool_registry.list_tools()

    if any(t["name"] == "learning_tool" for t in available_tools):
        ref_data = tool_registry.execute("learning_tool", question)
        if ref_data:
            new_context.append(f"[Educational Reference]\n{ref_data}")

    if any(t["name"] == "web_search_tool" for t in available_tools):
        search_data = tool_registry.execute("web_search_tool", question)
        if search_data:
            new_context.append(f"[Web Reference]\n{search_data}")

    combined_context = existing_context + new_context

    return {
        "context": combined_context,
        "status": "learned",
        "workflow_history": history
    }
