from typing import Optional
from app.schemas.call import EvaluationResult, RasnaScore


class EvaluationService:
    """
    RASNA evaluation service with deterministic mock output
    """

    async def evaluate_call(
        self,
        transcription_text: Optional[str],
        call_context: dict
    ) -> dict:
        """
        Evaluate sales call using RASNA framework

        RASNA Framework:
        - Rapport: Building connection and trust
        - Situation: Understanding customer's current state
        - Pain: Identifying customer's challenges
        - Need: Articulating what customer needs
        - Ask: Closing and next steps

        Returns deterministic mock evaluation based on call context

        TODO: Replace with actual LLM-based evaluation logic:
        1. Parse transcription into conversation segments
        2. Use LLM to identify RASNA components in conversation
        3. Score each component based on effectiveness
        4. Generate actionable feedback using LLM
        5. Provide specific quotes and timestamps
        """

        # Deterministic mock based on lead_type and call_stage
        lead_type = call_context.get("lead_type", "warm")
        call_stage = call_context.get("call_stage", "main")
        deck_shared = call_context.get("deck_shared", False)

        # Base scores vary by lead type (deterministic)
        base_scores = self._get_base_scores(lead_type)

        # Adjust scores based on call stage
        adjusted_scores = self._adjust_for_stage(base_scores, call_stage)

        # Bonus for deck sharing
        if deck_shared:
            adjusted_scores["need"] = min(100, adjusted_scores["need"] + 5)
            adjusted_scores["ask"] = min(100, adjusted_scores["ask"] + 5)

        # Calculate overall
        overall = sum(adjusted_scores.values()) // 5

        # Create RASNA score object
        rasna_score = RasnaScore(
            rapport=adjusted_scores["rapport"],
            situation=adjusted_scores["situation"],
            pain=adjusted_scores["pain"],
            need=adjusted_scores["need"],
            ask=adjusted_scores["ask"],
            overall=overall
        )

        # Generate deterministic feedback
        strengths = self._generate_strengths(adjusted_scores, call_context)
        improvements = self._generate_improvements(adjusted_scores, call_context)
        next_focus = self._determine_next_focus(adjusted_scores)

        # Build evaluation result
        evaluation_result = EvaluationResult(
            scores=rasna_score,
            strengths=strengths,
            improvements=improvements,
            next_call_focus=next_focus
        )

        return {
            "result": evaluation_result.model_dump(),
            "status": "completed"
        }

    def _get_base_scores(self, lead_type: str) -> dict:
        """Deterministic base scores by lead type"""
        scores = {
            "hot": {
                "rapport": 85,
                "situation": 82,
                "pain": 88,
                "need": 86,
                "ask": 84
            },
            "warm": {
                "rapport": 75,
                "situation": 72,
                "pain": 70,
                "need": 73,
                "ask": 68
            },
            "cold": {
                "rapport": 60,
                "situation": 58,
                "pain": 55,
                "need": 62,
                "ask": 52
            }
        }
        return scores.get(lead_type, scores["warm"])

    def _adjust_for_stage(self, scores: dict, stage: str) -> dict:
        """Adjust scores based on call stage"""
        adjusted = scores.copy()

        if stage == "qualification":
            # Qualification calls focus on situation and pain
            adjusted["situation"] = min(100, adjusted["situation"] + 8)
            adjusted["pain"] = min(100, adjusted["pain"] + 5)
            adjusted["ask"] = max(0, adjusted["ask"] - 10)

        elif stage == "main":
            # Main calls should be balanced
            pass  # Use base scores

        elif stage == "follow-up":
            # Follow-up calls focus on need and ask
            adjusted["rapport"] = min(100, adjusted["rapport"] + 10)
            adjusted["need"] = min(100, adjusted["need"] + 8)
            adjusted["ask"] = min(100, adjusted["ask"] + 12)

        return adjusted

    def _generate_strengths(self, scores: dict, context: dict) -> list[str]:
        """Generate deterministic strengths based on scores"""
        strengths = []

        if scores["rapport"] >= 80:
            strengths.append("Strong rapport building with active listening")

        if scores["situation"] >= 75:
            strengths.append("Clear understanding of customer's current situation")

        if scores["pain"] >= 75:
            strengths.append("Effective pain point identification")

        if scores["need"] >= 75:
            strengths.append("Well-articulated solution positioning")

        if scores["ask"] >= 75:
            strengths.append("Clear call-to-action and next steps")

        if context.get("deck_shared"):
            strengths.append("Good use of visual aids to support presentation")

        # Ensure at least 2 strengths
        if len(strengths) < 2:
            strengths.append("Maintained professional tone throughout")
            strengths.append("Stayed on track with call objectives")

        return strengths[:4]  # Max 4 strengths

    def _generate_improvements(self, scores: dict, context: dict) -> list[str]:
        """Generate deterministic improvements based on scores"""
        improvements = []

        if scores["rapport"] < 70:
            improvements.append("Build stronger rapport before diving into business discussion")

        if scores["situation"] < 70:
            improvements.append("Ask more open-ended questions to understand customer situation")

        if scores["pain"] < 70:
            improvements.append("Dig deeper into pain points with follow-up questions")

        if scores["need"] < 70:
            improvements.append("Connect solution features more directly to customer needs")

        if scores["ask"] < 70:
            improvements.append("Strengthen the close with clearer next steps and commitments")

        if not context.get("deck_shared") and context.get("call_stage") == "main":
            improvements.append("Consider sharing deck to visualize solution benefits")

        # Ensure at least 2 improvements
        if len(improvements) < 2:
            improvements.append("Reduce filler words for more confident delivery")
            improvements.append("Allow more silence for customer to process and respond")

        return improvements[:4]  # Max 4 improvements

    def _determine_next_focus(self, scores: dict) -> str:
        """Determine primary focus area for next call"""
        # Find lowest scoring component
        min_score = min(scores.values())

        focus_map = {
            "rapport": "Focus on building deeper rapport and trust in opening",
            "situation": "Spend more time understanding customer's current state",
            "pain": "Probe deeper into pain points and their business impact",
            "need": "Better articulate how solution addresses specific needs",
            "ask": "Strengthen close with concrete next steps and commitments"
        }

        for component, score in scores.items():
            if score == min_score:
                return focus_map.get(component, "Continue balanced approach across all RASNA components")

        return "Continue balanced approach across all RASNA components"

    def get_evaluation_status(self, call_id: int) -> dict:
        """
        Get status of evaluation job

        TODO: Implement status checking for async evaluation jobs
        """
        return {
            "status": "completed",
            "progress": 100
        }
