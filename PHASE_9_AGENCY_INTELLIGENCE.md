# Phase 9: Agency & Team Intelligence

## Overview

Phase 9 adds **Team-Level Aggregated Intelligence** - a manager/agency feature that enables viewing team-wide performance insights WITHOUT violating individual ownership, privacy, or trust.

This is **NOT** individual performance tracking. This is **aggregated team-level analytics** with strict privacy guarantees.

## What Is Team Intelligence?

Team intelligence provides:

- **Aggregated RASNA averages** across team members
- **Team-level trend analysis** (comparing team snapshots)
- **Manager visibility** into team performance evolution
- **Zero interference** with personal baselines

## What It Is NOT

Team intelligence is **NOT**:

- ❌ Individual performance tracking (personal data remains private)
- ❌ Cross-user raw call data access
- ❌ Automatic enrollment or data sharing
- ❌ Replacement for personal baselines (Phase 7)
- ❌ LLM-based analysis or forecasting
- ❌ Background jobs or automatic aggregation

## Privacy Guarantees

### Individual Performance Remains Private

- **Members** can ONLY view their own personal data
- **Members** CANNOT see team aggregates or other members' scores
- **No individual scores** are exposed in team views
- **No raw call data** is accessible across users

### Aggregation Safety

- Team baselines show ONLY averaged scores
- Requires minimum team size (2+ members) for aggregation
- Individual scores cannot be reverse-engineered from team averages
- Snapshots are created ONLY on explicit manager action

### Permission Model

| Role | Can View Team Aggregates | Can Generate Team Baseline | Can View Personal Data |
|------|-------------------------|---------------------------|----------------------|
| **Owner** | ✅ Yes | ✅ Yes | ✅ Yes (own only) |
| **Manager** | ✅ Yes | ✅ Yes | ✅ Yes (own only) |
| **Member** | ❌ No | ❌ No | ✅ Yes (own only) |

## How It Works Safely

### 1. Explicit Team Creation

Teams are created explicitly by an owner (agency manager):

```typescript
POST /api/v1/teams/
{
  "name": "Sales Team Alpha"
}
```

- Creator becomes **owner**
- No other members added until explicitly invited
- No auto-enrollment

### 2. Explicit Member Invitation

Owners and managers can invite members:

```typescript
POST /api/v1/teams/{team_id}/members
{
  "user_id": 123,
  "role": "manager"  // or "member"
}
```

- No automatic acceptance (future: invitation flow)
- Role assignment is explicit
- Members have NO access to team aggregates

### 3. Explicit Baseline Generation

Team baselines are created ONLY when managers explicitly request them:

```typescript
POST /api/v1/teams/{team_id}/baseline/generate
```

**What happens:**
1. Service fetches all team member user IDs
2. For each member, collects completed evaluation scores
3. Computes averaged RASNA scores across all members
4. Creates immutable team baseline snapshot
5. NO individual scores stored or exposed

**Privacy safeguard:**
- Requires minimum 2 team members for aggregation
- Only aggregated averages are stored
- Individual call data is NEVER exposed

### 4. Team Trend Analysis

Compare last 2 team snapshots to show team evolution:

```typescript
GET /api/v1/teams/{team_id}/trends
```

**Returns:**
- Improved dimensions (at team level)
- Declined dimensions (at team level)
- Stable dimensions
- Delta values (aggregate changes only)

**Privacy safeguard:**
- Returns 204 No Content if <2 snapshots
- Shows ONLY team-wide deltas
- NO individual performance data

## API Endpoints

All under `/api/v1/teams` prefix.

### `POST /teams`

Create a new team.

**Auth Required**: Yes
**Permission**: Any authenticated user
**Body**:
```json
{
  "name": "Sales Team Alpha"
}
```

**Response**:
```json
{
  "id": 1,
  "name": "Sales Team Alpha",
  "created_by": 5,
  "created_at": "2024-01-20T10:00:00",
  "role": "owner"
}
```

---

### `GET /teams`

Get all teams current user is a member of.

**Auth Required**: Yes
**Permission**: Any authenticated user
**Response**:
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Sales Team Alpha",
      "created_by": 5,
      "created_at": "2024-01-20T10:00:00",
      "role": "owner"
    }
  ]
}
```

---

### `POST /teams/{team_id}/members`

Add a member to a team.

**Auth Required**: Yes
**Permission**: Owner or Manager only
**Body**:
```json
{
  "user_id": 123,
  "role": "manager"  // or "member"
}
```

**Response**:
```json
{
  "team_id": 1,
  "user_id": 123,
  "role": "manager",
  "joined_at": "2024-01-20T11:00:00"
}
```

**Errors**:
- `400`: Invalid role or user doesn't exist
- `403`: Only owners/managers can invite members

---

### `GET /teams/{team_id}/members`

Get all members of a team.

**Auth Required**: Yes
**Permission**: Any team member
**Response**:
```json
{
  "members": [
    {
      "user_id": 5,
      "name": "Alice Manager",
      "email": "alice@example.com",
      "role": "owner",
      "joined_at": "2024-01-20T10:00:00"
    },
    {
      "user_id": 123,
      "name": "Bob Agent",
      "email": "bob@example.com",
      "role": "member",
      "joined_at": "2024-01-20T11:00:00"
    }
  ]
}
```

**Note**: NO personal performance data included.

---

### `POST /teams/{team_id}/baseline/generate`

Generate team baseline from aggregated evaluations.

**Auth Required**: Yes
**Permission**: Owner or Manager only
**Body**: None

**Response**:
```json
{
  "team_id": 1,
  "aggregated_rasna_averages": {
    "rapport": 7.8,
    "ask": 8.2,
    "situation": 7.5,
    "next_steps": 8.0,
    "articulation": 8.3
  },
  "agent_count": 5,
  "snapshot_created_at": "2024-01-20T15:00:00"
}
```

**Errors**:
- `400`: Team has <2 members (privacy requirement)
- `400`: No completed evaluations found
- `403`: Only owners/managers can generate team baselines

---

### `GET /teams/{team_id}/baseline`

Get latest team baseline.

**Auth Required**: Yes
**Permission**: Owner or Manager only
**Response**:
```json
{
  "team_id": 1,
  "aggregated_rasna_averages": {
    "rapport": 7.8,
    "ask": 8.2,
    "situation": 7.5,
    "next_steps": 8.0,
    "articulation": 8.3
  },
  "agent_count": 5,
  "snapshot_created_at": "2024-01-20T15:00:00"
}
```

**Errors**:
- `403`: Members cannot view team aggregates
- `404`: No team baseline generated yet

---

### `GET /teams/{team_id}/trends`

Get team baseline evolution trends.

**Auth Required**: Yes
**Permission**: Owner or Manager only
**Response** (when ≥2 snapshots exist):
```json
{
  "improved_dimensions": ["rapport", "articulation"],
  "declined_dimensions": ["ask"],
  "stable_dimensions": ["situation", "next_steps"],
  "dimension_deltas": {
    "rapport": 0.7,
    "ask": -0.6,
    "situation": 0.2,
    "next_steps": -0.1,
    "articulation": 0.9
  },
  "summary": "The team has improved in rapport, articulation (strongest: articulation +0.9). These areas declined at team level: ask",
  "snapshots_compared": 2,
  "latest_snapshot_date": "2024-01-25T15:00:00",
  "previous_snapshot_date": "2024-01-20T15:00:00",
  "latest_agent_count": 6,
  "previous_agent_count": 5
}
```

**Response** (when <2 snapshots exist):
- HTTP `204 No Content`
- No body (per HTTP semantics)

**Errors**:
- `403`: Members cannot view team trends

## Database Schema

### New Tables

#### `teams`

```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_created_by ON teams(created_by);
```

---

#### `team_members`

```sql
CREATE TABLE team_members (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role TEXT NOT NULL CHECK (role IN ('owner', 'manager', 'member')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_user UNIQUE (team_id, user_id)
);

CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
```

---

#### `team_baseline_snapshots`

```sql
CREATE TABLE team_baseline_snapshots (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    aggregated_rasna_averages JSON NOT NULL,
    agent_count INTEGER NOT NULL,
    snapshot_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_baseline_snapshots_team_id ON team_baseline_snapshots(team_id);
```

**Design Decision**: Separate snapshot table (vs adding to teams) for:
- Historical trend tracking
- Immutable snapshot preservation
- Clean separation of current vs. historical data

## Why Team Baselines ≠ Personal Baselines

| Aspect | Personal Baseline (Phase 7) | Team Baseline (Phase 9) |
|--------|----------------------------|------------------------|
| **Scope** | Individual user only | Aggregated across team |
| **Data** | User's best calls | All team members' evaluations |
| **Access** | User owns and views | Only owners/managers view |
| **Privacy** | User's personal data | Aggregated averages only |
| **Purpose** | Self-reflection | Team performance insights |
| **Triggers** | User marks "Best Call" | Manager generates explicitly |

## Architectural Benefits

### Isolation

- Separate models (`Team`, `TeamMember`, `TeamBaselineSnapshot`)
- Separate repositories
- Separate services (`TeamService`, `TeamBaselineService`, `TeamTrendService`)
- Separate endpoints (`/api/v1/teams/*`)

Easy to:
- Disable if needed
- Remove without breaking Phase 1-8
- Extend with more team features

### Non-Breaking Design

- ✅ Phase 1-8 behavior unchanged
- ✅ Personal baselines still work identically
- ✅ User isolation maintained
- ✅ No data migration for existing users
- ✅ All team features are opt-in

### Extensibility

Future phases can build on this:
- **Phase 10**: Team coaching recommendations
- **Phase 11**: Cross-team benchmarking (with explicit consent)
- **Phase 12**: Agency-wide analytics dashboards

## Example User Journeys

### Journey 1: Agency Owner Creates Team

1. Alice (agency owner) creates team: `POST /teams {"name": "Sales Team Alpha"}`
2. Alice is automatically assigned "owner" role
3. Alice invites Bob and Carol as members: `POST /teams/1/members {"user_id": 2, "role": "member"}`
4. Bob and Carol can upload calls and view their own data (Phase 1-7)
5. Bob and Carol **CANNOT** see team aggregates

### Journey 2: Manager Generates Team Baseline

1. Alice promotes Dave to manager: (future: role update endpoint)
2. Dave generates team baseline: `POST /teams/1/baseline/generate`
3. System aggregates all team members' completed evaluations
4. Team baseline shows averaged scores (NO individual scores)
5. Dave views team baseline: `GET /teams/1/baseline`
6. Bob (member) tries to view team baseline → `403 Forbidden`

### Journey 3: Tracking Team Evolution

1. Week 1: Dave generates first team baseline → Snapshot #1 created
2. Week 2: Team members upload more calls, improve skills
3. Week 2: Dave generates second team baseline → Snapshot #2 created
4. Dave views team trends: `GET /teams/1/trends`
5. Trends show team improved in "rapport" and "articulation"
6. Dave shares aggregate insights with team (manually, outside system)
7. Individual member performance remains private

## Why This Design Avoids Trust Erosion

### No Surveillance

- Members are NOT automatically tracked
- Members explicitly join teams (invitation model)
- Members know what data is aggregated (documented)
- Members cannot be identified from team averages

### No Forced Sharing

- Personal baselines remain private
- Members choose which calls to mark as "Best Call"
- Members can leave teams (future: leave endpoint)
- No cross-user raw data access ever

### Transparent Aggregation

- Clear documentation of what's aggregated
- Minimum team size requirement (2+) for privacy
- Only averages stored, never individual scores
- Managers see same data members would see if they had permission

### Manager Boundaries

- Managers CANNOT access individual call transcripts
- Managers CANNOT see individual evaluation scores
- Managers CANNOT modify member's personal baselines
- Managers can ONLY view aggregated team averages

## Safety Checklist

Before using Phase 9 in production, verify:

- [ ] Team baselines show ONLY aggregated averages
- [ ] Members cannot view team aggregates (403 enforced)
- [ ] Individual call data is never exposed via team APIs
- [ ] Minimum team size (2+) enforced for aggregation
- [ ] Phase 1-8 functionality unchanged
- [ ] Personal baselines work identically to before
- [ ] All backend files compile
- [ ] API returns proper HTTP status codes (403, 404, 204)

## Summary

Phase 9 provides **safe, aggregated, opt-in team intelligence** that helps managers understand team performance evolution WITHOUT violating individual privacy or trust.

**Key Principle**: "Help managers see the team's aggregate progress while keeping individual performance private."

No surveillance. No forced sharing. No trust erosion. Pure team-level aggregated analytics.

---

# Phase 9.1: Trust & UX Safeguards

## Overview

Phase 9.1 is a **hardening and UX refinement phase** focused on preventing misinterpretation and reinforcing trust guarantees. This phase does NOT add new features—it makes existing features **psychologically safer** and **semantically clearer**.

## Why UX Wording Matters

Team intelligence features carry **inherent trust risk**. Without careful UX design, they can be perceived as:

- ❌ Surveillance tools
- ❌ Individual performance tracking
- ❌ Ranking systems
- ❌ Punitive mechanisms

**Phase 9.1 prevents this** by making privacy guarantees **visually and semantically explicit**.

## Backend Hardening (Phase 9.1)

### 1. Strict Minimum Team Size Enforcement

**Before (Phase 9):**
- Checked team size, returned error

**After (Phase 9.1):**
- Checked team size with **explicit privacy explanation**
- Added clear warning logs when aggregation blocked
- Error messages explain **why** minimum size protects privacy

**Example error message:**
```
"Team must have at least 2 members for aggregation.
This protects individual privacy by preventing reverse-engineering of scores."
```

**Logging:**
```python
logger.warning(
    f"Team baseline generation blocked for team {team_id}: "
    f"Only {len(member_ids)} member(s), minimum 2 required for privacy"
)
```

### 2. Minimum Snapshot Enforcement for Trends

**What happens:**
- `GET /teams/{id}/trends` returns `None` if <2 snapshots
- API returns `204 No Content` (no body)
- Clear log message explains why trends unavailable

**Logging:**
```python
logger.info(
    f"Team trend analysis unavailable for team {team_id}: "
    f"Only {len(snapshots)} snapshot(s), minimum 2 required for trend analysis"
)
```

### 3. Graceful Degradation with Transparency

All aggregation failures now log:
- **Why** the operation failed
- **What** data was missing
- **How many** members/snapshots were insufficient

This helps debugging **without** exposing individual data.

## UX Language Guidelines

### ✅ Safe Language

**Use these phrases:**
- "Team average"
- "Aggregated team data"
- "No individual scores shown"
- "Team-level insight"
- "Averaged across team"
- "Aggregated (no individual attribution)"

**Show role awareness:**
- "You are viewing this as a Manager"
- "Members cannot see this data"
- "Only owners and managers can view team aggregates"

### ❌ Unsafe Language

**Never say:**
- "Performance of agents"
- "Employee rankings"
- "Individual scores"
- "Who performed best"
- "Compare agents"
- "Track individual performance"

## Frontend UX Safeguards (Guidance)

When implementing team dashboards, these UX signals should be included:

### 1. Team Baseline Cards

**Every team aggregate card must include:**

```tsx
<div className="text-xs text-gray-600 mb-2">
  📊 Aggregated team data — no individual scores shown
</div>
```

**Visual hierarchy:**
- Team name (prominent)
- Role indicator: "You are viewing as Manager"
- Aggregated data (with disclaimer)
- Clear "Generate Baseline" button (manager only)

### 2. Role Awareness Banner

**For managers/owners:**
```tsx
<div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
  <p className="text-sm text-blue-900">
    You are viewing team aggregates as a <strong>Manager</strong>.
    Members cannot see this data.
  </p>
</div>
```

**For members (if they somehow access team page):**
```tsx
<div className="bg-gray-50 border border-gray-200 rounded p-4">
  <p className="text-sm text-gray-700">
    Team-level aggregated data is only visible to owners and managers.
    You can view your own personal baseline in your dashboard.
  </p>
</div>
```

### 3. Trend Availability Messaging

**When `GET /teams/{id}/trends` returns 204:**

```tsx
<div className="bg-gray-50 rounded-lg p-6 text-center">
  <p className="text-sm text-gray-600">
    Team trends appear after at least two team baselines are generated.
  </p>
  <p className="text-xs text-gray-500 mt-2">
    Generate your team's baseline from the team dashboard.
  </p>
</div>
```

**Calm, neutral tone—not an error.**

### 4. Empty States

**No team baseline yet:**
```tsx
<div className="bg-white rounded-lg p-8 text-center border border-gray-200">
  <p className="text-gray-600 mb-2">No team baseline generated yet</p>
  <p className="text-sm text-gray-500">
    Team baselines show aggregated averages across all team members.
  </p>
  <button className="mt-4 ...">Generate Team Baseline</button>
</div>
```

**Emphasis:**
- "Aggregated averages"
- "Across all team members"
- No individual attribution

### 5. Staleness Awareness (Future)

If team composition changes (new members join after last snapshot):

```tsx
{teamCompositionChanged && (
  <div className="bg-amber-50 border border-amber-200 rounded p-4 mb-4">
    <h3 className="text-sm font-medium text-amber-900 mb-1">
      Team composition changed
    </h3>
    <p className="text-sm text-amber-800">
      New members joined since last baseline.
      Regenerate baseline for updated team averages.
    </p>
  </div>
)}
```

**No auto-regeneration. User stays in control.**

## How Aggregation Protects Teams

### Privacy by Design

**Problem:** If team has only 1 member, team average = individual score.
**Solution:** Minimum 2 members enforced for all aggregation.

**Problem:** Members might fear being identifiable in small teams.
**Solution:** Clear messaging that only averages are shown.

**Example:**
- Team of 5 members
- RASNA rapport scores: [7.5, 8.0, 8.2, 7.8, 8.5]
- **Team average shown:** 8.0
- **Individual scores:** NEVER exposed

Even if a member leaves, historical snapshots remain aggregated.

### Why Members Never See Team Analytics

**Design Decision:** Members can ONLY view their personal data.

**Rationale:**
1. **Prevents social comparison anxiety**
   - Members don't know if they're "above" or "below" team average
   - No implied ranking

2. **Prevents gaming the system**
   - Members can't adjust behavior to match team averages
   - Focus stays on personal improvement (Phase 7)

3. **Maintains trust**
   - Members know managers see only aggregates
   - No fear of individual score exposure

4. **Avoids toxic competition**
   - No leaderboards
   - No peer pressure based on team metrics

## Why This Avoids Fear-Based Adoption Failure

### Common Failure Modes (Other Systems)

**Failure Mode 1: Surveillance Perception**
- Problem: Users perceive team analytics as "Big Brother watching"
- Result: Resistance, minimal adoption, trust erosion

**Phase 9.1 Solution:**
- Clear role boundaries ("Members cannot see this")
- No automatic tracking
- Explicit "aggregated only" labels

**Failure Mode 2: Individual Attribution**
- Problem: Users fear being identified from aggregated data
- Result: Anxiety, reduced engagement

**Phase 9.1 Solution:**
- Minimum team size (2+) enforced
- "No individual scores shown" repeated everywhere
- Mathematical impossibility to reverse-engineer in larger teams

**Failure Mode 3: Forced Participation**
- Problem: Users enrolled in teams without consent
- Result: Resentment, sabotage

**Phase 9.1 Solution:**
- Explicit invitation only
- No auto-enrollment
- Users can (future) leave teams

### Trust-Building Language Patterns

**Pattern 1: Transparency**
- "Here's what managers can see: [aggregated averages]"
- "Here's what members cannot see: [team aggregates]"

**Pattern 2: User Control**
- "Only you can mark your best calls" (Phase 7)
- "Team baselines require your completed evaluations, but your scores are averaged"

**Pattern 3: Privacy Explanation**
- "Minimum 2 members prevents individual identification"
- "Team trends compare team averages over time, not individuals"

## Testing Checklist (Phase 9.1)

Before deploying Phase 9.1, verify:

### Backend:
- [ ] Team baseline generation fails with <2 members
- [ ] Error message explains privacy reasoning
- [ ] Warning logs generated for blocked aggregations
- [ ] Team trends return `None` with <2 snapshots
- [ ] Info logs generated for insufficient snapshots
- [ ] No partial aggregation ever occurs

### Frontend (when team dashboard implemented):
- [ ] All team aggregate cards show "no individual scores" disclaimer
- [ ] Role awareness banner appears for managers
- [ ] Members receive clear message if accessing team page
- [ ] Empty states use calm, neutral language
- [ ] Trend unavailability shows helpful hint (not error)
- [ ] No language implies surveillance or ranking

### Copy Audit:
- [ ] No use of "performance of agents"
- [ ] No use of "employee" language
- [ ] No ranking or leaderboard implications
- [ ] "Team average" used consistently
- [ ] "Aggregated" appears near all team data

## Architectural Benefits of Phase 9.1

### 1. Prevents Trust Erosion

By making privacy **visible**, not just enforced:
- Users understand WHY minimum team size exists
- Managers understand they see ONLY aggregates
- Clear boundaries prevent feature creep into surveillance

### 2. Reduces Support Load

Clear error messages reduce confusion:
- "Why can't I generate team baseline?" → Error explains minimum 2 members
- "Where are team trends?" → Message explains need for 2 snapshots

### 3. Enables Safe Scaling

Trust safeguards enable:
- Larger team deployments
- Cross-team features (future)
- Agency-wide rollouts

Without Phase 9.1, adoption resistance would limit growth.

## Summary

Phase 9.1 transforms team intelligence from **technically safe** to **psychologically safe**.

**Key Improvements:**
- ✅ Explicit privacy explanations in errors
- ✅ Clear logging for debugging without exposing data
- ✅ UX language guidelines prevent misinterpretation
- ✅ Role awareness prevents unauthorized access attempts
- ✅ Empty states guide users without frustration

**Result:** Team features that users **trust** and managers **adopt confidently**.

**Philosophy:** "Privacy by design, trust by transparency."
