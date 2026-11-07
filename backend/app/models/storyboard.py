from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.base import BaseDocument


class ShotType(str, Enum):
    EXTREME_WIDE = "extreme_wide"
    WIDE = "wide"
    MEDIUM_WIDE = "medium_wide"
    MEDIUM = "medium"
    MEDIUM_CLOSE_UP = "medium_close_up"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    POV = "point_of_view"
    OVER_THE_SHOULDER = "over_the_shoulder"


class CameraAngle(str, Enum):
    EYE_LEVEL = "eye_level"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    DUTCH_ANGLE = "dutch_angle"
    BIRDS_EYE = "birds_eye"
    GROUND_LEVEL = "ground_level"


class CameraMovement(str, Enum):
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    ORBIT = "orbit"
    CRANE = "crane"
    HANDHELD = "handheld_organic"


class AspectRatio(str, Enum):
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    SQUARE = "1:1"
    CINEMATIC = "2.39:1"


class CameraSpecs(BaseModel):
    """Cinematic camera and visual parameters."""
    shot_type: ShotType = ShotType.MEDIUM
    camera_angle: CameraAngle = CameraAngle.EYE_LEVEL
    movement: CameraMovement = CameraMovement.STATIC
    lens: str = Field(default="35mm cinematic lens", description="Lens specification e.g. 24mm, 50mm, 85mm anamorphic")
    depth_of_field: str = Field(default="shallow depth of field", description="Depth of field e.g. shallow, deep focus")
    lighting: str = Field(default="cinematic natural light", description="Lighting atmosphere e.g. volumetric rays, rim lighting")


class CharacterProfile(BaseModel):
    """Character definition for visual consistency across scenes."""
    name: str
    appearance: str = Field(..., description="Facial features, hair, build, age")
    outfit: str = Field(..., description="Clothing, accessories, color palette")
    consistency_tags: List[str] = Field(default_factory=list, description="Keyword anchors used across all prompts")


class StoryboardScene(BaseModel):
    """A detailed filmable scene specification."""
    scene_number: int
    title: str
    duration_seconds: int = 5
    script_scene_number: Optional[int] = None
    action_description: str
    narration_cue: Optional[str] = None
    camera: CameraSpecs
    characters_present: List[str] = Field(default_factory=list)
    environment: str = Field(..., description="Setting, location, weather, time of day")
    visual_prompt: str = Field(..., description="Rich diffusion prompt for video generation (Runway/Pika/Luma)")
    negative_prompt: str = Field(
        default="blurry, distorted, low quality, artifacts, text, watermark, deformed limbs",
        description="Elements to avoid in video generation"
    )
    motion_strength: int = Field(default=5, ge=1, le=10, description="Amount of motion in the shot (1-10)")
    transition_to_next: str = "cut"


class Storyboard(BaseDocument):
    """Full storyboard document stored in MongoDB."""
    project_id: str
    script_id: str
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE
    visual_theme: str = "cinematic, photorealistic, 8k resolution"
    characters: List[CharacterProfile] = Field(default_factory=list)
    scenes: List[StoryboardScene]
    total_scenes: int
    total_duration_seconds: int


# ---- API Request / Response Schemas ----

class StoryboardGenerateRequest(BaseModel):
    project_id: str
    script_id: str
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE
    visual_theme: Optional[str] = None


class StoryboardSceneUpdate(BaseModel):
    action_description: Optional[str] = None
    visual_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    motion_strength: Optional[int] = Field(None, ge=1, le=10)
    camera: Optional[CameraSpecs] = None


class PromptRegenerateRequest(BaseModel):
    additional_guidance: Optional[str] = None
