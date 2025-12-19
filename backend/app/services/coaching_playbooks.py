from typing import Optional, Dict, List
import logging
from sqlalchemy.orm import Session

from app.services.baseline import BaselineService
from app.services.baseline_trends import BaselineTrendService
from app.services.team_baseline import TeamBaselineService
from app.services.team_trends import TeamTrendService

logger = logging.getLogger(__name__)

# Phase 10: Coaching thresholds
# These determine when to generate specific coaching suggestions
STRONG_DIMENSION_THRESHOLD = 8.0  # Dimension is a strength
IMPROVEMENT_NEEDED_THRESHOLD = 7.0  # Dimension needs focus
SIGNIFICANT_TREND_DELTA = 0.5  # Trend delta worth highlighting


class CoachingPlaybookService:
    """
    Phase 10: Coaching playbook generation service.

    Purpose:
    - Generate actionable improvement suggestions from baseline + trend data
    - Provide supportive, non-judgmental coaching guidance
    - Translate insights into specific next steps
    - ZERO database writes, ZERO auto-triggers

    This is NOT:
    - Performance evaluation or ranking
    - Automated surveillance or monitoring
    - Predictive scoring or ML forecasting
    - Mandatory training enforcement

    Philosophy:
    "Help users improve FUTURE conversations, not judge PAST ones."

    Privacy:
    - Personal playbooks use ONLY the user's own data
    - Team playbooks use ONLY aggregated team data (no individual exposure)
    - Respects existing Phase 9.1 trust principles
    """

    # Phase 10: Prohibited language (judgmental, punitive, harsh)
    PROHIBITED_WORDS = [
        "poor", "weak", "failed", "inadequate", "insufficient",
        "bad", "terrible", "awful", "unacceptable", "subpar"
    ]

    # Phase 10: Supportive language patterns
    SUPPORTIVE_PHRASES = [
        "consider", "may help", "often effective", "worth trying",
        "opportunity to", "could strengthen", "builds on"
    ]

    def __init__(self, db: Session):
        """
        Initialize coaching service with required dependencies.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.baseline_service = BaselineService(db)
        self.trend_service = BaselineTrendService(db)
        self.team_baseline_service = TeamBaselineService(db)
        self.team_trend_service = TeamTrendService(db)

    def generate_personal_playbook(self, user_id: int) -> Optional[Dict]:
        """
        Generate personal coaching playbook for a user.

        Combines:
        - Personal baseline (strengths, improvement areas)
        - Personal trends (what's improving, what's declining)

        Returns structured coaching suggestions:
        - Focus areas (dimensions needing attention)
        - Strengths to preserve (dimensions performing well)
        - Suggested actions (specific, actionable next steps)

        Phase 10: Returns None if insufficient data (graceful degradation).
        Minimum requirement: Personal baseline must exist.

        Args:
            user_id: ID of the user

        Returns:
            dict: Coaching playbook, or None if insufficient data
        """
        # Fetch personal baseline
        baseline = self.baseline_service.get_baseline_for_user(user_id)
        if not baseline:
            logger.info(
                f"Personal coaching playbook unavailable for user {user_id}: "
                f"No baseline exists. User must generate baseline first."
            )
            return None

        # Fetch personal trends (optional - playbook can work without trends)
        trend = self.trend_service.get_trend_for_user(user_id)

        # Analyze baseline data
        rasna_averages = baseline.get("rasna_averages", {})
        summary = baseline.get("summary", {})
        is_stale = baseline.get("is_stale", False)

        # Identify focus areas and strengths from baseline
        focus_areas = self._identify_focus_areas(
            rasna_averages,
            summary.get("common_improvement_themes", [])
        )
        strengths = self._identify_strengths(
            rasna_averages,
            summary.get("common_strengths", [])
        )

        # If trends available, refine focus areas based on recent changes
        if trend:
            focus_areas = self._refine_focus_with_trends(
                focus_areas,
                trend.get("declined_dimensions", []),
                trend.get("improved_dimensions", [])
            )

        # Generate specific coaching actions
        suggested_actions = self._generate_coaching_actions(
            focus_areas,
            strengths,
            trend
        )

        # Enforce supportive language
        suggested_actions = [
            self._enforce_supportive_language(action)
            for action in suggested_actions
        ]

        # Determine confidence level
        confidence = self._assess_confidence(baseline, trend)

        # Build playbook
        playbook = {
            "focus_areas": focus_areas,
            "strengths_to_preserve": strengths,
            "suggested_actions": suggested_actions,
            "tone": "supportive",
            "confidence": confidence,
            "disclaimer": (
                "These are suggestions to help improve future calls, "
                "not evaluations of past performance. Apply what feels helpful."
            ),
            "generated_from": "both" if trend else "baseline",
            "baseline_status": "stale" if is_stale else "current",
            "last_updated_context": baseline.get("updated_at")
        }

        logger.info(f"Generated personal coaching playbook for user {user_id}")
        return playbook

    def generate_team_playbook(self, team_id: int) -> Optional[Dict]:
        """
        Generate team coaching playbook.

        Phase 10: Uses ONLY aggregated team data.
        NO individual performance exposure.

        Combines:
        - Team baseline (aggregated averages)
        - Team trends (team-level evolution)

        Returns team-focused coaching suggestions:
        - Team focus areas (dimensions below team average)
        - Team strengths (dimensions performing well collectively)
        - Suggested team actions (practices to adopt)

        Args:
            team_id: ID of the team

        Returns:
            dict: Team coaching playbook, or None if insufficient data
        """
        # Fetch team baseline
        team_baseline = self.team_baseline_service.get_latest_team_baseline(team_id)
        if not team_baseline:
            logger.info(
                f"Team coaching playbook unavailable for team {team_id}: "
                f"No team baseline exists. Team owner must generate baseline first."
            )
            return None

        # Fetch team trends (optional)
        team_trend = self.team_trend_service.get_team_trend(team_id)

        # Analyze team baseline data
        aggregated_averages = team_baseline.get("aggregated_rasna_averages", {})
        agent_count = team_baseline.get("agent_count", 0)

        # Identify team focus areas and strengths
        focus_areas = self._identify_team_focus_areas(aggregated_averages)
        strengths = self._identify_team_strengths(aggregated_averages)

        # Refine with team trends if available
        if team_trend:
            focus_areas = self._refine_team_focus_with_trends(
                focus_areas,
                team_trend.get("declined_dimensions", []),
                team_trend.get("improved_dimensions", [])
            )

        # Generate team-level coaching actions
        suggested_actions = self._generate_team_coaching_actions(
            focus_areas,
            strengths,
            team_trend,
            agent_count
        )

        # Enforce supportive language
        suggested_actions = [
            self._enforce_supportive_language(action)
            for action in suggested_actions
        ]

        # Determine confidence level
        confidence = self._assess_team_confidence(team_baseline, team_trend, agent_count)

        # Build team playbook
        playbook = {
            "focus_areas": focus_areas,
            "strengths_to_preserve": strengths,
            "suggested_actions": suggested_actions,
            "tone": "supportive",
            "confidence": confidence,
            "disclaimer": (
                "These are team-level suggestions based on aggregated patterns, "
                "not individual performance reviews. Use what helps your team grow."
            ),
            "generated_from": "both" if team_trend else "baseline",
            "agent_count": agent_count,
            "last_updated_context": team_baseline.get("snapshot_created_at")
        }

        logger.info(f"Generated team coaching playbook for team {team_id} ({agent_count} agents)")
        return playbook

    # ==================== PERSONAL PLAYBOOK HELPERS ====================

    def _identify_focus_areas(
        self,
        rasna_averages: Dict[str, float],
        improvement_themes: List[str]
    ) -> List[str]:
        """
        Identify dimensions needing focus based on baseline data.

        Phase 10: Deterministic logic.
        Focus areas = dimensions below improvement threshold OR in improvement themes.

        Args:
            rasna_averages: RASNA dimension averages
            improvement_themes: Themes flagged as needing improvement

        Returns:
            list: Dimension names to focus on
        """
        focus = set()

        # Add dimensions below threshold
        for dimension, score in rasna_averages.items():
            if isinstance(score, (int, float)) and score < IMPROVEMENT_NEEDED_THRESHOLD:
                focus.add(dimension)

        # Add explicit improvement themes
        focus.update(improvement_themes)

        # Convert to sorted list for consistent ordering
        return sorted(list(focus))

    def _identify_strengths(
        self,
        rasna_averages: Dict[str, float],
        common_strengths: List[str]
    ) -> List[str]:
        """
        Identify strength dimensions to preserve.

        Phase 10: Strengths are dimensions performing well.
        Should be maintained while focusing on improvements.

        Args:
            rasna_averages: RASNA dimension averages
            common_strengths: Strengths identified in baseline

        Returns:
            list: Dimension names representing strengths
        """
        strengths = set()

        # Add dimensions above strength threshold
        for dimension, score in rasna_averages.items():
            if isinstance(score, (int, float)) and score >= STRONG_DIMENSION_THRESHOLD:
                strengths.add(dimension)

        # Add explicit common strengths
        strengths.update(common_strengths)

        return sorted(list(strengths))

    def _refine_focus_with_trends(
        self,
        initial_focus: List[str],
        declined_dimensions: List[str],
        improved_dimensions: List[str]
    ) -> List[str]:
        """
        Refine focus areas using trend data.

        Phase 10: Prioritize declining dimensions.
        Recent declines are higher priority than stable low scores.

        Args:
            initial_focus: Focus areas from baseline
            declined_dimensions: Dimensions that declined in trends
            improved_dimensions: Dimensions that improved in trends

        Returns:
            list: Refined focus areas (declining dims prioritized)
        """
        focus = set(initial_focus)

        # Add declining dimensions (high priority)
        focus.update(declined_dimensions)

        # Remove improved dimensions if they're no longer concerning
        # (keep if still in initial focus, meaning score still low)
        for improved_dim in improved_dimensions:
            if improved_dim in focus and improved_dim not in initial_focus:
                focus.discard(improved_dim)

        # Sort with declining dimensions first
        declined_set = set(declined_dimensions)
        focus_list = sorted(list(focus), key=lambda d: (d not in declined_set, d))

        return focus_list

    def _generate_coaching_actions(
        self,
        focus_areas: List[str],
        strengths: List[str],
        trend: Optional[Dict]
    ) -> List[str]:
        """
        Generate specific coaching actions for personal playbook.

        Phase 10: Deterministic, dimension-specific suggestions.
        NO generic advice. Each suggestion targets a RASNA dimension.

        Args:
            focus_areas: Dimensions needing focus
            strengths: Dimensions that are strengths
            trend: Optional trend data

        Returns:
            list: Specific, actionable coaching suggestions
        """
        actions = []

        # Dimension-specific action templates
        # Phase 10: These are deterministic mappings, not LLM-generated
        action_map = {
            "rapport": "Start calls by acknowledging the customer's context before diving into business topics",
            "ask": "Ask one clarifying question about the customer's current situation before presenting solutions",
            "situation": "Spend the first 2-3 minutes understanding the customer's business environment and challenges",
            "next_steps": "End every call by summarizing agreed action items and confirming who does what by when",
            "articulation": "After explaining a concept, pause and ask 'Does that make sense?' to ensure clarity"
        }

        # Generate actions for top 3 focus areas (avoid overwhelming with too many)
        for dimension in focus_areas[:3]:
            if dimension in action_map:
                actions.append(action_map[dimension])

        # If trending data shows improvement, acknowledge momentum
        if trend:
            improved = trend.get("improved_dimensions", [])
            if improved and improved[0] in action_map:
                # Add reinforcement for what's working
                top_improved = improved[0]
                actions.append(
                    f"Your {top_improved} has improved recently - keep using the techniques that are working"
                )

        # If no focus areas, suggest maintaining strengths
        if not actions and strengths:
            actions.append(
                f"Continue the practices that maintain your strength in {', '.join(strengths[:2])}"
            )

        # Fallback if no data available
        if not actions:
            actions.append(
                "Focus on building rapport at the start of each call and confirming next steps at the end"
            )

        return actions

    # ==================== TEAM PLAYBOOK HELPERS ====================

    def _identify_team_focus_areas(self, aggregated_averages: Dict[str, float]) -> List[str]:
        """
        Identify team focus areas from aggregated data.

        Phase 10: Same logic as personal, but using team averages.

        Args:
            aggregated_averages: Team RASNA averages

        Returns:
            list: Dimensions needing team focus
        """
        focus = []
        for dimension, score in aggregated_averages.items():
            if isinstance(score, (int, float)) and score < IMPROVEMENT_NEEDED_THRESHOLD:
                focus.append(dimension)
        return sorted(focus)

    def _identify_team_strengths(self, aggregated_averages: Dict[str, float]) -> List[str]:
        """
        Identify team strengths from aggregated data.

        Args:
            aggregated_averages: Team RASNA averages

        Returns:
            list: Team strength dimensions
        """
        strengths = []
        for dimension, score in aggregated_averages.items():
            if isinstance(score, (int, float)) and score >= STRONG_DIMENSION_THRESHOLD:
                strengths.append(dimension)
        return sorted(strengths)

    def _refine_team_focus_with_trends(
        self,
        initial_focus: List[str],
        declined_dimensions: List[str],
        improved_dimensions: List[str]
    ) -> List[str]:
        """
        Refine team focus areas using team trend data.

        Phase 10: Same prioritization logic as personal trends.

        Args:
            initial_focus: Initial team focus areas
            declined_dimensions: Team dimensions that declined
            improved_dimensions: Team dimensions that improved

        Returns:
            list: Refined team focus areas
        """
        # Same logic as personal, but for team-level data
        return self._refine_focus_with_trends(
            initial_focus,
            declined_dimensions,
            improved_dimensions
        )

    def _generate_team_coaching_actions(
        self,
        focus_areas: List[str],
        strengths: List[str],
        team_trend: Optional[Dict],
        agent_count: int
    ) -> List[str]:
        """
        Generate team-level coaching actions.

        Phase 10: Team actions suggest PRACTICES, not individual fixes.

        Args:
            focus_areas: Team focus dimensions
            strengths: Team strength dimensions
            team_trend: Optional team trend data
            agent_count: Number of agents in team

        Returns:
            list: Team-focused coaching suggestions
        """
        actions = []

        # Team-specific action templates
        # Phase 10: Focus on collective practices, not individual performance
        team_action_map = {
            "rapport": "Consider a team workshop on building customer rapport in the first 60 seconds of calls",
            "ask": "May help to develop a shared list of discovery questions the team finds most effective",
            "situation": "Worth trying team role-plays focused on uncovering customer business context",
            "next_steps": "Consider adopting a team standard: every call ends with confirmed action items",
            "articulation": "Often effective to have team members share examples of how they explain complex topics simply"
        }

        # Generate actions for top 3 team focus areas
        for dimension in focus_areas[:3]:
            if dimension in team_action_map:
                actions.append(team_action_map[dimension])

        # If team trend shows improvement, acknowledge collective progress
        if team_trend:
            improved = team_trend.get("improved_dimensions", [])
            if improved:
                actions.append(
                    f"The team's {improved[0]} has improved - consider documenting what practices are working"
                )

        # If small team, suggest peer learning
        if agent_count <= 5 and strengths:
            actions.append(
                "With a smaller team, peer shadowing can be valuable for sharing techniques"
            )

        # Fallback
        if not actions:
            actions.append(
                "Consider regular team debriefs where members share one technique that worked well in recent calls"
            )

        return actions

    # ==================== LANGUAGE ENFORCEMENT ====================

    def _enforce_supportive_language(self, text: str) -> str:
        """
        Enforce supportive, non-judgmental language.

        Phase 10: Validates coaching suggestions use appropriate tone.
        - NO harsh, punitive, or judgmental words
        - YES collaborative, growth-focused language

        Why this matters:
        - Coaching is NOT evaluation
        - Users should feel supported, not surveilled
        - Language shapes perception of the entire feature

        Args:
            text: Coaching suggestion text

        Returns:
            str: Validated text (unchanged if compliant)

        Raises:
            ValueError: If prohibited language detected (defensive safeguard)
        """
        text_lower = text.lower()

        # Check for prohibited words
        for prohibited in self.PROHIBITED_WORDS:
            if prohibited in text_lower:
                logger.error(
                    f"Coaching suggestion contains prohibited word '{prohibited}': {text}"
                )
                raise ValueError(
                    f"Coaching language validation failed: prohibited word '{prohibited}' detected. "
                    f"Coaching must use supportive language."
                )

        return text

    # ==================== CONFIDENCE ASSESSMENT ====================

    def _assess_confidence(self, baseline: Dict, trend: Optional[Dict]) -> str:
        """
        Assess confidence level for personal playbook.

        Phase 10: Confidence based on data quality and recency.

        High confidence:
        - Baseline exists with ≥3 calls
        - Baseline is current (not stale)
        - Trend data available

        Medium confidence:
        - Baseline exists with 1-2 calls
        - OR baseline is stale
        - No trend data

        Low confidence:
        - Baseline exists but minimal data

        Args:
            baseline: Personal baseline data
            trend: Optional trend data

        Returns:
            str: "high", "medium", or "low"
        """
        call_count = baseline.get("call_count", 0)
        is_stale = baseline.get("is_stale", False)
        has_trend = trend is not None

        if call_count >= 3 and not is_stale and has_trend:
            return "high"
        elif call_count >= 3 or has_trend:
            return "medium"
        else:
            return "low"

    def _assess_team_confidence(
        self,
        team_baseline: Dict,
        team_trend: Optional[Dict],
        agent_count: int
    ) -> str:
        """
        Assess confidence level for team playbook.

        Phase 10: Team confidence based on aggregation quality.

        High confidence:
        - ≥5 agents in team
        - Team trend data available

        Medium confidence:
        - 3-4 agents in team
        - OR trend data available

        Low confidence:
        - 2 agents (minimum for privacy)
        - No trend data

        Args:
            team_baseline: Team baseline data
            team_trend: Optional team trend data
            agent_count: Number of agents in team

        Returns:
            str: "high", "medium", or "low"
        """
        has_trend = team_trend is not None

        if agent_count >= 5 and has_trend:
            return "high"
        elif agent_count >= 3 or has_trend:
            return "medium"
        else:
            return "low"
