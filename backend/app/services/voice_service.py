import os
import httpx
from pathlib import Path
from typing import List, Optional
import edge_tts

from app.config import get_settings
from app.models.production import VoiceInfo, VoiceProviderType

settings = get_settings()

# Silent MP3 binary header for mock/offline testing
MOCK_SILENT_MP3 = (
    b"\xff\xfb\x90\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)

POPULAR_VOICES = [
    VoiceInfo(id="en-US-ChristopherNeural", name="Christopher (Authoritative, Deep)", language="English (US)", gender="Male", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-US-JennyNeural", name="Jenny (Engaging, Clear)", language="English (US)", gender="Female", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-US-GuyNeural", name="Guy (Conversational, Casual)", language="English (US)", gender="Male", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-US-AriaNeural", name="Aria (Expressive, Warm)", language="English (US)", gender="Female", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-GB-RyanNeural", name="Ryan (Sophisticated British)", language="English (UK)", gender="Male", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-GB-SoniaNeural", name="Sonia (Polished British)", language="English (UK)", gender="Female", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="en-AU-WilliamNeural", name="William (Australian Friendly)", language="English (AU)", gender="Male", provider=VoiceProviderType.EDGETTS),
    VoiceInfo(id="mock-narrator", name="Mock Studio Voice", language="English", gender="Neutral", provider=VoiceProviderType.MOCK),
]


class VoiceService:
    """Manages AI Voiceover generation using Edge-TTS, ElevenLabs, or Mock."""

    def get_available_voices(self) -> List[VoiceInfo]:
        """Returns catalogue of high-quality neural voices."""
        return POPULAR_VOICES

    async def generate_narration(
        self,
        text: str,
        output_file: Path,
        voice_name: str = "en-US-ChristopherNeural",
        provider: VoiceProviderType = VoiceProviderType.EDGETTS,
    ) -> Path:
        """Generates narration audio and writes to output_file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if not text or not text.strip():
            # If text is empty, write minimal silent audio
            output_file.write_bytes(MOCK_SILENT_MP3)
            return output_file

        if provider == VoiceProviderType.MOCK:
            output_file.write_bytes(MOCK_SILENT_MP3)
            return output_file

        if provider == VoiceProviderType.ELEVENLABS and settings.elevenlabs_api_key:
            return await self._generate_elevenlabs(text, output_file, voice_name)

        # Default: Neural Edge-TTS (No API key needed, zero latency, free)
        try:
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(str(output_file))
            return output_file
        except Exception as e:
            # Fallback to silent mock audio on network failure
            output_file.write_bytes(MOCK_SILENT_MP3)
            return output_file

    async def _generate_elevenlabs(self, text: str, output_file: Path, voice_id: str) -> Path:
        """Generate audio via ElevenLabs REST API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            output_file.write_bytes(resp.content)
            return output_file
