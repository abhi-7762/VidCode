from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.base import BaseDocument


class ScriptTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    HUMOROUS = "humorous"
    DRAMATIC = "dramatic"


class ScriptStyle(str, Enum):
    NARRATION = "narration"
    DIALOGUE = "dialogue"
    DOCUMENTARY = "documentary"
    TUTORIAL = "tutorial"
    STORYTELLING = "storytelling"


class NLUAnalysis(BaseModel):
    """Extracted intent from the user's raw prompt."""
    topic: str
    genre: str
    tone: ScriptTone
    style: ScriptStyle
    target_audience: str
    key_messages: List[str]
    suggested_duration_seconds: int
    visual_style: str
    mood: str
    language: str = "English"
    confidence: float = Field(ge=0.0, le=1.0)


class ScriptScene(BaseModel):
    """A single scene in the generated script."""
    scene_number: int
    title: str
    duration_seconds: int
    narration: Optional[str] = None
    dialogue: Optional[str] = None
    action: str                   # What's happening visually
    emotion: str
    transition: str = "cut"       # cut, fade, dissolve, wipe


class Script(BaseDocument):
    """Full generated script stored in MongoDB."""
    project_id: str
    raw_prompt: str
    nlu_analysis: NLUAnalysis
    title: str
    logline: str                  # One-sentence story summary
    hook: str                     # Opening hook (first 5 seconds)
    scenes: List[ScriptScene]
    call_to_action: Optional[str] = None
    total_duration_seconds: int
    word_count: int
    gemini_model: str = "gemini-1.5-pro"
    generation_tokens: int = 0


# ---- Request / Response ----

class ScriptGenerateRequest(BaseModel):
    project_id: str
    prompt: str = Field(..., min_length=10, max_length=5000)
    duration_seconds: int = Field(default=60, ge=10, le=600)
    tone: Optional[ScriptTone] = None
    style: Optional[ScriptStyle] = None
    target_audience: Optional[str] = None


class ScriptResponse(BaseModel):
    id: str
    project_id: str
    title: str
    logline: str
    hook: str
    scenes: List[ScriptScene]
    call_to_action: Optional[str]
    total_duration_seconds: int
    word_count: int
    nlu_analysis: NLUAnalysis
    created_at: str

