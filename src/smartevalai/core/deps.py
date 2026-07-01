"""Shared FastAPI dependencies for authentication and authorization."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from smartevalai.core.security import decode_access_token
from smartevalai.db.session import get_session
from smartevalai.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the current authenticated user from the JWT bearer token.

    Raises:
        HTTPException: 401 if the token is missing, invalid, expired, or
            no longer matches an existing user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = session.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    """Dependency that only allows teacher accounts through."""
    if user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a teacher account.",
        )
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    """Dependency that only allows student accounts through."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a student account.",
        )
    return user