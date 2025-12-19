# Phase 8: Baseline Evolution & Trend Intelligence

## Overview

Phase 8 adds **Baseline Evolution Tracking** - an optional feature that helps users understand how their performance baseline changes over time.

This is **NOT** forecasting or predictive analytics. This is **pure arithmetic comparison** of consecutive baseline snapshots.

## What Is Baseline Evolution?

Baseline evolution tracking:

- **Historical snapshots**: Creates timestamped snapshots each time user regenerates their baseline
- **Trend analysis**: Compares last 2 snapshots to show improvement/decline per RASNA dimension
- **User-specific**: Each user's evolution is tracked independently
- **Explicit opt-in**: Snapshots only created when user explicitly regenerates baseline
- **Completely optional**: System works perfectly without it (graceful degradation)

## What It Is NOT

Baseline evolution is **NOT**:

- ❌ Machine learning, forecasting, or predictive modeling
- ❌ Automatic background processing
- ❌ Required for baseline functionality (Phase 7 works independently)
- ❌ Cross-user analysis (each user's evolution is private)
- ❌ LLM-based insight generation (pure arithmetic only)

## How It Works Safely

### 1. Snapshot Creation

Snapshots are created **ONLY** when:

- User explicitly clicks "Generate My Baseline" (from Phase 7)
- Baseline generation succeeds
- No automatic creation, no background jobs

Each snapshot stores:
- RASNA averages at that point in time
- Summary insights
- Number of baseline calls used
- Timestamp of snapshot creation

### 2. Trend Computation (Pure Arithmetic)

The trend service performs **deterministic arithmetic**:

- Fetches last 2 snapshots for user (newest first)
- Calculates delta for each RASNA dimension: `latest_score - previous_score`
- Categorizes changes using thresholds:
  - **Improved**: delta ≥ +0.5
  - **Declined**: delta ≤ -0.5
  - **Stable**: |delta| < 0.5
- Generates human-readable summary

**No ML, no LLM, no forecasting** - just `latest - previous`.

### 3. Graceful Degradation

If user has <2 snapshots:

- `GET /baseline/trends` returns `204 No Content`
- No error thrown, no crash
- Frontend can hide "Evolution" section until data available

### 4. User Isolation

All evolution operations are user-scoped:

- User A cannot see User B's snapshots or trends
- Snapshots only include calls belonging to `current_user.id`
- Multi-user isolation maintained from Phase 6

## API Endpoints

### `GET /api/v1/baseline/trends`

Get baseline evolution trend for current user.

**Auth Required**: Yes

**Prerequisites**:
- User has regenerated baseline at least **2 times**
- (First generation + at least 1 regeneration)

**Response** (when ≥2 snapshots exist):
```json
{
  "improved_dimensions": ["rapport", "articulation"],
  "declined_dimensions": ["ask"],
  "stable_dimensions": ["situation", "next_steps"],
  "dimension_deltas": {
    "rapport": 0.7,
    "ask": -0.8,
    "situation": 0.2,
    "next_steps": -0.1,
    "articulation": 1.2
  },
  "summary": "Since your last baseline: You've improved in rapport, articulation. You've declined in ask. Situation, next_steps remained stable.",
  "snapshots_compared": 2,
  "latest_snapshot_date": "2024-01-20T15:30:00",
  "previous_snapshot_date": "2024-01-15T10:30:00",
  "latest_call_count": 5,
  "previous_call_count": 3
}
```

**Response** (when <2 snapshots exist):
- HTTP `204 No Content`
- Message: "Insufficient snapshots for trend analysis. Regenerate your baseline at least once more to see evolution trends."

**Errors**:
- Never throws 500 (defensive programming throughout)

### `POST /api/v1/baseline/generate` (Extended)

**Phase 8 Enhancement**: Now creates a snapshot after successful baseline generation.

- Snapshot creation failure does NOT break baseline generation (graceful degradation)
- User still gets their baseline even if snapshot fails
- Error logged but not propagated

## Database Schema

### New Table: `user_baseline_snapshots`

```sql
CREATE TABLE user_baseline_snapshots (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    rasna_averages JSON NOT NULL,
    summary_json JSON NOT NULL,
    call_count INTEGER NOT NULL,
    snapshot_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_user_baseline_snapshots_user_id ON user_baseline_snapshots(user_id);
```

**Design Decisions**:
- **Separate table** (not columns on `user_baselines`) for:
  - Preserves full history (no deletions)
  - Unlimited snapshots over time
  - Clean query for "last 2 snapshots"
  - No impact on existing baseline table

- **No UPDATE operations**: Snapshots are immutable
- **No DELETE operations**: History preserved for analysis

## Updated TypeScript Types

### New Interface: `BaselineTrend`

```typescript
export interface BaselineTrend {
  improved_dimensions: string[];
  declined_dimensions: string[];
  stable_dimensions: string[];
  dimension_deltas: Record<string, number>;
  summary: string;
  snapshots_compared: number;
  latest_snapshot_date: string;
  previous_snapshot_date: string;
  latest_call_count: number;
  previous_call_count: number;
}
```

## Service Layer Architecture

### `BaselineTrendService`

**Pure logic service** with centralized thresholds:

```python
# Phase 8: Centralized trend threshold constants
TREND_IMPROVEMENT_THRESHOLD = 0.5  # Score increase >= 0.5 considered improvement
TREND_DECLINE_THRESHOLD = 0.5      # Score decrease >= 0.5 considered decline
```

**Methods**:
- `get_trend_for_user(user_id)`: Returns trend or None
- `_compute_dimension_deltas(prev, latest)`: Defensive delta calculation
- `_categorize_changes(deltas)`: Sorts into improved/declined/stable
- `_generate_evolution_summary(...)`: Human-readable text generation

**Safety Features**:
- Type validation on all inputs
- Graceful handling of missing dimensions
- Try-except blocks for defensive extraction
- Returns None instead of crashing

### `BaselineService` (Extended)

**New behavior**:
- After baseline creation/update → create snapshot
- Snapshot creation wrapped in try-except (doesn't break baseline generation)

## Frontend Integration (Minimal)

### Dashboard Page (Optional Enhancement)

Add section: **"Your Baseline Evolution"**

- Only shows if `GET /baseline/trends` returns 200 (not 204)
- Displays:
  - ✅ Improved dimensions (green)
  - 📉 Declined dimensions (red/yellow)
  - ➡️ Stable dimensions (gray)
  - Summary text
  - Snapshot comparison metadata

**If <2 snapshots**:
- Show message: "Regenerate your baseline at least once more to see how you're evolving"

Language examples:
- "Since your last baseline: You've improved in rapport, articulation"
- "Ask has declined slightly - consider focusing here in your next calls"
- "Situation, next_steps remained stable"

## Safety & Non-Breaking Design

### Phase 1-7 Unchanged

- ✅ No modifications to existing baseline generation logic
- ✅ No changes to RASNA evaluation
- ✅ No changes to baseline comparison logic
- ✅ All existing API routes work unchanged
- ✅ All existing schemas backward compatible

### Graceful Degradation

System continues to work perfectly if:
- User never regenerates baseline (no snapshots, returns 204)
- Snapshot creation fails (baseline still works)
- Trend computation fails (returns None, no crash)
- User has only 1 snapshot (returns 204, waits for next regeneration)

### No Data Mutation

- Snapshot creation does NOT modify existing baselines
- Snapshot creation does NOT modify calls
- Snapshots are immutable (no updates)
- Trend computation is pure GET (no side effects)

### No Automatic Behavior

- **No background jobs**
- **No automatic snapshot creation**
- **No scheduled tasks**
- User must explicitly regenerate baseline to create new snapshot

## Phase 8 Architecture Benefits

### Isolation

- Separate model (`UserBaselineSnapshot`)
- Separate repository (`UserBaselineSnapshotRepository`)
- Separate service (`BaselineTrendService`)
- Separate endpoint (`GET /baseline/trends`)

Easy to:
- Disable if needed
- Remove without breaking Phase 7
- Extend with more advanced analytics later

### Extensibility

Future phases can build on this:
- **Phase 9**: Team-wide baseline trends
- **Phase 10**: Long-term evolution charts (3+ snapshots)
- **Phase 11**: Dimension-specific coaching recommendations

### Defensive Programming

Throughout Phase 8:
- Type validation on all inputs
- Graceful handling of missing/malformed data
- Try-except blocks for safe extraction
- Returns None/204 instead of crashing
- Extensive logging for debugging

## Thresholds Reference

| Threshold | Value | Purpose |
|-----------|-------|---------|
| `TREND_IMPROVEMENT_THRESHOLD` | 0.5 | Min score increase to be considered "improved" |
| `TREND_DECLINE_THRESHOLD` | 0.5 | Min score decrease to be considered "declined" |

Changes within ±0.5 are considered "stable" to avoid noise.

## Testing Checklist

Before deployment, verify:

- [ ] User can generate baseline (Phase 7 still works)
- [ ] Snapshot created after baseline generation
- [ ] `GET /baseline/trends` returns 204 with <2 snapshots
- [ ] `GET /baseline/trends` returns trend data with ≥2 snapshots
- [ ] Trend correctly categorizes improved/declined/stable dimensions
- [ ] Dimension deltas calculated correctly
- [ ] Snapshot creation failure doesn't break baseline generation
- [ ] User A cannot access User B's trends
- [ ] Phase 1-7 functionality unchanged
- [ ] All backend files compile
- [ ] TypeScript types compile

## Example User Journey

### First Baseline Generation
1. User marks 3 calls as "Best Call"
2. Clicks "Generate My Baseline"
3. Baseline created with RASNA averages
4. **Snapshot #1 created** (behind the scenes)
5. User sees baseline summary

### Regenerating Baseline (Week Later)
1. User marks 2 more calls as "Best Call" (now 5 total)
2. Clicks "Regenerate My Baseline"
3. Baseline updated with new averages
4. **Snapshot #2 created** (behind the scenes)
5. User can now view evolution trends

### Viewing Evolution
1. User clicks "View Evolution" (or similar)
2. Frontend calls `GET /baseline/trends`
3. Trend shows:
   - Rapport improved by 0.7
   - Ask declined by 0.8
   - Other dimensions stable
4. User sees which areas improved and which need focus

## Summary

Phase 8 provides **optional, explicit, non-breaking historical tracking** that helps users understand how their baseline evolves as they mark new best calls.

It's safe, isolated, reversible, and builds cleanly on top of Phase 7 baseline logic.

**Key Principle**: "Show me how I'm evolving compared to my own past performance" - pure arithmetic, no ML, no LLM.
