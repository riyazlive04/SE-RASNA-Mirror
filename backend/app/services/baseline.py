from typing import Optional, Dict, List
import logging
from sqlalchemy.orm import Session

from app.models.call import Call
from app.repositories.call import CallRepository
from app.repositories.user_baseline import UserBaselineRepository
from app.repositories.user_baseline_snapshot import UserBaselineSnapshotRepository

logger = logging.getLogger(__name__)

# Phase 7.1: Centralized threshold constants
STRENGTH_THRESHOLD = 8.0  # RASNA score >= 8.0 considered a strength
IMPROVEMENT_THRESHOLD = 7.0  # RASNA score < 7.0 needs improvement
COMPARISON_DELTA_THRESHOLD = 0.5  # Min difference for meaningful baseline comparison


class BaselineService:
    """
    Personal baseline intelligence service.

    Phase 7: Aggregates intelligence from user's "Best Calls" to create
    a personal baseline for comparison. NO LLM usage - pure aggregation.

    This is NOT ML model training. This is structured intelligence aggregation
    from calls manually marked as is_baseline=True by the user.
    """

    def __init__(self, db: Session):
        self.db = db
        self.call_repo = CallRepository(db)
        self.baseline_repo = UserBaselineRepository(db)
        self.snapshot_repo = UserBaselineSnapshotRepository(db)  # Phase 8: Snapshot tracking

    def generate_baseline_for_user(self, user_id: int) -> Dict:
        """
        Generate or regenerate personal baseline from user's best calls.

        Prerequisites:
        - At least 1 call marked as is_baseline=True
        - All baseline calls must have evaluation_status="completed"

        Process:
        1. Fetch all baseline calls for user
        2. Validate prerequisites
        3. Aggregate RASNA scores
        4. Identify common patterns
        5. Store or update baseline

        Args:
            user_id: ID of the user

        Returns:
            dict: Generated baseline data

        Raises:
            ValueError: If prerequisites not met
        """
        # Fetch baseline calls for this user
        baseline_calls = self._get_baseline_calls(user_id)

        # Validate prerequisites
        if not baseline_calls:
            raise ValueError("No calls marked as baseline. Mark at least 1 call as 'Best Call' first.")

        # Check all have completed evaluations
        incomplete = [c for c in baseline_calls if c.evaluation_status != "completed"]
        if incomplete:
            raise ValueError(
                f"{len(incomplete)} baseline call(s) lack completed evaluation. "
                "All best calls must be evaluated first."
            )

        # Aggregate RASNA scores
        rasna_averages = self._calculate_rasna_averages(baseline_calls)

        # Identify common patterns (deterministic, no LLM)
        summary = self._generate_summary(baseline_calls, rasna_averages)

        # Prepare baseline data
        # Phase 7.1: Set is_stale=False when generating/regenerating
        baseline_data = {
            "user_id": user_id,
            "rasna_averages": rasna_averages,
            "summary_json": summary,
            "call_count": len(baseline_calls),
            "is_stale": False  # Fresh baseline
        }

        # Check if baseline already exists
        existing = self.baseline_repo.get_by_user_id(user_id)

        if existing:
            # Update (regenerate)
            result = self.baseline_repo.update(user_id, baseline_data)
            logger.info(f"Regenerated baseline for user {user_id} from {len(baseline_calls)} calls")
        else:
            # Create new
            result = self.baseline_repo.create(baseline_data)
            logger.info(f"Generated baseline for user {user_id} from {len(baseline_calls)} calls")

        # Phase 8: Create snapshot for trend tracking
        # Snapshot created ONLY when user explicitly regenerates baseline
        # No automatic creation - explicit user action required
        snapshot_data = {
            "user_id": user_id,
            "rasna_averages": rasna_averages,
            "summary_json": summary,
            "call_count": len(baseline_calls)
        }
        try:
            self.snapshot_repo.create(snapshot_data)
            logger.info(f"Created baseline snapshot for user {user_id}")
        except Exception as e:
            # Graceful degradation: snapshot creation failure doesn't break baseline generation
            logger.error(f"Failed to create baseline snapshot for user {user_id}: {e}")

        return self._format_baseline_response(result)

    def get_baseline_for_user(self, user_id: int) -> Optional[Dict]:
        """
        Get existing baseline for user.

        Args:
            user_id: ID of the user

        Returns:
            dict: Baseline data, or None if not found
        """
        baseline = self.baseline_repo.get_by_user_id(user_id)
        if not baseline:
            return None
        return self._format_baseline_response(baseline)

    def mark_baseline_as_stale(self, user_id: int) -> None:
        """
        Phase 7.1: Mark baseline as stale when baseline calls change.

        Called when:
        - A call is marked as baseline (new best call added)
        - A call is unmarked from baseline (best call removed)

        Does NOT auto-regenerate. User must explicitly regenerate.

        Args:
            user_id: ID of the user
        """
        baseline = self.baseline_repo.get_by_user_id(user_id)
        if baseline and not baseline.is_stale:
            self.baseline_repo.update(user_id, {"is_stale": True})
            logger.info(f"Marked baseline as stale for user {user_id}")

    def compare_to_baseline(self, user_id: int, evaluation_details: Dict) -> Optional[Dict]:
        """
        Compare a call's evaluation against user's baseline.

        Returns None if no baseline exists (graceful degradation).

        Args:
            user_id: ID of the user
            evaluation_details: RASNA evaluation from call

        Returns:
            dict: Comparison summary, or None if no baseline
        """
        baseline = self.baseline_repo.get_by_user_id(user_id)
        if not baseline:
            return None

        # Phase 7.1: Defensive extraction with safeguards
        try:
            rasna_scores = evaluation_details.get("rasna_scores", {})
            if not isinstance(rasna_scores, dict):
                logger.warning("Invalid rasna_scores format in evaluation_details")
                return None

            baseline_averages = baseline.rasna_averages
            if not isinstance(baseline_averages, dict):
                logger.warning("Invalid rasna_averages format in baseline")
                return None
        except (AttributeError, TypeError) as e:
            logger.warning(f"Failed to extract scores for baseline comparison: {e}")
            return None

        # Compare each dimension
        above_baseline = []
        below_baseline = []

        for dimension in ["rapport", "ask", "situation", "next_steps", "articulation"]:
            try:
                # Defensive: handle both nested dict and direct score
                dim_data = rasna_scores.get(dimension, {})
                current_score = dim_data.get("score", 0) if isinstance(dim_data, dict) else dim_data
                if not isinstance(current_score, (int, float)):
                    current_score = 0

                baseline_score = baseline_averages.get(dimension, 0)
                if not isinstance(baseline_score, (int, float)):
                    baseline_score = 0

                # Compare using centralized threshold
                if current_score > baseline_score + COMPARISON_DELTA_THRESHOLD:
                    above_baseline.append(dimension)
                elif current_score < baseline_score - COMPARISON_DELTA_THRESHOLD:
                    below_baseline.append(dimension)
            except (AttributeError, TypeError, KeyError):
                # Skip dimension on error
                continue

        # Generate comparison summary
        summary = self._generate_comparison_summary(above_baseline, below_baseline)

        return {
            "above_baseline": above_baseline,
            "below_baseline": below_baseline,
            "summary": summary
        }

    def _get_baseline_calls(self, user_id: int) -> List[Call]:
        """
        Fetch all baseline calls for user.

        Only returns calls where:
        - user_id matches
        - is_baseline == True
        """
        return self.db.query(Call).filter(
            Call.user_id == user_id,
            Call.is_baseline == True
        ).all()

    def _calculate_rasna_averages(self, calls: List[Call]) -> Dict[str, float]:
        """
        Phase 7.1: Defensive aggregation with safeguards.

        Calculate average RASNA scores across baseline calls.
        Guards against:
        - Missing dimensions
        - None/null scores
        - Empty score lists
        - Malformed evaluation data

        Args:
            calls: List of baseline calls with completed evaluations

        Returns:
            dict: Average scores for each RASNA dimension (0.0 if missing)
        """
        dimensions = ["rapport", "ask", "situation", "next_steps", "articulation"]
        averages = {}

        for dimension in dimensions:
            scores = []
            for call in calls:
                try:
                    # Defensive: check evaluation_details exists and is dict
                    if not call.evaluation_details or not isinstance(call.evaluation_details, dict):
                        continue

                    rasna_scores = call.evaluation_details.get("rasna_scores", {})
                    if not isinstance(rasna_scores, dict):
                        continue

                    # Defensive: handle both nested dict and direct score
                    dim_data = rasna_scores.get(dimension)
                    if dim_data is None:
                        continue

                    # Extract score (handle both {"score": X} and direct number)
                    score = dim_data.get("score") if isinstance(dim_data, dict) else dim_data
                    if score is not None and isinstance(score, (int, float)):
                        scores.append(float(score))
                except (AttributeError, TypeError, KeyError):
                    # Skip malformed data gracefully
                    continue

            # Calculate average with defensive guard against division by zero
            if scores:
                averages[dimension] = round(sum(scores) / len(scores), 2)
            else:
                averages[dimension] = 0.0
                logger.warning(f"No valid scores found for dimension '{dimension}' in baseline calls")

        return averages

    def _generate_summary(self, calls: List[Call], rasna_averages: Dict[str, float]) -> Dict:
        """
        Generate summary insights from baseline calls.

        Pure aggregation, no LLM. Identifies:
        - Common strengths (dimensions with avg score ≥ STRENGTH_THRESHOLD)
        - Common improvement themes (dimensions with avg score < IMPROVEMENT_THRESHOLD)
        - Overall average score

        Args:
            calls: List of baseline calls
            rasna_averages: Calculated RASNA averages

        Returns:
            dict: Summary insights
        """
        # Identify strengths and improvement areas using centralized thresholds
        common_strengths = [dim for dim, score in rasna_averages.items() if score >= STRENGTH_THRESHOLD]
        common_improvement_themes = [dim for dim, score in rasna_averages.items() if score < IMPROVEMENT_THRESHOLD]

        # Calculate overall average
        overall_avg = round(sum(rasna_averages.values()) / len(rasna_averages), 2)

        return {
            "common_strengths": common_strengths,
            "common_improvement_themes": common_improvement_themes,
            "average_overall_score": overall_avg
        }

    def _generate_comparison_summary(self, above: List[str], below: List[str]) -> str:
        """
        Generate human-readable comparison summary.

        Calm, non-judgmental language focused on "your own best patterns".

        Args:
            above: Dimensions above baseline
            below: Dimensions below baseline

        Returns:
            str: Summary text
        """
        if not above and not below:
            return "This call matches your baseline pattern"

        parts = []
        if above:
            parts.append(f"Stronger than your baseline: {', '.join(above)}")
        if below:
            parts.append(f"Room to match your best: {', '.join(below)}")

        return ". ".join(parts)

    def _format_baseline_response(self, baseline) -> Dict:
        """Format baseline model to response dict"""
        return {
            "id": baseline.id,
            "user_id": baseline.user_id,
            "rasna_averages": baseline.rasna_averages,
            "summary": baseline.summary_json,
            "call_count": baseline.call_count,
            "is_stale": baseline.is_stale,  # Phase 7.1: Staleness indicator
            "created_at": baseline.created_at.isoformat(),
            "updated_at": baseline.updated_at.isoformat()
        }
