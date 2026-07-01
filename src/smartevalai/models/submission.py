"""Models for the student submission -> OCR -> evaluation -> feedback pipeline."""

from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class StudentSubmission(SQLModel, table=True):
    """A student's uploaded answer sheet for a given exam.

    Attributes:
        file_path: Path to the raw uploaded PDF/image on disk.
    """

    id: int | None = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id")
    student_id: int = Field(foreign_key="user.id")
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    exam: "Exam" = Relationship(back_populates="submissions")  # noqa: F821
    student: "User" = Relationship(back_populates="submissions")  # noqa: F821
    ocr_result: "OCRResult" = Relationship(back_populates="submission")
    evaluations: list["Evaluation"] = Relationship(back_populates="submission")


class OCRResult(SQLModel, table=True):
    """Raw and cleaned text extracted from a submission via OCR.

    Attributes:
        raw_text: Unprocessed OCR output.
        cleaned_text: Text after noise removal / cleanup.
        answers_by_question: JSON-encoded dict mapping question number to
            the student's extracted answer text for that question.
    """

    id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="studentsubmission.id", unique=True)
    raw_text: str
    cleaned_text: str
    answers_by_question: str  # JSON-encoded: {"1": "...", "2": "..."}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    submission: StudentSubmission = Relationship(back_populates="ocr_result")


class Evaluation(SQLModel, table=True):
    """The scoring result for one student's answer to one question.

    Attributes:
        similarity_score: Cosine similarity between student and official
            answer embeddings, in [0, 1].
        llm_score: Gemini's own score for this answer, in [0, max_marks].
        final_marks: The blended hybrid score actually awarded.
        explanation: Gemini's reasoning for the score.
        missing_points: JSON-encoded list of concepts the student missed.
        strong_points: JSON-encoded list of things the student got right.
    """

    id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="studentsubmission.id")
    question_id: int = Field(foreign_key="question.id")

    similarity_score: float | None = None
    llm_score: float | None = None
    final_marks: float

    explanation: str | None = None
    missing_points: str | None = None  # JSON-encoded list[str]
    strong_points: str | None = None  # JSON-encoded list[str]

    created_at: datetime = Field(default_factory=datetime.utcnow)

    submission: StudentSubmission = Relationship(back_populates="evaluations")
    feedback: "Feedback" = Relationship(back_populates="evaluation")


class Feedback(SQLModel, table=True):
    """Personalized feedback text generated for one evaluation.

    Kept as its own table (rather than a column on Evaluation) so we can
    later support regenerating feedback or storing feedback history without
    touching the scoring record.
    """

    id: int | None = Field(default=None, primary_key=True)
    evaluation_id: int = Field(foreign_key="evaluation.id", unique=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    evaluation: Evaluation = Relationship(back_populates="feedback")