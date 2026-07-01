"""Authentication business logic: registration and login."""

from fastapi import HTTPException, status
from sqlmodel import Session, select

from smartevalai.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from smartevalai.models.user import User
from smartevalai.schemas.auth import UserLogin, UserRegister


def register_user(session: Session, payload: UserRegister) -> User:
    """Create a new user account.

    Raises:
        HTTPException: 409 if the email is already registered.
    """
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, payload: UserLogin) -> str:
    """Verify credentials and return a signed JWT access token.

    Raises:
        HTTPException: 401 if the email doesn't exist or password is wrong.
    """
    user = session.exec(select(User).where(User.email == payload.email)).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return create_access_token(subject=str(user.id), role=user.role.value)