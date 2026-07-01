"""Hybrid scoring: combines semantic similarity and LLM evaluation.

Per the spec, the final score for a descriptive answer blends:
- 40% semantic similarity (sentence-transformer cosine similarity)
- 60% Gemini's own evaluation score

MCQs are scored entirely by Gemini's correctness check (no similarity
blend applies, since MCQ correctness is binary, not a matter of degree).
"""

from smartevalai.services.ai.evaluator import evaluate_descriptive_answer, evaluate_mcq_answer
from smartevalai.services.evaluation.similarity import compute_similarity

SIMILARITY_WEIGHT = 0.4
LLM_WEIGHT = 0.6


class DescriptiveEvaluationResult:
    """Full evaluation result for one descriptive answer.

    Attributes:
        similarity_score: Cosine similarity in [0, 1].
        llm_score: Gemini's raw score in [0, max_marks].
        final_marks: The blended hybrid score actually awarded.
        explanation: Gemini's reasoning.
        missing_points: Concepts the student missed.
        strong_points: Concepts the student got right.
    """

    def __init__(
        self,
        similarity_score: float,
        llm_score: float,
        final_marks: float,
        explanation: str,
        missing_points: list[str],
        strong_points: list[str],
    ):
        self.similarity_score = similarity_score
        self.llm_score = llm_score
        self.final_marks = final_marks
        self.explanation = explanation
        self.missing_points = missing_points
        self.strong_points = strong_points


def score_descriptive_answer(
    question_text: str, official_answer: str, student_answer: str, max_marks: float
) -> DescriptiveEvaluationResult:
    """Score a descriptive answer using the hybrid similarity + LLM approach.

    Args:
        question_text: The question being answered.
        official_answer: The teacher-provided model answer.
        student_answer: The student's extracted answer text.
        max_marks: The maximum marks available for this question.

    Returns:
        A DescriptiveEvaluationResult with the blended final score.
    """
    similarity = compute_similarity(student_answer, official_answer)

    llm_result = evaluate_descriptive_answer(
        question_text, official_answer, student_answer, max_marks
    )
    llm_score = float(llm_result["llm_score"])

    # Both scores are normalized to [0, max_marks] before blending so the
    # weights apply on a consistent scale.
    similarity_marks = similarity * max_marks
    final_marks = (SIMILARITY_WEIGHT * similarity_marks) + (LLM_WEIGHT * llm_score)

    return DescriptiveEvaluationResult(
        similarity_score=similarity,
        llm_score=llm_score,
        final_marks=round(final_marks, 2),
        explanation=llm_result["explanation"],
        missing_points=llm_result["missing_points"],
        strong_points=llm_result["strong_points"],
    )


def score_mcq_answer(
    question_text: str, correct_option: str, student_selected_option: str, max_marks: float
) -> dict:
    """Score an MCQ answer (no similarity blend — correctness is binary).

    Returns:
        dict with keys: is_correct, final_marks, explanation.
    """
    result = evaluate_mcq_answer(question_text, correct_option, student_selected_option, max_marks)
    return {
        "is_correct": result["is_correct"],
        "final_marks": float(result["marks_awarded"]),
        "explanation": result["explanation"],
    }