"""Report download and analytics API routes (teacher-only)."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlmodel import Session

from smartevalai.core.deps import require_teacher
from smartevalai.db.session import get_session
from smartevalai.models.user import User
from smartevalai.services.analytics_service import get_exam_analytics
from smartevalai.services.exam_service import get_exam_or_404
from smartevalai.services.report_service import (
    gather_report_rows,
    generate_csv_report,
    generate_pdf_report,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/exams/{exam_id}/csv")
def download_csv_report(
    exam_id: int,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> Response:
    """Download a CSV evaluation report for all submissions on an exam."""
    rows = gather_report_rows(session, exam_id)
    csv_content = generate_csv_report(rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=exam_{exam_id}_report.csv"},
    )


@router.get("/exams/{exam_id}/pdf")
def download_pdf_report(
    exam_id: int,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> Response:
    """Download a PDF evaluation report for all submissions on an exam."""
    exam = get_exam_or_404(session, exam_id)
    rows = gather_report_rows(session, exam_id)
    pdf_content = generate_pdf_report(rows, exam_title=exam.title)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=exam_{exam_id}_report.pdf"},
    )


@router.get("/exams/{exam_id}/analytics")
def get_analytics(
    exam_id: int,
    teacher: User = Depends(require_teacher),
    session: Session = Depends(get_session),
) -> dict:
    """Get summary analytics for an exam (averages, score distribution)."""
    return get_exam_analytics(session, exam_id)