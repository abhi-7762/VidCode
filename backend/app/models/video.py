from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.base import BaseDocument


class VideoProviderType(str, Enum):
    MOCK = "mock"
    RUNWAY = "runway"
    LUMA = "luma"
    PIKA = "pika"


class ClipStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class VideoClip(BaseDocument):
    """Document representing an individual AI-generated video clip for a scene."""
    project_id: str
    storyboard_id: str
    scene_number: int
    provider: VideoProviderType = VideoProviderType.MOCK
    external_task_id: Optional[str] = None
    status: ClipStatus = ClipStatus.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    prompt_used: str
    negative_prompt_used: Optional[str] = None
    video_url: Optional[str] = None
    local_file_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: float = 5.0
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


# ---- Request & Response Schemas ----

class GenerateClipsRequest(BaseModel):
    project_id: str
    storyboard_id: str
    provider: VideoProviderType = VideoProviderType.MOCK
    scene_numbers: Optional[List[int]] = Field(
        default=None,
        description="Specific scenes to generate. If omitted, generates all scenes in storyboard."
    )


class RegenerateClipRequest(BaseModel):
    prompt_override: Optional[str] = None
    negative_prompt_override: Optional[str] = None
    provider: Optional[VideoProviderType] = None


class VideoClipResponse(BaseModel):
    id: str
    project_id: str
    storyboard_id: str
    scene_number: int
    provider: VideoProviderType
    status: ClipStatus
    progress: int
    prompt_used: str
    video_url: Optional[str] = None
    duration_seconds: float
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BatchClipsResponse(BaseModel):
    project_id: str
    storyboard_id: str
    total_clips: int
    clips: List[Dict[str, Any]]
