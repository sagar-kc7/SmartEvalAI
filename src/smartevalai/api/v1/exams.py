"""Exam and question API routes (teacher-only for creation)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from smartevalai.core.deps import require_teacher
from smartevalai.db.session import get_session
from smartevalai.models.user import User
from smartevalai.schemas.exam import (
    ExamCreate,
    ExamRead,
    QuestionCreate,
    QuestionRead,
    SubjectCreate,
    SubjectRead,
)
from smartevalai.services.exam_service import (
    create_exam,
    create_question,
    create_subject,
    list_questions_for_exam,
)

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("/subjects", response_model=SubjectRead, status_code=201)
def create_subject_route(
    payload: SubjectCreate,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> SubjectRead:
    """Create a subject (or return the existing one with that name)."""
    subject = create_subject(session, payload)
    return SubjectRead.model_validate(subject)


@router.post("", response_model=ExamRead, status_code=201)
def create_exam_route(
    payload: ExamCreate,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> ExamRead:
    """Create a new exam owned by the authenticated teacher."""
    exam = create_exam(session, payload, teacher)
    return ExamRead.model_validate(exam)


@router.post("/{exam_id}/questions", response_model=QuestionRead, status_code=201)
def create_question_route(
    exam_id: int,
    payload: QuestionCreate,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> QuestionRead:
    """Add a question (MCQ or descriptive) to an exam."""
    question = create_question(session, exam_id, payload, teacher)
    return QuestionRead.model_validate(question)


@router.get("/{exam_id}/questions", response_model=list[QuestionRead])
def list_questions_route(
    exam_id: int,
    session: Session = Depends(get_session),
) -> list[QuestionRead]:
    """List all questions for an exam (answer keys excluded from response)."""
    questions = list_questions_for_exam(session, exam_id)
    return [QuestionRead.model_validate(q) for q in questions]