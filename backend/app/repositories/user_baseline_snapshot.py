from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.user_baseline_snapshot import UserBaselineSnapshot


class UserBaselineSnapshotRepository:
    """
    Repository for UserBaselineSnapshot operations.

    Phase 8: Handles CRUD operations for baseline snapshots.
    All operations are user-scoped for multi-user isolation.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, snapshot_data: dict) -> UserBaselineSnapshot:
        """
        Create a new baseline snapshot.

        Args:
            snapshot_data: Dictionary containing snapshot fields
                - user_id: int
                - rasna_averages: dict
                - summary_json: dict
                - call_count: int

        Returns:
            UserBaselineSnapshot: The created snapshot with ID populated

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db_snapshot = UserBaselineSnapshot(**snapshot_data)
            self.db.add(db_snapshot)
            self.db.commit()
            self.db.refresh(db_snapshot)
            return db_snapshot
        except Exception as e:
            self.db.rollback()
            raise e

    def get_latest_snapshots(self, user_id: int, limit: int = 2) -> List[UserBaselineSnapshot]:
        """
        Get most recent snapshots for a user.

        Phase 8: Used for trend analysis.
        Returns snapshots ordered by creation time (newest first).

        Args:
            user_id: ID of the user
            limit: Maximum number of snapshots to retrieve (default 2 for trends)

        Returns:
            List[UserBaselineSnapshot]: List of snapshots, newest first
        """
        return self.db.query(UserBaselineSnapshot).filter(
            UserBaselineSnapshot.user_id == user_id
        ).order_by(
            UserBaselineSnapshot.snapshot_created_at.desc()
        ).limit(limit).all()

    def count_for_user(self, user_id: int) -> int:
        """
        Count total snapshots for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Number of snapshots
        """
        return self.db.query(UserBaselineSnapshot).filter(
            UserBaselineSnapshot.user_id == user_id
        ).count()
