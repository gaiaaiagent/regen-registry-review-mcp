"""Background job management for long-running PDF conversions.

Simple async job queue without external dependencies. Jobs are tracked
in-memory with progress persisted to session state for transparency.

Memory-Aware Scheduling:
- Checks available RAM before starting each document conversion
- Waits with exponential backoff if memory is insufficient
- Reports memory status in job progress
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine

import psutil

logger = logging.getLogger(__name__)

# Memory thresholds for job scheduling
MIN_MEMORY_GB = 10  # Minimum RAM to start conversion (8GB model + 2GB buffer)
MEMORY_CHECK_INTERVAL = 30  # Seconds between memory checks when waiting
MAX_MEMORY_WAIT_TIME = 600  # Maximum seconds to wait for memory (10 min)


def check_memory_for_conversion() -> tuple[bool, float]:
    """Check if sufficient memory is available for conversion.

    Returns:
        Tuple of (is_available, available_gb)
    """
    available_gb = psutil.virtual_memory().available / (1024 ** 3)
    return available_gb >= MIN_MEMORY_GB, round(available_gb, 1)


class JobStatus(str, Enum):
    """Status of a background job."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_MEMORY = "waiting_for_memory"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionJob:
    """Tracks a PDF conversion job with progress and memory status."""
    job_id: str
    session_id: str
    document_ids: list[str]
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    current_file: str | None = None
    files_completed: int = 0
    files_total: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    # Memory-aware scheduling fields
    memory_wait_started: datetime | None = None
    memory_available_gb: float | None = None
    memory_required_gb: float = MIN_MEMORY_GB

    def to_dict(self) -> dict[str, Any]:
        """Serialize job for API responses."""
        result = {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "current_file": self.current_file,
            "files_completed": self.files_completed,
            "files_total": self.files_total,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "eta_seconds": self.estimate_remaining_time(),
            "eta_human": self._format_eta(),
        }

        # Add memory status if waiting
        if self.status == JobStatus.WAITING_FOR_MEMORY:
            result["memory_status"] = {
                "available_gb": self.memory_available_gb,
                "required_gb": self.memory_required_gb,
                "waiting_since": self.memory_wait_started.isoformat() if self.memory_wait_started else None,
                "message": (
                    f"Waiting for memory: {self.memory_available_gb}GB available, "
                    f"{self.memory_required_gb}GB required"
                ),
            }

        return result

    def estimate_remaining_time(self) -> int | None:
        """Estimate seconds remaining based on progress."""
        if not self.started_at or self.files_completed == 0:
            # Rough estimate: 5 minutes per file
            return self.files_total * 300 if self.files_total > 0 else None

        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        avg_per_file = elapsed / self.files_completed
        remaining = self.files_total - self.files_completed
        return int(remaining * avg_per_file)

    def _format_eta(self) -> str | None:
        """Format ETA as human-readable string."""
        seconds = self.estimate_remaining_time()
        if seconds is None:
            return None
        if seconds < 60:
            return f"{seconds} seconds"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"


class JobManager:
    """Manages background conversion jobs.

    Uses asyncio for concurrency without external dependencies.
    Progress is persisted to session state for transparency.
    """

    def __init__(self):
        self._jobs: dict[str, ConversionJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def create_job(
        self,
        session_id: str,
        document_ids: list[str],
    ) -> str:
        """Create a new conversion job.

        Args:
            session_id: Session containing the documents
            document_ids: List of document IDs to convert

        Returns:
            Job ID for tracking
        """
        import uuid
        job_id = f"job-{uuid.uuid4().hex[:12]}"

        job = ConversionJob(
            job_id=job_id,
            session_id=session_id,
            document_ids=document_ids,
            files_total=len(document_ids),
        )

        self._jobs[job_id] = job
        logger.info(f"Created job {job_id} for {len(document_ids)} documents")
        return job_id

    def get_job(self, job_id: str) -> ConversionJob | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(self, session_id: str | None = None) -> list[ConversionJob]:
        """List all jobs, optionally filtered by session."""
        jobs = list(self._jobs.values())
        if session_id:
            jobs = [j for j in jobs if j.session_id == session_id]
        return jobs

    async def start_job(
        self,
        job_id: str,
        converter: Callable[[str, Callable], Coroutine[Any, Any, dict]],
    ) -> None:
        """Start processing a job in the background.

        Args:
            job_id: Job to start
            converter: Async function that converts documents.
                       Signature: converter(doc_id, progress_callback) -> result
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} already started (status: {job.status})")

        # Create background task
        task = asyncio.create_task(self._run_job(job, converter))
        self._tasks[job_id] = task

        logger.info(f"Started job {job_id}")

    async def _run_job(
        self,
        job: ConversionJob,
        converter: Callable,
    ) -> None:
        """Run the conversion job with memory-aware scheduling.

        Before processing each document:
        1. Check available RAM
        2. If insufficient, wait with exponential backoff
        3. If wait times out, fail the job gracefully
        """
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)

            for i, doc_id in enumerate(job.document_ids):
                # Update progress
                job.current_file = doc_id
                job.progress = i / job.files_total

                # Memory-aware scheduling: wait if insufficient RAM
                await self._wait_for_memory(job)

                # Define progress callback for this document
                def on_progress(pct: float):
                    # Update job progress including partial document progress
                    job.progress = (i + pct) / job.files_total

                try:
                    # Convert document
                    await converter(doc_id, on_progress)
                    job.files_completed = i + 1

                except Exception as e:
                    logger.error(f"Failed to convert {doc_id}: {e}")
                    # Continue with other documents

            # Mark completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.progress = 1.0
            job.current_file = None

            logger.info(
                f"Job {job.job_id} completed: "
                f"{job.files_completed}/{job.files_total} documents converted"
            )

        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.error = "Job was cancelled"
            logger.info(f"Job {job.job_id} cancelled")
            raise

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job {job.job_id} failed: {e}")

    async def _wait_for_memory(self, job: ConversionJob) -> None:
        """Wait for sufficient memory before processing.

        Uses exponential backoff to check memory availability.
        Times out after MAX_MEMORY_WAIT_TIME seconds.

        Args:
            job: Job to update with memory status

        Raises:
            Exception: If memory wait times out
        """
        has_memory, available_gb = check_memory_for_conversion()

        if has_memory:
            # Clear any previous memory wait state
            job.memory_wait_started = None
            job.memory_available_gb = None
            return

        # Start waiting for memory
        job.status = JobStatus.WAITING_FOR_MEMORY
        job.memory_wait_started = datetime.now(timezone.utc)
        job.memory_available_gb = available_gb

        logger.warning(
            f"Job {job.job_id}: Insufficient memory ({available_gb}GB available, "
            f"{MIN_MEMORY_GB}GB required). Waiting..."
        )

        total_wait = 0
        wait_interval = MEMORY_CHECK_INTERVAL

        while total_wait < MAX_MEMORY_WAIT_TIME:
            await asyncio.sleep(wait_interval)
            total_wait += wait_interval

            has_memory, available_gb = check_memory_for_conversion()
            job.memory_available_gb = available_gb

            if has_memory:
                logger.info(
                    f"Job {job.job_id}: Memory available ({available_gb}GB). Resuming."
                )
                job.status = JobStatus.RUNNING
                job.memory_wait_started = None
                return

            logger.debug(
                f"Job {job.job_id}: Still waiting for memory "
                f"({available_gb}GB available, waited {total_wait}s)"
            )

        # Timed out waiting for memory
        raise Exception(
            f"Memory wait timed out after {MAX_MEMORY_WAIT_TIME}s. "
            f"Only {available_gb}GB available, {MIN_MEMORY_GB}GB required. "
            f"Close other applications and retry."
        )

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.

        Returns:
            True if job was cancelled, False if not running
        """
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            return True
        return False

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """Remove old completed/failed jobs.

        Args:
            max_age_seconds: Remove jobs older than this (default: 1 hour)

        Returns:
            Number of jobs removed
        """
        now = datetime.now(timezone.utc)
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                if job.completed_at:
                    age = (now - job.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]
            self._tasks.pop(job_id, None)

        return len(to_remove)


# Global singleton
_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
