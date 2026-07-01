"""Authentication API routes: register and login."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from smartevalai.db.session import get_session
from smartevalai.schemas.auth import Token, UserLogin, UserRead, UserRegister
from smartevalai.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserRegister, session: Session = Depends(get_session)) -> UserRead:
    """Create a new teacher or student account."""
    user = register_user(session, payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    """Authenticate and receive a JWT access token.

    Uses OAuth2PasswordRequestForm (standard `username`/`password` form
    fields) rather than a JSON body, since this is what FastAPI's built-in
    `OAuth2PasswordBearer` and the interactive /docs "Authorize" button
    expect. We map `username` to our `email` field internally.
    """
    payload = UserLogin(email=form_data.username, password=form_data.password)
    access_token = authenticate_user(session, payload)
    return Token(access_token=access_token)