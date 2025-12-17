# LLM Integration - Production-Ready RASNA Evaluation

## Overview

This document describes the integration of LLM-based intelligence into SE RASNA Mirror's evaluation system. The implementation prioritizes safety, reliability, and graceful degradation while maintaining all existing contracts and workflows.

## Architecture

### System Flow

```
Call Evaluation Request
    ↓
[EvaluationService.evaluate_call()]
    ↓
Try: LLM Evaluation
    ├─→ Build Prompt (transcript + context)
    ├─→ Call LLM (with retry + timeout)
    ├─→ Validate JSON Response
    ├─→ Validate Schema (Pydantic)
    ├─→ Return EvaluationResult + llm_used=true
    ↓
Catch: Any Exception
    ├─→ Log Warning (no PII)
    ├─→ Fall Back to Deterministic Mock
    ├─→ Return EvaluationResult + llm_used=false
    ↓
Always: Return 200 OK with valid result
```

## Components

### 1. LLMClient (`app/services/llm_client.py`)

**Purpose**: Safe wrapper around OpenAI API with retry, timeout, and error handling.

**Features**:
- **Model**: `gpt-4o-mini` (fast, cost-effective)
- **Temperature**: `0.0` (deterministic output)
- **Max Tokens**: `2000` (sufficient for RASNA evaluation)
- **Timeout**: `30 seconds`
- **Max Retries**: `2` with exponential backoff
- **JSON Mode**: Forces `response_format={"type": "json_object"}`

**Error Handling**:
```python
APITimeoutError → Retry with backoff (2^attempt seconds)
RateLimitError → Retry with longer backoff (2^(attempt+1) seconds)
OpenAIError → Retry then raise RuntimeError
JSONDecodeError → Raise ValueError
Empty response → Raise ValueError
```

**Logging**:
```python
✓ Request attempt number and model
✓ Success with token usage
✓ Timeouts and retries
✓ Rate limits
✓ API errors
✗ No transcripts or PII
```

### 2. RASNA Evaluation Prompt (`app/services/prompts/rasna_evaluation_prompt.py`)

**Purpose**: Structured prompt template that guides LLM to output valid RASNA evaluations.

**Function**: `build_evaluation_prompt(transcript, lead_type, call_stage, deck_shared)`

**System Prompt Structure**:
1. Role definition (expert sales call evaluator)
2. RASNA framework explanation
3. Scoring guidelines (0-40 poor, 41-60 fair, 61-80 good, 81-100 excellent)
4. Context considerations (how lead_type and call_stage affect scoring)
5. Exact JSON schema specification
6. Requirements (2-4 strengths, 2-4 improvements, specific examples)

**User Prompt Structure**:
1. Call context (lead_type, call_stage, deck_shared)
2. Full transcript
3. Instruction to follow JSON schema

**Output Schema**:
```json
{
  "scores": {
    "rapport": 0-100,
    "situation": 0-100,
    "pain": 0-100,
    "need": 0-100,
    "ask": 0-100,
    "overall": 0-100
  },
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "next_call_focus": "..."
}
```

### 3. EvaluationService (`app/services/evaluation.py`)

**Updated Flow**:

**Primary Path** (`_evaluate_with_llm`):
1. Build prompt from context
2. Call LLM via LLMClient
3. Validate response structure (all required fields present)
4. Validate RASNA scores (all 5 components + overall)
5. Validate arrays (2-4 strengths, 2-4 improvements)
6. Create Pydantic models (strict validation)
7. Return `EvaluationResult` + metadata

**Fallback Path** (`_evaluate_with_mock`):
- Original deterministic logic preserved
- Same scoring rules by lead_type and call_stage
- Same strength/improvement generation
- No changes from Phase 1

**Metadata Flag**:
```python
# LLM success
result["llm_used"] = True

# LLM failure (fallback)
result["llm_used"] = False
```

### 4. Configuration (`app/core/config.py`)

**New Settings**:
```python
OPENAI_API_KEY: str = ""  # Required for LLM
LLM_MODEL: str = "gpt-4o-mini"  # Can override
LLM_TEMPERATURE: float = 0.0  # Deterministic
LLM_MAX_TOKENS: int = 2000  # Evaluation limit
LLM_TIMEOUT_SECONDS: int = 30  # Request timeout
LLM_MAX_RETRIES: int = 2  # Retry attempts
```

**Environment Loading**:
```python
class Config:
    env_file = ".env"  # Reads from .env file
```

### 5. Environment Template (`.env.example`)

**Required**:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

**Optional** (defaults provided):
```bash
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=2000
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

## Safety Guarantees

### 1. Strict Validation

**JSON Parsing**:
```python
✓ Force JSON via response_format
✓ Strict json.loads() with error handling
✓ ValueError on parse failure
```

**Schema Validation**:
```python
✓ Check all required fields exist
✓ Validate field types
✓ Pydantic enforces ranges (0-100)
✓ Array length validation (2-4 items)
```

**Score Computation**:
```python
✓ All 5 RASNA components required
✓ Overall computed if missing
✓ Fallback to computed value if invalid
```

### 2. Error Handling

**Never Expose Raw LLM Output**:
```python
try:
    result = await llm_client.generate_json(...)
    # Validate before returning
    validate_structure(result)
    return EvaluationResult(**result)
except Exception:
    # Fallback to mock - never expose error to client
    return mock_evaluation(context)
```

**Status Always "completed"**:
```python
# LLM or fallback, status is always "completed"
return {"result": ..., "status": "completed"}

# Never return "failed" for evaluation
# (Different from transcription, which can fail)
```

### 3. Graceful Degradation

**Automatic Fallback**:
```python
Scenario                    → Fallback    → User Impact
─────────────────────────────────────────────────────────
OPENAI_API_KEY not set      → Mock        → None
LLM timeout                 → Mock        → None
Rate limit exceeded         → Mock        → None
Invalid JSON response       → Mock        → None
Missing required fields     → Mock        → None
Invalid score ranges        → Mock        → None
Network error               → Mock        → None
```

**Metadata Transparency**:
```python
# Check if LLM was used
if evaluation_result["llm_used"]:
    print("Real LLM intelligence")
else:
    print("Deterministic fallback")
```

### 4. Logging

**Logged**:
- Evaluation start (with context, no transcript)
- LLM request attempts
- LLM success with token usage
- LLM failures with error type
- Fallback triggered
- Evaluation completion

**NOT Logged**:
- Transcripts (PII)
- Customer names (PII)
- LLM response content (could contain PII)

## Setup Instructions

### 1. Get OpenAI API Key

```bash
# Visit: https://platform.openai.com/api-keys
# Create new secret key
# Copy key (starts with sk-...)
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env

# Edit .env
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# Installs: openai==1.12.0
```

### 4. Run Application

```bash
uvicorn app.main:app --reload
```

### 5. Verify Integration

```bash
# Upload call and transcribe
curl -X POST http://localhost:8000/api/v1/calls/1/transcribe

# Evaluate (should use LLM if API key set)
curl -X POST http://localhost:8000/api/v1/calls/1/evaluate

# Check response
{
  "result": {
    "scores": {...},
    "strengths": [...],
    "improvements": [...],
    "next_call_focus": "...",
    "llm_used": true  # <-- Confirms LLM was used
  },
  "status": "completed"
}
```

## Testing Scenarios

### Scenario 1: LLM Success
```bash
# Prerequisites
✓ OPENAI_API_KEY set in .env
✓ Valid API key with credits
✓ Network connectivity

# Expected
→ LLM evaluation runs
→ Response validated
→ llm_used = true
→ Realistic, context-aware scores
```

### Scenario 2: LLM Failure (No API Key)
```bash
# Prerequisites
✗ OPENAI_API_KEY not set

# Expected
→ Warning logged: "OPENAI_API_KEY not set"
→ LLM client initialization succeeds (no crash)
→ Evaluation triggers LLM → fails immediately
→ Fallback to mock
→ llm_used = false
→ Deterministic scores based on context
```

### Scenario 3: LLM Timeout
```bash
# Prerequisites
✓ OPENAI_API_KEY set
✗ Slow network or API timeout

# Expected
→ First attempt times out after 30s
→ Retry attempt 1 (2s backoff)
→ Retry attempt 2 (4s backoff)
→ Max retries exceeded
→ Fallback to mock
→ llm_used = false
→ User gets result without delay
```

### Scenario 4: Invalid LLM Response
```bash
# Prerequisites
✓ OPENAI_API_KEY set
✗ LLM returns invalid JSON or missing fields

# Expected
→ JSON parsing fails or validation fails
→ ValueError raised
→ Logged: "LLM evaluation failed, falling back to mock"
→ Fallback to mock
→ llm_used = false
→ User gets valid result
```

### Scenario 5: Rate Limit
```bash
# Prerequisites
✓ OPENAI_API_KEY set
✗ Rate limit exceeded

# Expected
→ RateLimitError raised
→ Retry with longer backoff
→ Max retries exceeded
→ Fallback to mock
→ llm_used = false
→ User gets result
```

## Cost Analysis

### Model: gpt-4o-mini

**Pricing** (as of 2024):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Average RASNA Evaluation**:
- Input tokens: ~1500 (system prompt + transcript)
- Output tokens: ~500 (JSON evaluation)
- Cost per evaluation: ~$0.0005 (0.05 cents)

**Monthly Estimates**:
- 100 evaluations/day = $1.50/month
- 1000 evaluations/day = $15/month
- 10,000 evaluations/day = $150/month

**Cost vs. Value**:
- Deterministic mock: $0
- LLM evaluation: $0.0005
- Value: Context-aware, intelligent feedback
- Recommendation: Use LLM for production, mock for dev/testing

## Performance

### Latency

**LLM Path**:
```
Network latency:     100-500ms
LLM generation:      2-5 seconds
Validation:          < 10ms
Total:               2-6 seconds
```

**Fallback Path**:
```
Mock computation:    < 10ms
Total:               < 10ms
```

**Timeout Protection**:
```
Max wait:            30 seconds
Retry backoff:       2s, 4s, 8s
Total max:           ~42 seconds → fallback
```

### Throughput

**LLM Rate Limits** (varies by tier):
- Free tier: ~3 requests/minute
- Pay-as-you-go tier 1: ~60 requests/minute
- Higher tiers: 500+ requests/minute

**Fallback Handling**:
- Rate limit → automatic fallback
- No user-facing queue
- Instant response with mock

## Monitoring

### Key Metrics to Track

1. **LLM Success Rate**:
   ```python
   SELECT
     COUNT(*) FILTER (WHERE evaluation_details->>'llm_used' = 'true') AS llm_count,
     COUNT(*) FILTER (WHERE evaluation_details->>'llm_used' = 'false') AS fallback_count
   FROM calls;
   ```

2. **Evaluation Latency**:
   - Track time from request to response
   - Separate LLM vs fallback latency

3. **LLM Error Types**:
   - Timeouts
   - Rate limits
   - JSON validation failures
   - Score validation failures

4. **Cost Tracking**:
   - Token usage per evaluation
   - Daily/monthly API costs

### Logs to Monitor

```bash
# LLM success
INFO: LLM request successful (tokens_used=2000)

# LLM failure
WARNING: LLM evaluation failed, falling back to deterministic mock: <reason>

# Timeout
WARNING: LLM request timeout (attempt 1): <error>

# Rate limit
WARNING: LLM rate limit hit (attempt 1): <error>
```

## Troubleshooting

### Issue: All evaluations use fallback (llm_used=false)

**Check**:
1. Is OPENAI_API_KEY set in .env?
2. Is .env file in correct location (backend/.env)?
3. Is API key valid (starts with sk-)?
4. Does API key have credits?
5. Check logs for specific error

**Fix**:
```bash
# Verify env loading
python -c "from app.core.config import settings; print(settings.OPENAI_API_KEY)"

# Should print your API key, not empty string
```

### Issue: Slow evaluation responses

**Check**:
1. Network latency to OpenAI
2. LLM timeout setting
3. Retry backoff adding delay

**Fix**:
```python
# In .env, reduce timeout for faster fallback
LLM_TIMEOUT_SECONDS=10  # Default: 30
LLM_MAX_RETRIES=1  # Default: 2
```

### Issue: High API costs

**Check**:
1. Token usage per evaluation
2. Number of evaluations per day
3. Model being used

**Fix**:
```python
# Use mock for dev/testing
# Only use LLM for production evals

# Or reduce max tokens
LLM_MAX_TOKENS=1500  # Default: 2000
```

## Future Enhancements

### Phase 5 Possibilities

1. **Multi-Provider Support**:
   - Add Anthropic Claude support
   - Add Google Gemini support
   - Provider selection via config

2. **Caching**:
   - Cache evaluations for identical transcripts
   - TTL-based cache invalidation
   - Redis integration

3. **Async Processing**:
   - Background job queue (Celery/RQ)
   - Webhook callbacks on completion
   - Status polling endpoint

4. **Advanced Prompts**:
   - Few-shot examples
   - Chain-of-thought reasoning
   - Multi-turn refinement

5. **A/B Testing**:
   - Compare LLM vs mock quality
   - Track user satisfaction
   - Optimize prompts

## Security Considerations

**API Key Protection**:
- ✅ Stored in .env (not committed)
- ✅ Not exposed to frontend
- ✅ Not logged
- ✅ Pydantic-settings auto-loading

**PII Protection**:
- ✅ Transcripts not logged
- ✅ Customer names not logged
- ✅ LLM responses not logged
- ✅ Only metadata logged (error types, token counts)

**Input Validation**:
- ✅ All LLM outputs validated
- ✅ Pydantic enforces schema
- ✅ Invalid outputs rejected
- ✅ Fallback on validation failure

**Rate Limiting**:
- ✅ OpenAI handles rate limits
- ✅ Retry with backoff
- ✅ Fallback after max retries
- ✅ No user-facing errors

---

**Status**: ✅ PRODUCTION READY
**Safe for**: Demos, pilots, and production use
**Fallback**: Always available (zero user impact)
**Monitoring**: Comprehensive logging without PII
