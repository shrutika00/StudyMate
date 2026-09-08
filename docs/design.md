# StudyMate — Architecture and Technical Design Document

## 1. Executive Summary

StudyMate implements Problem Statement 3 (“StudyMate — Personalized AI Learning Agent”) from the AI Agent Suite evaluation assignment. It creates a personalized study plan for a stated learning goal, teaches and tests the student, measures actual performance, and continuously replans based on that performance.

Built strictly at D:\StudyMate using:
- **Python 3.13**
- **FastAPI**
- **LangGraph** (Real cyclic StateGraph topology)
- **Google Gemini API** (gemini-3.6-flash)
- **SQLite** (Persistent Cross-Session Memory Tier)
- **Vanilla HTML5 / CSS3 / JavaScript frontend**

---

## 2. The 8 Specialized Agents

1. **Assessment Agent** (ackend/agents/assessment.py):
   - Diagnoses current proficiency level (eginner, intermediate, dvanced).
   - Identifies strengths, knowledge gaps, and baseline diagnostic summaries.

2. **Learning Planner Agent** (ackend/agents/learning_planner.py):
   - Breaks down learning goals into a structured 5-topic curriculum roadmap.
   - Assigns target milestone days and initial status (in_progress, pending).
   - Persists the roadmap to SQLite Tier 2 Memory.

3. **Concept / Tutor Agent** (ackend/agents/tutor.py):
   - Retrieves grounded context chunks from the local RAG knowledge layer.
   - Explains core concepts, mechanics, and memory models grounded strictly in authoritative documents.

4. **Quiz Agent** (ackend/agents/quiz.py):
   - Generates 4-option multiple-choice comprehension questions with explanations.

5. **Practice Agent** (ackend/agents/practice.py):
   - Generates realistic coding exercises with starter code, constraints, and expected output.

6. **Evaluation Agent** (ackend/agents/evaluation.py):
   - Implements hybrid evaluation: deterministic verification for objective answers and code execution + structured Gemini rubric evaluation for open-ended explanations.

7. **Performance Agent** (ackend/agents/performance.py):
   - Tracks topic mastery across sessions.
   - Evaluates learning pace against target deadlines.
   - Determines the deterministic routing decision: ADVANCE (>=80%), REINFORCE (50-79%), or FULL_REPLAN (<50%).

8. **Planner Update Agent** (ackend/agents/planner_update.py):
   - Dynamically reorganizes the remaining study roadmap upon persistent weakness or low scores.
   - Injects targeted Foundational Remediation modules and recalibrates milestone dates.

---

## 3. Real Cyclic LangGraph Workflow

The state machine is built with LangGraph's StateGraph(StudyState):

`	ext
START -> Assessment -> Learning Planner -> Tutor -> Quiz -> Practice -> Evaluation -> Performance
                                             ^                                            |
                                             |                                    Conditional Router
                                             |                                     /      |      \
                                             |                            ADVANCE /   REINF|      \ REPLAN
                                             |                                   v        v        v
                                             +------------------------------ Advance   Reinforce  PlannerUpdate
                                             |                                   |        |        |
                                             +-----------------------------------+--------+--------+
                                                                                 |
                                                                        (Roadmap Complete OR Max Cycles)
                                                                                 v
                                                                             Finalizer -> END
`

---

## 4. Two Memory Tiers

1. **Tier 1: Session-Scoped Memory (Ephemeral)**
   - TypedDict StudyState passed from node to node in LangGraph.
   - Holds the transient context of the active learning session (teaching, quiz, practice code, evaluation rubric, cycle count).

2. **Tier 2: Persistent Cross-Session Memory (SQLite)**
   - Stored in D:\StudyMate\data\studymate.db.
   - Tables:
     - students: Profiles, learning goals, assessed levels, and deadlines.
     - student_roadmaps: Active multi-topic roadmaps and current topic index.
     - 	opic_mastery: Historical mastery scores, statuses (mastered, einforcing, weak), and attempt counts.
     - learning_sessions: Complete historical logs of learning cycles.

---

## 5. Local RAG Knowledge Retrieval Layer

Located at ackend/knowledge/rag.py:
- 6 curated technical reference documents covering core Python data structures, asyncio concurrency, FastAPI HTTP routing, relational ACID transactions, and algorithmic complexity.
- TF-IDF vectorizer with cosine similarity retrieval.
- Integrated into Concept/Tutor and Practice agents to ensure factual accuracy and avoid hallucinations.
