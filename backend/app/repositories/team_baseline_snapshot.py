from sqlalchemy.orm import Session
from typing import List

from app.models.team_baseline_snapshot import TeamBaselineSnapshot


class TeamBaselineSnapshotRepository:
    """
    Repository for TeamBaselineSnapshot operations.

    Phase 9: Handles CRUD operations for team baseline snapshots.
    All snapshots are immutable aggregated data.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, snapshot_data: dict) -> TeamBaselineSnapshot:
        """
        Create a new team baseline snapshot.

        Args:
            snapshot_data: Dictionary containing snapshot fields
                - team_id: int
                - aggregated_rasna_averages: dict
                - agent_count: int

        Returns:
            TeamBaselineSnapshot: The created snapshot with ID populated
        """
        try:
            db_snapshot = TeamBaselineSnapshot(**snapshot_data)
            self.db.add(db_snapshot)
            self.db.commit()
            self.db.refresh(db_snapshot)
            return db_snapshot
        except Exception as e:
            self.db.rollback()
            raise e

    def get_latest_snapshots(self, team_id: int, limit: int = 2) -> List[TeamBaselineSnapshot]:
        """
        Get most recent snapshots for a team.

        Phase 9: Used for team trend analysis.
        Returns snapshots ordered by creation time (newest first).

        Args:
            team_id: ID of the team
            limit: Maximum number of snapshots to retrieve (default 2 for trends)

        Returns:
            List[TeamBaselineSnapshot]: List of snapshots, newest first
        """
        return self.db.query(TeamBaselineSnapshot).filter(
            TeamBaselineSnapshot.team_id == team_id
        ).order_by(
            TeamBaselineSnapshot.snapshot_created_at.desc()
        ).limit(limit).all()

    def count_for_team(self, team_id: int) -> int:
        """
        Count total snapshots for a team.

        Args:
            team_id: ID of the team

        Returns:
            int: Number of snapshots
        """
        return self.db.query(TeamBaselineSnapshot).filter(
            TeamBaselineSnapshot.team_id == team_id
        ).count()

    def get_latest(self, team_id: int) -> TeamBaselineSnapshot:
        """Get the most recent snapshot for a team."""
        return self.db.query(TeamBaselineSnapshot).filter(
            TeamBaselineSnapshot.team_id == team_id
        ).order_by(
            TeamBaselineSnapshot.snapshot_created_at.desc()
        ).first()
