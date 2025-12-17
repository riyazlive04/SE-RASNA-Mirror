from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from pathlib import Path

from app.api.deps import get_database
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
    db: Session = Depends(get_database)
):
    """
    Upload a sales call audio file with context
    """
    # Validate lead_type
    if lead_type not in ["hot", "warm", "cold"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lead_type. Must be: hot, warm, or cold"
        )

    # Validate call_stage
    if call_stage not in ["qualification", "main", "follow-up"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid call_stage. Must be: qualification, main, or follow-up"
        )
    # Validate file format
    file_extension = Path(audio_file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio format. Allowed: {settings.ALLOWED_AUDIO_FORMATS}"
        )

    # Read file content
    file_content = await audio_file.read()
    file_size = len(file_content)

    # Validate file size
    if file_size > settings.MAX_AUDIO_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_AUDIO_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save audio file
    storage_service = StorageService()
    filename, file_path = await storage_service.save_audio_file(
        file_content,
        audio_file.filename
    )

    # Create call record
    call_repo = CallRepository(db)
    call_data = {
        "agent_name": agent_name,
        "customer_name": customer_name,
        "call_type": call_type,
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

    db_call = call_repo.create(call_data)

    # TODO: Trigger async transcription job
    # TODO: Trigger async evaluation job after transcription

    return _format_call_response(db_call)


@router.get("/", response_model=CallListResponse)
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database)
):
    """
    List all calls with pagination
    """
    call_repo = CallRepository(db)
    calls = call_repo.get_all(skip=skip, limit=limit)
    total = call_repo.count()

    return {
        "total": total,
        "calls": [_format_call_response(call) for call in calls]
    }


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    db: Session = Depends(get_database)
):
    """
    Get call details by ID
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    return _format_call_response(db_call)


@router.post("/{call_id}/transcribe", response_model=TranscriptionResponse)
async def trigger_transcription(
    call_id: int,
    db: Session = Depends(get_database)
):
    """
    Manually trigger transcription for a call

    Requirements:
    - Call must exist
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

    # Prevent re-transcription if already completed
    if db_call.transcription_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transcription already completed for this call"
        )

    try:
        # TODO: Trigger actual transcription service
        transcription_service = TranscriptionService()
        result = await transcription_service.transcribe_audio(Path(db_call.audio_path))

        # Persist transcription to database
        call_repo.update(call_id, {
            "transcription_text": result.get("text"),
            "transcription_status": result.get("status", "pending")
        })

        return {
            "text": result.get("text"),
            "status": result.get("status", "pending")
        }

    except Exception as e:
        # Handle transcription failure
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
    db: Session = Depends(get_database)
):
    """
    Manually trigger RASNA evaluation for a call

    Requirements:
    - Call must exist
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


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: int,
    db: Session = Depends(get_database)
):
    """
    Delete a call and its audio file
    """
    call_repo = CallRepository(db)
    db_call = call_repo.get_by_id(call_id)

    if not db_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    # Delete audio file
    storage_service = StorageService()
    storage_service.delete_audio_file(db_call.audio_filename)

    # Delete database record
    call_repo.delete(call_id)

    return None


def _format_call_response(db_call) -> dict:
    """Helper to format call model to response schema"""
    return {
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
            "status": db_call.evaluation_status
        },
        "created_at": db_call.created_at,
        "updated_at": db_call.updated_at
    }
