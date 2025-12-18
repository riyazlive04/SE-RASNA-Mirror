from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.call import Call


class CallRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, call_data: dict) -> Call:
        """
        Create a new call record in the database

        Args:
            call_data: Dictionary containing call fields

        Returns:
            Call: The created call object with ID populated

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db_call = Call(**call_data)
            self.db.add(db_call)
            self.db.commit()
            self.db.refresh(db_call)
            return db_call
        except Exception as e:
            # Rollback transaction on any error
            self.db.rollback()
            raise e

    def get_by_id(self, call_id: int) -> Optional[Call]:
        return self.db.query(Call).filter(Call.id == call_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Call]:
        return self.db.query(Call).offset(skip).limit(limit).all()

    def get_all_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Call]:
        """Get all calls for a specific user with pagination - multi-user isolation"""
        return self.db.query(Call).filter(Call.user_id == user_id).offset(skip).limit(limit).all()

    def count(self) -> int:
        return self.db.query(Call).count()

    def count_for_user(self, user_id: int) -> int:
        """Count total calls for a specific user - multi-user isolation"""
        return self.db.query(Call).filter(Call.user_id == user_id).count()

    def update(self, call_id: int, update_data: dict) -> Optional[Call]:
        db_call = self.get_by_id(call_id)
        if db_call:
            for key, value in update_data.items():
                setattr(db_call, key, value)
            self.db.commit()
            self.db.refresh(db_call)
        return db_call

    def delete(self, call_id: int) -> bool:
        db_call = self.get_by_id(call_id)
        if db_call:
            self.db.delete(db_call)
            self.db.commit()
            return True
        return False

    def mark_as_baseline(self, call_id: int) -> Optional[Call]:
        """
        Mark a call as baseline (best call example).

        Purpose: Allows users to mark exceptional calls for future comparison.
        User-specific: Each user has their own baseline calls.

        Args:
            call_id: ID of the call to mark as baseline

        Returns:
            Call: The updated call object, or None if not found
        """
        db_call = self.get_by_id(call_id)
        if db_call:
            db_call.is_baseline = True
            db_call.baseline_marked_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_call)
        return db_call

    def unmark_as_baseline(self, call_id: int) -> Optional[Call]:
        """
        Remove baseline marking from a call.

        Args:
            call_id: ID of the call to unmark as baseline

        Returns:
            Call: The updated call object, or None if not found
        """
        db_call = self.get_by_id(call_id)
        if db_call:
            db_call.is_baseline = False
            db_call.baseline_marked_at = None
            self.db.commit()
            self.db.refresh(db_call)
        return db_call
