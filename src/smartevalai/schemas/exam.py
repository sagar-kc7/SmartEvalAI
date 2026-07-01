"""Request/response schemas for exams and questions."""

from pydantic import BaseModel

from smartevalai.models.exam import QuestionType


class SubjectCreate(BaseModel):
    """Payload for creating a subject."""

    name: str


class SubjectRead(BaseModel):
    """Public representation of a subject."""

    model_config = {"from_attributes": True}

    id: int
    name: str


class ExamCreate(BaseModel):
    """Payload for creating an exam."""

    title: str
    subject_id: int


class ExamRead(BaseModel):
    """Public representation of an exam."""

    model_config = {"from_attributes": True}

    id: int
    title: str
    subject_id: int
    teacher_id: int
    question_paper_path: str | None


class QuestionCreate(BaseModel):
    """Payload for creating a question within an exam.

    For MCQ: `options` and `correct_option` are required.
    For descriptive: `official_answer` is required.
    """

    question_number: str
    question_text: str
    question_type: QuestionType
    max_marks: float = 1.0
    options: list[str] | None = None
    correct_option: str | None = None
    official_answer: str | None = None


class QuestionRead(BaseModel):
    """Public representation of a question (hides the answer key from students)."""

    model_config = {"from_attributes": True}

    id: int
    exam_id: int
    question_number: str
    question_text: str
    question_type: QuestionType
    max_marks: float
    options: str | None  # JSON-encoded list, decoded client-side if needed