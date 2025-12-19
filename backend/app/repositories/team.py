from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.team import Team


class TeamRepository:
    """
    Repository for Team operations.

    Phase 9: Handles CRUD operations for teams.
    All operations maintain strict ownership rules.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, team_data: dict) -> Team:
        """
        Create a new team.

        Args:
            team_data: Dictionary containing team fields
                - name: str
                - created_by: int (user_id of owner)

        Returns:
            Team: The created team with ID populated
        """
        try:
            db_team = Team(**team_data)
            self.db.add(db_team)
            self.db.commit()
            self.db.refresh(db_team)
            return db_team
        except Exception as e:
            self.db.rollback()
            raise e

    def get_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID."""
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_teams_owned_by_user(self, user_id: int) -> List[Team]:
        """Get all teams created by a specific user."""
        return self.db.query(Team).filter(Team.created_by == user_id).all()

    def delete(self, team_id: int) -> bool:
        """
        Delete a team.

        Note: Should only be called by team owner.
        Cascade deletion of team members and snapshots handled by service layer.
        """
        team = self.get_by_id(team_id)
        if not team:
            return False

        try:
            self.db.delete(team)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
