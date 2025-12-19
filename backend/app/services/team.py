from sqlalchemy.orm import Session
from typing import Optional, Dict, List
import logging

from app.repositories.team import TeamRepository
from app.repositories.team_member import TeamMemberRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class TeamService:
    """
    Phase 9: Team management service.

    Purpose:
    - Handle team creation
    - Manage team membership
    - Enforce permission rules (owner/manager/member)

    This is NOT:
    - Personal baseline manipulation
    - Auto-enrollment
    - Cross-user data exposure
    """

    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.member_repo = TeamMemberRepository(db)
        self.user_repo = UserRepository(db)

    def create_team(self, name: str, created_by_user_id: int) -> Dict:
        """
        Create a new team.

        Creator automatically becomes owner.
        No other members added until explicitly invited.

        Args:
            name: Team name
            created_by_user_id: User ID of team creator

        Returns:
            dict: Team data with ID
        """
        # Create team
        team_data = {
            "name": name,
            "created_by": created_by_user_id
        }
        team = self.team_repo.create(team_data)

        # Add creator as owner
        member_data = {
            "team_id": team.id,
            "user_id": created_by_user_id,
            "role": "owner"
        }
        self.member_repo.create(member_data)

        logger.info(f"Team '{name}' created by user {created_by_user_id}")

        return {
            "id": team.id,
            "name": team.name,
            "created_by": team.created_by,
            "created_at": team.created_at.isoformat(),
            "role": "owner"
        }

    def add_member(self, team_id: int, user_id: int, role: str, inviter_user_id: int) -> Dict:
        """
        Add a member to a team.

        Phase 9: Explicit invitation only.
        Inviter must be owner or manager.

        Args:
            team_id: Team to add member to
            user_id: User to add
            role: "manager" or "member"
            inviter_user_id: User performing the invitation

        Returns:
            dict: Team member data

        Raises:
            ValueError: If permissions invalid or user doesn't exist
        """
        # Check inviter has permission
        if not self.can_manage_team(team_id, inviter_user_id):
            raise ValueError("Only owners and managers can invite members")

        # Validate role
        if role not in ["manager", "member"]:
            raise ValueError("Role must be 'manager' or 'member' (owner role cannot be assigned)")

        # Check user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check not already a member
        existing = self.member_repo.get_membership(team_id, user_id)
        if existing:
            raise ValueError(f"User {user_id} is already a member of team {team_id}")

        # Add member
        member_data = {
            "team_id": team_id,
            "user_id": user_id,
            "role": role
        }
        member = self.member_repo.create(member_data)

        logger.info(f"User {user_id} added to team {team_id} as {role}")

        return {
            "team_id": member.team_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at.isoformat()
        }

    def can_view_team_aggregates(self, team_id: int, user_id: int) -> bool:
        """
        Check if user can view team-level aggregated data.

        Phase 9: Only owners and managers can view team aggregates.
        Members can ONLY view their personal data.

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            bool: True if user can view team aggregates
        """
        membership = self.member_repo.get_membership(team_id, user_id)
        if not membership:
            return False

        return membership.role in ["owner", "manager"]

    def can_manage_team(self, team_id: int, user_id: int) -> bool:
        """
        Check if user can manage team (invite members, generate baselines).

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            bool: True if user can manage team
        """
        return self.can_view_team_aggregates(team_id, user_id)

    def get_user_teams(self, user_id: int) -> List[Dict]:
        """
        Get all teams a user is a member of.

        Returns teams with user's role in each.
        """
        memberships = self.member_repo.get_user_teams(user_id)
        teams = []

        for membership in memberships:
            team = self.team_repo.get_by_id(membership.team_id)
            if team:
                teams.append({
                    "id": team.id,
                    "name": team.name,
                    "created_by": team.created_by,
                    "created_at": team.created_at.isoformat(),
                    "role": membership.role
                })

        return teams

    def get_team_members(self, team_id: int, requester_user_id: int) -> List[Dict]:
        """
        Get all members of a team.

        Requester must be a member of the team.
        Returns member list with roles but NO personal performance data.

        Args:
            team_id: Team ID
            requester_user_id: User requesting the list

        Returns:
            List[Dict]: Team members with basic info

        Raises:
            ValueError: If requester is not a team member
        """
        # Verify requester is team member
        requester_membership = self.member_repo.get_membership(team_id, requester_user_id)
        if not requester_membership:
            raise ValueError("You must be a team member to view the member list")

        members = self.member_repo.get_team_members(team_id)
        result = []

        for member in members:
            user = self.user_repo.get_by_id(member.user_id)
            if user:
                result.append({
                    "user_id": member.user_id,
                    "name": user.name,
                    "email": user.email,
                    "role": member.role,
                    "joined_at": member.joined_at.isoformat()
                })

        return result
