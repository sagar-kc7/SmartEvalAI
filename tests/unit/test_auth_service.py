"""Unit tests for authentication business logic."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from smartevalai.models.user import UserRole
from smartevalai.schemas.auth import UserLogin, UserRegister
from smartevalai.services.auth_service import authenticate_user, register_user


class TestRegisterUser:
    def test_creates_user_successfully(self, session: Session):
        payload = UserRegister(
            full_name="Sagar KC",
            email="sagar@test.com",
            password="securepass",
            role=UserRole.STUDENT,
        )
        user = register_user(session, payload)
        assert user.id is not None
        assert user.email == "sagar@test.com"
        assert user.role == UserRole.STUDENT
        assert user.hashed_password != "securepass"

    def test_raises_on_duplicate_email(self, session: Session):
        payload = UserRegister(
            full_name="Sagar KC",
            email="duplicate@test.com",
            password="pass",
            role=UserRole.STUDENT,
        )
        register_user(session, payload)
        with pytest.raises(HTTPException) as exc_info:
            register_user(session, payload)
        assert exc_info.value.status_code == 409

    def test_teacher_role_stored_correctly(self, session: Session):
        payload = UserRegister(
            full_name="Prof Test",
            email="prof@test.com",
            password="pass",
            role=UserRole.TEACHER,
        )
        user = register_user(session, payload)
        assert user.role == UserRole.TEACHER


class TestAuthenticateUser:
    def test_returns_token_for_valid_credentials(self, session: Session):
        payload = UserRegister(
            full_name="Sagar KC",
            email="auth@test.com",
            password="correctpass",
            role=UserRole.STUDENT,
        )
        register_user(session, payload)
        token = authenticate_user(session, UserLogin(email="auth@test.com", password="correctpass"))
        assert isinstance(token, str)
        assert len(token) > 20

    def test_raises_for_wrong_password(self, session: Session):
        payload = UserRegister(
            full_name="Sagar KC",
            email="wrong@test.com",
            password="correctpass",
            role=UserRole.STUDENT,
        )
        register_user(session, payload)
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(session, UserLogin(email="wrong@test.com", password="wrongpass"))
        assert exc_info.value.status_code == 401

    def test_raises_for_nonexistent_email(self, session: Session):
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(session, UserLogin(email="ghost@test.com", password="pass"))
        assert exc_info.value.status_code == 401