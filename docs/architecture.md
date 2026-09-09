# StudyMate — System Architecture Specification

## 1. Overview
StudyMate is a personalized AI learning agent built according to **Problem Statement 3** of the evaluation rubric. It creates a personalized study roadmap for a student's stated goal and timeline, teaches and tests the student, evaluates objective and subjective performance, and autonomously replans via a real cyclic LangGraph workflow.

`
+---------------------------------------------------------------------------------------------------+
|                                         STUDYMATE SYSTEM                                          |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [Frontend Single-Page Web App] <----> [FastAPI REST Endpoints: /study, /progress, /history]       |
|                                                  |                                                |
|                                                  v                                                |
|                                    [LangGraph StateGraph Engine]                                  |
|                                                  |                                                |
|            +-------------------------------------+-------------------------------------+          |
|            |                                                                           |          |
|            v                                                                           v          |
|  [Tier 1: Ephemeral Session Memory]                                  [Tier 2: Persistent SQLite]  |
|  - StudyState TypedDict                                              - D:\StudyMate\data\studymate.db
|  - Current session answers, code, cycle counts                       - students, roadmaps,        |
|                                                                        topic_mastery, sessions    |
+---------------------------------------------------------------------------------------------------+
`

---

## 2. The 8 Specialized Agents

StudyMate employs 8 dedicated, single-responsibility agent nodes coordinated by LangGraph:

`mermaid
graph TD
    A[1. Assessment Agent] --> B[2. Learning Planner Agent]
    B --> C[3. Concept / Tutor Agent]
    C --> D[4. Quiz Agent]
    D --> E[5. Practice Agent]
    E --> F[6. Evaluation Agent]
    F --> G[7. Performance Agent]
    G --> H{Conditional Router}
    
    H -->|>= 80% (ADVANCE)| I[Advance Handler]
    H -->|50-79% (REINFORCE)| J[Reinforce Handler]
    H -->|< 50% or Deadline Drift (FULL_REPLAN)| K[8. Planner Update Agent]
    
    I -->|Next Topic| C
    J -->|Reteach Weak Concepts| C
    K -->|Reorganized Plan| C
    
    I -->|All Topics Mastered| L[Finalizer Agent]
    L --> M((END))
`

1. **Agent 1: Assessment Agent (ackend/agents/assessment.py)**
   - Conducts multi-question diagnostic testing of the student's baseline knowledge.
   - Categorizes level into eginner, intermediate, or dvanced.
   - Identifies strengths and specific prerequisite knowledge gaps.

2. **Agent 2: Learning Planner Agent (ackend/agents/learning_planner.py)**
   - Synthesizes goal, timeline, and diagnostic level into a 5-step milestone roadmap.
   - Checks Tier 2 persistent memory to preserve existing roadmaps.
   - Detects multi-day gaps and schedule drift (>2 days) and recalibrates remaining deadlines without restarting mastered topics.

3. **Agent 3: Concept / Tutor Agent (ackend/agents/tutor.py)**
   - Grounds explanations in authoritative reference documents retrieved via local RAG.
   - Dynamically adapts tone and depth to assessed student level (eginner vs dvanced).
   - Focuses specifically on remediating flagged weak areas if called via REINFORCE or FULL_REPLAN.

4. **Agent 4: Quiz Agent (ackend/agents/quiz.py)**
   - Generates 4-option multiple-choice comprehension questions with explanations.
   - Persists questions in SQLite student_active_quizzes table to guarantee reliable grading against exact displayed choices.

5. **Agent 5: Practice Agent (ackend/agents/practice.py)**
   - Queries local RAG knowledge to create contextual, production-aligned coding exercises.
   - Supplies starter code boilerplate, input/output specifications, and edge-case constraints.

6. **Agent 6: Evaluation Agent (ackend/agents/evaluation.py)**
   - Deterministic scoring for multiple-choice quiz questions (zero hallucination).
   - Deterministic AST/syntax verification and validation for student code.
   - Structured rubric-based grading for free-text answers and stylistic code feedback.

7. **Agent 7: Performance Agent (ackend/agents/performance.py)**
   - Aggregates current score and historical topic mastery from SQLite persistent memory.
   - Tracks learning pace against target days: computes progress_pct vs 	ime_pct.
   - Generates deterministic routing decisions:
     - ADVANCE: score >= 80% (and not severely behind).
     - REINFORCE: 50% <= score < 80%.
     - FULL_REPLAN: score < 50% OR major deadline drift (	ime_pct - progress_pct > 0.25).
   - Logs complete session audit record to SQLite learning_sessions.

8. **Agent 8: Planner Update Agent (ackend/agents/planner_update.py)**
   - Injects targeted Foundational Remediation modules into the active roadmap.
   - Recalibrates target dates for remaining modules to preserve overall timeline.
   - Saves modified roadmap directly to Tier 2 persistent storage.

---

## 3. Real Cyclic LangGraph State Machine

Unlike linear chains wrapped in Python loops, StudyMate uses LangGraph's native StateGraph with conditional edges:

`python
# Defined in backend/graph.py
workflow.add_conditional_edges(
    performance,
    route_after_performance,
    {
        advance: advance_topic,
        reinforce: reinforce_topic,
        full_replan: planner_update,
        finalize: finalizer
    }
)
workflow.add_edge(reinforce_topic, tutor)      # Cyclic loop back to Tutor
workflow.add_edge(planner_update, tutor)        # Cyclic loop back to Tutor with replanned topic
workflow.add_edge(advance_topic, tutor)         # Loop to Tutor for next topic
`

---

## 4. Two-Tier Memory Architecture

| Memory Tier | Storage | Scope | Content |
|---|---|---|---|
| **Tier 1: Ephemeral Session Memory** | StudyState TypedDict | Single Graph Execution | Active messages, retrieved chunks, quiz state, practice code, iteration cycle counter |
| **Tier 2: Persistent Cross-Session Memory** | SQLite (D:\StudyMate\data\studymate.db) | Cross-Session & Multi-Day | students profiles, student_roadmaps (5 milestones & pointer), 	opic_mastery (historical mastery & status), learning_sessions (audit logs), student_active_quizzes |

---

## 5. Local RAG Retrieval Layer

- Located at ackend/knowledge/rag.py.
- Features 6 indexed technical reference corpuses: Python primitives, asynchronous I/O, FastAPI REST routing, relational SQL ACID semantics, and algorithm complexity.
- TF-IDF vectorization with cosine similarity scoring.
- Injected into **Tutor Agent** and **Practice Agent** prompts to guarantee factual rigor and prevent generative drift.
