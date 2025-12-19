from sqlalchemy.orm import Session
from typing import Optional, Dict, List
import logging

from app.repositories.team import TeamRepository
from app.repositories.team_member import TeamMemberRepository
from app.repositories.team_baseline_snapshot import TeamBaselineSnapshotRepository
from app.repositories.call import CallRepository

logger = logging.getLogger(__name__)


class TeamBaselineService:
    """
    Phase 9: Team baseline aggregation service.

    Purpose:
    - Compute team-wide aggregated RASNA averages
    - Create team baseline snapshots for trend tracking
    - NO individual score exposure
    - NO personal baseline manipulation

    Privacy Guarantees:
    - Only aggregated averages are computed
    - Individual agent performance is NEVER exposed
    - Members cannot reverse-engineer individual scores
    - Aggregation requires minimum team size for privacy

    This is NOT:
    - Personal baseline generation (that's Phase 7)
    - Individual performance tracking
    - Cross-user raw data access
    """

    # Phase 9: Minimum team size for aggregation privacy
    MIN_TEAM_SIZE_FOR_AGGREGATION = 2

    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.member_repo = TeamMemberRepository(db)
        self.snapshot_repo = TeamBaselineSnapshotRepository(db)
        self.call_repo = CallRepository(db)

    def generate_team_baseline(self, team_id: int) -> Dict:
        """
        Generate team baseline by aggregating completed evaluations.

        Phase 9: Explicit action only.
        Computes average RASNA scores across all team members.

        Phase 9.1: Enforces privacy guardrails strictly.

        Args:
            team_id: Team to generate baseline for

        Returns:
            dict: Aggregated team baseline data

        Raises:
            ValueError: If insufficient data or team doesn't exist
        """
        team = self.team_repo.get_by_id(team_id)
        if not team:
            logger.warning(f"Team baseline generation failed: Team {team_id} not found")
            raise ValueError(f"Team {team_id} not found")

        # Get all team member user IDs
        member_ids = self.member_repo.get_team_member_ids(team_id)

        # Phase 9.1: Strict minimum team size enforcement for privacy
        if len(member_ids) < self.MIN_TEAM_SIZE_FOR_AGGREGATION:
            logger.warning(
                f"Team baseline generation blocked for team {team_id}: "
                f"Only {len(member_ids)} member(s), minimum {self.MIN_TEAM_SIZE_FOR_AGGREGATION} required for privacy"
            )
            raise ValueError(
                f"Team must have at least {self.MIN_TEAM_SIZE_FOR_AGGREGATION} members for aggregation. "
                f"This protects individual privacy by preventing reverse-engineering of scores."
            )

        # Aggregate RASNA scores across all team members
        aggregated_averages = self._aggregate_team_rasna_scores(member_ids)

        # Phase 9.1: Fail gracefully if no data available
        if not aggregated_averages or all(v == 0.0 for v in aggregated_averages.values()):
            logger.warning(
                f"Team baseline generation failed for team {team_id}: "
                f"No completed evaluations found for {len(member_ids)} member(s)"
            )
            raise ValueError("No completed evaluations found for team members")

        # Create snapshot
        snapshot_data = {
            "team_id": team_id,
            "aggregated_rasna_averages": aggregated_averages,
            "agent_count": len(member_ids)
        }

        snapshot = self.snapshot_repo.create(snapshot_data)

        logger.info(f"Generated team baseline for team {team_id} with {len(member_ids)} agents")

        return {
            "team_id": snapshot.team_id,
            "aggregated_rasna_averages": snapshot.aggregated_rasna_averages,
            "agent_count": snapshot.agent_count,
            "snapshot_created_at": snapshot.snapshot_created_at.isoformat()
        }

    def get_latest_team_baseline(self, team_id: int) -> Optional[Dict]:
        """
        Get the most recent team baseline snapshot.

        Returns None if no baseline has been generated yet.
        """
        snapshot = self.snapshot_repo.get_latest(team_id)
        if not snapshot:
            return None

        return {
            "team_id": snapshot.team_id,
            "aggregated_rasna_averages": snapshot.aggregated_rasna_averages,
            "agent_count": snapshot.agent_count,
            "snapshot_created_at": snapshot.snapshot_created_at.isoformat()
        }

    def _aggregate_team_rasna_scores(self, member_user_ids: List[int]) -> Dict[str, float]:
        """
        Aggregate RASNA scores across multiple team members.

        Phase 9: Privacy-preserving aggregation.
        - Computes average score per RASNA dimension across all team members
        - NO individual scores exposed
        - Only looks at completed evaluations

        Args:
            member_user_ids: List of user IDs in the team

        Returns:
            dict: Averaged RASNA scores
                {"rapport": 7.8, "ask": 8.2, ...}
        """
        dimensions = ["rapport", "ask", "situation", "next_steps", "articulation"]
        dimension_scores = {dim: [] for dim in dimensions}

        # Collect scores from all team members' completed evaluations
        for user_id in member_user_ids:
            # Get all calls for this user with completed evaluations
            calls = self.call_repo.get_by_user_id(user_id)

            for call in calls:
                # Only include completed evaluations
                if call.evaluation_status != "completed" or not call.evaluation_details:
                    continue

                try:
                    rasna_scores = call.evaluation_details.get("rasna_scores", {})
                    if not isinstance(rasna_scores, dict):
                        continue

                    # Extract scores for each dimension
                    for dimension in dimensions:
                        dim_data = rasna_scores.get(dimension)
                        if dim_data is None:
                            continue

                        # Handle both nested dict and direct score
                        score = dim_data.get("score") if isinstance(dim_data, dict) else dim_data

                        if score is not None and isinstance(score, (int, float)):
                            dimension_scores[dimension].append(float(score))

                except (AttributeError, TypeError, KeyError) as e:
                    logger.warning(f"Failed to extract scores from call {call.id}: {e}")
                    continue

        # Compute averages
        aggregated_averages = {}
        for dimension in dimensions:
            scores = dimension_scores[dimension]
            if scores:
                aggregated_averages[dimension] = round(sum(scores) / len(scores), 2)
            else:
                aggregated_averages[dimension] = 0.0

        return aggregated_averages
