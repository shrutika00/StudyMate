import os
import json
import pytest
from langchain_core.messages import AIMessage
from backend.agents.llm import set_test_llm, reset_test_llm


class DeterministicMockLLM:
    """
    Configurable deterministic mock LLM for testing the 8-agent LangGraph workflow.
    """
    def __init__(self, eval_score=85, eval_passed=True):
        self.call_count = 0
        self.eval_score = eval_score
        self.eval_passed = eval_passed

    def invoke(self, messages, **kwargs):
        self.call_count += 1
        prompt_text = ""
        for m in messages:
            prompt_text += f"\n{getattr(m, 'content', '')}"

        # 1. Assessment Agent
        if "Assessment Agent" in prompt_text:
            import re
            from backend.agents.assessment import generate_topic_diagnostic_questions
            goal_match = re.search(r'Goal:\s*"([^"]+)"', prompt_text)
            current_goal = goal_match.group(1) if goal_match else "Python"
            questions = generate_topic_diagnostic_questions(current_goal)
            return AIMessage(content=json.dumps({
                "diagnostic_questions": questions,
                "assessed_level": "beginner",
                "strengths": [f"Clear technical ambition in {current_goal}", "Direct practical orientation"],
                "knowledge_gaps": [f"Core mechanics of {current_goal}", f"Applied paradigms in {current_goal}"],
                "diagnostic_summary": f"Assessed at beginner level for {current_goal}."
            }))

        # 2. Learning Planner Agent
        if "Learning Planner Agent" in prompt_text:
            import re
            goal_match = re.search(r'Goal:\s*"([^"]+)"', prompt_text)
            current_goal = goal_match.group(1) if goal_match else "Python"
            if "sql" in current_goal.lower():
                from backend.agents.learning_planner import DEFAULT_SQL_ROADMAP
                roadmap_items = DEFAULT_SQL_ROADMAP
            else:
                from backend.agents.learning_planner import DEFAULT_ROADMAP
                roadmap_items = DEFAULT_ROADMAP
            return AIMessage(content=json.dumps({
                "roadmap": roadmap_items
            }))

        # 3. Tutor Agent
        if "Concept / Tutor Agent" in prompt_text:
            return AIMessage(content=json.dumps({
                "explanation": "Authoritative explanation grounded in retrieved documentation. Python lists are dynamic arrays with O(1) append.",
                "key_points": [
                    "Dynamic typing with reference semantics",
                    "Contiguous memory array allocation",
                    "Deterministic garbage collection via reference counting"
                ]
            }))

        # 4. Quiz Agent
        if "Quiz Agent" in prompt_text:
            return AIMessage(content=json.dumps({
                "questions": [
                    {
                        "id": 1,
                        "question": "What does a Python function allow you to do?",
                        "options": ["A) Store data permanently", "B) Reuse a block of code", "C) Create a database", "D) Install Python"],
                        "correct_option": "B",
                        "explanation": "Functions encapsulate reusable logic.",
                        "question_type": "multiple_choice"
                    },
                    {
                        "id": 2,
                        "question": "Which keyword defines a function in Python?",
                        "options": ["A) func", "B) def", "C) function", "D) define"],
                        "correct_option": "B",
                        "explanation": "The 'def' keyword defines functions.",
                        "question_type": "multiple_choice"
                    },
                    {
                        "id": 3,
                        "question": "What is the average time complexity of a dictionary key lookup in Python?",
                        "options": ["A) O(1)", "B) O(n)", "C) O(log n)", "D) O(n^2)"],
                        "correct_option": "A",
                        "explanation": "Dictionaries use hash tables with open addressing.",
                        "question_type": "multiple_choice"
                    },
                    {
                        "id": 4,
                        "question": "Python passes arguments by object reference.",
                        "options": ["A) True", "B) False"],
                        "correct_option": "A",
                        "explanation": "Object reference semantics.",
                        "question_type": "true_false"
                    },
                    {
                        "id": 5,
                        "question": "What is returned if no explicit return is provided in Python?",
                        "options": ["A) None", "B) 0", "C) False", "D) Error"],
                        "correct_option": "A",
                        "explanation": "Python implicitly returns None.",
                        "question_type": "multiple_choice"
                    }
                ]
            }))

        # 5. Practice Agent
        if "Practice Agent" in prompt_text:
            return AIMessage(content=json.dumps({
                "title": "Build a Resilient Memory Cache",
                "problem_statement": "Write a Python function 'get_user_cache(user_ids)' that stores counts in a dictionary.",
                "starter_code": "def get_user_cache(user_ids):\n    return {uid: user_ids.count(uid) for uid in set(user_ids)}",
                "expected_output": "Dictionary mapping user_ids to count",
                "hints": ["Use dictionary comprehension"]
            }))

        # 6. Evaluation Agent
        if "Evaluation Agent" in prompt_text:
            return AIMessage(content=json.dumps({
                "score": self.eval_score,
                "passed": self.eval_passed,
                "answer_type": "code",
                "correctness": "High correctness" if self.eval_passed else "Needs improvement",
                "missing_concepts": [] if self.eval_passed else ["Edge case handling"],
                "feedback": "Strong performance." if self.eval_passed else "Need to practice edge cases."
            }))

        # General Fallback
        return AIMessage(content="{\"status\": \"ok\"}")


@pytest.fixture(autouse=True)
def clean_state():
    from backend.database.db import get_connection
    with get_connection() as conn:
        conn.execute("DELETE FROM student_roadmaps")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM topic_mastery")
        conn.execute("DELETE FROM learning_sessions")
        conn.execute("DELETE FROM student_active_quizzes")
        conn.commit()
    yield
    reset_test_llm()
