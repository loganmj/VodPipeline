"""Internal state management for tracking the current job."""
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class JobState:
    """
    Internal state object for tracking the current job.
    
    This is the authoritative in-memory representation of the current job,
    used to respond to status requests.
    """
    job_id: Optional[str]
    file_name: Optional[str]
    stage: str
    percent: int
    started_at: Optional[datetime]
    last_updated_at: datetime
    error_message: Optional[str]
    is_running: bool
    
    def to_dict(self) -> dict:
        """
        Convert JobState to a dictionary suitable for JSON serialization.
        
        Returns:
            dict: Dictionary representation with ISO format timestamps (Z suffix)
        """
        return {
            "jobId": self.job_id,
            "fileName": self.file_name,
            "stage": self.stage,
            "percent": self.percent,
            "timestamp": self.last_updated_at.isoformat().replace('+00:00', 'Z'),
            "errorMessage": self.error_message
        }


class JobStateManager:
    """
    Thread-safe singleton manager for job state.
    
    This manager maintains the internal state of the current job and provides
    methods to update it as the job progresses.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._state_lock = threading.Lock()
        self._state = JobState(
            job_id=None,
            file_name=None,
            stage="Idle",
            percent=0,
            started_at=None,
            last_updated_at=datetime.now(timezone.utc),
            error_message=None,
            is_running=False
        )
        self._initialized = True
    
    def get_state(self) -> JobState:
        """
        Get a snapshot of the current state.
        
        Returns:
            JobState: A copy of the current state
        """
        with self._state_lock:
            # Create a copy to avoid race conditions
            return JobState(
                job_id=self._state.job_id,
                file_name=self._state.file_name,
                stage=self._state.stage,
                percent=self._state.percent,
                started_at=self._state.started_at,
                last_updated_at=self._state.last_updated_at,
                error_message=self._state.error_message,
                is_running=self._state.is_running
            )
    
    def start_job(self, job_id: str, file_name: str) -> None:
        """
        Update state when a job starts.
        
        Args:
            job_id: Unique job identifier
            file_name: Name of the file being processed
        """
        with self._state_lock:
            now = datetime.now(timezone.utc)
            self._state.job_id = job_id
            self._state.file_name = file_name
            self._state.stage = "Starting"
            self._state.percent = 0
            self._state.started_at = now
            self._state.last_updated_at = now
            self._state.error_message = None
            self._state.is_running = True
    
    def update_stage(self, stage: str, percent: int) -> None:
        """
        Update state when the stage changes.
        
        Args:
            stage: New stage name
            percent: Current progress percentage
        """
        with self._state_lock:
            self._state.stage = stage
            self._state.percent = percent
            self._state.last_updated_at = datetime.now(timezone.utc)
    
    def update_progress(self, percent: int) -> None:
        """
        Update state when progress changes.
        
        Args:
            percent: Current progress percentage
        """
        with self._state_lock:
            self._state.percent = percent
            self._state.last_updated_at = datetime.now(timezone.utc)
    
    def complete_job(self) -> None:
        """Update state when a job completes successfully."""
        with self._state_lock:
            self._state.stage = "Completed"
            self._state.percent = 100
            self._state.last_updated_at = datetime.now(timezone.utc)
            self._state.is_running = False
    
    def fail_job(self, error_message: str) -> None:
        """
        Update state when a job fails.
        
        Args:
            error_message: Error message describing the failure
        """
        with self._state_lock:
            self._state.stage = "Failed"
            self._state.error_message = error_message
            self._state.last_updated_at = datetime.now(timezone.utc)
            self._state.is_running = False
    
    def reset_to_idle(self) -> None:
        """Reset state to idle when no job is running."""
        with self._state_lock:
            self._state.job_id = None
            self._state.file_name = None
            self._state.stage = "Idle"
            self._state.percent = 0
            self._state.started_at = None
            self._state.last_updated_at = datetime.now(timezone.utc)
            self._state.error_message = None
            self._state.is_running = False
