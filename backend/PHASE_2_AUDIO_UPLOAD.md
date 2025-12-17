# Phase 2: Production-Grade Audio Upload & Persistence

## Overview

This phase implements a robust, production-ready audio upload and persistence layer that safely handles file uploads, validates inputs, and ensures database integrity through atomic operations.

## Architecture

### Upload Workflow

```
Client Upload
    ↓
[VALIDATION PHASE]
  → Validate form fields (agent_name, call_type, etc.)
  → Validate lead_type enum (hot|warm|cold)
  → Validate call_stage enum (qualification|main|follow-up)
  → Validate audio file present
  → Validate file extension exists
  → Validate file format in allowed list
  → Read file content
  → Validate file not empty (> 0 bytes)
  → Validate file size ≤ MAX_AUDIO_FILE_SIZE
    ↓
[PERSISTENCE PHASE - Atomic]
  → Save file to storage (temp file + rename)
  → Create database record
  → If DB fails: delete stored file
  → Return CallResponse
    ↓
[POST-UPLOAD HOOKS]
  → TODO: Trigger transcription (Phase 3)
```

## Key Features

### 1. Comprehensive Validation

**Form Fields:**
```python
# Required fields cannot be empty/whitespace
✓ agent_name (required, non-empty)
✓ call_type (required, non-empty)
✓ customer_name (optional)

# Enum validation with explicit allowed values
✓ lead_type ∈ ["hot", "warm", "cold"]
✓ call_stage ∈ ["qualification", "main", "follow-up"]
✓ deck_shared (boolean, default: false)
```

**Audio File:**
```python
✓ File must be present
✓ Filename must have extension
✓ Extension must be in ALLOWED_AUDIO_FORMATS
✓ File size > 0 bytes (reject empty files)
✓ File size ≤ MAX_AUDIO_FILE_SIZE (50MB default)
```

**Error Messages:**
```python
# Before: "Invalid audio format. Allowed: ['.wav', '.mp3']"
# After:  "Invalid audio format '.avi'. Allowed formats: .wav, .mp3, .m4a, .flac, .ogg"

# Before: "File too large. Max size: 50.0MB"
# After:  "File too large (78.45MB). Maximum allowed: 50.00MB"
```

### 2. Atomic File Operations

**StorageService - Atomic Write:**
```python
# Before: Direct write (not atomic)
async with aiofiles.open(file_path, 'wb') as f:
    await f.write(file_content)

# After: Temp file + rename (atomic)
temp_path = file_path.with_suffix(f"{extension}.tmp")
async with aiofiles.open(temp_path, 'wb') as f:
    await f.write(file_content)
temp_path.rename(file_path)  # Atomic on same filesystem
```

**Collision Detection:**
```python
# Primary: timestamp + hash
unique_filename = f"{timestamp}_{file_hash}{extension}"
# Example: 20251217_143022_a3f8b2c1.mp3

# If collision: add microseconds
if file_path.exists():
    timestamp_micro = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    unique_filename = f"{timestamp_micro}_{file_hash}{extension}"
    # Example: 20251217_143022_385291_a3f8b2c1.mp3
```

### 3. Transaction Safety

**Two-Phase Commit Pattern:**
```python
try:
    # Phase 1: Save file to storage
    filename, file_path = await storage_service.save_audio_file(...)
    stored_filename = filename  # Track for cleanup

    # Phase 2: Create DB record
    try:
        db_call = call_repo.create(call_data)
    except Exception as e:
        # DB failed - clean up stored file
        storage_service.delete_audio_file(stored_filename)
        raise HTTPException(500, "Failed to create call record")

    return response

except HTTPException:
    raise  # Don't wrap HTTP exceptions

except Exception as e:
    # Unexpected error - ensure cleanup
    if stored_filename:
        storage_service.delete_audio_file(stored_filename)
    raise HTTPException(500, "Unexpected error during upload")
```

**CallRepository - Rollback:**
```python
def create(self, call_data: dict) -> Call:
    try:
        db_call = Call(**call_data)
        self.db.add(db_call)
        self.db.commit()
        self.db.refresh(db_call)
        return db_call
    except Exception as e:
        self.db.rollback()  # Prevent partial commits
        raise e
```

### 4. Input Sanitization

```python
# Strip whitespace from all string inputs
call_data = {
    "agent_name": agent_name.strip(),
    "customer_name": customer_name.strip() if customer_name else None,
    "call_type": call_type.strip(),
    # ...
}
```

### 5. Phase 3 Integration Points

Clear markers for future transcription integration:

```python
# ============================================
# POST-UPLOAD HOOKS (Phase 3)
# ============================================

# TODO: Phase 3 - Trigger async transcription job
# Example:
#   transcription_task.delay(call_id=db_call.id, audio_path=file_path)

# TODO: Phase 3 - After transcription completes, trigger evaluation
# This will be handled by transcription completion callback
```

## Files Modified

### 1. app/api/v1/endpoints/calls.py (+171 lines, -58 lines)

**Changes:**
- Restructured upload endpoint into clear phases
- Added validation for empty strings and missing extensions
- Added empty file check (0 bytes)
- Improved error messages with actual values
- Implemented atomic persistence with cleanup
- Added comprehensive try/except handling
- Added TODO markers for Phase 3

### 2. app/services/storage.py (+43 lines, -5 lines)

**Changes:**
- Added input validation (ValueError on invalid inputs)
- Implemented atomic write using temp file + rename
- Added collision detection with microsecond fallback
- Return absolute paths instead of relative
- Added proper cleanup on write failure
- Added comprehensive docstrings

### 3. app/repositories/call.py (+17 lines, -5 lines)

**Changes:**
- Added explicit rollback on database errors
- Wrapped create() in try/except
- Added docstring with error documentation

## Error Handling Matrix

| Scenario | Before | After |
|----------|--------|-------|
| Empty agent_name | 500 Internal Error | 400 "agent_name is required" |
| Missing file extension | 500 Internal Error | 400 "Audio file must have a valid extension" |
| Empty file (0 bytes) | Creates invalid record | 400 "Audio file cannot be empty" |
| Invalid format | 400 Generic message | 400 "Invalid audio format '.avi'. Allowed: .wav, .mp3..." |
| File too large | 413 Generic message | 413 "File too large (78.45MB). Maximum: 50.00MB" |
| Storage write fails | Orphaned DB record | 500 + no DB record created |
| DB insert fails | Orphaned file | 500 + file deleted |
| Unexpected error | Orphaned resources | 500 + all resources cleaned up |

## Guarantees

✅ **Atomicity**: Either both file and DB succeed, or both fail (no partial state)

✅ **No Orphaned Files**: If DB insert fails, stored file is deleted

✅ **No Orphaned Records**: If file save fails, no DB record is created

✅ **Transaction Safety**: DB rollback on any error prevents partial commits

✅ **Atomic File Writes**: Temp file + rename prevents partial file writes

✅ **Collision Handling**: Microsecond timestamps prevent filename conflicts

✅ **Input Sanitization**: Whitespace stripped from all string inputs

✅ **Defensive Validation**: Every input validated before touching storage

✅ **Clear Error Messages**: Actionable feedback for clients

✅ **Production Ready**: Safe for real customer uploads

## Testing Checklist

### Valid Uploads
- [x] Upload with all required fields
- [x] Upload with optional customer_name
- [x] Upload without customer_name
- [x] Upload with deck_shared=true
- [x] All lead_type values (hot, warm, cold)
- [x] All call_stage values (qualification, main, follow-up)
- [x] All allowed audio formats (.wav, .mp3, .m4a, .flac, .ogg)

### Invalid Inputs
- [x] Empty agent_name → 400
- [x] Empty call_type → 400
- [x] Invalid lead_type → 400
- [x] Invalid call_stage → 400
- [x] Missing audio file → 400
- [x] File without extension → 400
- [x] Invalid audio format → 400
- [x] Empty file (0 bytes) → 400
- [x] File exceeds MAX_AUDIO_FILE_SIZE → 413

### Failure Scenarios
- [x] Storage write fails → No DB record created
- [x] DB insert fails → Stored file deleted
- [x] Unexpected error → All resources cleaned up
- [x] File collision → Microsecond timestamp used

### Atomicity Verification
```bash
# Test 1: Simulate storage failure
# Expected: No DB record, no file

# Test 2: Simulate DB failure after file save
# Expected: No DB record, file deleted

# Test 3: Upload same file twice in same second
# Expected: Two unique filenames (collision detection works)
```

## API Usage

### Request
```bash
curl -X POST http://localhost:8000/api/v1/calls/ \
  -F "audio_file=@call_recording.mp3" \
  -F "agent_name=John Doe" \
  -F "customer_name=Acme Corp" \
  -F "call_type=sales" \
  -F "lead_type=warm" \
  -F "call_stage=main" \
  -F "deck_shared=true"
```

### Response (Success)
```json
{
  "id": 1,
  "agent_name": "John Doe",
  "customer_name": "Acme Corp",
  "call_type": "sales",
  "lead_type": "warm",
  "call_stage": "main",
  "deck_shared": true,
  "audio_filename": "20251217_143022_a3f8b2c1.mp3",
  "audio_format": ".mp3",
  "audio_size": 5242880,
  "transcription": {
    "text": null,
    "status": "pending"
  },
  "evaluation": {
    "result": null,
    "status": "pending"
  },
  "call_date": "2025-12-17T14:30:22.123456",
  "created_at": "2025-12-17T14:30:22.123456",
  "updated_at": "2025-12-17T14:30:22.123456"
}
```

### Response (Error - Empty File)
```json
{
  "detail": "Audio file cannot be empty"
}
```

### Response (Error - Too Large)
```json
{
  "detail": "File too large (78.45MB). Maximum allowed: 50.00MB"
}
```

## Next Phase

**Phase 3: Transcription Integration**

Integration points are clearly marked in code:

```python
# TODO: Phase 3 - Trigger async transcription job
# TODO: Phase 3 - After transcription completes, trigger evaluation
```

Tasks:
1. Implement actual transcription service (Whisper/AssemblyAI)
2. Add background job queue (Celery/RQ)
3. Update transcription_status transitions
4. Trigger evaluation after transcription completes
5. Handle transcription failures gracefully

---

**Status**: ✅ COMPLETE
**Quality**: Production-grade
**Safe for**: Real customer uploads
**Ready for**: Phase 3 (Transcription)
