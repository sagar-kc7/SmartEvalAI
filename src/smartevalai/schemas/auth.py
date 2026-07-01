"""Request/response schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr

from smartevalai.models.user import UserRole


class UserRegister(BaseModel):
    """Payload for registering a new user."""

    full_name: str
    email: EmailStr
    password: str
    role: UserRole


class UserLogin(BaseModel):
    """Payload for logging in."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public-facing representation of a user (never includes the password)."""

    model_config = {"from_attributes": True}

    id: int
    full_name: str
    email: str
    role: UserRole


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"