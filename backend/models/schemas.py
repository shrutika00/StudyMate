from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class RoadmapItemStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    mastered = "mastered"
    reinforcing = "reinforcing"


class PaceStatus(str, Enum):
    ahead = "ahead"
    on_track = "on_track"
    behind = "behind"


class RoutingDecision(str, Enum):
    advance = "ADVANCE"
    reinforce = "REINFORCE"
    full_replan = "FULL_REPLAN"
    complete = "COMPLETE"


# ==========================================
# 1. Assessment Schemas
# ==========================================
class AssessmentQuestion(BaseModel):
    id: int
    question: str
    options: List[str] = Field(default_factory=list)
    correct_option: str
    explanation: Optional[str] = None


class AssessmentResult(BaseModel):
    assessed_level: DifficultyLevel
    strengths: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    diagnostic_summary: str
    diagnostic_score: Optional[int] = None
    questions: List[AssessmentQuestion] = Field(default_factory=list)


# ==========================================
# 2. Learning Plan Schemas
# ==========================================
class RoadmapItem(BaseModel):
    id: int
    topic: str
    description: str = ""
    target_day: int
    status: RoadmapItemStatus = RoadmapItemStatus.pending


class LearningPlan(BaseModel):
    goal: str
    target_days: int = 30
    roadmap: List[RoadmapItem] = Field(default_factory=list)


# ==========================================
# 3. Teaching / Concept Schemas
# ==========================================
class TeachingContent(BaseModel):
    topic: str
    explanation: str
    key_points: List[str] = Field(default_factory=list)
    grounded_sources: List[str] = Field(default_factory=list)


# ==========================================
# 4. Quiz Schemas (Multi-question 3-5)
# ==========================================
class QuizQuestion(BaseModel):
    id: int = 1
    question: str
    options: List[str] = Field(default_factory=list)
    correct_option: str
    explanation: str
    question_type: str = "multiple_choice"


class Quiz(BaseModel):
    topic: str
    questions: List[QuizQuestion] = Field(default_factory=list)


class QuizQuestionResult(BaseModel):
    question_id: int
    question: str
    student_answer: str
    correct_option: str
    is_correct: bool
    explanation: str


class QuizResult(BaseModel):
    score: int
    total: int
    percentage: int
    question_results: List[QuizQuestionResult] = Field(default_factory=list)
    areas_to_improve: List[str] = Field(default_factory=list)
    passed: bool = False


# ==========================================
# 5. Practice Schemas
# ==========================================
class PracticeExercise(BaseModel):
    title: str
    problem_statement: str
    starter_code: str
    expected_output: str
    hints: List[str] = Field(default_factory=list)


# ==========================================
# 6. Evaluation Schemas
# ==========================================
class EvaluationResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Overall score between 0 and 100")
    quiz_score: Optional[int] = None
    practice_score: Optional[int] = None
    passed: bool
    answer_type: str
    correctness: str
    missing_concepts: List[str] = Field(default_factory=list)
    feedback: str


# ==========================================
# 7. Performance & Planner Update Schemas
# ==========================================
class PerformanceAnalysis(BaseModel):
    strong_topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    mastery_percentage: int = Field(default=0, ge=0, le=100)
    current_score: int = Field(default=0, ge=0, le=100)
    pace_status: PaceStatus = PaceStatus.on_track
    routing_decision: RoutingDecision = RoutingDecision.advance
    summary: str


class PlannerUpdate(BaseModel):
    reason: str
    changes_summary: str
    updated_roadmap: List[RoadmapItem] = Field(default_factory=list)


# ==========================================
# 8. API Requests & Responses
# ==========================================
class CodeExecutionRequest(BaseModel):
    code: str
    timeout_seconds: Optional[int] = Field(default=5, ge=1, le=15)


class CodeExecutionResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    error: Optional[str] = None


class StudyRequest(BaseModel):
    student_id: Optional[str] = Field(default="student_default")
    learning_goal: Optional[str] = Field(default="I want to learn Python for backend development in 30 days")
    target_days: Optional[int] = Field(default=30)
    current_day: Optional[int] = Field(default=None)
    assessed_level: Optional[str] = Field(default=None)
    quiz_answer: Optional[str] = Field(default=None)
    quiz_answers: Optional[Dict[int, str]] = Field(default=None)
    practice_code: Optional[str] = Field(default=None)
    action: Optional[str] = Field(default="auto")


class StudyResponse(BaseModel):
    student_id: str
    learning_goal: str
    assessed_level: str
    current_topic: str
    current_day: int
    target_days: int
    roadmap: List[RoadmapItem]
    assessment: Optional[AssessmentResult] = None
    teaching: Optional[TeachingContent] = None
    quiz: Optional[QuizQuestion] = None
    quiz_multi: Optional[Quiz] = None
    quiz_result: Optional[QuizResult] = None
    practice: Optional[PracticeExercise] = None
    evaluation: Optional[EvaluationResult] = None
    performance: Optional[PerformanceAnalysis] = None
    planner_update: Optional[PlannerUpdate] = None
    routing_decision: str
    workflow_history: List[str] = Field(default_factory=list)
    cycle_count: int = 0
    status: str
