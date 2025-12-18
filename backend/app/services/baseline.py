from typing import Optional, Dict, List
import logging
from sqlalchemy.orm import Session

from app.models.call import Call
from app.repositories.call import CallRepository
from app.repositories.user_baseline import UserBaselineRepository

logger = logging.getLogger(__name__)


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
        baseline_data = {
            "user_id": user_id,
            "rasna_averages": rasna_averages,
            "summary_json": summary,
            "call_count": len(baseline_calls)
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

        # Extract scores from evaluation
        rasna_scores = evaluation_details.get("rasna_scores", {})
        baseline_averages = baseline.rasna_averages

        # Compare each dimension
        above_baseline = []
        below_baseline = []

        for dimension in ["rapport", "ask", "situation", "next_steps", "articulation"]:
            current_score = rasna_scores.get(dimension, {}).get("score", 0)
            baseline_score = baseline_averages.get(dimension, 0)

            # Threshold: >0.5 points difference to be meaningful
            if current_score > baseline_score + 0.5:
                above_baseline.append(dimension)
            elif current_score < baseline_score - 0.5:
                below_baseline.append(dimension)

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
        Calculate average RASNA scores across baseline calls.

        Args:
            calls: List of baseline calls with completed evaluations

        Returns:
            dict: Average scores for each RASNA dimension
        """
        dimensions = ["rapport", "ask", "situation", "next_steps", "articulation"]
        averages = {}

        for dimension in dimensions:
            scores = []
            for call in calls:
                if call.evaluation_details:
                    rasna_scores = call.evaluation_details.get("rasna_scores", {})
                    score = rasna_scores.get(dimension, {}).get("score")
                    if score is not None:
                        scores.append(score)

            # Calculate average (or 0 if no scores)
            averages[dimension] = round(sum(scores) / len(scores), 2) if scores else 0.0

        return averages

    def _generate_summary(self, calls: List[Call], rasna_averages: Dict[str, float]) -> Dict:
        """
        Generate summary insights from baseline calls.

        Pure aggregation, no LLM. Identifies:
        - Common strengths (dimensions with avg score ≥ 8.0)
        - Common improvement themes (dimensions with avg score < 7.0)
        - Overall average score

        Args:
            calls: List of baseline calls
            rasna_averages: Calculated RASNA averages

        Returns:
            dict: Summary insights
        """
        # Identify strengths and improvement areas
        common_strengths = [dim for dim, score in rasna_averages.items() if score >= 8.0]
        common_improvement_themes = [dim for dim, score in rasna_averages.items() if score < 7.0]

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
            "created_at": baseline.created_at.isoformat(),
            "updated_at": baseline.updated_at.isoformat()
        }
