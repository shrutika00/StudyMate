# StudyMate — Technical Design Decisions & Rationale

This document details the key technical, architectural, and algorithmic design choices made in StudyMate.

---

## 1. Why LangGraph for Cyclic Replanning?
- **The Problem**: Linear chaining libraries (like standard LangChain chains or sequential pipelines) execute in a single forward pass. Real learning, however, is inherently non-linear and feedback-driven: students misunderstand concepts, fail evaluations, require remediation, or drift behind schedule.
- **The Decision**: StudyMate uses LangGraph's cyclic StateGraph. Nodes represent individual specialized agents, and conditional edges evaluate performance thresholds to route backward or forward.
- **Benefits**:
  - Genuine cycles without recursion limits or infinite loops (guarded by cycle_count and state counters).
  - Clear separation of concerns between teaching, testing, grading, performance analysis, and replanning.
  - State immutability and transparent history logging for full auditability.

---

## 2. Deterministic Routing Policy vs. LLM Pacing Hallucinations
- **The Problem**: Letting an LLM decide when a student should advance or replan frequently leads to sycophancy, inconsistent thresholds, and unpredictable syllabus adjustments.
- **The Decision**: StudyMate uses explicit, deterministic scoring logic in ackend/agents/performance.py:
  - **ADVANCE**: score >= 80% (and no major deadline drift).
  - **REINFORCE**: 50% <= score < 80% &rarr; loops back to Tutor with targeted focus.
  - **FULL_REPLAN**: score < 50% OR major deadline drift (	ime_pct - progress_pct > 0.25) &rarr; routes to Planner Update Agent.
- **Benefits**:
  - Consistent, objective learning criteria across all topics.
  - Transparent expectations for the student.

---

## 3. Hybrid Evaluation (Deterministic + Rubric)
- **The Problem**: Pure LLM grading suffers from prompt injection, score drift, and grading inconsistency on objective questions. Conversely, pure deterministic grading cannot evaluate code style, architectural reasoning, or open-ended explanations.
- **The Decision**: A two-pronged hybrid evaluation model in ackend/agents/evaluation.py:
  - **Multiple Choice / Objective Questions**: Evaluated deterministically in Python against stored answer keys. Guaranteed zero hallucinations.
  - **Code Practice**: First validated via Python's AST parser to ensure syntactical validity and detect illegal constructs. Then evaluated against a structured rubric by Gemini for efficiency, readability, and adherence to constraints.
  - **Weighting**: Deterministic objective score (50%) + Code/Practice rubric score (50%).

---

## 4. Two-Tier Memory Architecture
- **Tier 1 (Session State)**: Implemented as a LangGraph StudyState (TypedDict). Fast, strictly in-memory, thread-safe, and scoped to the active execution run.
- **Tier 2 (Persistent SQLite)**: Implemented via SQLite in D:\StudyMate\data\studymate.db. Stores long-term student profiles, the active 5-step roadmap, historical topic mastery scores, and complete session logs.
- **Why SQLite?**:
  - Zero external database server dependencies (works out of the box on Windows/Linux).
  - Fast, ACID-compliant file-based storage perfectly suited for single-node deployment.
  - Easy cross-session queries for progress dashboards and historical trend analysis.

---

## 5. Multi-Day Gap & Schedule Drift Recalibration
- **The Problem**: If a student is absent for several days or falls significantly behind pace, naïve systems either do nothing (causing them to miss their target deadline) or restart the entire curriculum from scratch (frustrating the learner).
- **The Decision**:
  - When a student returns, the Learning Planner checks current_day against the expected 	arget_day for the active topic.
  - If drift &ge; 2 days:
    - Mastered topics remain untouched.
    - Deadlines for remaining topics are proportionally compressed across the remaining days (	arget_days - current_day).
    - A PlannerUpdate record is generated informing the student of the schedule recalibration.

---

## 6. Local RAG Retrieval Layer
- **Why Local TF-IDF Vectorizer?**:
  - Instant initialization with zero external vector database overhead (no Chroma/Pinecone servers required).
  - Deterministic similarity search over curated technical documentation (ackend/knowledge/rag.py).
  - Pre-grounded reference documents eliminate LLM hallucinations regarding syntax, protocol RFCs, and API behaviors.

---

## 7. Model Strategy & High Availability
- **Model Choice**: Google Gemini (gemini-3.1-flash-lite primary with automatic fallback to gemini-3.5-flash-lite).
- **Rationale**: Flash-lite models provide sub-second token generation, large context windows for RAG injection, and generous free-tier rate limits, eliminating 429 quota exhaustion during rapid interactive test cycles.
