from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from pathlib import Path

from app.api.deps import get_database, get_current_user
from app.schemas.call import (
    CallResponse,
    CallListResponse,
    TranscriptionResponse,
    EvaluationResponse
)
from app.repositories.call import CallRepository
from app.services.storage import StorageService
from app.services.transcription import TranscriptionService
from app.services.evaluation import EvaluationService
from app.core.config import settings
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def upload_call(
    audio_file: UploadFile = File(...),
    agent_name: str = Form(...),
    customer_name: str = Form(None),
    call_type: str = Form(...),
    lead_type: str = Form(...),
    call_stage: str = Form(...),
    deck_shared: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Upload a sales call audio file with context

    This endpoint handles the complete audio upload and persistence workflow:
    1. Validates all input parameters
    2. Validates audio file format and size
    3. Persists audio file to storage
    4. Creates database record atomically
    5. Returns call metadata for client

    Phase 3 Integration Points:
    - TODO: After successful upload, trigger async transcription job
    - TODO: After transcription completes, trigger evaluation job
    """
    storage_service = StorageService()
    call_repo = CallRepository(db)
    stored_filename = None

    # ============================================
    # VALIDATION PHASE
    # ============================================

    # Validate required string fields
    if not agent_name or not agent_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="agent_name is required and cannot be empty"
        )

    if not call_type or not call_type.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="call_type is required and cannot be empty"
        )

    # Validate lead_type enum
    if lead_type not in ["hot", "warm", "cold"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lead_type. Must be: hot, warm, or cold"
        )

    # Validate call_stage enum
    if call_stage not in ["qualification", "main", "follow-up"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid call_stage. Must be: qualification, main, or follow-up"
        )

    # Validate audio file is present
    if not audio_file or not audio_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required"
        )

    # Validate file format
    file_extension = Path(audio_file.filename).suffix.lower()
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file must have a valid extension"
        )

    if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio format '{file_extension}'. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )

    # Read and validate file content
    try:
        file_content = await audio_file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read audio file: {str(e)}"
        )

    file_size = len(file_content)

    # Validate file is not empty
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file cannot be empty"
        )

    # Validate file size limit
    if file_size > settings.MAX_AUDIO_FILE_SIZE:
        max_size_mb = settings.MAX_AUDIO_FILE_SIZE / 1024 / 1024
        actual_size_mb = file_size / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({actual_size_mb:.2f}MB). Maximum allowed: {max_size_mb:.2f}MB"
        )

    # ============================================
    # PERSISTENCE PHASE (Atomic)
    # ============================================

    try:
        # Step 1: Save audio file to storage
        try:
            filename, file_path = await storage_service.save_audio_file(
                file_content,
                audio_file.filename
            )
            stored_filename = filename
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save audio file: {str(e)}"
            )

        # Step 2: Create database record
        call_data = {
            "user_id": current_user.id,
            "agent_name": agent_name.strip(),
            "customer_name": customer_name.strip() if customer_name else None,
            "call_type": call_type.strip(),
            "lead_type": lead_type,
            "call_stage": call_stage,
            "deck_shared": deck_shared,
            "audio_filename": filename,
            "audio_path": file_path,
            "audio_format": file_extension,
            "audio_size": file_size,
            "transcription_status": "pending",
            "evaluation_status": "pending"
        }

        try:
            db_call = call_repo.create(call_data)
        except Exception as e:
            # Database insert failed - clean up stored file to maintain atomicity
            if stored_filename:
                try:
                    storage_service.delete_audio_file(stored_filename)
                except Exception:
                    # Log this in production, but don't fail the request
                    pass

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create call record: {str(e)}"
            )

        # ============================================
        # POST-UPLOAD HOOKS (Phase 3)
        # ============================================

        # TODO: Phase 3 - Trigger async transcription job
        # Example:
        #   transcription_task.delay(call_id=db_call.id, audio_path=file_path)

        # TODO: Phase 3 - After transcription completes, trigger evaluation
        # This will be handled by transcription completion callback

        # Return successful response
        return _format_call_response(db_call, current_user.id, db)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors and clean up
        if stored_filename:
            try:
                storage_service.delete_audio_file(stored_filename)
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during upload: {str(e)}"
        )


@router.get("/", response_model=CallListResponse)
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    List all calls for the current user with pagination

    User isolation: Returns only calls belonging to the authenticated user
    """
    call_repo = CallRepository(db)
    calls = call_repo.get_all_for_user(current_user.id, skip=skip, limit=limit)
    total = call_repo.count_for_user(current_user.id)

    return {
        "total": total,
        "calls": [_format_call_response(call, current_user.id, db) for call in calls]
    }


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get call details by ID

    User isolation: Enforces ownership - users can only access their own calls
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this call"
        )

    return _format_call_response(db_call, current_user.id, db)


@router.post("/{call_id}/transcribe", response_model=TranscriptionResponse)
async def trigger_transcription(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Manually trigger transcription for a call

    Requirements:
    - Call must exist
    - User must own the call
    - Transcription must not already be completed
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    # Validate call exists
    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this call"
        )

    # Prevent re-transcription if already completed
    if db_call.transcription_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transcription already completed for this call"
        )

    try:
        # TODO: Phase 4 - Replace mock with actual STT provider (Whisper/AssemblyAI/Google)
        transcription_service = TranscriptionService()
        result = await transcription_service.transcribe_audio(Path(db_call.audio_path))

        # Validate transcription result
        transcription_text = result.get("text")
        transcription_status = result.get("status")

        if not transcription_text or not transcription_status:
            raise ValueError("Invalid transcription result: missing text or status")

        # Persist transcription to database
        call_repo.update(call_id, {
            "transcription_text": transcription_text,
            "transcription_status": transcription_status
        })

        return {
            "text": transcription_text,
            "status": transcription_status
        }

    except FileNotFoundError as e:
        # Audio file not found - mark as failed
        call_repo.update(call_id, {
            "transcription_status": "failed"
        })
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found: {str(e)}"
        )

    except ValueError as e:
        # Invalid audio file or transcription result - mark as failed
        call_repo.update(call_id, {
            "transcription_status": "failed"
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio file: {str(e)}"
        )

    except Exception as e:
        # Unexpected error - mark as failed
        call_repo.update(call_id, {
            "transcription_status": "failed"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/{call_id}/evaluate", response_model=EvaluationResponse)
async def trigger_evaluation(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Manually trigger RASNA evaluation for a call

    Requirements:
    - Call must exist
    - User must own the call
    - Transcription must be completed
    - Evaluation must not already be completed
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    # Validate call exists
    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this call"
        )

    # Validate transcription is completed
    if db_call.transcription_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription must be completed before evaluation. Current status: {db_call.transcription_status}"
        )

    # Prevent re-evaluation if already completed
    if db_call.evaluation_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evaluation already completed for this call"
        )

    try:
        # TODO: Replace mock evaluation with actual LLM-based evaluation
        evaluation_service = EvaluationService()
        result = await evaluation_service.evaluate_call(
            db_call.transcription_text,
            {
                "agent_name": db_call.agent_name,
                "customer_name": db_call.customer_name,
                "call_type": db_call.call_type,
                "lead_type": db_call.lead_type,
                "call_stage": db_call.call_stage,
                "deck_shared": db_call.deck_shared
            }
        )

        # Extract evaluation result
        evaluation_result = result.get("result")
        evaluation_status = result.get("status", "completed")
        overall_score = evaluation_result.get("scores", {}).get("overall") if evaluation_result else None

        # Persist evaluation to database
        call_repo.update(call_id, {
            "evaluation_score": overall_score,
            "evaluation_details": evaluation_result,
            "evaluation_status": evaluation_status
        })

        return {
            "result": evaluation_result,
            "status": evaluation_status
        }

    except Exception as e:
        # Handle evaluation failure
        call_repo.update(call_id, {
            "evaluation_status": "failed"
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/{call_id}/baseline", response_model=CallResponse)
async def mark_as_baseline(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Mark a call as baseline (best call example)

    Purpose: Allows users to mark exceptional calls as "best examples"
    for future comparison and learning. This helps track performance
    against ideal call patterns.

    Requirements:
    - Call must exist
    - User must own the call
    - Transcription must be completed
    - Evaluation must be completed

    Note: Baseline calls are user-specific - each user has their own baseline
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    # Validate call exists
    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this call"
        )

    # Enforce rule: transcription must be completed
    if db_call.transcription_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot mark as baseline: transcription must be completed. Current status: {db_call.transcription_status}"
        )

    # Enforce rule: evaluation must be completed
    if db_call.evaluation_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot mark as baseline: evaluation must be completed. Current status: {db_call.evaluation_status}"
        )

    # Mark as baseline
    updated_call = call_repo.mark_as_baseline(call_id)

    return _format_call_response(updated_call, current_user.id, db)


@router.delete("/{call_id}/baseline", response_model=CallResponse)
async def unmark_as_baseline(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Remove baseline marking from a call

    Purpose: Allows users to unmark a call that was previously
    marked as a baseline example.
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    # Validate call exists
    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this call"
        )

    # Unmark as baseline
    updated_call = call_repo.unmark_as_baseline(call_id)

    return _format_call_response(updated_call, current_user.id, db)


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Delete a call and its audio file

    User isolation: Only the owner can delete their call
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    if db_call.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy call requires migration before access"
        )

    if db_call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this call"
        )

    # Delete audio file
    storage_service = StorageService()
    storage_service.delete_audio_file(db_call.audio_filename)

    # Delete database record
    call_repo.delete(call_id)

    return None


def _format_call_response(db_call, user_id: int = None, db: Session = None) -> dict:
    """
    Helper to format call model to response schema.

    Phase 7: Optionally includes baseline comparison if:
    - user_id and db are provided
    - User has a baseline
    - Call has completed evaluation
    """
    from app.services.baseline import BaselineService

    # Build base response
    response = {
        "id": db_call.id,
        "agent_name": db_call.agent_name,
        "customer_name": db_call.customer_name,
        "call_type": db_call.call_type,
        "call_date": db_call.call_date,
        "lead_type": db_call.lead_type,
        "call_stage": db_call.call_stage,
        "deck_shared": db_call.deck_shared,
        "audio_filename": db_call.audio_filename,
        "audio_format": db_call.audio_format,
        "audio_size": db_call.audio_size,
        "transcription": {
            "text": db_call.transcription_text,
            "status": db_call.transcription_status
        },
        "evaluation": {
            "result": db_call.evaluation_details,
            "status": db_call.evaluation_status,
            "comparison_to_baseline": None  # Default: null (graceful degradation)
        },
        "is_baseline": db_call.is_baseline,
        "baseline_marked_at": db_call.baseline_marked_at,
        "created_at": db_call.created_at,
        "updated_at": db_call.updated_at
    }

    # Phase 7: Add baseline comparison if available
    if user_id and db and db_call.evaluation_status == "completed" and db_call.evaluation_details:
        try:
            baseline_service = BaselineService(db)
            comparison = baseline_service.compare_to_baseline(user_id, db_call.evaluation_details)
            if comparison:
                response["evaluation"]["comparison_to_baseline"] = comparison
        except Exception:
            # Graceful degradation: if baseline comparison fails, just omit it
            pass

    return response
