# Phase 10: Coaching Playbooks

## Overview

Phase 10 adds **Coaching Playbooks** - an optional, advisory layer that translates baseline and trend insights into actionable improvement suggestions. Playbooks help users (and teams) improve **future conversations**, not judge **past performance**.

This is **NOT** performance evaluation. This is **supportive coaching guidance** with strict non-judgmental language.

## What Are Coaching Playbooks?

Coaching playbooks provide:

- **Actionable improvement suggestions** based on patterns in baseline + trends
- **Supportive, non-judgmental language** focused on growth
- **Specific next steps** tied to RASNA dimensions
- **Confidence indicators** based on data quality
- **Zero automatic triggers** - users fetch coaching when they want it

## What It Is NOT

Coaching playbooks are **NOT**:

- ❌ Performance evaluations or rankings
- ❌ Mandatory training requirements
- ❌ Automated surveillance or monitoring
- ❌ Judgmental assessments of past calls
- ❌ LLM-generated advice (deterministic logic only, for now)
- ❌ Automatic notifications or interventions
- ❌ Stored in database (computed on-the-fly every time)

## Guiding Philosophy

> **"Help users improve FUTURE conversations, not judge PAST ones."**

Coaching exists to:
- **Support** improvement, not enforce compliance
- **Suggest** techniques, not mandate changes
- **Translate** data into actions, not scores into shame
- **Encourage** growth, not punish shortcomings

## Privacy Guarantees

### Personal Playbooks

- Use **ONLY** the user's own baseline and trend data
- **No cross-user comparison** or benchmarking
- User fetches their playbook explicitly via API
- Zero automatic exposure or notifications

### Team Playbooks

- Use **ONLY** aggregated team baseline and trend data
- **No individual performance exposure**
- **Owner/Manager access ONLY** (members cannot view team playbooks)
- Prevents members from comparing themselves to aggregates
- Respects Phase 9.1 trust principles

## How It Works

### Personal Coaching Playbook

Users can fetch personalized coaching suggestions based on their baseline and trends:

```typescript
GET /api/v1/coaching/personal
```

**Prerequisites:**
- User must have generated a personal baseline (Phase 7)
- Trends are optional (Phase 8) but improve suggestions

**What happens:**
1. Service fetches user's baseline (strengths, improvement areas)
2. Service fetches user's trends (improved/declined dimensions)
3. Identifies focus areas using deterministic logic
4. Generates specific, actionable coaching suggestions
5. Enforces supportive language (no harsh words)
6. Returns structured playbook with confidence level

**Example Response:**
```json
{
  "focus_areas": ["next_steps", "situation"],
  "strengths_to_preserve": ["rapport", "ask"],
  "suggested_actions": [
    "End every call by summarizing agreed action items and confirming who does what by when",
    "Spend the first 2-3 minutes understanding the customer's business environment and challenges"
  ],
  "tone": "supportive",
  "confidence": "high",
  "disclaimer": "These are suggestions to help improve future calls, not evaluations of past performance. Apply what feels helpful.",
  "generated_from": "both",
  "baseline_status": "current",
  "last_updated_context": "2024-01-20T10:00:00"
}
```

**Graceful Degradation:**
- Returns **204 No Content** if user has no baseline
- User sees clear message: "Generate your baseline first"

---

### Team Coaching Playbook

Team owners and managers can fetch team-level coaching suggestions:

```typescript
GET /api/v1/coaching/teams/{team_id}
```

**Prerequisites:**
- Team must have a baseline (Phase 9)
- Trends are optional but improve suggestions
- **Permission: Owner or Manager only**

**What happens:**
1. Service checks permission (owner/manager only)
2. Fetches team baseline (aggregated averages)
3. Fetches team trends (team-level evolution)
4. Identifies team focus areas using deterministic logic
5. Generates team-specific coaching actions
6. Enforces supportive language
7. Returns structured team playbook

**Example Response:**
```json
{
  "focus_areas": ["next_steps"],
  "strengths_to_preserve": ["rapport"],
  "suggested_actions": [
    "Consider adopting a team standard: every call ends with confirmed action items",
    "The team's rapport has improved - consider documenting what practices are working"
  ],
  "tone": "supportive",
  "confidence": "high",
  "disclaimer": "These are team-level suggestions based on aggregated patterns, not individual performance reviews. Use what helps your team grow.",
  "generated_from": "both",
  "agent_count": 5,
  "last_updated_context": "2024-01-20T15:00:00"
}
```

**Access Control:**
- **Members CANNOT view team playbooks** (prevents ranking/comparison)
- Only owners and managers can access
- Returns **403 Forbidden** for members with helpful message

**Graceful Degradation:**
- Returns **204 No Content** if team has no baseline
- Manager sees clear message: "Generate team baseline first"

## Coaching Logic (Deterministic)

### Focus Area Identification

**Personal:**
1. Dimensions with baseline score < 7.0 → focus area
2. Dimensions in baseline "common_improvement_themes" → focus area
3. Dimensions that declined in trends → **prioritized** focus area
4. Dimensions that improved are removed from focus (unless still low)

**Team:**
1. Dimensions with team average < 7.0 → team focus area
2. Dimensions that declined in team trends → **prioritized** focus area
3. Same logic as personal, but using aggregated team data

### Strength Identification

**Personal:**
1. Dimensions with baseline score ≥ 8.0 → strength
2. Dimensions in baseline "common_strengths" → strength

**Team:**
1. Dimensions with team average ≥ 8.0 → team strength

### Action Generation

Phase 10 uses **deterministic action templates** (no LLM yet):

| Dimension | Personal Action | Team Action |
|-----------|----------------|-------------|
| **rapport** | "Start calls by acknowledging the customer's context before diving into business topics" | "Consider a team workshop on building customer rapport in the first 60 seconds of calls" |
| **ask** | "Ask one clarifying question about the customer's current situation before presenting solutions" | "May help to develop a shared list of discovery questions the team finds most effective" |
| **situation** | "Spend the first 2-3 minutes understanding the customer's business environment and challenges" | "Worth trying team role-plays focused on uncovering customer business context" |
| **next_steps** | "End every call by summarizing agreed action items and confirming who does what by when" | "Consider adopting a team standard: every call ends with confirmed action items" |
| **articulation** | "After explaining a concept, pause and ask 'Does that make sense?' to ensure clarity" | "Often effective to have team members share examples of how they explain complex topics simply" |

**Limit:** Top 3 focus areas only (avoid overwhelming users)

**Trend Reinforcement:**
- If dimension improved in trends, add: *"Your {dimension} has improved recently - keep using the techniques that are working"*
- If team dimension improved, add: *"The team's {dimension} has improved - consider documenting what practices are working"*

### Confidence Assessment

**Personal Confidence:**
- **High**: ≥3 baseline calls + baseline is current + trends available
- **Medium**: ≥3 baseline calls OR trends available
- **Low**: <3 baseline calls + no trends

**Team Confidence:**
- **High**: ≥5 agents + team trends available
- **Medium**: 3-4 agents OR trends available
- **Low**: 2 agents (minimum) + no trends

## Language Enforcement

### Prohibited Words (Harsh, Judgmental)

Phase 10 **BLOCKS** these words in coaching suggestions:
- "poor", "weak", "failed", "inadequate", "insufficient"
- "bad", "terrible", "awful", "unacceptable", "subpar"

**Why:** Coaching is supportive, not punitive. Language shapes perception.

**Enforcement:** `_enforce_supportive_language()` validates all suggestions before returning. Raises error if prohibited words detected (defensive safeguard).

### Supportive Language Patterns

Coaching suggestions use:
- "consider", "may help", "often effective", "worth trying"
- "opportunity to", "could strengthen", "builds on"

**Examples:**
- ❌ BAD: "Your rapport is weak. Improve it."
- ✅ GOOD: "Consider starting calls by acknowledging the customer's context before diving into business topics"

- ❌ BAD: "Team failed at next_steps."
- ✅ GOOD: "Consider adopting a team standard: every call ends with confirmed action items"

## Why Playbooks Are NOT Rankings

### Concerns Addressed

**Concern:** "Playbooks feel like performance reviews."
- **Reality:** Playbooks are opt-in, advisory suggestions. Users fetch them when they want guidance. No automatic delivery.

**Concern:** "Team playbooks enable manager surveillance."
- **Reality:** Team playbooks use ONLY aggregated data. NO individual scores. Members cannot view team playbooks (prevents self-comparison).

**Concern:** "Suggestions feel mandatory."
- **Reality:** Every playbook includes disclaimer: *"Apply what feels helpful."* Tone is always "consider", "may help", never "must".

**Concern:** "Low confidence playbooks are punishing."
- **Reality:** Confidence indicates data quality, not user quality. Low confidence = "I have less data, so take suggestions lightly."

### Design Safeguards

1. **Zero Storage:** Playbooks computed on-the-fly, never stored. No "coaching history" database.
2. **Zero Auto-Triggers:** No background jobs, no notifications, no automatic coaching delivery.
3. **Explicit Fetch:** User/manager must explicitly request playbook via API.
4. **Graceful Degradation:** Returns 204 No Content if no data, not errors. No shame for missing data.
5. **Supportive Language:** Enforced programmatically. Suggestions sound like a coach, not a judge.
6. **Disclaimer Included:** Every playbook reminds users that suggestions are optional.

## API Endpoints

All under `/api/v1/coaching` prefix.

### `GET /coaching/personal`

Get personal coaching playbook.

**Auth Required**: Yes
**Permission**: Any authenticated user (fetches own data only)
**Body**: None

**Response (200 OK):**
```json
{
  "focus_areas": ["next_steps", "situation"],
  "strengths_to_preserve": ["rapport"],
  "suggested_actions": [
    "End every call by summarizing agreed action items and confirming who does what by when",
    "Spend the first 2-3 minutes understanding the customer's business environment and challenges"
  ],
  "tone": "supportive",
  "confidence": "medium",
  "disclaimer": "These are suggestions to help improve future calls, not evaluations of past performance. Apply what feels helpful.",
  "generated_from": "baseline",
  "baseline_status": "current",
  "last_updated_context": "2024-01-20T10:00:00"
}
```

**Response (204 No Content):**
- User has no baseline yet
- Frontend shows: "Generate your baseline first to get coaching suggestions"

**User Isolation**: Uses ONLY current user's data
**No Side Effects**: Pure GET, zero database writes
**Read-Only**: Computed on-the-fly every time

---

### `GET /coaching/teams/{team_id}`

Get team coaching playbook.

**Auth Required**: Yes
**Permission**: Owner or Manager only
**Body**: None

**Response (200 OK):**
```json
{
  "focus_areas": ["next_steps"],
  "strengths_to_preserve": ["rapport", "ask"],
  "suggested_actions": [
    "Consider adopting a team standard: every call ends with confirmed action items",
    "The team's rapport has improved - consider documenting what practices are working"
  ],
  "tone": "supportive",
  "confidence": "high",
  "disclaimer": "These are team-level suggestions based on aggregated patterns, not individual performance reviews. Use what helps your team grow.",
  "generated_from": "both",
  "agent_count": 5,
  "last_updated_context": "2024-01-20T15:00:00"
}
```

**Response (204 No Content):**
- Team has no baseline yet
- Frontend shows: "Generate team baseline first to get coaching suggestions"

**Response (403 Forbidden):**
- Current user is a **member** (not owner/manager)
- Message: *"Only team owners and managers can view team coaching playbooks. Members can view their personal coaching at GET /coaching/personal."*

**Access Control**: Owner/Manager only
**Privacy**: Uses ONLY aggregated team data (no individual exposure)
**No Side Effects**: Pure GET, zero database writes
**Read-Only**: Computed on-the-fly every time

## Implementation Details

### Service Layer

**File:** `backend/app/services/coaching_playbooks.py`

**Class:** `CoachingPlaybookService`

**Methods:**
- `generate_personal_playbook(user_id)` - Personal coaching logic
- `generate_team_playbook(team_id)` - Team coaching logic
- `_identify_focus_areas()` - Focus area detection
- `_identify_strengths()` - Strength detection
- `_refine_focus_with_trends()` - Trend-based refinement
- `_generate_coaching_actions()` - Action template mapping
- `_enforce_supportive_language(text)` - Language validation
- `_assess_confidence()` - Confidence level calculation

**Zero Database Writes:** Service contains NO `db.add()`, `db.commit()`, `db.update()`.

**Deterministic Logic:** No LLM calls (yet). Pure rule-based action mapping.

### Schema Layer

**File:** `backend/app/schemas/coaching_playbook.py`

**Schemas:**
- `CoachingPlaybook` - Base schema
- `PersonalCoachingPlaybook` - Personal playbook (extends base)
- `TeamCoachingPlaybook` - Team playbook (extends base)

**Key Fields:**
- `focus_areas`: Dimensions needing attention
- `strengths_to_preserve`: Dimensions performing well
- `suggested_actions`: Actionable next steps
- `tone`: Always "supportive"
- `confidence`: "high", "medium", or "low"
- `disclaimer`: Reminder that suggestions are advisory
- `generated_from`: "baseline", "trends", or "both"

### API Layer

**File:** `backend/app/api/v1/endpoints/coaching.py`

**Endpoints:**
- `GET /coaching/personal` - Personal playbook endpoint
- `GET /coaching/teams/{team_id}` - Team playbook endpoint

**Access Control:**
- Personal: Uses `get_current_user` dependency
- Team: Checks `team_service.can_view_team_aggregates()` for owner/manager

**Graceful Degradation:**
- Returns `Response(status_code=204)` if no data (not 404)
- No response body per HTTP semantics

## Data Flow

### Personal Playbook Flow

```
User Request: GET /coaching/personal
         ↓
Endpoint: coaching.get_personal_coaching()
         ↓
Auth: get_current_user (extract user_id)
         ↓
Service: CoachingPlaybookService.generate_personal_playbook(user_id)
         ↓
Fetch: BaselineService.get_baseline_for_user(user_id)
         ↓
Fetch: BaselineTrendService.get_trend_for_user(user_id)  [optional]
         ↓
Analyze: _identify_focus_areas(baseline.rasna_averages, baseline.summary)
         ↓
Analyze: _identify_strengths(baseline.rasna_averages, baseline.summary)
         ↓
Refine: _refine_focus_with_trends(focus, trend.declined, trend.improved)  [if trend exists]
         ↓
Generate: _generate_coaching_actions(focus, strengths, trend)
         ↓
Validate: _enforce_supportive_language(each action)
         ↓
Assess: _assess_confidence(baseline, trend)
         ↓
Return: PersonalCoachingPlaybook (or None if no baseline)
         ↓
Endpoint: Return 200 OK (playbook) OR 204 No Content (no baseline)
```

**Zero DB Writes:** Entire flow is read-only.

### Team Playbook Flow

```
Manager Request: GET /coaching/teams/{team_id}
         ↓
Endpoint: coaching.get_team_coaching(team_id)
         ↓
Auth: get_current_user (extract user_id)
         ↓
Permission Check: team_service.can_view_team_aggregates(team_id, user_id)
         ↓  [403 if member]
Service: CoachingPlaybookService.generate_team_playbook(team_id)
         ↓
Fetch: TeamBaselineService.get_latest_team_baseline(team_id)
         ↓
Fetch: TeamTrendService.get_team_trend(team_id)  [optional]
         ↓
Analyze: _identify_team_focus_areas(team_baseline.aggregated_averages)
         ↓
Analyze: _identify_team_strengths(team_baseline.aggregated_averages)
         ↓
Refine: _refine_team_focus_with_trends(focus, team_trend.declined, team_trend.improved)
         ↓
Generate: _generate_team_coaching_actions(focus, strengths, team_trend, agent_count)
         ↓
Validate: _enforce_supportive_language(each action)
         ↓
Assess: _assess_team_confidence(team_baseline, team_trend, agent_count)
         ↓
Return: TeamCoachingPlaybook (or None if no team baseline)
         ↓
Endpoint: Return 200 OK (playbook) OR 204 No Content (no baseline)
```

**Zero DB Writes:** Entire flow is read-only.
**Privacy:** Uses ONLY aggregated team data.

## Trust Principles (Phase 9.1 Alignment)

Phase 10 respects Phase 9.1 trust safeguards:

### 1. Calm, Non-Judgmental Language

✅ **Enforced:** `_enforce_supportive_language()` validates all suggestions.
✅ **Pattern:** "Consider", "may help", "often effective" (never "must", "poor", "failed").
✅ **Disclaimer:** Every playbook reminds users suggestions are optional.

### 2. Graceful Degradation

✅ **No Errors for Missing Data:** Returns 204 No Content if no baseline/trends.
✅ **Clear Messaging:** Endpoints include helpful error messages for 403/204 responses.
✅ **Low Confidence ≠ Punishment:** Low confidence indicates data quality, not user quality.

### 3. Privacy Isolation

✅ **Personal Playbooks:** Use ONLY user's own data. No cross-user access.
✅ **Team Playbooks:** Use ONLY aggregated data. No individual exposure.
✅ **Access Control:** Members CANNOT view team playbooks (prevents comparison).

### 4. Explicit User Action

✅ **No Auto-Triggers:** Users/managers must explicitly fetch playbooks via API.
✅ **No Background Jobs:** Zero scheduled tasks, zero automatic delivery.
✅ **No Storage:** Playbooks computed on-the-fly, never persisted.

### 5. Transparency

✅ **Confidence Indicators:** Users know when suggestions are based on limited data.
✅ **Generated From:** Users see if suggestions use baseline, trends, or both.
✅ **Agent Count (Team):** Managers see team size (context for aggregation quality).

## Future Enhancements (NOT Phase 10)

Phase 10 uses **deterministic logic** only. Future phases may add:

- **LLM-Enhanced Coaching:** GPT-4 generates personalized suggestions (while respecting language rules)
- **Custom Action Templates:** Users/managers can define their own coaching actions
- **Coaching History:** Opt-in storage of playbooks to track coaching evolution
- **Coaching Reminders:** Opt-in notifications when new coaching data available
- **Integration with Call Notes:** Link coaching suggestions to specific call moments

**Phase 10 Scope:** Deterministic, read-only, zero-storage, zero-LLM.

## Example Use Cases

### Use Case 1: New Agent Learning

**Scenario:** Junior sales agent has 3 baseline calls, no trends yet.

**Action:** Agent clicks "Get Coaching" in UI.

**Request:** `GET /api/v1/coaching/personal`

**Response:**
```json
{
  "focus_areas": ["situation", "next_steps"],
  "strengths_to_preserve": ["rapport"],
  "suggested_actions": [
    "Spend the first 2-3 minutes understanding the customer's business environment and challenges",
    "End every call by summarizing agreed action items and confirming who does what by when"
  ],
  "confidence": "medium",
  "generated_from": "baseline",
  "baseline_status": "current"
}
```

**Outcome:** Agent sees 2 specific techniques to try. No judgment, no pressure.

---

### Use Case 2: Team Slipping in Next Steps

**Scenario:** Sales team has improved in rapport but declined in next_steps.

**Action:** Manager generates team baseline (creates snapshot), then fetches coaching.

**Request:** `GET /api/v1/coaching/teams/1`

**Response:**
```json
{
  "focus_areas": ["next_steps"],
  "strengths_to_preserve": ["rapport"],
  "suggested_actions": [
    "Consider adopting a team standard: every call ends with confirmed action items",
    "The team's rapport has improved - consider documenting what practices are working"
  ],
  "confidence": "high",
  "agent_count": 5
}
```

**Outcome:** Manager sees team needs next_steps focus. Can run team workshop. Also sees rapport is improving (positive reinforcement).

---

### Use Case 3: No Baseline Yet

**Scenario:** User hasn't marked any calls as "Best Call" yet.

**Action:** User clicks "Get Coaching" in UI.

**Request:** `GET /api/v1/coaching/personal`

**Response:** `204 No Content`

**Frontend Shows:** *"Generate your baseline first to get coaching suggestions. Mark your best calls and click 'Generate My Baseline'."*

**Outcome:** Clear guidance on next steps. No shame for missing data.

---

### Use Case 4: Member Tries to View Team Playbook

**Scenario:** Team member (not owner/manager) tries to view team coaching.

**Action:** Member navigates to `/coaching/teams/1` in UI.

**Request:** `GET /api/v1/coaching/teams/1`

**Response:** `403 Forbidden`

**Message:** *"Only team owners and managers can view team coaching playbooks. Members can view their personal coaching at GET /coaching/personal."*

**Outcome:** Clear permission boundary. Member understands they can view personal coaching instead.

## Validation Checklist

Before deploying Phase 10:

- ✅ CoachingPlaybookService contains ZERO database writes (`db.add`, `db.commit`)
- ✅ Personal playbook uses ONLY user's own data
- ✅ Team playbook uses ONLY aggregated team data
- ✅ Team playbook enforces owner/manager permission check
- ✅ Endpoints return 204 No Content when no data available
- ✅ `_enforce_supportive_language()` validates all suggestions
- ✅ No prohibited words in action templates
- ✅ All suggestions use "consider", "may help", "often effective" patterns
- ✅ Every playbook includes disclaimer
- ✅ Confidence levels based on data quality, not user quality
- ✅ No automatic triggers or background jobs
- ✅ No playbook storage (computed on-the-fly)
- ✅ Phase 9.1 trust principles respected

## Summary

Phase 10 adds **optional, supportive coaching** without evaluation, ranking, or surveillance. Playbooks exist to help users improve future calls by translating baseline and trend insights into specific, actionable suggestions.

**Key Principles:**
- **Advisory, not evaluative:** Suggestions, not judgments
- **Opt-in, not automatic:** Users fetch when they want guidance
- **Supportive, not harsh:** Language matters
- **Privacy-first:** Personal data stays personal, team data stays aggregated
- **Read-only:** Zero database writes, zero storage
- **Transparent:** Confidence levels, data sources, disclaimers

**User Value:**
- Agents see concrete techniques to try (not vague "improve rapport")
- Managers see team patterns to address (not individual performance scores)
- Everyone gets growth-focused guidance (not punitive assessments)

**Trust Safeguards:**
- Language enforcement (no harsh words)
- Graceful degradation (no errors for missing data)
- Access control (members can't view team playbooks)
- Explicit fetch (no automatic delivery)
- Confidence indicators (users know data quality)

Phase 10 transforms data into action while preserving trust.
