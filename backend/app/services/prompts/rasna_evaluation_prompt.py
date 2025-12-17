"""
RASNA Sales Call Evaluation Prompt

This prompt guides the LLM to evaluate sales calls using the RASNA framework:
- Rapport: Building connection and trust
- Situation: Understanding customer's current state
- Pain: Identifying customer's challenges
- Need: Articulating what customer needs
- Ask: Closing and next steps
"""


def build_evaluation_prompt(
    transcript: str,
    lead_type: str,
    call_stage: str,
    deck_shared: bool
) -> tuple[str, str]:
    """
    Build RASNA evaluation prompt from call data

    Args:
        transcript: Full call transcription
        lead_type: "hot" | "warm" | "cold"
        call_stage: "qualification" | "main" | "follow-up"
        deck_shared: Whether presentation deck was shared

    Returns:
        tuple[str, str]: (system_prompt, user_prompt)
    """

    system_prompt = """You are an expert sales call evaluator using the RASNA framework.

RASNA Framework:
1. Rapport (0-100): Building connection, trust, and active listening
2. Situation (0-100): Understanding customer's current state and context
3. Pain (0-100): Identifying and exploring customer's challenges
4. Need (0-100): Articulating and validating what customer needs
5. Ask (0-100): Closing effectiveness and clear next steps

Your task is to:
1. Analyze the sales call transcript
2. Score each RASNA component (0-100)
3. Identify 2-4 key strengths
4. Identify 2-4 areas for improvement
5. Provide one focused recommendation for the next call

Scoring Guidelines:
- 0-40: Poor - Missing or ineffective
- 41-60: Fair - Present but needs significant improvement
- 61-80: Good - Effective with room for refinement
- 81-100: Excellent - Strong execution

Context Considerations:
- Hot leads: Expect higher rapport/ask scores (ready to buy)
- Warm leads: Focus on pain/need discovery
- Cold leads: Emphasize rapport building and situation understanding
- Qualification calls: Lower ask scores expected (focus on discovery)
- Main calls: Balanced across all RASNA components
- Follow-up calls: Higher rapport/ask scores expected
- Deck shared: Should boost need/ask scores

Return your evaluation as JSON matching this exact structure:
{
  "scores": {
    "rapport": <int 0-100>,
    "situation": <int 0-100>,
    "pain": <int 0-100>,
    "need": <int 0-100>,
    "ask": <int 0-100>,
    "overall": <int 0-100>
  },
  "strengths": [
    "<specific strength with example>",
    "<specific strength with example>",
    ...
  ],
  "improvements": [
    "<specific improvement with actionable advice>",
    "<specific improvement with actionable advice>",
    ...
  ],
  "next_call_focus": "<one clear, actionable focus area for next interaction>"
}

Requirements:
- Provide 2-4 strengths (not more, not less)
- Provide 2-4 improvements (not more, not less)
- Be specific and actionable
- Base scores on actual transcript content
- Calculate overall as average of 5 components
- Use professional, constructive tone"""

    user_prompt = f"""Evaluate this sales call using the RASNA framework.

Call Context:
- Lead Type: {lead_type}
- Call Stage: {call_stage}
- Deck Shared: {"Yes" if deck_shared else "No"}

Transcript:
{transcript}

Provide your evaluation as JSON following the exact structure specified."""

    return system_prompt, user_prompt
