"""Models for Subject, Exam, and Question."""

from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class QuestionType(str, Enum):
    """The two supported question formats."""

    MCQ = "mcq"
    DESCRIPTIVE = "descriptive"


class Subject(SQLModel, table=True):
    """A subject/course that groups multiple exams (e.g. 'Data Structures')."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    exams: list["Exam"] = Relationship(back_populates="subject")


class Exam(SQLModel, table=True):
    """An exam created by a teacher, containing one or more questions.

    Attributes:
        question_paper_path: Path to the uploaded question paper PDF/image,
            stored on disk (or object storage in production).
    """

    id: int | None = Field(default=None, primary_key=True)
    title: str
    subject_id: int = Field(foreign_key="subject.id")
    teacher_id: int = Field(foreign_key="user.id")
    question_paper_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    subject: Subject = Relationship(back_populates="exams")
    teacher: "User" = Relationship(back_populates="exams")  # noqa: F821
    questions: list["Question"] = Relationship(back_populates="exam")
    submissions: list["StudentSubmission"] = Relationship(back_populates="exam")


class Question(SQLModel, table=True):
    """A single question within an exam.

    For MCQ: `options` holds the choices and `correct_option` the answer key.
    For descriptive: `official_answer` holds the teacher-provided model answer.

    Attributes:
        question_number: The number/label as it appears on the physical
            question paper (e.g. "1", "2a"). This — not the database `id` —
            is what OCR-extracted student answers are matched against,
            since students write answers numbered the way the question
            paper presents them, not by our internal primary key.
    """

    id: int | None = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id")
    question_number: str
    question_text: str
    question_type: QuestionType
    max_marks: float = 1.0

    # MCQ-specific fields (nullable for descriptive questions)
    options: str | None = None  # stored as JSON-encoded list of strings
    correct_option: str | None = None

    # Descriptive-specific field (nullable for MCQ)
    official_answer: str | None = None

    exam: Exam = Relationship(back_populates="questions")