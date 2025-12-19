from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.team_member import TeamMember


class TeamMemberRepository:
    """
    Repository for TeamMember operations.

    Phase 9: Handles CRUD operations for team membership.
    Enforces role-based access control.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, member_data: dict) -> TeamMember:
        """
        Add a user to a team with a specific role.

        Args:
            member_data: Dictionary containing member fields
                - team_id: int
                - user_id: int
                - role: str ("owner", "manager", "member")

        Returns:
            TeamMember: The created team member record
        """
        try:
            db_member = TeamMember(**member_data)
            self.db.add(db_member)
            self.db.commit()
            self.db.refresh(db_member)
            return db_member
        except Exception as e:
            self.db.rollback()
            raise e

    def get_membership(self, team_id: int, user_id: int) -> Optional[TeamMember]:
        """Get team membership record for a specific user in a team."""
        return self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

    def get_team_members(self, team_id: int) -> List[TeamMember]:
        """Get all members of a team."""
        return self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()

    def get_user_teams(self, user_id: int) -> List[TeamMember]:
        """Get all team memberships for a user."""
        return self.db.query(TeamMember).filter(
            TeamMember.user_id == user_id
        ).all()

    def get_team_member_ids(self, team_id: int) -> List[int]:
        """
        Get list of user IDs who are members of a team.

        Used for aggregation queries.
        """
        members = self.db.query(TeamMember.user_id).filter(
            TeamMember.team_id == team_id
        ).all()
        return [member.user_id for member in members]

    def update_role(self, team_id: int, user_id: int, new_role: str) -> Optional[TeamMember]:
        """Update a team member's role."""
        member = self.get_membership(team_id, user_id)
        if not member:
            return None

        try:
            member.role = new_role
            self.db.commit()
            self.db.refresh(member)
            return member
        except Exception as e:
            self.db.rollback()
            raise e

    def remove(self, team_id: int, user_id: int) -> bool:
        """Remove a user from a team."""
        member = self.get_membership(team_id, user_id)
        if not member:
            return False

        try:
            self.db.delete(member)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
