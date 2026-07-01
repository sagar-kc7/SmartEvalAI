"""Generates CSV and PDF reports of exam results for teachers."""

import csv
import io
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlmodel import Session, select

from smartevalai.models.exam import Exam, Question
from smartevalai.models.submission import Evaluation, Feedback, StudentSubmission
from smartevalai.models.user import User
from smartevalai.services.exam_service import get_exam_or_404


class ReportRow:
    """One row of report data: a single question's evaluation for one student.

    Attributes:
        student_name: The student's display name.
        question_text: The question being evaluated.
        marks: Final marks awarded.
        max_marks: Maximum marks possible for the question.
        similarity_score: Cosine similarity (None for MCQs).
        llm_score: Gemini's raw score (None for MCQs).
        feedback: Personalized feedback text.
    """

    def __init__(
        self,
        student_name: str,
        question_text: str,
        marks: float,
        max_marks: float,
        similarity_score: float | None,
        llm_score: float | None,
        feedback: str,
    ):
        self.student_name = student_name
        self.question_text = question_text
        self.marks = marks
        self.max_marks = max_marks
        self.similarity_score = similarity_score
        self.llm_score = llm_score
        self.feedback = feedback


def gather_report_rows(session: Session, exam_id: int) -> list[ReportRow]:
    """Gather all evaluation data for an exam, one row per (student, question).

    Args:
        session: Active DB session.
        exam_id: The exam to report on.

    Returns:
        A list of ReportRow, one per evaluated question per student.
    """
    get_exam_or_404(session, exam_id)

    submissions = list(
        session.exec(select(StudentSubmission).where(StudentSubmission.exam_id == exam_id)).all()
    )

    rows: list[ReportRow] = []
    for submission in submissions:
        student = session.get(User, submission.student_id)
        evaluations = list(
            session.exec(
                select(Evaluation).where(Evaluation.submission_id == submission.id)
            ).all()
        )

        for evaluation in evaluations:
            question = session.get(Question, evaluation.question_id)
            feedback = session.exec(
                select(Feedback).where(Feedback.evaluation_id == evaluation.id)
            ).first()

            rows.append(
                ReportRow(
                    student_name=student.full_name if student else "Unknown",
                    question_text=question.question_text if question else "Unknown",
                    marks=evaluation.final_marks,
                    max_marks=question.max_marks if question else 0.0,
                    similarity_score=evaluation.similarity_score,
                    llm_score=evaluation.llm_score,
                    feedback=feedback.content if feedback else "",
                )
            )

    return rows


def generate_csv_report(rows: list[ReportRow]) -> str:
    """Render report rows as CSV text.

    Returns:
        The full CSV content as a string.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Student Name", "Question", "Marks", "Max Marks", "Similarity Score", "AI Score", "Feedback"]
    )
    for row in rows:
        writer.writerow(
            [
                row.student_name,
                row.question_text,
                row.marks,
                row.max_marks,
                row.similarity_score if row.similarity_score is not None else "",
                row.llm_score if row.llm_score is not None else "",
                row.feedback,
            ]
        )
    return buffer.getvalue()


def generate_pdf_report(rows: list[ReportRow], exam_title: str) -> bytes:
    """Render report rows as a formatted PDF.

    Returns:
        The PDF file content as raw bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Evaluation Report: {exam_title}", styles["Title"]))
    elements.append(Spacer(1, 12))

    table_data = [["Student", "Question", "Marks", "Similarity", "AI Score", "Feedback"]]
    for row in rows:
        table_data.append(
            [
                row.student_name,
                Paragraph(row.question_text, styles["BodyText"]),
                f"{row.marks}/{row.max_marks}",
                f"{row.similarity_score:.2f}" if row.similarity_score is not None else "—",
                f"{row.llm_score:.2f}" if row.llm_score is not None else "—",
                Paragraph(row.feedback, styles["BodyText"]),
            ]
        )

    table = Table(table_data, repeatRows=1, colWidths=[80, 150, 60, 70, 70, 220])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()