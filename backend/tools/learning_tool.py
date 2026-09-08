from typing import Dict, Any
from .registry import BaseTool, tool_registry


EDUCATIONAL_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "recursion": {
        "definition": "A programming technique where a function solves a problem by calling itself with smaller inputs until reaching a base condition.",
        "core_components": [
            "Base Case: The stopping condition preventing infinite self-invocation.",
            "Recursive Case: Dividing the main problem into a smaller sub-instance of the same problem.",
            "Call Stack: The memory stack frames allocated for each nested function invocation."
        ],
        "common_pitfalls": "Missing base case leading to stack overflow, redundant computations without memoization.",
        "real_world_analogy": "Russian nesting dolls (Matryoshka) - opening each doll until reaching the smallest solid doll that cannot be opened.",
        "code_snippet": "def factorial(n):\n    if n <= 1: return 1  # Base Case\n    return n * factorial(n - 1)  # Recursive Case"
    },
    "binary search": {
        "definition": "An efficient O(log n) algorithm for locating an element within a sorted array by repeatedly halving the search interval.",
        "core_components": [
            "Precondition: Data structure must be sorted.",
            "Midpoint calculation: mid = (low + high) // 2.",
            "Interval reduction: Discard left or right half based on target comparison."
        ],
        "common_pitfalls": "Applying on unsorted data, off-by-one errors in boundary adjustments.",
        "real_world_analogy": "Looking up a word in a printed dictionary by opening to the middle page and flipping forward or backward.",
        "code_snippet": "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: low = mid + 1\n        else: high = mid - 1\n    return -1"
    },
    "dynamic programming": {
        "definition": "An optimization technique solving complex problems by breaking them down into overlapping subproblems and storing results.",
        "core_components": [
            "Optimal Substructure: Solution to overall problem is composed of solutions to subproblems.",
            "Overlapping Subproblems: Same subproblems evaluated repeatedly.",
            "Memoization (Top-down) or Tabulation (Bottom-up)."
        ],
        "common_pitfalls": "Confusing divide-and-conquer with DP (DP requires overlapping subproblems).",
        "real_world_analogy": "Writing down '1+1+1+1' on paper = 4. Adding another '+ 1' immediately yields 5 because you remember the previous sum.",
        "code_snippet": "memo = {}\ndef fib(n):\n    if n in memo: return memo[n]\n    if n <= 1: return n\n    memo[n] = fib(n - 1) + fib(n - 2)\n    return memo[n]"
    },
    "api": {
        "definition": "Application Programming Interface: A standardized contract that enables different software systems to communicate.",
        "core_components": [
            "Endpoints: Specific URLs where resources can be accessed.",
            "HTTP Methods: GET (retrieve), POST (create), PUT/PATCH (update), DELETE (remove).",
            "Headers & Payload: Metadata (auth, content-type) and transmitted JSON data."
        ],
        "common_pitfalls": "Not handling network errors, missing rate limiting, failing to validate input.",
        "real_world_analogy": "A restaurant menu and waiter: You (client) pick an item from the menu (endpoint), waiter takes request to kitchen (server) and brings back food (response).",
        "code_snippet": "@app.get('/items/{item_id}')\ndef get_item(item_id: int):\n    return {'item_id': item_id, 'name': 'Sample'}"
    }
}


class LearningTool(BaseTool):
    """
    Curated educational reference tool providing structured conceptual facts,
    definitions, analogies, and code snippets for fundamental topics.
    """
    name = "learning_tool"
    description = "Searches curated curriculum reference for conceptual definitions, principles, pitfalls, and analogies."

    def run(self, query: str, **kwargs) -> str:
        q_clean = query.lower()
        for topic, info in EDUCATIONAL_KNOWLEDGE_BASE.items():
            if topic in q_clean or any(word in q_clean for word in topic.split()):
                components = "\n".join(f"- {c}" for c in info.get("core_components", []))
                return (
                    f"Topic: {topic.title()}\n"
                    f"Definition: {info['definition']}\n"
                    f"Core Components:\n{components}\n"
                    f"Common Pitfalls: {info.get('common_pitfalls', 'None listed')}\n"
                    f"Analogy: {info.get('real_world_analogy', '')}\n"
                    f"Example Snippet:\n{info.get('code_snippet', '')}"
                )
        return (
            f"Concept Reference for '{query}':\n"
            f"- Foundational concept: break the topic into foundational primitives, core mechanisms, and real-world practical use.\n"
            f"- Include clear terminology, edge-cases, and common misconceptions for student clarity."
        )


# Register tool instance in registry
learning_tool = LearningTool()
tool_registry.register(learning_tool)
