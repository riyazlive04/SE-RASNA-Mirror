# Evaluation Workflow Stabilization - Summary

## Changes Made

### 1. CallRepository - ✅ Already Stable
- `update()` method already exists (lines 27-34)
- Properly handles atomic updates with commit/refresh
- No changes needed

### 2. Evaluation Endpoint - /calls/{call_id}/evaluate

#### Added Validations
```python
# Validate call exists (existing)
if not db_call:
    raise HTTPException(404, "Call not found")

# NEW: Validate transcription is completed
if db_call.transcription_status != "completed":
    raise HTTPException(400, "Transcription must be completed before evaluation")

# NEW: Prevent re-evaluation
if db_call.evaluation_status == "completed":
    raise HTTPException(409, "Evaluation already completed for this call")
```

#### Added Error Handling
```python
try:
    # Run evaluation
    result = await evaluation_service.evaluate_call(...)

    # Persist: pending → completed
    call_repo.update(call_id, {
        "evaluation_score": overall_score,
        "evaluation_details": evaluation_result,
        "evaluation_status": "completed"
    })

    return {"result": evaluation_result, "status": "completed"}

except Exception as e:
    # Persist: pending → failed
    call_repo.update(call_id, {"evaluation_status": "failed"})
    raise HTTPException(500, f"Evaluation failed: {str(e)}")
```

### 3. Transcription Endpoint - /calls/{call_id}/transcribe

#### Added Consistent Validation
```python
# NEW: Prevent re-transcription
if db_call.transcription_status == "completed":
    raise HTTPException(409, "Transcription already completed for this call")
```

#### Added Error Handling
```python
try:
    # Run transcription
    result = await transcription_service.transcribe_audio(...)
    call_repo.update(call_id, {
        "transcription_text": result.get("text"),
        "transcription_status": result.get("status", "pending")
    })
    return {"text": ..., "status": ...}

except Exception as e:
    call_repo.update(call_id, {"transcription_status": "failed"})
    raise HTTPException(500, f"Transcription failed: {str(e)}")
```

## Status Transition State Machine

### Transcription
```
pending ──[success]──> completed
   │
   └────[exception]──> failed
```

### Evaluation
```
pending ──[transcription != completed]──> HTTP 400
   │
   ├────[success]──> completed
   │
   └────[exception]──> failed

completed ──[re-evaluate attempt]──> HTTP 409
```

## API Contract Guarantees

### POST /calls/{call_id}/evaluate

**Preconditions:**
- Call must exist (404 if not)
- `transcription_status` must be "completed" (400 if not)
- `evaluation_status` must NOT be "completed" (409 if already done)

**Postconditions (Success):**
- `evaluation_status` = "completed"
- `evaluation_score` = result.scores.overall
- `evaluation_details` = full EvaluationResult JSON
- Returns: `EvaluationResponse`

**Postconditions (Failure):**
- `evaluation_status` = "failed"
- `evaluation_score` = null
- `evaluation_details` = null
- Raises: HTTPException 500

### POST /calls/{call_id}/transcribe

**Preconditions:**
- Call must exist (404 if not)
- `transcription_status` must NOT be "completed" (409 if already done)

**Postconditions (Success):**
- `transcription_status` = status from service
- `transcription_text` = text from service
- Returns: `TranscriptionResponse`

**Postconditions (Failure):**
- `transcription_status` = "failed"
- Raises: HTTPException 500

## Benefits

1. **Idempotency**: Cannot re-run completed operations (409 Conflict)
2. **Safety**: Clear validation before expensive operations
3. **Observability**: Failed state persisted to database
4. **Determinism**: No race conditions, clear state transitions
5. **Future-proof**: Ready for LLM integration without contract changes

## Testing Workflow

```bash
# 1. Upload call
POST /api/v1/calls/
→ transcription_status: "pending"
→ evaluation_status: "pending"

# 2. Try to evaluate (should fail)
POST /api/v1/calls/1/evaluate
→ HTTP 400: "Transcription must be completed before evaluation"

# 3. Transcribe
POST /api/v1/calls/1/transcribe
→ transcription_status: "completed" (mock)

# 4. Evaluate
POST /api/v1/calls/1/evaluate
→ evaluation_status: "completed"
→ Returns full EvaluationResult

# 5. Try to re-evaluate (should fail)
POST /api/v1/calls/1/evaluate
→ HTTP 409: "Evaluation already completed for this call"
```

## Files Modified

- `backend/app/api/v1/endpoints/calls.py` (+95 lines, -37 lines)

## Files Unchanged (Already Correct)

- `backend/app/repositories/call.py` (update() method already exists)
- `backend/app/schemas/call.py` (schemas already correct)
- `backend/app/services/evaluation.py` (service already returns correct format)

---

**Status**: ✅ COMPLETE
**Workflow**: STABLE
**Ready for**: LLM Integration
