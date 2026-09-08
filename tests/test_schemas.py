import pytest
from pydantic import ValidationError
from backend.models.schemas import (
    AssessmentResult,
    RoadmapItem,
    RoadmapItemStatus,
    QuizQuestion,
    PracticeExercise,
    EvaluationResult,
    PerformanceAnalysis,
    PaceStatus,
    RoutingDecision,
    StudyRequest,
    StudyResponse,
)


def test_schema_validations():
    """Requirement 2: Structured schema validation for agent outputs."""
    # 1. Assessment schema
    ar = AssessmentResult(
        assessed_level="beginner",
        strengths=["Quick learner"],
        knowledge_gaps=["OOP"],
        diagnostic_summary="Beginner with practical ambition"
    )
    assert ar.assessed_level == "beginner"

    # 2. RoadmapItem schema
    item = RoadmapItem(
        id=1,
        topic="Python Basics",
        description="Variables and loops",
        target_day=5,
        status=RoadmapItemStatus.in_progress
    )
    assert item.status == RoadmapItemStatus.in_progress

    # 3. EvaluationResult schema
    er = EvaluationResult(
        score=85,
        passed=True,
        answer_type="code",
        correctness="Accurate",
        missing_concepts=[],
        feedback="Well done"
    )
    assert er.score == 85
    assert er.passed is True

    # 4. PerformanceAnalysis schema
    pa = PerformanceAnalysis(
        strong_topics=["Python Basics (90%)"],
        weak_topics=[],
        mastery_percentage=90,
        current_score=90,
        pace_status=PaceStatus.ahead,
        routing_decision=RoutingDecision.advance,
        summary="Mastery achieved."
    )
    assert pa.routing_decision == RoutingDecision.advance

    # 5. Quiz & QuizResult schemas
    from backend.models.schemas import Quiz, QuizResult, QuizQuestionResult, AssessmentQuestion
    aq = AssessmentQuestion(id=1, question="What is a function?", options=["A", "B"], correct_option="A")
    assert aq.id == 1

    quiz = Quiz(topic="Functions", questions=[
        QuizQuestion(id=1, question="Def keyword?", options=["A", "B"], correct_option="B", explanation="Def")
    ])
    assert len(quiz.questions) == 1

    q_res = QuizResult(score=4, total=5, percentage=80, question_results=[], areas_to_improve=["Return values"], passed=True)
    assert q_res.percentage == 80
    assert q_res.passed is True
