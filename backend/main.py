import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Suppress harmless Google GenAI SDK AFC advisory warnings
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, check_gemini_key, ConfigurationError, GEMINI_API_KEY
from .models.schemas import (
    StudyRequest,
    StudyResponse,
    AssessmentResult,
    AssessmentQuestion,
    Quiz,
    QuizResult,
    TeachingContent,
    PracticeExercise,
    EvaluationResult,
    PerformanceAnalysis,
    RoadmapItem
)
from .state import StudyState
from .graph import study_graph
from .database.db import (
    init_db,
    get_student,
    get_roadmap,
    get_student_mastery,
    get_student_sessions,
    get_recent_history,
    save_or_update_student,
    save_roadmap
)
from .tools.registry import tool_registry

# Initialize SQLite Tier 2 Persistent Memory on startup
init_db()

app = FastAPI(
    title="StudyMate API",
    description="Personalized AI Learning Agent powered by LangGraph cyclic replanning and Google Gemini",
    version="2.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", summary="Serve student web interface")
def serve_home():
    """Serves the single-page StudyMate interface."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Welcome to StudyMate API. Visit /docs for API documentation."}


@app.get("/health", summary="Service health check")
def health_check():
    """Health check reporting service readiness and Gemini API configuration status."""
    is_gemini_configured = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
    return {
        "status": "healthy",
        "service": "StudyMate",
        "version": "2.0.0",
        "gemini_configured": is_gemini_configured,
        "tools_registered": [t["name"] for t in tool_registry.list_tools()]
    }


@app.post("/study", response_model=StudyResponse, summary="Execute personalized learning cycle")
def study_endpoint(request: StudyRequest):
    """
    Executes an autonomous personalized learning cycle through the 8-agent LangGraph pipeline:
    Assessment -> Learning Planner -> Tutor -> Quiz -> Practice -> Evaluation -> Performance ->
    Conditional Routing (ADVANCE / REINFORCE / FULL_REPLAN) -> Finalizer.
    """
    from .agents.llm import _TEST_LLM_OVERRIDE
    if _TEST_LLM_OVERRIDE is None:
        try:
            check_gemini_key()
        except ConfigurationError as ce:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(ce)
            )

    student_id = request.student_id or "student_default"
    learning_goal = request.learning_goal or "I want to learn Python for backend development in 30 days"
    target_days = request.target_days or 30

    initial_state: StudyState = {
        "student_id": student_id,
        "learning_goal": learning_goal,
        "target_days": target_days,
        "current_day": 1,
        "assessed_level": request.assessed_level or "beginner",
        "assessment": None,
        "diagnostic_answers": request.quiz_answers,
        "roadmap": [],
        "current_topic_index": 0,
        "current_topic": "",
        "retrieved_context": [],
        "teaching": None,
        "quiz": None,
        "quiz_multi": None,
        "practice": None,
        "student_quiz_answer": request.quiz_answer,
        "student_quiz_answers": request.quiz_answers,
        "student_practice_code": request.practice_code,
        "evaluation": None,
        "performance": None,
        "planner_update": None,
        "routing_decision": "ADVANCE",
        "cycle_count": 0,
        "max_cycles": 1 if request.action in ["start", "assess_submit", "quiz_submit", "practice_submit"] else 2,
        "workflow_history": [],
        "status": "started",
        "errors": []
    }

    try:
        final_state = study_graph.invoke(initial_state)
    except Exception as e:
        if "GEMINI_API_KEY" in str(e) or isinstance(e, ConfigurationError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Configuration Error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution error: {str(e)}"
        )

    final_answer_data = final_state.get("final_answer")
    if not final_answer_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph execution completed without producing a final answer."
        )

    return StudyResponse(**final_answer_data)


@app.get("/history", summary="Get recent study sessions")
def history_endpoint(student_id: Optional[str] = None, limit: int = 20):
    """Retrieve historical learning sessions from Tier 2 Persistent Memory."""
    if student_id:
        return get_student_sessions(student_id, limit=limit)
    return get_recent_history(limit=limit)


@app.get("/progress", summary="Get student progress and topic mastery")
def progress_endpoint(student_id: str = Query(default="student_default")):
    """
    Retrieve persistent student learning progress, active roadmap,
    and topic mastery metrics.
    """
    profile = get_student(student_id)
    roadmap_info = get_roadmap(student_id)
    mastery = get_student_mastery(student_id)

    return {
        "student_id": student_id,
        "profile": profile,
        "roadmap": roadmap_info["roadmap"] if roadmap_info else [],
        "current_topic_index": roadmap_info["current_topic_index"] if roadmap_info else 0,
        "mastery_records": mastery
    }
