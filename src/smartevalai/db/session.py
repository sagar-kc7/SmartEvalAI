"""Database engine and session management.

The engine is created once at import time and reused across the app.
`get_session` is a FastAPI dependency that yields a SQLModel Session per
request and guarantees it's closed afterward, even if the request fails.
"""

from collections.abc import Generator

from sqlmodel import Session, create_engine

from smartevalai.core.config import get_settings

settings = get_settings()

# `connect_args` is only needed for SQLite to allow usage across threads,
# which FastAPI's threadpool-backed sync endpoints require.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=connect_args,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Usage:
        @app.get("/items")
        def list_items(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session