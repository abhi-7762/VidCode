from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.base import BaseDocument


class ValidationResult(BaseModel):
    """Technical health and metadata validation of a rendered video file."""
    file_exists: bool
    is_valid: bool
    format_name: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    video_codec: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    has_audio: bool = False
    audio_codec: Optional[str] = None
    issues: List[str] = Field(default_factory=list)


class VisualQualityCheck(BaseModel):
    """Gemini-powered aesthetic and consistency review of storyboard scenes."""
    overall_aesthetic_score: float = Field(ge=0.0, le=10.0)
    character_consistency_score: float = Field(ge=0.0, le=10.0)
    cinematography_score: float = Field(ge=0.0, le=10.0)
    scene_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    detected_flaws: List[str] = Field(default_factory=list)
    optimization_recommendations: List[str] = Field(default_factory=list)


class CostEstimate(BaseModel):
    """Cost breakdown across Gemini, Video Generation, and Voice engines."""
    project_id: str
    gemini_tokens: int
    gemini_cost_usd: float
    tts_characters: int
    tts_cost_usd: float
    video_seconds: float
    video_cost_usd: float
    total_estimated_cost_usd: float
    cost_saving_recommendations: List[str] = Field(default_factory=list)


class VideoVersion(BaseDocument):
    """Discrete version record for project renders (v1, v2, v3)."""
    project_id: str
    version_number: int
    label: str = "Initial Render"
    video_path: str
    video_url: str
    duration_seconds: float
    file_size_bytes: int
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpliceSceneRequest(BaseModel):
    project_id: str
    storyboard_id: str
    scene_number: int
    new_prompt: Optional[str] = None
    version_label: Optional[str] = "Spliced Scene Update"

