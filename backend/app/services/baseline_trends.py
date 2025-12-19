from typing import Optional, Dict, List
import logging
from sqlalchemy.orm import Session

from app.repositories.user_baseline_snapshot import UserBaselineSnapshotRepository

logger = logging.getLogger(__name__)

# Phase 8: Centralized trend threshold constants
TREND_IMPROVEMENT_THRESHOLD = 0.5  # Score increase >= 0.5 considered improvement
TREND_DECLINE_THRESHOLD = 0.5      # Score decrease >= 0.5 considered decline
# Within ±0.5 = stable


class BaselineTrendService:
    """
    Phase 8: Baseline trend and evolution intelligence service.

    Purpose:
    - Compare consecutive baseline snapshots
    - Identify improved/declined/stable dimensions
    - Provide human-readable evolution insights
    - NO forecasting, NO ML, NO LLM - pure arithmetic comparison

    This is NOT:
    - Team analytics (Phase 9)
    - Predictive modeling
    - Automatic regeneration
    """

    def __init__(self, db: Session):
        self.db = db
        self.snapshot_repo = UserBaselineSnapshotRepository(db)

    def get_trend_for_user(self, user_id: int) -> Optional[Dict]:
        """
        Get baseline evolution trend for user.

        Compares last two snapshots to show:
        - Which dimensions improved
        - Which dimensions declined
        - Which dimensions stayed stable
        - Delta values per dimension

        Requires at least 2 snapshots. Returns None if insufficient data.

        Args:
            user_id: ID of the user

        Returns:
            dict: Trend analysis, or None if <2 snapshots exist
        """
        # Fetch latest 2 snapshots
        snapshots = self.snapshot_repo.get_latest_snapshots(user_id, limit=2)

        # Require at least 2 snapshots for comparison
        if len(snapshots) < 2:
            return None

        # Latest snapshot is first (ordered desc)
        latest_snapshot = snapshots[0]
        previous_snapshot = snapshots[1]

        # Defensive: validate snapshot data
        try:
            latest_averages = latest_snapshot.rasna_averages
            previous_averages = previous_snapshot.rasna_averages

            if not isinstance(latest_averages, dict) or not isinstance(previous_averages, dict):
                logger.warning(f"Invalid snapshot data for user {user_id}")
                return None
        except (AttributeError, TypeError) as e:
            logger.warning(f"Failed to extract snapshot data for user {user_id}: {e}")
            return None

        # Compute dimension deltas
        dimension_deltas = self._compute_dimension_deltas(previous_averages, latest_averages)

        # Categorize changes
        categorization = self._categorize_changes(dimension_deltas)

        # Generate summary text
        summary = self._generate_evolution_summary(categorization, dimension_deltas)

        return {
            "improved_dimensions": categorization["improved"],
            "declined_dimensions": categorization["declined"],
            "stable_dimensions": categorization["stable"],
            "dimension_deltas": dimension_deltas,
            "summary": summary,
            "snapshots_compared": 2,
            "latest_snapshot_date": latest_snapshot.snapshot_created_at.isoformat(),
            "previous_snapshot_date": previous_snapshot.snapshot_created_at.isoformat(),
            "latest_call_count": latest_snapshot.call_count,
            "previous_call_count": previous_snapshot.call_count
        }

    def _compute_dimension_deltas(
        self,
        previous_averages: Dict[str, float],
        latest_averages: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Phase 8: Defensive delta computation.

        Compute change in score for each RASNA dimension.
        Positive delta = improvement, negative delta = decline.

        Guards against:
        - Missing dimensions
        - Non-numeric values
        - Malformed data

        Args:
            previous_averages: RASNA averages from previous snapshot
            latest_averages: RASNA averages from latest snapshot

        Returns:
            dict: Delta per dimension (latest - previous)
        """
        dimensions = ["rapport", "ask", "situation", "next_steps", "articulation"]
        deltas = {}

        for dimension in dimensions:
            try:
                # Defensive: extract with fallback to 0.0
                previous_score = previous_averages.get(dimension, 0.0)
                latest_score = latest_averages.get(dimension, 0.0)

                # Type validation
                if not isinstance(previous_score, (int, float)):
                    previous_score = 0.0
                if not isinstance(latest_score, (int, float)):
                    latest_score = 0.0

                # Calculate delta (latest - previous)
                delta = round(float(latest_score) - float(previous_score), 2)
                deltas[dimension] = delta

            except (TypeError, ValueError, KeyError) as e:
                # Skip dimension on error, default to 0 delta
                logger.warning(f"Failed to compute delta for dimension '{dimension}': {e}")
                deltas[dimension] = 0.0

        return deltas

    def _categorize_changes(self, dimension_deltas: Dict[str, float]) -> Dict[str, List[str]]:
        """
        Phase 8: Categorize dimension changes into improved/declined/stable.

        Uses centralized thresholds:
        - Delta >= +TREND_IMPROVEMENT_THRESHOLD → improved
        - Delta <= -TREND_DECLINE_THRESHOLD → declined
        - Otherwise → stable

        Args:
            dimension_deltas: Delta per dimension

        Returns:
            dict: {
                "improved": [list of dimensions],
                "declined": [list of dimensions],
                "stable": [list of dimensions]
            }
        """
        improved = []
        declined = []
        stable = []

        for dimension, delta in dimension_deltas.items():
            try:
                if delta >= TREND_IMPROVEMENT_THRESHOLD:
                    improved.append(dimension)
                elif delta <= -TREND_DECLINE_THRESHOLD:
                    declined.append(dimension)
                else:
                    stable.append(dimension)
            except (TypeError, ValueError):
                # Treat invalid deltas as stable
                stable.append(dimension)

        return {
            "improved": improved,
            "declined": declined,
            "stable": stable
        }

    def _generate_evolution_summary(
        self,
        categorization: Dict[str, List[str]],
        dimension_deltas: Dict[str, float]
    ) -> str:
        """
        Generate human-readable evolution summary.

        Calm, non-judgmental language focused on "your own evolution".

        Args:
            categorization: Improved/declined/stable dimensions
            dimension_deltas: Delta values per dimension

        Returns:
            str: Summary text
        """
        improved = categorization["improved"]
        declined = categorization["declined"]

        if not improved and not declined:
            return "Your baseline has remained stable since your last regeneration"

        parts = []

        if improved:
            # Show top improvement
            top_improvement = max(improved, key=lambda d: dimension_deltas.get(d, 0))
            delta = dimension_deltas.get(top_improvement, 0)
            parts.append(f"You've improved in {', '.join(improved)} (strongest: {top_improvement} +{delta:.1f})")

        if declined:
            # Show areas that slipped
            parts.append(f"These slipped compared to your last baseline: {', '.join(declined)}")

        return ". ".join(parts)
