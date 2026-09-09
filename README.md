# StudyMate 🎓 — Personalized AI Learning Companion

> **Problem Statement 3 — AI Agent Suite Evaluation Assignment**  
> Built strictly at `D:\StudyMate` with **FastAPI**, **LangGraph (Real Cyclic StateGraph)**, **Google Gemini (`gemini-3.1-flash-lite`)**, **SQLite (2-Tier Memory)**, and a **Step-Based Interactive Learning UI**.  
> **Core Architectural Pattern**: Real Cyclic Graph with 3-Way Conditional Routing & Continuous Replanning (`ADVANCE`, `REINFORCE`, `FULL REPLAN`).

---

## 1. Interactive Step-Based Learning Journey

StudyMate is organized into a clean, multi-stage learning progression rather than a single giant page:

1. **Learning Goal**: Student specifies what they want to learn, timeline (e.g., 30 days), and self-declared level.
2. **Diagnostic Assessment**: Assessment Agent provides a short 3-question diagnostic. The student answers each question, receives their assessed level (`BEGINNER`, `INTERMEDIATE`, or `ADVANCED`), which is persisted to state and SQLite.
3. **Learning Plan**: Learning Planner Agent renders the customized curriculum roadmap with milestone target days and statuses.
4. **Learn / Concept**: Tutor Agent delivers deep explanations grounded in the local RAG knowledge layer with explicit source citations.
5. **Interactive Topic Quiz**: Quiz Agent generates 3–5 high-quality questions (multiple-choice, true/false). The student selects answers, submits the quiz, and receives real instant objective scoring (e.g., `4 / 5 (80%)`) with question-by-question explanations and areas to improve.
6. **Hands-On Practice**: Practice Agent provides a realistic code challenge with starter code and hints. The student edits and submits their code.
7. **Evaluation & Performance**: Evaluation Agent grades quiz answers deterministically and code via AST syntax checks + Gemini rubric. Performance Agent aggregates scores, tracks pace vs. deadline, and identifies strong/weak topics.
8. **Conditional Routing Decision**: The LangGraph router selects and visibly displays:
   - 🟢 **`ADVANCE`**: Mastery achieved (&ge; 80%) &rarr; Advance to next topic.
   - 🟡 **`REINFORCE`**: Partial understanding (50-79%) &rarr; Re-teach and re-quiz current topic.
   - 🔵 **`FULL REPLAN`**: Significant difficulty (< 50%) &rarr; Planner Update Agent reorganizes roadmap and injects remediation.
9. **Next Learning Task**: Triggers the real LangGraph cycle back to Tutor or next module.

---

## 2. The 8 Specialized Agents

| Agent | Module | Core Responsibility |
|---|---|---|
| **1. Assessment Agent** | `backend/agents/assessment.py` | Generates diagnostic questions, assesses student proficiency level, identifies gaps, persists student profile. |
| **2. Learning Planner Agent** | `backend/agents/learning_planner.py` | Creates structured 5-module 30-day roadmap with deadlines; saves to persistent memory. |
| **3. Concept / Tutor Agent** | `backend/agents/tutor.py` | Teaches topic concepts, grounded strictly in local RAG knowledge base chunks. |
| **4. Quiz Agent** | `backend/agents/quiz.py` | Generates 3–5 multi-choice and true/false diagnostic questions targeting topic and level. |
| **5. Practice Agent** | `backend/agents/practice.py` | Generates hands-on coding challenges with starter code, expected output, and hints. |
| **6. Evaluation Agent** | `backend/agents/evaluation.py` | Performs deterministic objective quiz checking, deterministic code syntax verification, and rubric grading. |
| **7. Performance Agent** | `backend/agents/performance.py` | Aggregates session results, calculates pace vs. deadline, updates topic mastery, determines routing decision. |
| **8. Planner Update Agent** | `backend/agents/planner_update.py` | Reorganizes remaining roadmap, injects `"Foundational Remediation"` modules, and stretches deadlines when needed. |

---

## 3. Real Cyclic LangGraph Architecture

```text
               +---------------------------+
               |           START           |
               +---------------------------+
                             |
                             v
               +---------------------------+
               |      Assessment Agent     |
               +---------------------------+
                             |
                             v
               +---------------------------+
               |   Learning Planner Agent  |
               +---------------------------+
                             |
                             v
           +-> +---------------------------+ <---------------+
           |   |    Concept / Tutor Agent  |                 |
           |   +---------------------------+                 |
           |                 |                               |
           |                 v                               |
           |   +---------------------------+                 |
           |   |         Quiz Agent        |                 |
           |   +---------------------------+                 |
           |                 |                               |
           |                 v                               |
           |   +---------------------------+                 |
           |   |       Practice Agent      |                 |
           |   +---------------------------+                 |
           |                 |                               |
           |                 v                               |
           |   +---------------------------+                 |
           |   |      Evaluation Agent     |                 |
           |   +---------------------------+                 |
           |                 |                               |
           |                 v                               |
           |   +---------------------------+                 |
           |   |     Performance Agent     |                 |
           |   +---------------------------+                 |
           |                 |                               |
           |                 v                               |
           |   +---------------------------+                 |
           |   |     Conditional Router    |                 |
           |   +---------------------------+                 |
           |     /           |           \                   |
           |    / (Score     | (Score     \ (Score < 50%     |
           |   /  >= 80%)    |  50-79%)    \  or struggling) |
           |  v              v              v                |
      +---------+      +-----------+   +----------------+    |
      | ADVANCE |      | REINFORCE |   | PLANNER UPDATE |----+
      +---------+      +-----------+   +----------------+
           |                 |                  (Reorganizes roadmap &
           | (Cycles to next | (Cycles back for  injects remediation)
           |  roadmap topic) |  reteaching)
           +--------+--------+
                    |
                    v (Roadmap completed OR Max Cycles reached)
           +-----------------+
           |    Finalizer    |
           +-----------------+
                    |
                    v
           +-----------------+
           |       END       |
           +-----------------+
```

---

## 4. Full Cyclic Execution Demonstration Transcript

Below is an actual verified execution transcript illustrating a full **Poor Performance &rarr; REINFORCE &rarr; Re-teach &rarr; Re-quiz &rarr; Improved Performance &rarr; ADVANCE** cycle:

```text
=== CYCLE 1: INITIAL PASS ===
[Student]: "I want to learn Python for backend development in 30 days"
[Assessment Agent]: Diagnosed level -> BEGINNER
[Learning Planner Agent]: Created 5-step roadmap (Topic 1: Python Fundamentals & Data Structures)
[Tutor Agent]: Grounded explanation retrieved from local RAG ('Python Data Structures & Memory Complexity')
[Quiz Agent]: Generated 5 conceptual questions on functions, dictionaries, and time complexities
[Student Quiz Submission]: 3/5 correct (60%) -> Missed return value mechanics and hash collisions
[Student Practice Submission]: Code with empty body -> Syntax valid, missing logic
[Evaluation Agent]: Hybrid score -> 60% (Passed: False)
[Performance Agent]:
  - Current Score: 60%
  - Weak Topics: ["Python Fundamentals (60%)"]
  - Pace: On Track
  - ROUTING DECISION: 🟡 REINFORCE
[Action Node - Reinforce]: Topic retained as 'reinforcing'. Bounded cycle incremented (cycle_count = 1).

=== CYCLE 2: REINFORCEMENT LOOP (CYCLIC RETURN TO TUTOR) ===
[Tutor Agent]: Re-teaches with targeted focus on return values and dictionary hash operations
[Quiz Agent]: Re-tests student with focused questions
[Student Quiz Submission]: 5/5 correct (100%)
[Student Practice Submission]: Complete dictionary accumulator code
[Evaluation Agent]: Hybrid score -> 92% (Passed: True)
[Performance Agent]:
  - Current Score: 92%
  - Strong Topics: ["Python Fundamentals (92%)"]
  - Pace: Ahead
  - ROUTING DECISION: 🟢 ADVANCE
[Action Node - Advance]: Topic 1 marked as 'mastered'. Roadmap advanced to Topic 2 ('Functions, Scope, and OOP').
[Finalizer Node]: Structured response compiled and persisted to SQLite.
```

---

## 5. Two Memory Tiers

1. **Tier 1: Session-Scoped Memory (Ephemeral)**
   - Stored in LangGraph's `StudyState` (`backend/state.py`).
   - Carries intermediate inputs and outputs across all 8 agents during an active invocation (active assessment, diagnostic answers, RAG context, teaching, multi-question quiz, practice attempts, evaluation rubric, and cycle counters).
2. **Tier 2: Persistent Cross-Session Memory (SQLite)**
   - Database file at `D:\StudyMate\data\studymate.db`.
   - Tables: `students`, `student_roadmaps`, `topic_mastery`, and `learning_sessions`.
   - Remembers student level, current topic index, mastery percentages, and past session histories across restarts.

---

## 6. Documentation Deliverables
- 📄 **[System Architecture](docs/architecture.md)**: Full component breakdown, agent roles, LangGraph conditional edges, and memory topology.
- 📄 **[Sample Execution Transcript](docs/sample_transcript.md)**: Two-cycle execution transcript tracing struggle, targeted reteaching, and advancement.
- 📄 **[Technical Design Decisions](docs/design_decisions.md)**: Detailed rationale for cyclic routing, deterministic scoring, two-tier memory, and multi-day gap recalibration.

---

## 7. How to Run the Application

### 1. Run Automated Test Suite (28/28 Passing)
```powershell
cd D:\StudyMate
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\pytest.exe -v tests
```

### 2. Launch FastAPI Server
```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open Interactive Web App
Open your browser to:
```
http://127.0.0.1:8000
```
Follow the step-based flow:
- Enter Goal &rarr; Take 3-Question Diagnostic &rarr; Review Roadmap &rarr; Learn Concept &rarr; Take 5-Question Quiz &rarr; Complete Code Lab &rarr; View Performance & Routing Decision.
