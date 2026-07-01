"""High-level evaluation functions combining prompts with the Gemini client."""

from smartevalai.services.ai.gemini_client import generate_json
from smartevalai.services.ai.prompts import (
    build_descriptive_evaluation_prompt,
    build_feedback_prompt,
    build_mcq_evaluation_prompt,
)


def evaluate_descriptive_answer(
    question_text: str, official_answer: str, student_answer: str, max_marks: float
) -> dict:
    """Evaluate a descriptive answer using Gemini.

    Returns:
        dict with keys: llm_score, explanation, missing_points, strong_points.
    """
    prompt = build_descriptive_evaluation_prompt(
        question_text, official_answer, student_answer, max_marks
    )
    return generate_json(prompt)


def evaluate_mcq_answer(
    question_text: str, correct_option: str, student_selected_option: str, max_marks: float
) -> dict:
    """Evaluate an MCQ answer using Gemini.

    Returns:
        dict with keys: is_correct, marks_awarded, explanation.
    """
    prompt = build_mcq_evaluation_prompt(
        question_text, correct_option, student_selected_option, max_marks
    )
    return generate_json(prompt)


def generate_feedback(
    question_text: str,
    student_answer: str,
    missing_points: list[str],
    strong_points: list[str],
) -> str:
    """Generate personalized feedback text for a student's answer.

    Returns:
        The feedback text as a plain string.
    """
    prompt = build_feedback_prompt(question_text, student_answer, missing_points, strong_points)
    result = generate_json(prompt)
    return result["feedback"]