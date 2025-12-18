from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # User identity
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    # User workspace context
    # Purpose: Allows filtering/grouping users by domain in future
    # For now, single user = single workspace
    domain = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
