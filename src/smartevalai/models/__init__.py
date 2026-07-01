"""Central import point for all SQLModel tables.

SQLModel relationships use forward references (e.g. "Exam", "User") as
strings. For those to resolve correctly, every model class must be
imported somewhere before the tables are created. Importing this package
(`from smartevalai import models`) guarantees that.
"""

from smartevalai.models.exam import Exam, Question, QuestionType, Subject
from smartevalai.models.submission import (
    Evaluation,
    Feedback,
    OCRResult,
    StudentSubmission,
)
from smartevalai.models.user import User, UserRole

__all__ = [
    "User",
    "UserRole",
    "Subject",
    "Exam",
    "Question",
    "QuestionType",
    "StudentSubmission",
    "OCRResult",
    "Evaluation",
    "Feedback",
]