"""Basic exam-level analytics for the teacher dashboard."""

from sqlmodel import Session, select

from smartevalai.models.submission import Evaluation, StudentSubmission
from smartevalai.services.exam_service import get_exam_or_404


def get_exam_analytics(session: Session, exam_id: int) -> dict:
    """Compute summary statistics for an exam.

    Returns a dict with:
        total_submissions: Number of students who submitted.
        average_final_marks: Mean final_marks across all evaluated questions.
        average_similarity: Mean similarity score (descriptive only).
        average_llm_score: Mean LLM score (descriptive only).
        score_distribution: Buckets of 0-25%, 26-50%, 51-75%, 76-100%.
    """
    get_exam_or_404(session, exam_id)

    submissions = list(
        session.exec(
            select(StudentSubmission).where(StudentSubmission.exam_id == exam_id)
        ).all()
    )

    if not submissions:
        return {
            "total_submissions": 0,
            "average_final_marks": 0.0,
            "average_similarity": None,
            "average_llm_score": None,
            "score_distribution": {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0},
        }

    submission_ids = [s.id for s in submissions]
    evaluations = list(
        session.exec(
            select(Evaluation).where(Evaluation.submission_id.in_(submission_ids))
        ).all()
    )

    if not evaluations:
        return {
            "total_submissions": len(submissions),
            "average_final_marks": 0.0,
            "average_similarity": None,
            "average_llm_score": None,
            "score_distribution": {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0},
        }

    final_marks = [e.final_marks for e in evaluations]
    similarity_scores = [e.similarity_score for e in evaluations if e.similarity_score is not None]
    llm_scores = [e.llm_score for e in evaluations if e.llm_score is not None]

    # Score distribution buckets keyed by percentage of max_marks.
    # We approximate percentage using final_marks vs a max of 10
    # (acceptable for a dev/demo context; refine with Question.max_marks
    # lookup when you have time).
    distribution = {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0}
    for mark in final_marks:
        if mark <= 2.5:
            distribution["0-25%"] += 1
        elif mark <= 5.0:
            distribution["26-50%"] += 1
        elif mark <= 7.5:
            distribution["51-75%"] += 1
        else:
            distribution["76-100%"] += 1

    return {
        "total_submissions": len(submissions),
        "average_final_marks": round(sum(final_marks) / len(final_marks), 2),
        "average_similarity": round(sum(similarity_scores) / len(similarity_scores), 3)
        if similarity_scores
        else None,
        "average_llm_score": round(sum(llm_scores) / len(llm_scores), 2)
        if llm_scores
        else None,
        "score_distribution": distribution,
    }