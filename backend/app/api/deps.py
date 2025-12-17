from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import get_db


def get_database() -> Generator[Session, None, None]:
    """Dependency for database session"""
    yield from get_db()
