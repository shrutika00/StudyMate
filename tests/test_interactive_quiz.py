import pytest
from backend.models.schemas import QuizQuestion, Quiz, QuizResult, AssessmentQuestion
from backend.agents.assessment import assessment_agent_node, DIAGNOSTIC_QUESTIONS_BANK
from backend.agents.quiz import quiz_agent_node
from backend.agents.evaluation import evaluate_quiz_submission, evaluation_agent_node
from backend.state import StudyState
from backend.agents.llm import set_test_llm
from .conftest import DeterministicMockLLM


def test_assessment_diagnostic_questions_and_scoring():
    """Verify Assessment Agent produces structured diagnostic questions and scores submissions."""
    set_test_llm(DeterministicMockLLM())
    state_start: StudyState = {
        "student_id": "test_diag_student",
        "learning_goal": "I want to learn Python for backend development in 30 days",
        "target_days": 30,
        "workflow_history": []
    }
    res_start = assessment_agent_node(state_start)
    assert "assessment" in res_start
    assert "diagnostic_questions" in res_start
    assert len(res_start["diagnostic_questions"]) == 3
    assert res_start["diagnostic_questions"][0]["question"] == "What is a Python function?"

    state_submit: StudyState = {
        "student_id": "test_diag_student_2",
        "learning_goal": "I want to learn Python for backend development in 30 days",
        "target_days": 30,
        "diagnostic_answers": {"1": "A", "2": "B", "3": "C"},
        "workflow_history": []
    }
    res_submit = assessment_agent_node(state_submit)
    assert res_submit["assessment"]["diagnostic_score"] == 100
    assert res_submit["assessed_level"] in ["beginner", "intermediate", "advanced"]


def test_quiz_agent_generates_multi_questions():
    """Verify Quiz Agent generates 3-5 structured questions with options, correct answers, and types."""
    set_test_llm(DeterministicMockLLM())
    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "assessed_level": "beginner",
        "retrieved_context": ["Dictionaries are O(1) hash maps", "Lists are dynamic contiguous arrays"],
        "workflow_history": []
    }
    res = quiz_agent_node(state)
    assert "quiz_multi" in res
    quiz_multi = res["quiz_multi"]
    assert len(quiz_multi["questions"]) >= 3
    for q in quiz_multi["questions"]:
        assert q["id"] >= 1
        assert len(q["question"]) > 5
        assert len(q["options"]) >= 2
        assert q["correct_option"] in ["A", "B", "C", "D"]
        assert q["question_type"] in ["multiple_choice", "true_false", "short_answer"]


def test_quiz_evaluation_calculates_real_score():
    """Verify objective evaluation evaluates answers, calculates percentage, and flags weak areas."""
    quiz_data = {
        "questions": [
            {
                "id": 1,
                "question": "What does a Python function allow you to do?",
                "correct_option": "B",
                "explanation": "Functions encapsulate reusable logic."
            },
            {
                "id": 2,
                "question": "Which keyword defines a function?",
                "correct_option": "C",
                "explanation": "def keyword."
            },
            {
                "id": 3,
                "question": "What is returned if no return statement is specified?",
                "correct_option": "A",
                "explanation": "None is returned."
            },
            {
                "id": 4,
                "question": "Arguments are passed by reference.",
                "correct_option": "A",
                "explanation": "Object reference."
            },
            {
                "id": 5,
                "question": "Dictionary key lookup time complexity?",
                "correct_option": "A",
                "explanation": "O(1) average lookup."
            }
        ]
    }

    # Student answers 4 out of 5 correctly (misses Q3)
    student_answers = {
        1: "B",
        2: "C",
        3: "B",
        4: "A",
        5: "A"
    }

    eval_res = evaluate_quiz_submission(quiz_data, student_answers)
    assert eval_res.score == 4
    assert eval_res.total == 5
    assert eval_res.percentage == 80
    assert eval_res.passed is True
    assert len(eval_res.areas_to_improve) == 1
    assert "What is returned" in eval_res.areas_to_improve[0]


def test_evaluation_agent_receives_student_quiz_and_practice():
    """Verify Evaluation Agent integrates actual student quiz answers and practice code into EvaluationResult."""
    set_test_llm(DeterministicMockLLM(eval_score=85, eval_passed=True))

    state: StudyState = {
        "current_topic": "Python Fundamentals & Data Structures",
        "quiz_multi": {
            "questions": [
                {"id": 1, "question": "Function keyword?", "correct_option": "B", "explanation": "def keyword"}
            ]
        },
        "practice": {
            "title": "Calculate Sum",
            "problem_statement": "Write calculate_total(a, b) returning sum",
            "starter_code": "def calculate_total(a, b):\n    pass"
        },
        "student_quiz_answers": {1: "B"},
        "student_practice_code": "def calculate_total(a, b):\n    return a + b",
        "workflow_history": []
    }

    res = evaluation_agent_node(state)
    assert "evaluation" in res
    assert "quiz_result" in res
    assert res["quiz_result"]["score"] == 1
    assert res["quiz_result"]["percentage"] == 100
    assert res["evaluation"]["score"] >= 80
    assert res["evaluation"]["passed"] is True


def test_sql_goal_generates_sql_diagnostic_questions():
    """Verify that learning goal containing SQL returns SQL diagnostic questions instead of Python."""
    set_test_llm(DeterministicMockLLM())
    state_sql: StudyState = {
        "student_id": "test_sql_student",
        "learning_goal": "i want to learn sql",
        "target_days": 30,
        "workflow_history": []
    }
    res_sql = assessment_agent_node(state_sql)
    assert "assessment" in res_sql
    assert "diagnostic_questions" in res_sql
    questions = res_sql["diagnostic_questions"]
    assert len(questions) == 3
    # Verify questions are SQL-specific, not Python
    assert "SQL" in questions[0]["question"] or "database" in questions[0]["question"]
    assert any("SELECT" in opt for opt in questions[0]["options"])
    assert any("WHERE" in opt for opt in questions[1]["options"])
    assert any("JOIN" in opt for opt in questions[2]["options"])

    # Verify scoring for SQL diagnostic submission
    state_sql_submit: StudyState = {
        "student_id": "test_sql_student_2",
        "learning_goal": "i want to learn sql",
        "target_days": 30,
        "diagnostic_answers": {"1": "A", "2": "B", "3": "A"},
        "workflow_history": []
    }
    res_submit = assessment_agent_node(state_sql_submit)
    assert res_submit["assessment"]["diagnostic_score"] == 100


def test_diagnostic_questions_api_endpoint():
    """Verify GET /diagnostic-questions returns goal-tailored questions for both SQL and Python."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 1. SQL Goal
    resp_sql = client.get("/diagnostic-questions?goal=i%20want%20to%20learn%20sql")
    assert resp_sql.status_code == 200
    data_sql = resp_sql.json()
    assert len(data_sql["questions"]) == 3
    assert "SQL" in data_sql["questions"][0]["question"] or "database" in data_sql["questions"][0]["question"]

    # 2. Python Goal
    resp_py = client.get("/diagnostic-questions?goal=Learn%20Python%20for%20backend")
    assert resp_py.status_code == 200
    data_py = resp_py.json()
    assert len(data_py["questions"]) == 3
    assert "Python" in data_py["questions"][0]["question"]


def test_requirement_1_goal_sql_diagnostic_questions():
    """Test 1: Goal = 'I want to learn SQL' -> diagnostic questions are SQL-related."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/diagnostic-questions?goal=I%20want%20to%20learn%20SQL")
    assert resp.status_code == 200
    data = resp.json()
    questions = data["questions"]
    assert len(questions) == 3
    q_texts = " ".join([q["question"] + " " + " ".join(q["options"]) for q in questions]).lower()
    assert "sql" in q_texts or "database" in q_texts or "select" in q_texts
    assert "python" not in q_texts


def test_requirement_2_goal_python_diagnostic_questions():
    """Test 2: Goal = 'I want to learn Python for backend development' -> diagnostic questions are Python-related."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/diagnostic-questions?goal=I%20want%20to%20learn%20Python%20for%20backend%20development")
    assert resp.status_code == 200
    data = resp.json()
    questions = data["questions"]
    assert len(questions) == 3
    q_texts = " ".join([q["question"] + " " + " ".join(q["options"]) for q in questions]).lower()
    assert "python" in q_texts


def test_requirement_3_switch_python_to_sql_diagnostic_questions():
    """Test 3: Start with Python -> click New Goal -> enter SQL -> diagnostic uses SQL, not Python."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    student_id = "test_student_switch_py_sql"

    # 1. Start with Python goal
    resp_py = client.get(f"/diagnostic-questions?goal=I%20want%20to%20learn%20Python&student_id={student_id}")
    assert resp_py.status_code == 200
    py_text = " ".join([q["question"] for q in resp_py.json()["questions"]]).lower()
    assert "python" in py_text

    # 2. Click "New Goal" (triggers reset-session)
    reset_resp = client.post(f"/reset-session?student_id={student_id}")
    assert reset_resp.status_code == 200

    # 3. Enter SQL goal
    resp_sql = client.get(f"/diagnostic-questions?goal=I%20want%20to%20learn%20SQL&student_id={student_id}")
    assert resp_sql.status_code == 200
    sql_questions = resp_sql.json()["questions"]
    sql_text = " ".join([q["question"] + " " + " ".join(q["options"]) for q in sql_questions]).lower()

    # Diagnostic MUST use SQL, and NOT Python
    assert "sql" in sql_text or "database" in sql_text or "select" in sql_text
    assert "python" not in sql_text


def test_requirement_4_switch_sql_to_java_diagnostic_questions():
    """Test 4: Start with SQL -> click New Goal -> enter Java -> diagnostic uses Java, not SQL."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    student_id = "test_student_switch_sql_java"

    # 1. Start with SQL goal
    resp_sql = client.get(f"/diagnostic-questions?goal=I%20want%20to%20learn%20SQL&student_id={student_id}")
    assert resp_sql.status_code == 200
    sql_text = " ".join([q["question"] for q in resp_sql.json()["questions"]]).lower()
    assert "sql" in sql_text or "database" in sql_text

    # 2. Click "New Goal" (triggers reset-session)
    reset_resp = client.post(f"/reset-session?student_id={student_id}")
    assert reset_resp.status_code == 200

    # 3. Enter Java goal
    resp_java = client.get(f"/diagnostic-questions?goal=I%20want%20to%20learn%20Java&student_id={student_id}")
    assert resp_java.status_code == 200
    java_questions = resp_java.json()["questions"]
    java_text = " ".join([q["question"] + " " + " ".join(q["options"]) for q in java_questions]).lower()

    # Diagnostic MUST use Java, and NOT SQL
    assert "java" in java_text or "jvm" in java_text
    assert "select" not in java_text


