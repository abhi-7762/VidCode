from typing import Dict, Any, List
from bson import ObjectId
from fastapi import HTTPException

from app.database import get_db
from app.models.quality import CostEstimate


class CostService:
    """Calculates AI resource consumption, token costs, and optimization recommendations."""

    # Industry standard API pricing
    GEMINI_INPUT_PER_1K = 0.00125
    GEMINI_OUTPUT_PER_1K = 0.005
    RUNWAY_COST_PER_SEC = 0.05
    LUMA_COST_PER_SEC = 0.06
    ELEVENLABS_PER_1K_CHARS = 0.30

    async def calculate_project_cost(self, project_id: str) -> CostEstimate:
        """Estimates and aggregates total API expenses incurred or projected for a project."""
        db = get_db()
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project ID")

        project = await db["projects"].find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. Script & Gemini Tokens
        script = await db["scripts"].find_one({"project_id": project_id})
        words = script.get("word_count", 150) if script else 150
        est_tokens = int(words * 4.5)  # prompt + response tokens
        gemini_cost = (est_tokens / 1000.0) * ((self.GEMINI_INPUT_PER_1K + self.GEMINI_OUTPUT_PER_1K) / 2.0)

        # 2. Voice Narration Characters
        narration_text = ""
        if script:
            narration_text = " ".join((s.get("narration") or "") for s in script.get("scenes", []))
        tts_chars = len(narration_text) if narration_text else (words * 6)
        tts_cost = 0.0  # Default Edge-TTS is free ($0.00)

        # 3. Video Clip Generation
        clips_cursor = db["video_clips"].find({"project_id": project_id})
        clips = [c async for c in clips_cursor]
        total_video_secs = sum(c.get("duration_seconds", 5.0) for c in clips)
        if not clips and script:
            total_video_secs = float(script.get("total_duration_seconds", 60.0))

        # Check if Runway or Mock was selected
        has_runway = any(c.get("provider") == "runway" for c in clips)
        video_cost = (total_video_secs * self.RUNWAY_COST_PER_SEC) if has_runway else 0.0

        total_cost = round(gemini_cost + tts_cost + video_cost, 4)

        recommendations = [
            "Use built-in Edge-TTS to eliminate voiceover expenses entirely ($0.00 vs ElevenLabs $0.30/1k chars).",
            "Target 4-6 second scene lengths to maximize video diffusion fidelity and minimize credit burn.",
            "Use Mock provider during early storyboard drafting and test renders before switching to cloud diffusion.",
        ]

        return CostEstimate(
            project_id=project_id,
            gemini_tokens=est_tokens,
            gemini_cost_usd=round(gemini_cost, 4),
            tts_characters=tts_chars,
            tts_cost_usd=round(tts_cost, 4),
            video_seconds=total_video_secs,
            video_cost_usd=round(video_cost, 4),
            total_estimated_cost_usd=total_cost,
            cost_saving_recommendations=recommendations,
        )

