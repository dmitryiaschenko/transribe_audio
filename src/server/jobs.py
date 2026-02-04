"""In-memory job manager for tracking transcription jobs."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Literal, Callable, Awaitable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from src.api.transcription_service import TranscriptionService, TranscriptionResult, TranscriptionError
from src.logger import logger


JobStatus = Literal["pending", "uploading", "processing", "completed", "failed"]


@dataclass
class Job:
    """Represents a transcription job."""
    id: str
    status: JobStatus = "pending"
    progress: int = 0
    stage: str = "pending"
    result: Optional[TranscriptionResult] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    filename: Optional[str] = None
    language: Optional[str] = None
    conversation_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert job to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "status": self.status,
            "progress": self.progress,
            "stage": self.stage,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "filename": self.filename,
            "language": self.language,
            "conversation_type": self.conversation_type,
        }
        if self.result:
            data["result"] = {
                "text": self.result.text,
                "input_tokens": self.result.input_tokens,
                "output_tokens": self.result.output_tokens,
                "total_tokens": self.result.total_tokens,
                "input_cost": self.result.input_cost,
                "output_cost": self.result.output_cost,
                "total_cost": self.result.total_cost,
            }
        return data


ProgressCallback = Callable[[str, str, int], Awaitable[None]]


class JobManager:
    """Manages transcription jobs in-memory."""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._transcription_service = TranscriptionService()
        logger.info("JobManager initialized")

    def create_job(self) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = Job(id=job_id)
        logger.info(f"Created job: {job_id}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        result: Optional[TranscriptionResult] = None,
        error: Optional[str] = None,
        filename: Optional[str] = None,
        language: Optional[str] = None,
        conversation_type: Optional[str] = None,
    ) -> Optional[Job]:
        """Update a job's fields."""
        job = self._jobs.get(job_id)
        if not job:
            return None

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if stage is not None:
            job.stage = stage
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if filename is not None:
            job.filename = filename
        if language is not None:
            job.language = language
        if conversation_type is not None:
            job.conversation_type = conversation_type

        return job

    async def run_transcription(
        self,
        job_id: str,
        file_path: Path,
        language: str,
        conversation_type: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Run transcription in background thread with progress updates."""
        job = self._jobs.get(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return

        async def notify_progress(stage: str, percent: int):
            self.update_job(job_id, stage=stage, progress=percent)
            if progress_callback:
                await progress_callback(job_id, stage, percent)

        try:
            # Update job metadata
            self.update_job(
                job_id,
                status="processing",
                filename=file_path.name,
                language=language,
                conversation_type=conversation_type,
            )
            await notify_progress("processing", 10)

            # Initialize service if needed
            if not self._transcription_service.is_initialized:
                await notify_progress("initializing", 20)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    self._executor,
                    self._transcription_service.initialize
                )

            await notify_progress("transcribing", 30)

            # Run transcription in thread pool
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self._executor,
                lambda: self._transcription_service.transcribe(
                    str(file_path),
                    language,
                    conversation_type,
                )
            )

            # Set result BEFORE notifying so callback can access it
            self.update_job(job_id, status="completed", result=result)
            await notify_progress("completed", 100)
            logger.info(f"Job {job_id} completed successfully")

        except TranscriptionError as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.update_job(job_id, status="failed", error=str(e))
            if progress_callback:
                await progress_callback(job_id, "failed", 0)

        except Exception as e:
            logger.exception(f"Job {job_id} failed with unexpected error")
            self.update_job(job_id, status="failed", error=str(e))
            if progress_callback:
                await progress_callback(job_id, "failed", 0)

        finally:
            # Clean up uploaded file
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up uploaded file: {file_path}")

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than max_age_hours. Returns count of removed jobs."""
        now = datetime.now()
        to_remove = []
        for job_id, job in self._jobs.items():
            age = (now - job.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
        return len(to_remove)


# Global job manager instance
job_manager = JobManager()
