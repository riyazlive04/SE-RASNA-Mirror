from sqlalchemy.orm import Session
from typing import Optional

from app.models.user_baseline import UserBaseline


class UserBaselineRepository:
    """
    Repository for UserBaseline operations.

    Phase 7: Handles CRUD operations for personal baseline intelligence.
    All operations are user-scoped for multi-user isolation.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, baseline_data: dict) -> UserBaseline:
        """
        Create a new baseline for a user.

        Args:
            baseline_data: Dictionary containing baseline fields
                - user_id: int
                - rasna_averages: dict
                - summary_json: dict
                - call_count: int

        Returns:
            UserBaseline: The created baseline object with ID populated

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db_baseline = UserBaseline(**baseline_data)
            self.db.add(db_baseline)
            self.db.commit()
            self.db.refresh(db_baseline)
            return db_baseline
        except Exception as e:
            self.db.rollback()
            raise e

    def get_by_user_id(self, user_id: int) -> Optional[UserBaseline]:
        """
        Get baseline for a specific user.

        Args:
            user_id: ID of the user

        Returns:
            UserBaseline: The user's baseline, or None if not found
        """
        return self.db.query(UserBaseline).filter(UserBaseline.user_id == user_id).first()

    def update(self, user_id: int, update_data: dict) -> Optional[UserBaseline]:
        """
        Update existing baseline for a user (regeneration).

        Args:
            user_id: ID of the user
            update_data: Dictionary containing fields to update

        Returns:
            UserBaseline: The updated baseline object, or None if not found
        """
        db_baseline = self.get_by_user_id(user_id)
        if db_baseline:
            for key, value in update_data.items():
                setattr(db_baseline, key, value)
            self.db.commit()
            self.db.refresh(db_baseline)
        return db_baseline

    def delete(self, user_id: int) -> bool:
        """
        Delete baseline for a user.

        Args:
            user_id: ID of the user

        Returns:
            bool: True if deleted, False if not found
        """
        db_baseline = self.get_by_user_id(user_id)
        if db_baseline:
            self.db.delete(db_baseline)
            self.db.commit()
            return True
        return False

    def exists_for_user(self, user_id: int) -> bool:
        """
        Check if baseline exists for a user.

        Args:
            user_id: ID of the user

        Returns:
            bool: True if baseline exists, False otherwise
        """
        return self.db.query(UserBaseline).filter(UserBaseline.user_id == user_id).first() is not None
