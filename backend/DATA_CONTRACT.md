# SE RASNA Mirror - Data Contract Specification

## Overview

This document defines the stable, production-grade data contracts for the SE RASNA Mirror backend. These contracts are locked and should be treated as the source of truth for frontend and AI integration.

## Call Context Fields

### Required on Upload

```python
{
    "agent_name": str,           # Sales agent name
    "customer_name": str | None, # Customer name (optional)
    "call_type": str,            # Type of call
    "lead_type": "hot" | "warm" | "cold",  # Lead temperature
    "call_stage": "qualification" | "main" | "follow-up",  # Call stage
    "deck_shared": bool          # Whether presentation deck was shared
}
```

### Lead Type
- **hot**: High-intent lead, ready to buy
- **warm**: Engaged lead, needs nurturing
- **cold**: New lead, exploratory stage

### Call Stage
- **qualification**: Initial discovery and qualification
- **main**: Primary sales presentation
- **follow-up**: Post-presentation follow-up

## RASNA Evaluation Schema

### RasnaScore

```python
{
    "rapport": int,      # 0-100: Rapport building effectiveness
    "situation": int,    # 0-100: Situation understanding
    "pain": int,         # 0-100: Pain identification quality
    "need": int,         # 0-100: Need articulation clarity
    "ask": int,          # 0-100: Close/ask effectiveness
    "overall": int       # 0-100: Overall RASNA score (average)
}
```

### EvaluationResult

```python
{
    "scores": RasnaScore,
    "strengths": [str],           # 2-4 key strengths
    "improvements": [str],        # 2-4 improvement areas
    "next_call_focus": str        # Primary focus for next call
}
```

## API Endpoints

### Upload Call
**POST** `/api/v1/calls/`

Form data:
- `audio_file`: File (required)
- `agent_name`: string (required)
- `customer_name`: string (optional)
- `call_type`: string (required)
- `lead_type`: "hot" | "warm" | "cold" (required)
- `call_stage`: "qualification" | "main" | "follow-up" (required)
- `deck_shared`: boolean (default: false)

Response: `CallResponse`

### Trigger Evaluation
**POST** `/api/v1/calls/{call_id}/evaluate`

Response: `EvaluationResponse`

## Database Schema

### calls table

```sql
id: INTEGER PRIMARY KEY
agent_name: VARCHAR NOT NULL
customer_name: VARCHAR NULL
call_type: VARCHAR NOT NULL
call_date: DATETIME DEFAULT NOW

-- RASNA context
lead_type: VARCHAR NOT NULL          -- hot | warm | cold
call_stage: VARCHAR NOT NULL         -- qualification | main | follow-up
deck_shared: BOOLEAN DEFAULT FALSE

-- Audio
audio_filename: VARCHAR UNIQUE NOT NULL
audio_path: VARCHAR NOT NULL
audio_format: VARCHAR NOT NULL
audio_size: INTEGER NOT NULL

-- Transcription
transcription_text: TEXT NULL
transcription_status: VARCHAR DEFAULT 'pending'  -- pending | completed | failed

-- Evaluation
evaluation_score: FLOAT NULL         -- Overall RASNA score
evaluation_details: JSON NULL        -- Full EvaluationResult
evaluation_status: VARCHAR DEFAULT 'pending'  -- pending | completed | failed

created_at: DATETIME DEFAULT NOW
updated_at: DATETIME DEFAULT NOW
```

## Mock Evaluation Logic

Current implementation provides deterministic mock evaluations based on:

1. **Base scores** determined by `lead_type`:
   - Hot leads: 82-88 range
   - Warm leads: 68-75 range
   - Cold leads: 52-62 range

2. **Adjustments** based on `call_stage`:
   - Qualification: +8 situation, +5 pain, -10 ask
   - Main: no adjustment
   - Follow-up: +10 rapport, +8 need, +12 ask

3. **Bonus** for `deck_shared`: +5 need, +5 ask

### TODO: AI Integration

Replace deterministic logic with LLM-based evaluation:

```python
# TODO in app/services/evaluation.py:evaluate_call()

1. Parse transcription into segments
2. Use LLM to analyze each RASNA component
3. Extract specific quotes and timestamps
4. Generate personalized feedback
5. Calculate scores based on conversation quality
```

## Frontend Integration

### Example: Upload Call

```javascript
const formData = new FormData();
formData.append('audio_file', audioFile);
formData.append('agent_name', 'John Doe');
formData.append('customer_name', 'Acme Corp');
formData.append('call_type', 'sales');
formData.append('lead_type', 'warm');
formData.append('call_stage', 'main');
formData.append('deck_shared', 'true');

const response = await fetch('/api/v1/calls/', {
    method: 'POST',
    body: formData
});

const call = await response.json();
```

### Example: Get Evaluation

```javascript
const response = await fetch(`/api/v1/calls/${callId}/evaluate`, {
    method: 'POST'
});

const evaluation = await response.json();

// evaluation.result.scores.overall => 75
// evaluation.result.strengths => ["Strong rapport...", ...]
// evaluation.result.improvements => ["Ask more questions...", ...]
// evaluation.result.next_call_focus => "Focus on building..."
```

## Validation Rules

- All lead_type values MUST be: hot, warm, or cold
- All call_stage values MUST be: qualification, main, or follow-up
- All RASNA scores MUST be integers between 0-100 (inclusive)
- strengths array MUST contain 2-4 items
- improvements array MUST contain 2-4 items
- Audio file size MUST NOT exceed 50MB
- Audio format MUST be: .wav, .mp3, .m4a, .flac, or .ogg

## Migration from Previous Schema

If upgrading from the initial schema:

1. Database will be recreated (SQLite, no migration needed)
2. Old calls without lead_type/call_stage will fail validation
3. Frontend must update upload form to include new fields
4. evaluation_details changed from arbitrary dict to strict EvaluationResult
5. evaluation.score moved to evaluation.result.scores.overall

---

**Status**: LOCKED ✅
**Version**: 1.0
**Last Updated**: 2025-12-17
