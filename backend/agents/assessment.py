import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import StudyState
from ..models.schemas import AssessmentResult, DifficultyLevel, AssessmentQuestion
from ..database.db import save_or_update_student, get_student
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


DIAGNOSTIC_QUESTIONS_BANK = [
    {
        "id": 1,
        "question": "What is a Python function?",
        "options": [
            "A) A reusable block of code designed to perform a specific task",
            "B) A database management system",
            "C) A variable that stores numbers only",
            "D) An operating system program"
        ],
        "correct_option": "A",
        "explanation": "Functions are reusable blocks of code executed when called."
    },
    {
        "id": 2,
        "question": "Which keyword is used in Python to define a function?",
        "options": [
            "A) func",
            "B) def",
            "C) function",
            "D) lambda_func"
        ],
        "correct_option": "B",
        "explanation": "The 'def' keyword is standard in Python for defining named functions."
    },
    {
        "id": 3,
        "question": "What is the average time complexity of looking up a key in a Python dictionary?",
        "options": [
            "A) O(n)",
            "B) O(log n)",
            "C) O(1)",
            "D) O(n^2)"
        ],
        "correct_option": "C",
        "explanation": "Python dictionaries use hash tables, giving O(1) average lookup time."
    }
]

SQL_DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "question": "Which SQL statement is used to retrieve data from a database table?",
        "options": [
            "A) SELECT",
            "B) EXTRACT",
            "C) GET",
            "D) OPEN"
        ],
        "correct_option": "A",
        "explanation": "The SELECT statement is the standard command used to query and fetch records from database tables."
    },
    {
        "id": 2,
        "question": "Which SQL clause is used to filter records based on specified conditions?",
        "options": [
            "A) ORDER BY",
            "B) WHERE",
            "C) GROUP BY",
            "D) LIMIT"
        ],
        "correct_option": "B",
        "explanation": "The WHERE clause filters rows satisfying a boolean condition before grouping or sorting."
    },
    {
        "id": 3,
        "question": "What is the primary difference between INNER JOIN and LEFT JOIN in SQL?",
        "options": [
            "A) INNER JOIN returns only matching rows; LEFT JOIN returns all rows from the left table plus matches",
            "B) INNER JOIN sorts data in ascending order; LEFT JOIN sorts in descending order",
            "C) LEFT JOIN can only be used on primary keys; INNER JOIN works on any column",
            "D) There is no difference between INNER JOIN and LEFT JOIN"
        ],
        "correct_option": "A",
        "explanation": "INNER JOIN requires matches in both tables; LEFT JOIN preserves all left-table rows regardless of matches in the right table."
    }
]

JS_DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "question": "Which keyword declares a block-scoped constant in modern JavaScript?",
        "options": [
            "A) const",
            "B) var",
            "C) let",
            "D) static"
        ],
        "correct_option": "A",
        "explanation": "'const' declares block-scoped constants that cannot be reassigned."
    },
    {
        "id": 2,
        "question": "What does 'typeof null' evaluate to in JavaScript?",
        "options": [
            "A) 'undefined'",
            "B) 'object'",
            "C) 'null'",
            "D) 'boolean'"
        ],
        "correct_option": "B",
        "explanation": "typeof null returns 'object' due to legacy design in JavaScript's type tagging."
    },
    {
        "id": 3,
        "question": "Which array method executes a callback for each element without returning a new array?",
        "options": [
            "A) map()",
            "B) filter()",
            "C) forEach()",
            "D) reduce()"
        ],
        "correct_option": "C",
        "explanation": "forEach() runs a function on each element and always returns undefined."
    }
]


def extract_topic_from_goal(goal: str) -> str:
    cleaned = (goal or "").strip()
    patterns = [
        r"^(?:i\s+want\s+to\s+learn\s+(?:how\s+to\s+use\s+|how\s+to\s+|to\s+code\s+in\s+|about\s+)?)(.*)$",
        r"^(?:learn\s+(?:about\s+|how\s+to\s+)?)(.*)$",
        r"^(?:study\s+)(.*)$"
    ]
    for pat in patterns:
        m = re.match(pat, cleaned, re.IGNORECASE)
        if m:
            cleaned = m.group(1).strip()
            break
    cleaned = re.sub(r"\s+in\s+\d+\s+(?:days?|weeks?|months?)", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else (goal or "Software Engineering")


def generate_topic_diagnostic_questions(goal: str) -> List[Dict[str, Any]]:
    """Generates 3 calibrated diagnostic multiple-choice questions for any learning goal."""
    if not goal:
        return DIAGNOSTIC_QUESTIONS_BANK

    goal_lower = goal.lower()
    if "python" in goal_lower:
        return DIAGNOSTIC_QUESTIONS_BANK
    elif any(k in goal_lower for k in ["sql", "database", "postgres", "mysql", "sqlite", "queries"]):
        return SQL_DIAGNOSTIC_QUESTIONS
    elif "java" in goal_lower and "javascript" not in goal_lower:
        return [
            {
                "id": 1,
                "question": "In Java, what is the primary role of the Java Virtual Machine (JVM)?",
                "options": [
                    "A) Direct compilation to native machine code without runtime bytecode",
                    "B) Executing compiled Java bytecode across different operating systems",
                    "C) Providing an embedded client-side browser DOM engine",
                    "D) Serving static HTML assets over local sockets"
                ],
                "correct_option": "B",
                "explanation": "The JVM interprets and JIT-compiles Java bytecode to achieve platform independence."
            },
            {
                "id": 2,
                "question": "Which keyword is used in Java to inherit a class?",
                "options": [
                    "A) implements",
                    "B) extends",
                    "C) inherits",
                    "D) super"
                ],
                "correct_option": "B",
                "explanation": "'extends' is the standard keyword in Java for class inheritance."
            },
            {
                "id": 3,
                "question": "In Java, which collection class provides O(1) average time complexity for key-value lookups?",
                "options": [
                    "A) ArrayList",
                    "B) LinkedList",
                    "C) HashMap",
                    "D) TreeSet"
                ],
                "correct_option": "C",
                "explanation": "HashMap uses a hash table providing O(1) average retrieval time."
            }
        ]
    elif any(k in goal_lower for k in ["machine learning", "ml", "deep learning", "artificial intelligence", "data science"]):
        return [
            {
                "id": 1,
                "question": "In Machine Learning, what is the primary purpose of splitting data into training and test sets?",
                "options": [
                    "A) To evaluate model generalization on unseen data and detect overfitting",
                    "B) To compress the dataset for faster storage",
                    "C) To eliminate feature engineering requirements",
                    "D) To encrypt features for privacy during training"
                ],
                "correct_option": "A",
                "explanation": "Test sets provide unbiased evaluation of a model's performance on unseen data."
            },
            {
                "id": 2,
                "question": "Which of the following is a supervised learning algorithm commonly used for classification?",
                "options": [
                    "A) K-Means Clustering",
                    "B) Random Forest",
                    "C) Principal Component Analysis (PCA)",
                    "D) Apriori Association Rules"
                ],
                "correct_option": "B",
                "explanation": "Random Forest is an ensemble supervised classification and regression algorithm."
            },
            {
                "id": 3,
                "question": "What does an optimization algorithm like Gradient Descent minimize during model training?",
                "options": [
                    "A) The learning rate schedule",
                    "B) The number of input features",
                    "C) The loss function (error between predictions and true labels)",
                    "D) The size of the test dataset"
                ],
                "correct_option": "C",
                "explanation": "Optimization algorithms iteratively adjust model weights to minimize the loss function."
            }
        ]
    else:
        topic = extract_topic_from_goal(goal)
        return [
            {
                "id": 1,
                "question": f"What is a foundational concept or primary purpose of {topic}?",
                "options": [
                    f"A) Core principles, syntax, and fundamental domain architecture of {topic}",
                    f"B) An unrelated operating system kernel driver",
                    f"C) A static hardware component used for cooling servers",
                    f"D) A legacy spreadsheet formula language"
                ],
                "correct_option": "A",
                "explanation": f"Understanding foundational concepts and architectures is required to build with {topic}."
            },
            {
                "id": 2,
                "question": f"Which core syntax, mechanism, or operation is fundamental when working with {topic}?",
                "options": [
                    f"A) Arbitrary memory corruption without type checking",
                    f"B) Idiomatic standard abstractions, modular workflows, and core libraries in {topic}",
                    f"C) Formatting hard drive sectors during routine compilation",
                    f"D) Disabling all runtime error handling and exceptions"
                ],
                "correct_option": "B",
                "explanation": f"Idiomatic conventions and core libraries form the building blocks of {topic}."
            },
            {
                "id": 3,
                "question": f"In practical application of {topic}, which engineering practice ensures stability and performance?",
                "options": [
                    f"A) Running untracked scripts without validation or testing",
                    f"B) Hardcoding secrets and credentials into source files",
                    f"C) Automated testing, modular component separation, and profiling for {topic}",
                    f"D) Ignoring memory leaks and latency degradation"
                ],
                "correct_option": "C",
                "explanation": f"Automated testing and profiling ensure production reliability when deploying {topic}."
            }
        ]


def get_diagnostic_questions_for_goal(goal: str) -> List[Dict[str, Any]]:
    """Return diagnostic assessment questions tailored to the student's learning goal."""
    return generate_topic_diagnostic_questions(goal)


def assessment_agent_node(state: StudyState) -> Dict[str, Any]:
    """
    Agent 1: Assessment Agent
    Role: Analyzes the student's learning goal, diagnostic answers, and background to determine
    the student's current proficiency level and initial knowledge gaps.
    Saves profile to Persistent Cross-Session Memory.
    """
    student_id = state.get("student_id", "student_default")
    goal = state.get("goal") or state.get("learning_goal") or "Python"
    target_days = state.get("target_days", 30)
    history = list(state.get("workflow_history", []))
    history.append("Assessment")

    # 1. Determine active diagnostic questions for this goal
    existing_questions = state.get("diagnostic_questions")
    if existing_questions and isinstance(existing_questions, list) and len(existing_questions) == 3:
        active_questions = existing_questions
    else:
        active_questions = generate_topic_diagnostic_questions(goal)

    diag_answers = state.get("diagnostic_answers") or {}
    score = None
    if diag_answers:
        correct_count = 0
        for q in active_questions:
            qid = str(q["id"])
            user_ans = str(diag_answers.get(qid, "")).strip().upper()
            corr = q["correct_option"].strip().upper()
            if user_ans and (user_ans == corr or corr in user_ans):
                correct_count += 1
        score = int((correct_count / len(active_questions)) * 100)

    existing_profile = get_student(student_id)
    same_goal = bool(
        existing_profile and
        existing_profile.get("learning_goal") and
        existing_profile.get("learning_goal", "").strip().lower() == goal.strip().lower()
    )
    if existing_profile and existing_profile.get("assessed_level") and not diag_answers and same_goal:
        assessed_level_str = existing_profile["assessed_level"]
        assessment_obj = AssessmentResult(
            assessed_level=DifficultyLevel(assessed_level_str),
            strengths=["Returning student with established profile"],
            knowledge_gaps=["Continuing customized roadmap"],
            diagnostic_summary=f"Welcome back! Resuming plan at {assessed_level_str} level.",
            questions=[AssessmentQuestion(**q) for q in active_questions]
        )
        return {
            "assessed_level": assessed_level_str,
            "assessment": assessment_obj.model_dump(),
            "diagnostic_questions": active_questions,
            "workflow_history": history,
            "status": "assessed"
        }

    inferred_level = "beginner"
    if score is not None:
        if score >= 80:
            inferred_level = "advanced"
        elif score >= 50:
            inferred_level = "intermediate"
        else:
            inferred_level = "beginner"

    llm = get_llm()
    prompt = f"""You are StudyMate's Assessment Agent.
Analyze the following student learning goal and generate diagnostic assessment details:
Goal: "{goal}"
Target Timeline: {target_days} days
Diagnostic Score: {score if score is not None else 'Initial diagnostic generation'}

Your task:
1. Generate 3 calibrated multiple-choice diagnostic questions to evaluate the student's baseline knowledge specifically for "{goal}".
   - Question 1: Fundamental syntax, concept, or terminology of {goal}.
   - Question 2: Core mechanism, operation, or rule in {goal}.
   - Question 3: Applied practical scenario or problem-solving application of {goal}.
   Format each question with:
   - "id": 1, 2, or 3
   - "question": Clear question text testing {goal}
   - "options": 4 choices formatted as ["A) ...", "B) ...", "C) ...", "D) ..."]
   - "correct_option": Single uppercase letter "A", "B", "C", or "D"
   - "explanation": Brief explanation of the correct option

2. Determine Assessed Level ('beginner', 'intermediate', or 'advanced').
3. List 2 strengths implied by this goal.
4. List 3 key knowledge gaps to address to master "{goal}".
5. Provide a concise diagnostic summary.

Output valid JSON matching this schema exactly:
{{
  "diagnostic_questions": [
    {{
      "id": 1,
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "A",
      "explanation": "..."
    }},
    {{
      "id": 2,
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "B",
      "explanation": "..."
    }},
    {{
      "id": 3,
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C",
      "explanation": "..."
    }}
  ],
  "assessed_level": "{inferred_level}",
  "strengths": ["Clear technical ambition in {goal}", "Structured timeline"],
  "knowledge_gaps": ["Core fundamentals of {goal}", "Applied patterns in {goal}", "Production best practices"],
  "diagnostic_summary": "Assessed at {inferred_level} level for {goal} target."
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are an expert technical curriculum diagnostician. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])
        raw_text = extract_text_content(response.content) if hasattr(response, "content") else str(response)
        data = extract_json(raw_text)
        llm_questions = data.get("diagnostic_questions") or data.get("questions")
        if llm_questions and isinstance(llm_questions, list) and len(llm_questions) == 3:
            if not diag_answers:
                active_questions = llm_questions
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            raise
        data = {}

    level_val = data.get("assessed_level", inferred_level).lower()
    if level_val not in ["beginner", "intermediate", "advanced"]:
        level_val = inferred_level

    strengths = data.get("strengths") or [
        f"Clear technical ambition in {goal}",
        "Committed structured timeline"
    ]
    gaps = data.get("knowledge_gaps") or [
        f"Core principles and fundamentals of {goal}",
        f"Applied idioms and practical syntax for {goal}",
        f"Building production projects with {goal}"
    ]
    summary = data.get("diagnostic_summary") or f"Assessed at {level_val} level for {goal} with {target_days}-day timeline."

    assessment_obj = AssessmentResult(
        assessed_level=DifficultyLevel(level_val),
        strengths=strengths,
        knowledge_gaps=gaps,
        diagnostic_summary=summary,
        diagnostic_score=score,
        questions=[AssessmentQuestion(**q) for q in active_questions]
    )

    save_or_update_student(
        student_id=student_id,
        learning_goal=goal,
        assessed_level=level_val,
        target_days=target_days,
        current_day=1
    )

    return {
        "assessed_level": level_val,
        "assessment": assessment_obj.model_dump(),
        "diagnostic_questions": active_questions,
        "workflow_history": history,
        "status": "assessed"
    }
