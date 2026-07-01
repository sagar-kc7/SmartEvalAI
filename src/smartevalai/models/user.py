"""User model: covers both teachers and students via a `role` field."""

from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    """Distinguishes teacher accounts from student accounts."""

    TEACHER = "teacher"
    STUDENT = "student"


class User(SQLModel, table=True):
    """A registered user — either a teacher or a student.

    Attributes:
        id: Primary key.
        full_name: Display name.
        email: Unique login identifier.
        hashed_password: Bcrypt-hashed password, never plaintext.
        role: Whether this user is a teacher or a student.
        created_at: Account creation timestamp.
    """

    id: int | None = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # An exam is "owned" by the teacher who created it.
    exams: list["Exam"] = Relationship(back_populates="teacher")
    # A submission belongs to the student who uploaded it.
    submissions: list["StudentSubmission"] = Relationship(back_populates="student")