# Phase 7: Personal Baseline Intelligence

## Overview

Phase 7 adds **Personal Baseline Intelligence** - a user-driven feature that allows each user to create their own performance benchmark from their best sales calls.

This is **NOT** machine learning model training. This is **structured intelligence aggregation** from calls manually marked as "Best Calls" by the user.

## What Is A Personal Baseline?

A personal baseline is:

- **User-specific**: Each user creates their own baseline from their own best calls
- **Explicit**: Users manually mark calls as "Best Call" (via Phase 5 functionality)
- **Opt-in**: Completely optional - system works perfectly without it
- **Aggregated intelligence**: Statistical averages and patterns from marked calls
- **Comparison tool**: Helps users see how new calls compare to their own best patterns

## What It Is NOT

A personal baseline is **NOT**:

- ❌ Machine learning or AI model training
- ❌ Automatic or implicit
- ❌ Team-wide or agency-wide (that's Phase 9)
- ❌ Required for system to function
- ❌ A replacement for RASNA evaluation (it builds ON TOP of evaluation)

## How It Works Safely

### 1. Prerequisites

Before a user can generate a baseline:

- Must have at least 1 call marked as "Best Call" (`is_baseline=True`)
- All marked calls must have completed evaluations
- User must explicitly click "Generate My Baseline"

### 2. Aggregation Logic (No LLM)

The baseline service performs **pure aggregation** (no LLM calls):

- Calculates average RASNA scores across all baseline calls
- Identifies common strengths (dimensions with avg ≥ 8.0)
- Identifies improvement themes (dimensions with avg < 7.0)
- Stores these aggregations in `user_baselines` table

### 3. Comparison Logic

When viewing a call with completed evaluation:

- IF user has a baseline: compare current call to baseline averages
- IF dimension is >0.5 points above baseline → "Stronger than baseline"
- IF dimension is >0.5 points below baseline → "Room to match your best"
- IF no baseline exists → gracefully degrade (show null)

### 4. User Isolation

All baseline operations are user-scoped:

- User A cannot see User B's baseline
- Baseline only aggregates calls belonging to `current_user.id`
- Multi-user isolation is maintained from Phase 6

## API Endpoints

### `POST /api/v1/baseline/generate`

Generate or regenerate personal baseline.

**Auth Required**: Yes

**Prerequisites**:
- ≥1 call marked as baseline
- All baseline calls have completed evaluations

**Response**:
```json
{
  "id": 1,
  "user_id": 123,
  "rasna_averages": {
    "rapport": 8.5,
    "ask": 9.0,
    "situation": 7.8,
    "next_steps": 8.2,
    "articulation": 8.8
  },
  "summary": {
    "common_strengths": ["rapport", "ask", "articulation"],
    "common_improvement_themes": ["situation"],
    "average_overall_score": 8.46
  },
  "call_count": 3,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Errors**:
- `400`: No baseline calls found
- `400`: Baseline calls lack completed evaluations

### `GET /api/v1/baseline`

Get existing baseline for current user.

**Auth Required**: Yes

**Response**: Same as above

**Errors**:
- `404`: Baseline not generated yet

## Database Schema

### New Table: `user_baselines`

```sql
CREATE TABLE user_baselines (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    rasna_averages JSON NOT NULL,
    summary_json JSON NOT NULL,
    call_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design Decision**: Separate table (vs JSON column on User) for:
- Cleaner schema evolution
- Easier querying and indexing
- Clear separation of concerns
- Better audit trail with timestamps

## Updated Schemas

### `EvaluationResponse` (Extended)

```json
{
  "result": { ... },
  "status": "completed",
  "comparison_to_baseline": {
    "above_baseline": ["rapport", "situation"],
    "below_baseline": ["ask"],
    "summary": "Stronger than your baseline: rapport, situation. Room to match your best: ask"
  }
}
```

**Note**: `comparison_to_baseline` is `null` if:
- User has no baseline
- Evaluation not completed
- Any error occurs (graceful degradation)

## Frontend Integration (Pending)

### Dashboard Page

Add button: **"Generate My Baseline"**

- Disabled until ≥1 call marked as "Best Call"
- Shows count of baseline calls
- Shows last generated timestamp
- Calls `POST /api/v1/baseline/generate`

### Call Analysis Page

Add section: **"Compared to Your Best Calls"**

- Only shows if `comparison_to_baseline` is not null
- Displays:
  - ✅ Dimensions above baseline (green)
  - ⚠️ Dimensions below baseline (yellow)
  - Summary text (calm, non-judgmental)

Language examples:
- "Stronger than your baseline: rapport, articulation"
- "Room to match your best: closing, needs discovery"

## Safety & Non-Breaking Design

### Phase 1-6 Unchanged

- No modifications to existing evaluation logic
- No changes to RASNA scoring rules
- No changes to LLM evaluation prompt
- All existing API routes unchanged
- All existing schemas backward compatible

### Graceful Degradation

System continues to work perfectly if:
- User never generates baseline (null comparison)
- Baseline generation fails (returns 400, doesn't crash)
- Baseline comparison fails (returns null, doesn't crash)

### No Data Mutation

- Baseline generation does NOT modify existing calls
- Baseline comparison does NOT modify evaluations
- Legacy calls (Phase 6.1) remain inaccessible

## Phase 7 Architecture Benefits

### Isolation

- Separate model (`UserBaseline`)
- Separate repository (`UserBaselineRepository`)
- Separate service (`BaselineService`)
- Separate endpoints (`/baseline/*`)

Easy to:
- Extend in future phases
- Disable if needed
- Remove without breaking other features

### Extensibility

Future phases can build on this:
- **Phase 8**: Baseline trends over time
- **Phase 9**: Team/agency aggregated baselines
- **Phase 10**: Baseline recommendations

## Testing Checklist

Before deployment, verify:

- [ ] User can generate baseline with ≥1 best call
- [ ] Baseline shows correct RASNA averages
- [ ] Call comparison shows above/below dimensions
- [ ] Graceful degradation when no baseline exists
- [ ] User A cannot access User B's baseline
- [ ] Phase 1-6 functionality unchanged
- [ ] Legacy calls still return 403 (Phase 6.1)
- [ ] All backend files compile
- [ ] API docs show new endpoints

## Summary

Phase 7 provides **optional, user-driven, non-breaking intelligence** that helps users understand how each call compares to their own best patterns.

It's safe, isolated, reversible, and builds cleanly on top of existing evaluation logic.
