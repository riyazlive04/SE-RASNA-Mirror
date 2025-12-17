from sqlalchemy.orm import Session
from typing import Optional

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

    def count(self) -> int:
        return self.db.query(Call).count()

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
