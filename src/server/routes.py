"""API routes for the transcription service."""

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.config import LANGUAGES, CONVERSATION_TYPES, SUPPORTED_EXTENSIONS, UPLOAD_DIR, MAX_FILE_SIZE
from src.server.jobs import job_manager
from src.server.websocket import connection_manager
from src.logger import logger

router = APIRouter(prefix="/api")


class UploadResponse(BaseModel):
    job_id: str


class ConfigResponse(BaseModel):
    languages: list[str]
    conversation_types: list[str]
    supported_extensions: list[str]
    max_file_size: int


class JobResponse(BaseModel):
    id: str
    status: str
    progress: int
    stage: str
    error: Optional[str] = None
    filename: Optional[str] = None
    language: Optional[str] = None
    conversation_type: Optional[str] = None
    result: Optional[dict] = None


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get application configuration for frontend."""
    return ConfigResponse(
        languages=list(LANGUAGES.keys()),
        conversation_types=CONVERSATION_TYPES,
        supported_extensions=list(SUPPORTED_EXTENSIONS),
        max_file_size=MAX_FILE_SIZE,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    language: str = Form(...),
    conversation_type: str = Form(...),
):
    """Upload an audio file and start transcription."""
    # Validate language
    if language not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Invalid language: {language}")

    # Validate conversation type
    if conversation_type not in CONVERSATION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid conversation type: {conversation_type}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Create job
    job_id = job_manager.create_job()

    # Save uploaded file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{job_id}{file_ext}"

    try:
        # Check file size while saving
        total_size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                buffer.write(chunk)

        logger.info(f"File saved: {file_path} ({total_size} bytes)")

        # Progress callback that sends WebSocket updates
        async def progress_callback(job_id: str, stage: str, percent: int):
            job = job_manager.get_job(job_id)
            if not job:
                return

            if stage == "failed" and job.error:
                await connection_manager.send_error(job_id, job.error)
            elif stage == "completed" and job.result:
                await connection_manager.send_completed(job_id, job.to_dict().get("result", {}))
            else:
                await connection_manager.send_progress(job_id, stage, percent)

        # Start transcription in background
        asyncio.create_task(
            job_manager.run_transcription(
                job_id,
                file_path,
                language,
                conversation_type,
                progress_callback,
            )
        )

        return UploadResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to save uploaded file: {e}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to process upload")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get the status and result of a transcription job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dict = job.to_dict()
    return JobResponse(
        id=job_dict["id"],
        status=job_dict["status"],
        progress=job_dict["progress"],
        stage=job_dict["stage"],
        error=job_dict.get("error"),
        filename=job_dict.get("filename"),
        language=job_dict.get("language"),
        conversation_type=job_dict.get("conversation_type"),
        result=job_dict.get("result"),
    )


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress updates."""
    # Verify job exists
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    await connection_manager.connect(websocket, job_id)

    try:
        # Send current status immediately
        job_dict = job.to_dict()
        if job.status == "completed" and job.result:
            await websocket.send_json({
                "type": "completed",
                "result": job_dict.get("result", {}),
            })
        elif job.status == "failed":
            await websocket.send_json({
                "type": "error",
                "message": job.error or "Unknown error",
            })
        else:
            await websocket.send_json({
                "type": "progress",
                "stage": job.stage,
                "percent": job.progress,
            })

        # Keep connection alive and wait for messages
        while True:
            try:
                # Wait for client messages (ping/pong or close)
                data = await websocket.receive_text()
                # Client can send ping to keep alive
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    finally:
        connection_manager.disconnect(websocket, job_id)
