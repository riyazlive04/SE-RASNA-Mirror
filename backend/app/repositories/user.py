from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: dict) -> User:
        """
        Create a new user

        Args:
            user_data: Dictionary containing user fields

        Returns:
            User: The created user object with ID populated

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db_user = User(**user_data)
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except Exception as e:
            self.db.rollback()
            raise e

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email - used for login"""
        return self.db.query(User).filter(User.email == email).first()

    def email_exists(self, email: str) -> bool:
        """Check if email already exists - used for signup validation"""
        return self.db.query(User).filter(User.email == email).first() is not None
