import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.code_executor import execute_code_safely

client = TestClient(app)


def test_code_executor_success():
    """Verify safe execution of valid Python code with stdout."""
    code = "def solve():\n    return [x**2 for x in range(4)]\nprint('Output:', solve())"
    res = execute_code_safely(code)
    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "Output: [0, 1, 4, 9]" in res["stdout"]
    assert res["error"] is None


def test_code_executor_syntax_error():
    """Verify safe execution catches syntax errors before running."""
    code = "def broken(\n    return 42"
    res = execute_code_safely(code)
    assert res["success"] is False
    assert res["exit_code"] == 1
    assert "SyntaxError" in res["stderr"]


def test_code_executor_runtime_error():
    """Verify safe execution catches runtime exceptions."""
    code = "def divide(a, b):\n    return a / b\nprint(divide(10, 0))"
    res = execute_code_safely(code)
    assert res["success"] is False
    assert res["exit_code"] == 1
    assert "ZeroDivisionError" in res["stderr"]


def test_code_executor_timeout():
    """Verify safe execution terminates infinite loops."""
    code = "while True:\n    pass"
    res = execute_code_safely(code, timeout_seconds=1)
    assert res["success"] is False
    assert res["exit_code"] == -2
    assert "timed out" in res["stderr"].lower()


def test_execute_code_endpoint():
    """Verify FastAPI /execute-code endpoint returns execution output."""
    response = client.post(
        "/execute-code",
        json={"code": "nums = [1, 2, 3]\nprint('Sum:', sum(nums))"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Sum: 6" in data["stdout"]
