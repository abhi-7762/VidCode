from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.base import BaseDocument


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectSettings(BaseModel):
    """User-configurable generation settings."""
    duration_seconds: int = Field(default=60, ge=10, le=600)
    resolution: str = Field(default="1080p", pattern=r"^(720p|1080p|4K)$")
    style: str = Field(default="cinematic")
    voice_id: Optional[str] = None
    background_music: bool = True
    subtitles: bool = True


class Project(BaseDocument):
    """Core project document stored in MongoDB."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    prompt: str = Field(..., min_length=10, max_length=5000)
    status: ProjectStatus = ProjectStatus.DRAFT
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    tags: List[str] = Field(default_factory=list)
    # Links filled in by later phases
    script_id: Optional[str] = None
    storyboard_id: Optional[str] = None
    output_video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_actual: Optional[float] = None


# ---- Request / Response schemas ----

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    prompt: str = Field(..., min_length=10, max_length=5000)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    tags: List[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    settings: Optional[ProjectSettings] = None
    tags: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    prompt: str
    status: ProjectStatus
    settings: ProjectSettings
    tags: List[str]
    created_at: str
    updated_at: str
    output_video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    model_config = {"from_attributes": True}

