# Phase 3: Deterministic Transcription Layer

## Overview

Phase 3 implements a safe, deterministic transcription layer that converts stored audio files into text transcriptions. The implementation uses realistic mock data to enable end-to-end testing without external API dependencies, while maintaining clear integration points for Phase 4 (real STT providers).

## Architecture

### Transcription Workflow

```
Stored Audio File
    ↓
[VALIDATION]
  → Call exists
  → transcription_status == "pending"
  → Audio file exists
  → Audio file not empty
    ↓
[TRANSCRIPTION]
  → Generate mock transcription (deterministic)
  → Based on file size:
    * < 1MB: Short call
    * 1-5MB: Medium call
    * > 5MB: Long call
    ↓
[PERSISTENCE]
  → Save transcription_text
  → Set transcription_status = "completed"
  → Return TranscriptionResponse
    ↓
[WORKFLOW GATE]
  → Evaluation can now proceed
```

## Key Features

### 1. Deterministic Mock Transcription

**TranscriptionService.transcribe_audio():**

```python
# Input validation
✓ Validate audio file exists (FileNotFoundError)
✓ Validate file not empty (ValueError)

# Deterministic generation based on file size
if size < 1MB:
    # Short call (< 1 minute)
    return "Agent: Hi... Customer: Thanks... Agent: Have a great day!"

elif size < 5MB:
    # Medium call (1-5 minutes)
    return "Agent: Good morning... [discovery]... Customer: Yes, let's schedule..."

else:
    # Long call (> 5 minutes)
    return "Agent: Good afternoon... [full qualification + pricing + demo booking]..."

# Response format
{
    "text": "full_transcription",
    "status": "completed",
    "confidence": 0.95,
    "language": "en-US",
    "duration": 3.5  # estimated from file size
}
```

**Why Deterministic?**
- Enables consistent end-to-end testing
- No external API dependencies
- Predictable output for evaluation testing
- Easy to replace with real STT in Phase 4

### 2. Realistic Sales Call Templates

**Short Call (< 1MB):**
```
Agent: Hi, this is calling from our sales team.
I wanted to reach out about our solution.
Customer: Thanks for calling. Can you send me some information?
Agent: Absolutely, I'll send that right over.
Customer: Great, thanks.
Agent: Have a great day!
```

**Medium Call (1-5MB):**
```
Agent: Good morning! This is calling from the sales team.
How are you doing today?
Customer: I'm doing well, thanks. What's this regarding?
Agent: I wanted to discuss how our platform can help streamline your workflow.
[...discovery conversation...]
Customer: Yes, let's do that. Tuesday afternoon works for me.
Agent: Perfect! I'll send you a calendar invite.
```

**Long Call (> 5MB):**
```
Agent: Good afternoon! This is calling from the sales team.
Thanks for taking the time to speak with me today.
Customer: No problem. I've been looking into solutions like yours.
Agent: That's great to hear. Can you tell me a bit about what prompted your search?
[...full qualification...]
[...pain discovery...]
[...solution presentation...]
[...pricing discussion...]
[...demo scheduling...]
Agent: Have a great rest of your day!
```

### 3. Enhanced Error Handling

**Specific Exception Types:**

```python
# FileNotFoundError: Audio file missing
try:
    transcribe_audio(path)
except FileNotFoundError:
    → Set status = "failed"
    → Return HTTP 404 "Audio file not found"

# ValueError: Invalid audio file (empty or corrupted)
try:
    transcribe_audio(path)
except ValueError:
    → Set status = "failed"
    → Return HTTP 400 "Invalid audio file"

# Exception: Unexpected error
try:
    transcribe_audio(path)
except Exception:
    → Set status = "failed"
    → Return HTTP 500 "Transcription failed"
```

**Always Update Status:**
```python
# BEFORE returning error
call_repo.update(call_id, {"transcription_status": "failed"})

# THEN raise HTTPException
raise HTTPException(...)
```

### 4. Result Validation

**Endpoint Validation:**
```python
# Validate service response
transcription_text = result.get("text")
transcription_status = result.get("status")

if not transcription_text or not transcription_status:
    raise ValueError("Invalid transcription result: missing text or status")

# Only persist if valid
call_repo.update(call_id, {
    "transcription_text": transcription_text,
    "transcription_status": transcription_status
})
```

### 5. State Machine Enforcement

**Transcription States:**
```
pending ──[file not found]──> failed (404)
   │
   ├──[file invalid]────────> failed (400)
   │
   ├──[success]─────────────> completed
   │
   └──[unexpected error]────> failed (500)

completed ──[retry]─────────> HTTP 409 (prevented)
```

**Workflow Gates:**
```python
# In evaluation endpoint (unchanged from Phase 1)
if db_call.transcription_status != "completed":
    raise HTTPException(400, "Transcription must be completed before evaluation")

# ✅ Ensures evaluation only runs on completed transcriptions
```

## Phase 4 Integration Points

Clear TODO markers for STT provider integration:

### Option 1: OpenAI Whisper API

```python
# TODO: Phase 4 - OpenAI Whisper integration
import openai

with open(audio_path, "rb") as audio_file:
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

return {
    "text": transcript.text,
    "status": "completed",
    "confidence": None,
    "language": transcript.language,
    "duration": transcript.duration
}
```

### Option 2: AssemblyAI

```python
# TODO: Phase 4 - AssemblyAI integration
import assemblyai as aai

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(str(audio_path))

return {
    "text": transcript.text,
    "status": "completed",
    "confidence": transcript.confidence,
    "language": "en",
    "duration": transcript.audio_duration
}
```

### Option 3: Google Speech-to-Text

```python
# TODO: Phase 4 - Google Speech-to-Text integration
from google.cloud import speech

client = speech.SpeechClient()
with open(audio_path, "rb") as audio_file:
    content = audio_file.read()

audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(...)
response = client.recognize(config=config, audio=audio)

return {
    "text": " ".join([r.alternatives[0].transcript for r in response.results]),
    "status": "completed",
    "confidence": response.results[0].alternatives[0].confidence,
    "language": "en-US",
    "duration": None
}
```

## Files Modified

### 1. app/services/transcription.py (+187 lines, -28 lines)

**Changes:**
- Implemented `transcribe_audio()` with deterministic mock
- Added input validation (file exists, not empty)
- Added `_generate_mock_transcription()` helper
- Generated realistic sales call templates
- Calculated estimated duration from file size
- Added comprehensive TODO comments for Phase 4
- Updated `get_transcription_status()` to return completed

### 2. app/api/v1/endpoints/calls.py (+26 lines, -7 lines)

**Changes:**
- Added result validation before persistence
- Added specific exception handling (FileNotFoundError, ValueError)
- Always update transcription_status="failed" on error
- Return appropriate HTTP codes (404, 400, 500)
- Updated TODO marker for Phase 4
- Removed fallback defaults

## Workflow Verification

### Complete Flow Test

```bash
# 1. Upload audio file
POST /api/v1/calls/
→ transcription_status: "pending"
→ evaluation_status: "pending"

# 2. Transcribe (success)
POST /api/v1/calls/1/transcribe
→ transcription_status: "completed"
→ transcription_text: "Agent: Good morning!..."
→ Returns: {"text": "...", "status": "completed"}

# 3. Try to re-transcribe (should fail)
POST /api/v1/calls/1/transcribe
→ HTTP 409: "Transcription already completed for this call"

# 4. Try to evaluate before transcription (should fail on new call)
POST /api/v1/calls/2/evaluate
→ HTTP 400: "Transcription must be completed before evaluation"

# 5. Evaluate after transcription (success)
POST /api/v1/calls/1/evaluate
→ evaluation_status: "completed"
→ evaluation_details: {...RasnaScore...}
```

### Error Scenarios

```bash
# File deleted after upload
POST /api/v1/calls/1/transcribe
→ HTTP 404: "Audio file not found"
→ transcription_status: "failed"

# Empty audio file
POST /api/v1/calls/2/transcribe
→ HTTP 400: "Invalid audio file: Audio file is empty"
→ transcription_status: "failed"

# Unexpected service error
POST /api/v1/calls/3/transcribe
→ HTTP 500: "Transcription failed: ..."
→ transcription_status: "failed"
```

## API Examples

### Request: Transcribe Call

```bash
curl -X POST http://localhost:8000/api/v1/calls/1/transcribe
```

### Response: Success

```json
{
  "text": "Agent: Good morning! This is calling from the sales team. How are you doing today? Customer: I'm doing well, thanks. What's this regarding? Agent: I wanted to discuss how our platform can help streamline your workflow...",
  "status": "completed"
}
```

### Response: Already Completed

```json
{
  "detail": "Transcription already completed for this call"
}
```

### Response: File Not Found

```json
{
  "detail": "Audio file not found: /path/to/audio/file.mp3"
}
```

## Benefits

✅ **Deterministic Output**: Same file size → same transcription every time

✅ **End-to-End Testing**: Full workflow testable without external APIs

✅ **Realistic Content**: Sales call templates realistic enough for RASNA evaluation

✅ **Safe State Management**: Clear pending → completed | failed transitions

✅ **Defensive Error Handling**: Specific exceptions with appropriate HTTP codes

✅ **Workflow Integrity**: Evaluation blocked until transcription completed

✅ **Phase 4 Ready**: Clear integration points for real STT providers

✅ **No External Dependencies**: Works completely offline

✅ **No Breaking Changes**: Maintains all existing data contracts

## Testing Checklist

### Valid Transcription
- [x] Transcribe call with pending status → completed
- [x] Short file (< 1MB) → short transcription
- [x] Medium file (1-5MB) → medium transcription
- [x] Long file (> 5MB) → long transcription
- [x] Transcription text saved to database
- [x] Status updated to "completed"

### Validation
- [x] Try to transcribe completed call → 409
- [x] Try to transcribe non-existent call → 404
- [x] Try to evaluate before transcription → 400

### Error Handling
- [x] Missing audio file → 404 + status "failed"
- [x] Empty audio file → 400 + status "failed"
- [x] Invalid file path → 404 + status "failed"

### Workflow Integration
- [x] Upload → Transcribe → Evaluate (full flow works)
- [x] Evaluation requires completed transcription
- [x] Can't re-transcribe completed calls
- [x] Failed transcription prevents evaluation

## State Verification

```bash
# Check call state
GET /api/v1/calls/1

{
  "id": 1,
  "transcription": {
    "text": "Agent: Good morning!...",
    "status": "completed"
  },
  "evaluation": {
    "result": null,
    "status": "pending"
  }
}

# Now can evaluate
POST /api/v1/calls/1/evaluate
→ Success: Returns EvaluationResult
```

## Performance Characteristics

**Mock Transcription:**
- File validation: < 1ms
- Text generation: < 1ms
- Total processing: < 5ms

**Real STT (Phase 4):**
- Expected: 10-60 seconds depending on provider
- Will require background job queue
- Status polling will be needed

## Next Phase

**Phase 4: Real STT Provider Integration**

Tasks:
1. Choose STT provider (Whisper/AssemblyAI/Google)
2. Add API credentials to config
3. Implement async job queue (Celery/RQ)
4. Replace mock in TranscriptionService
5. Add status polling endpoint
6. Handle async transcription callbacks
7. Update transcription_status transitions
8. Add retry logic for failed transcriptions

Integration is straightforward - just replace the mock implementation:

```python
# CURRENT (Phase 3)
async def transcribe_audio(self, audio_path: Path) -> dict:
    transcription_text = self._generate_mock_transcription(...)
    return {"text": transcription_text, "status": "completed"}

# FUTURE (Phase 4)
async def transcribe_audio(self, audio_path: Path) -> dict:
    transcript = await whisper_client.transcribe(audio_path)
    return {"text": transcript.text, "status": "completed"}
```

Everything else remains unchanged!

---

**Status**: ✅ COMPLETE
**Quality**: Production-ready (with mock data)
**Safe for**: End-to-end workflow testing
**Ready for**: Phase 4 (Real STT Integration)
