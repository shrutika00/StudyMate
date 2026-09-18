import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..config import DB_PATH
from ..models.schemas import RoadmapItem, RoadmapItemStatus


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes Persistent Cross-Session Memory tables in SQLite.
    Tier 2 Memory: Survives across sessions to maintain student profiles,
    roadmaps, topic mastery levels, weak topics, and progress history.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Student Profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                learning_goal TEXT NOT NULL,
                assessed_level TEXT NOT NULL,
                target_days INTEGER NOT NULL DEFAULT 30,
                current_day INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 2. Roadmaps (Current multi-topic plans per student)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_roadmaps (
                student_id TEXT PRIMARY KEY,
                roadmap_json TEXT NOT NULL,
                current_topic_index INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (student_id)
            )
        """)

        # 3. Topic Mastery & Performance Tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                topic_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 1,
                last_assessed_at TEXT NOT NULL,
                UNIQUE(student_id, topic_name)
            )
        """)

        # 4. Learning Sessions History Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                cycle_type TEXT NOT NULL,
                quiz_score INTEGER,
                practice_score INTEGER,
                overall_score INTEGER,
                feedback TEXT,
                pace_status TEXT,
                routing_decision TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # 5. Active Quiz Memory per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_active_quizzes (
                student_id TEXT PRIMARY KEY,
                quiz_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()


def save_or_update_student(
    student_id: str,
    learning_goal: str,
    assessed_level: str,
    target_days: int = 30,
    current_day: int = 1
) -> None:
    """Save or update student long-term profile in persistent memory."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (student_id, learning_goal, assessed_level, target_days, current_day, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                learning_goal = excluded.learning_goal,
                assessed_level = excluded.assessed_level,
                target_days = excluded.target_days,
                current_day = excluded.current_day,
                updated_at = excluded.updated_at
        """, (student_id, learning_goal, assessed_level, target_days, current_day, now, now))
        conn.commit()


def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve persistent student profile."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_roadmap(student_id: str, roadmap: List[Dict[str, Any]], current_topic_index: int = 0) -> None:
    """Persist student learning roadmap across sessions."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO student_roadmaps (student_id, roadmap_json, current_topic_index, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                roadmap_json = excluded.roadmap_json,
                current_topic_index = excluded.current_topic_index,
                updated_at = excluded.updated_at
        """, (student_id, json.dumps(roadmap), current_topic_index, now))
        conn.commit()


def get_roadmap(student_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve student persistent roadmap and active topic pointer."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student_roadmaps WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "student_id": row["student_id"],
            "roadmap": json.loads(row["roadmap_json"]),
            "current_topic_index": row["current_topic_index"],
            "updated_at": row["updated_at"]
        }


def clear_student_session(student_id: str) -> None:
    """Clear active roadmap and active quizzes for student when starting a fresh goal."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_roadmaps WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM student_active_quizzes WHERE student_id = ?", (student_id,))
        conn.commit()


def record_topic_mastery(student_id: str, topic_name: str, score: int, status: str) -> None:
    """Update topic mastery record for persistent tracking of strong and weak areas."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO topic_mastery (student_id, topic_name, score, status, attempts, last_assessed_at)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(student_id, topic_name) DO UPDATE SET
                score = excluded.score,
                status = excluded.status,
                attempts = attempts + 1,
                last_assessed_at = excluded.last_assessed_at
        """, (student_id, topic_name, score, status, now))
        conn.commit()


def get_student_mastery(student_id: str) -> List[Dict[str, Any]]:
    """Retrieve persistent mastery records across all topics for a student."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topic_mastery WHERE student_id = ? ORDER BY id ASC", (student_id,))
        return [dict(r) for r in cursor.fetchall()]


def save_session_record(
    student_id: str,
    topic: str,
    cycle_type: str,
    quiz_score: int,
    practice_score: int,
    overall_score: int,
    feedback: str,
    pace_status: str,
    routing_decision: str,
    session_id: Optional[str] = None
) -> int:
    """Save an immutable history log of a completed learning cycle."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    sid = session_id or str(uuid.uuid4())
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO learning_sessions (
                session_id, student_id, topic, cycle_type, quiz_score,
                practice_score, overall_score, feedback, pace_status, routing_decision, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sid, student_id, topic, cycle_type, quiz_score,
            practice_score, overall_score, feedback, pace_status, routing_decision, now
        ))
        conn.commit()
        return cursor.lastrowid


def get_student_sessions(student_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve historical learning cycles for a student."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM learning_sessions WHERE student_id = ? ORDER BY id DESC LIMIT ?
        """, (student_id, limit))
        return [dict(r) for r in cursor.fetchall()]


def get_recent_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve all recent learning sessions globally for UI display."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learning_sessions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]


def save_active_quiz(student_id: str, quiz_data: Dict[str, Any]) -> None:
    """Save active topic quiz to persistent memory so submissions grade against the exact same questions."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO student_active_quizzes (student_id, quiz_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                quiz_json = excluded.quiz_json,
                updated_at = excluded.updated_at
        """, (student_id, json.dumps(quiz_data), now))
        conn.commit()


def get_active_quiz(student_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the currently active quiz for a student."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quiz_json FROM student_active_quizzes WHERE student_id = ?
        """, (student_id,))
        row = cursor.fetchone()
        if row and row["quiz_json"]:
            try:
                return json.loads(row["quiz_json"])
            except Exception:
                return None
    return None


def clear_student_session(student_id: str) -> None:
    """Clear active roadmap, active quizzes, and student profile when starting a fresh goal."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_active_quizzes WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM student_roadmaps WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()

