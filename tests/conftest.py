"""Shared pytest fixtures for SmartEval AI tests.

Uses an in-memory SQLite database so tests are fully isolated from the
real development database and can run in any order without side effects.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from smartevalai.core.deps import get_current_user, get_session
from smartevalai.main import create_app
from smartevalai.models.user import User, UserRole


@pytest.fixture(name="session")
def session_fixture():
    """Yield a fresh in-memory SQLite session for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Yield a TestClient wired to the in-memory session."""
    app = create_app()

    app.dependency_overrides[get_session] = lambda: session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="teacher_user")
def teacher_user_fixture(session: Session) -> User:
    """Create and return a teacher user in the test DB."""
    from smartevalai.core.security import hash_password
    user = User(
        full_name="Test Teacher",
        email="teacher@test.com",
        hashed_password=hash_password("testpass"),
        role=UserRole.TEACHER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="student_user")
def student_user_fixture(session: Session) -> User:
    """Create and return a student user in the test DB."""
    from smartevalai.core.security import hash_password
    user = User(
        full_name="Test Student",
        email="student@test.com",
        hashed_password=hash_password("testpass"),
        role=UserRole.STUDENT,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="teacher_client")
def teacher_client_fixture(client: TestClient, teacher_user: User):
    """Yield a TestClient pre-authenticated as a teacher."""
    from smartevalai.main import create_app
    app = client.app
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    return client


@pytest.fixture(name="student_client")
def student_client_fixture(client: TestClient, student_user: User):
    """Yield a TestClient pre-authenticated as a student."""
    app = client.app
    app.dependency_overrides[get_current_user] = lambda: student_user
    return client