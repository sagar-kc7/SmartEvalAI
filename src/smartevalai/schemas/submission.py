"""Request/response schemas for student submissions and evaluation results."""

from pydantic import BaseModel


class SubmissionRead(BaseModel):
    """Public representation of a student's uploaded answer sheet."""

    model_config = {"from_attributes": True}

    id: int
    exam_id: int
    student_id: int
    file_path: str


class EvaluationRead(BaseModel):
    """Public representation of one question's evaluation result."""

    model_config = {"from_attributes": True}

    id: int
    question_id: int
    similarity_score: float | None
    llm_score: float | None
    final_marks: float
    explanation: str | None
    missing_points: str | None  # JSON-encoded list[str]
    strong_points: str | None  # JSON-encoded list[str]


class FeedbackRead(BaseModel):
    """Public representation of generated feedback for one evaluation."""

    model_config = {"from_attributes": True}

    id: int
    evaluation_id: int
    content: str


class SubmissionResultRead(BaseModel):
    """Combined result: a submission plus all its evaluations and feedback."""

    submission: SubmissionRead
    evaluations: list[EvaluationRead]
    feedback: list[FeedbackRead]