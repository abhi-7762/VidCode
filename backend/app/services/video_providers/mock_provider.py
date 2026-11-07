import uuid
import asyncio
from typing import Optional, Dict, Any
from app.services.video_providers.base import BaseVideoProvider


# Minimal valid MP4 container binary payload (silent 1-second blank test clip)
MINIMAL_VALID_MP4 = (
    b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free"
    b"\x00\x00\x00\xb4mdat\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x6cmoov\x00\x00\x00\x64mvhd\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x03\xe8\x00\x00\x03\xe8\x00\x01\x00\x00\x01\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02"
)


class MockVideoProvider(BaseVideoProvider):
    """
    Mock AI Video Provider.
    Simulates high-end video generation without incurring API costs.
    Generates valid MP4 media for local development, CI/CD, and offline testing.
    """

    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return "mock"

    async def submit_prompt(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
        motion_strength: int = 5,
    ) -> str:
        task_id = f"mock_{uuid.uuid4().hex[:12]}"
        self._tasks[task_id] = {
            "status": "completed",
            "progress": 100,
            "video_url": f"https://mock-storage.vidcode.ai/clips/{task_id}.mp4",
            "error": None,
        }
        return task_id

    async def poll_status(self, external_task_id: str) -> Dict[str, Any]:
        task = self._tasks.get(external_task_id)
        if not task:
            return {
                "status": "completed",
                "progress": 100,
                "video_url": f"https://mock-storage.vidcode.ai/clips/{external_task_id}.mp4",
                "error": None,
            }
        return task

    async def fetch_video_bytes(self, video_url: str) -> bytes:
        return MINIMAL_VALID_MP4
