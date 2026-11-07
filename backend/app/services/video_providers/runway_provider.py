import httpx
from typing import Optional, Dict, Any
from app.config import get_settings
from app.services.video_providers.base import BaseVideoProvider

settings = get_settings()


class RunwayVideoProvider(BaseVideoProvider):
    """
    RunwayML Gen-3 Alpha API Integration.
    Docs: https://docs.dev.runwayml.com/
    """
    BASE_URL = "https://api.dev.runwayml.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.runway_api_key

    @property
    def provider_name(self) -> str:
        return "runway"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": "2024-11-06",
            "Content-Type": "application/json",
        }

    async def submit_prompt(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
        motion_strength: int = 5,
    ) -> str:
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY is not configured in environment")

        payload = {
            "promptText": prompt,
            "model": "gen3a_turbo",
            "duration": min(max(duration_seconds, 5), 10),
            "ratio": "16:9" if "16:9" in aspect_ratio else "9:16",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/image_to_video",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["id"]

    async def poll_status(self, external_task_id: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY is not configured in environment")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/tasks/{external_task_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        raw_status = data.get("status", "").upper()
        status_map = {
            "PENDING": "queued",
            "THROTTLED": "queued",
            "RUNNING": "processing",
            "SUCCEEDED": "completed",
            "FAILED": "failed",
            "CANCELLED": "failed",
        }
        status = status_map.get(raw_status, "processing")
        progress = int(data.get("progressRatio", 0.0) * 100)

        output_urls = data.get("output", [])
        video_url = output_urls[0] if output_urls else None
        error = data.get("failure") or data.get("failureCode")

        return {
            "status": status,
            "progress": progress,
            "video_url": video_url,
            "error": error,
        }

    async def fetch_video_bytes(self, video_url: str) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(video_url)
            resp.raise_for_status()
            return resp.content

