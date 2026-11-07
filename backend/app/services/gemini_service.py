"""
Gemini AI Service — the core intelligence layer of VidCode.

Responsibilities:
  - Connect to Google Gemini API
  - Natural Language Understanding (NLU) of user prompts
  - Script generation with structured JSON output
  - Story arc planning
  - Retry / error handling
"""

import json
import re
import logging
from typing import Optional
import google.generativeai as genai

from app.config import get_settings
from app.models.script import (
    NLUAnalysis, Script, ScriptScene, ScriptTone, ScriptStyle,
    ScriptGenerateRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _init_gemini() -> genai.GenerativeModel:
    """Configure and return Gemini model instance."""
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8192,
        ),
    )


def _extract_json(text: str) -> dict:
    """
    Robustly extract JSON from Gemini's response.
    Handles markdown code fences and plain JSON.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Find the outermost {...}
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in Gemini response")
    return json.loads(text[start:end])


class GeminiService:
    """All interactions with the Gemini API."""

    def __init__(self):
        self.model = _init_gemini()

    # ------------------------------------------------------------------
    # 1. Natural Language Understanding
    # ------------------------------------------------------------------
    async def analyse_prompt(self, prompt: str, duration_seconds: int) -> NLUAnalysis:
        """
        Extract structured intent from a raw user prompt.
        Returns NLUAnalysis with topic, tone, style, audience, etc.
        """
        system = f"""You are an expert video content strategist and AI director.
Analyse the user's video idea and return ONLY valid JSON with this exact structure:
{{
  "topic": "main subject of the video",
  "genre": "e.g. educational, marketing, entertainment, documentary",
  "tone": one of ["professional","casual","educational","inspirational","humorous","dramatic"],
  "style": one of ["narration","dialogue","documentary","tutorial","storytelling"],
  "target_audience": "description of ideal viewers",
  "key_messages": ["message 1", "message 2", "message 3"],
  "suggested_duration_seconds": {duration_seconds},
  "visual_style": "e.g. cinematic, minimalist, vibrant, dark",
  "mood": "e.g. uplifting, tense, calm, energetic",
  "language": "English",
  "confidence": 0.95
}}
No extra text. Only JSON."""

        response = self.model.generate_content([system, f"User prompt: {prompt}"])
        data = _extract_json(response.text)
        return NLUAnalysis(**data)

    # ------------------------------------------------------------------
    # 2. Script Generation
    # ------------------------------------------------------------------
    async def generate_script(self, request: ScriptGenerateRequest, nlu: NLUAnalysis) -> dict:
        """
        Generate a full video script from NLU analysis.
        Returns a dict ready to be saved as a Script document.
        """
        scenes_count = max(3, request.duration_seconds // 15)  # ~15s per scene

        system = f"""You are a world-class video scriptwriter working for VidCode AI.
Create a complete, engaging video script based on the analysis below.

REQUIREMENTS:
- Target duration: {request.duration_seconds} seconds total
- Number of scenes: approximately {scenes_count}
- Tone: {nlu.tone}
- Style: {nlu.style}
- Target audience: {nlu.target_audience}
- Key messages to cover: {', '.join(nlu.key_messages)}
- Visual style: {nlu.visual_style}

Return ONLY valid JSON with this exact structure:
{{
  "title": "compelling video title",
  "logline": "one sentence that captures the entire video",
  "hook": "first 5-second hook to grab attention",
  "call_to_action": "what should the viewer do after watching",
  "total_duration_seconds": {request.duration_seconds},
  "word_count": 0,
  "scenes": [
    {{
      "scene_number": 1,
      "title": "scene title",
      "duration_seconds": 15,
      "narration": "exact narration text spoken by voiceover",
      "dialogue": null,
      "action": "detailed description of what is happening visually on screen",
      "emotion": "the dominant emotion of this scene",
      "transition": "cut"
    }}
  ]
}}
Make each scene vivid, specific, and cinematically interesting. No extra text. Only JSON."""

        prompt_text = f"""Topic: {nlu.topic}
Genre: {nlu.genre}
Original idea: {request.prompt}"""

        response = self.model.generate_content([system, prompt_text])

        data = _extract_json(response.text)

        # Calculate word count from all narration + dialogue
        all_text = " ".join(
            (s.get("narration") or "") + " " + (s.get("dialogue") or "")
            for s in data.get("scenes", [])
        )
        data["word_count"] = len(all_text.split())

        return data

    # ------------------------------------------------------------------
    # 3. Script Improvement / Rewrite
    # ------------------------------------------------------------------
    async def improve_script(self, script_data: dict, feedback: str) -> dict:
        """Rewrite an existing script based on user feedback."""
        system = """You are a senior video scriptwriter. 
Improve the provided script based on the user's feedback.
Return the COMPLETE improved script in the same JSON format. Only JSON."""

        prompt_text = f"""USER FEEDBACK: {feedback}

CURRENT SCRIPT:
{json.dumps(script_data, indent=2)}"""

        response = self.model.generate_content([system, prompt_text])
        return _extract_json(response.text)

    # ------------------------------------------------------------------
    # 4. Story Arc Suggestions
    # ------------------------------------------------------------------
    async def suggest_story_structures(self, topic: str, duration: int) -> list:
        """Generate 3 different story structure options for a topic."""
        system = """You are a creative video director. 
Suggest 3 different narrative structures for the given topic.
Return ONLY valid JSON: {"structures": [{"name": "...", "description": "...", "acts": ["act1", "act2", "act3"]}]}"""

        response = self.model.generate_content([
            system,
            f"Topic: {topic}, Duration: {duration} seconds"
        ])
        data = _extract_json(response.text)
        return data.get("structures", [])
