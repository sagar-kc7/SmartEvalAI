"""Submission upload, processing, and results API routes."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from smartevalai.core.deps import get_current_user, require_student
from smartevalai.db.session import get_session
from smartevalai.models.user import User
from smartevalai.schemas.submission import (
    EvaluationRead,
    FeedbackRead,
    SubmissionRead,
    SubmissionResultRead,
)
from smartevalai.services.submission_service import (
    get_submission_results,
    process_submission,
    upload_submission,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/exams/{exam_id}/upload", response_model=SubmissionRead, status_code=201)
def upload_submission_route(
    exam_id: int,
    file: UploadFile = File(...),
    student: User = Depends(require_student),
    session: Session = Depends(get_session),
) -> SubmissionRead:
    """Upload an answer sheet (PDF/JPG/PNG) for a given exam."""
    submission = upload_submission(session, exam_id, file, student)
    return SubmissionRead.model_validate(submission)


@router.post("/{submission_id}/process", response_model=SubmissionRead)
def process_submission_route(
    submission_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SubmissionRead:
    """Run OCR + evaluation + feedback generation for an uploaded submission.

    Open to either role for now (a teacher may want to trigger grading on
    a student's behalf); tighten this with `require_teacher` later if you
    want grading to be teacher-initiated only.
    """
    submission = process_submission(session, submission_id)
    return SubmissionRead.model_validate(submission)


@router.get("/{submission_id}/results", response_model=SubmissionResultRead)
def get_results_route(
    submission_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SubmissionResultRead:
    """Fetch the full evaluation + feedback results for a submission."""
    data = get_submission_results(session, submission_id)
    return SubmissionResultRead(
        submission=SubmissionRead.model_validate(data["submission"]),
        evaluations=[EvaluationRead.model_validate(e) for e in data["evaluations"]],
        feedback=[FeedbackRead.model_validate(f) for f in data["feedback"]],
    )