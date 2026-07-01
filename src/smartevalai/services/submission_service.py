"""Orchestrates the full submission -> OCR -> evaluation -> feedback pipeline."""

import json

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session, select

from smartevalai.models.exam import Question, QuestionType
from smartevalai.models.submission import Evaluation, Feedback, OCRResult, StudentSubmission
from smartevalai.models.user import User
from smartevalai.services.ai.evaluator import generate_feedback
from smartevalai.services.exam_service import get_exam_or_404
from smartevalai.services.ocr.pipeline import run_ocr_pipeline
from smartevalai.services.evaluation.scoring import score_descriptive_answer, score_mcq_answer
from smartevalai.utils.storage import save_upload


def upload_submission(
    session: Session, exam_id: int, file: UploadFile, student: User
) -> StudentSubmission:
    """Save an uploaded answer sheet and create a StudentSubmission record.

    This step only handles the upload itself — OCR and evaluation are
    triggered separately via `process_submission`, since OCR/Gemini calls
    are slow and shouldn't block the upload response.
    """
    get_exam_or_404(session, exam_id)

    file_path = save_upload(file, subfolder="submissions")

    submission = StudentSubmission(
        exam_id=exam_id,
        student_id=student.id,
        file_path=file_path,
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission


def _get_submission_or_404(session: Session, submission_id: int) -> StudentSubmission:
    submission = session.get(StudentSubmission, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found."
        )
    return submission


def process_submission(session: Session, submission_id: int) -> StudentSubmission:
    """Run the full pipeline for a submission: OCR -> evaluate each question -> feedback.

    Args:
        session: Active DB session.
        submission_id: The StudentSubmission to process.

    Returns:
        The same submission, after evaluations and feedback have been created.

    Raises:
        HTTPException: 404 if the submission doesn't exist.
        HTTPException: 409 if the submission was already processed.
    """
    submission = _get_submission_or_404(session, submission_id)

    existing_ocr = session.exec(
        select(OCRResult).where(OCRResult.submission_id == submission_id)
    ).first()
    if existing_ocr is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This submission has already been processed.",
        )

    # Step 1: OCR
    ocr_result = run_ocr_pipeline(submission.file_path)
    ocr_record = OCRResult(
        submission_id=submission_id,
        raw_text=ocr_result.raw_text,
        cleaned_text=ocr_result.cleaned_text,
        answers_by_question=json.dumps(ocr_result.answers_by_question),
    )
    session.add(ocr_record)
    session.commit()

    # Step 2: Evaluate each question against the student's extracted answer
    questions = session.exec(
        select(Question).where(Question.exam_id == submission.exam_id)
    ).all()

    for question in questions:
        # Match by the teacher-defined question_number (e.g. "1", "2a"),
        # which is what students actually write on their answer sheets —
        # not the internal database id.
        student_answer = ocr_result.answers_by_question.get(question.question_number, "")

        # Fallback only if no matching number was found at all: assume OCR
        # and DB questions are in the same order. This is a weaker
        # assumption and should be rare once question_number is set correctly.
        if not student_answer and ocr_result.answers_by_question:
            ordered_answers = list(ocr_result.answers_by_question.values())
            position = questions.index(question)
            if position < len(ordered_answers):
                student_answer = ordered_answers[position]

        if question.question_type == QuestionType.MCQ:
            options = json.loads(question.options) if question.options else []
            scored = score_mcq_answer(
                question_text=question.question_text,
                correct_option=question.correct_option,
                student_selected_option=student_answer,
                max_marks=question.max_marks,
            )
            evaluation = Evaluation(
                submission_id=submission_id,
                question_id=question.id,
                similarity_score=None,
                llm_score=None,
                final_marks=scored["final_marks"],
                explanation=scored["explanation"],
                missing_points=None,
                strong_points=None,
            )
        else:  # descriptive
            scored = score_descriptive_answer(
                question_text=question.question_text,
                official_answer=question.official_answer,
                student_answer=student_answer,
                max_marks=question.max_marks,
            )
            evaluation = Evaluation(
                submission_id=submission_id,
                question_id=question.id,
                similarity_score=scored.similarity_score,
                llm_score=scored.llm_score,
                final_marks=scored.final_marks,
                explanation=scored.explanation,
                missing_points=json.dumps(scored.missing_points),
                strong_points=json.dumps(scored.strong_points),
            )

        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)

        # Step 3: Generate personalized feedback for this evaluation
        missing = json.loads(evaluation.missing_points) if evaluation.missing_points else []
        strong = json.loads(evaluation.strong_points) if evaluation.strong_points else []
        feedback_text = generate_feedback(
            question_text=question.question_text,
            student_answer=student_answer,
            missing_points=missing,
            strong_points=strong,
        )
        feedback = Feedback(evaluation_id=evaluation.id, content=feedback_text)
        session.add(feedback)
        session.commit()

    session.refresh(submission)
    return submission


def get_submission_results(session: Session, submission_id: int) -> dict:
    """Fetch a submission along with all its evaluations and feedback.

    Returns:
        dict with keys: submission, evaluations, feedback.
    """
    submission = _get_submission_or_404(session, submission_id)
    evaluations = list(
        session.exec(select(Evaluation).where(Evaluation.submission_id == submission_id)).all()
    )
    evaluation_ids = [e.id for e in evaluations]
    feedback = []
    if evaluation_ids:
        feedback = list(
            session.exec(
                select(Feedback).where(Feedback.evaluation_id.in_(evaluation_ids))
            ).all()
        )

    return {"submission": submission, "evaluations": evaluations, "feedback": feedback}