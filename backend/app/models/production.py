from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.base import BaseDocument


class VoiceProviderType(str, Enum):
    EDGETTS = "edge_tts"
    ELEVENLABS = "elevenlabs"
    MOCK = "mock"


class SubtitleFormat(str, Enum):
    SRT = "srt"
    VTT = "vtt"


class VideoResolution(str, Enum):
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_4K = "4K"


class ProductionSettings(BaseModel):
    """Configuration for final assembly and rendering."""
    voice_provider: VoiceProviderType = VoiceProviderType.EDGETTS
    voice_name: str = "en-US-ChristopherNeural"  # Default expressive neural voice
    include_voiceover: bool = True
    include_subtitles: bool = True
    subtitle_format: SubtitleFormat = SubtitleFormat.SRT
    background_music_enabled: bool = False
    background_music_volume: float = Field(default=0.15, ge=0.0, le=1.0)
    voice_volume: float = Field(default=1.0, ge=0.0, le=2.0)
    resolution: VideoResolution = VideoResolution.RES_1080P
    fps: int = Field(default=30, ge=24, le=60)


class RenderStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderJob(BaseDocument):
    """Document tracking the final video production pipeline."""
    project_id: str
    storyboard_id: str
    status: RenderStatus = RenderStatus.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = "Queued"
    settings: ProductionSettings = Field(default_factory=ProductionSettings)
    output_video_path: Optional[str] = None
    output_video_url: Optional[str] = None
    voiceover_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None


# ---- API Request / Response Schemas ----

class StartRenderRequest(BaseModel):
    project_id: str
    storyboard_id: str
    settings: Optional[ProductionSettings] = None


class RenderJobResponse(BaseModel):
    id: str
    project_id: str
    storyboard_id: str
    status: RenderStatus
    progress: int
    current_step: str
    output_video_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class VoiceInfo(BaseModel):
    id: str
    name: str
    language: str
    gender: str
    provider: VoiceProviderType
