"""Business logic for creating and reading subjects, exams, and questions."""

import json

from fastapi import HTTPException, status
from sqlmodel import Session, select

from smartevalai.models.exam import Exam, Question, Subject
from smartevalai.models.user import User
from smartevalai.schemas.exam import ExamCreate, QuestionCreate, SubjectCreate


def create_subject(session: Session, payload: SubjectCreate) -> Subject:
    """Create a subject, or return the existing one if the name already exists.

    Subjects are shared across teachers (e.g. "Data Structures" should be
    one row, not duplicated per teacher), so we treat this as get-or-create.
    """
    existing = session.exec(select(Subject).where(Subject.name == payload.name)).first()
    if existing is not None:
        return existing

    subject = Subject(name=payload.name)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


def create_exam(session: Session, payload: ExamCreate, teacher: User) -> Exam:
    """Create a new exam owned by the given teacher.

    Raises:
        HTTPException: 404 if the subject_id doesn't exist.
    """
    subject = session.get(Subject, payload.subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )

    exam = Exam(title=payload.title, subject_id=payload.subject_id, teacher_id=teacher.id)
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


def get_exam_or_404(session: Session, exam_id: int) -> Exam:
    """Fetch an exam by id, raising 404 if it doesn't exist."""
    exam = session.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")
    return exam


def create_question(session: Session, exam_id: int, payload: QuestionCreate, teacher: User) -> Question:
    """Add a question to an exam.

    Raises:
        HTTPException: 404 if the exam doesn't exist; 403 if the exam
            belongs to a different teacher; 400 if required fields for the
            given question type are missing.
    """
    exam = get_exam_or_404(session, exam_id)

    if exam.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add questions to your own exams.",
        )

    if payload.question_type.value == "mcq":
        if not payload.options or not payload.correct_option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MCQ questions require 'options' and 'correct_option'.",
            )
    else:  # descriptive
        if not payload.official_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Descriptive questions require 'official_answer'.",
            )

    question = Question(
        exam_id=exam_id,
        question_number=payload.question_number,
        question_text=payload.question_text,
        question_type=payload.question_type,
        max_marks=payload.max_marks,
        options=json.dumps(payload.options) if payload.options else None,
        correct_option=payload.correct_option,
        official_answer=payload.official_answer,
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


def list_questions_for_exam(session: Session, exam_id: int) -> list[Question]:
    """Return all questions belonging to an exam."""
    get_exam_or_404(session, exam_id)
    return list(session.exec(select(Question).where(Question.exam_id == exam_id)).all())