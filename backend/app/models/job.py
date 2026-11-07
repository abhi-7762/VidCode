from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from app.models.base import BaseDocument


class JobType(str, Enum):
    SCRIPT_GENERATION = "script_generation"
    STORYBOARD_GENERATION = "storyboard_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    FINAL_RENDER = "final_render"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Job(BaseDocument):
    """Tracks every async Celery task."""
    project_id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    celery_task_id: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: JobType
    status: JobStatus
    progress: int
    error_message: Optional[str]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

