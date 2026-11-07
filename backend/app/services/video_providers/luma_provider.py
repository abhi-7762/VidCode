import httpx
from typing import Optional, Dict, Any
from app.config import get_settings
from app.services.video_providers.base import BaseVideoProvider

settings = get_settings()


class LumaVideoProvider(BaseVideoProvider):
    """
    Luma Dream Machine API Integration.
    Docs: https://lumalabs.ai/dream-machine/api/
    """
    BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

    def __init__(self, api_key: Optional[str] = None):
        # Can be set via environment or passed directly
        self.api_key = api_key or getattr(settings, "luma_api_key", "")

    @property
    def provider_name(self) -> str:
        return "luma"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json",
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
            raise ValueError("LUMA_API_KEY is not configured in environment")

        payload = {
            "prompt": prompt,
            "aspect_ratio": "16:9" if "16:9" in aspect_ratio else "9:16",
            "loop": False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/generations",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["id"]

    async def poll_status(self, external_task_id: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("LUMA_API_KEY is not configured in environment")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/generations/{external_task_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        state = data.get("state", "").lower()
        status_map = {
            "queued": "queued",
            "dreaming": "processing",
            "completed": "completed",
            "failed": "failed",
        }
        status = status_map.get(state, "processing")
        progress = 100 if status == "completed" else (50 if status == "processing" else 10)

        assets = data.get("assets", {})
        video_url = assets.get("video")
        error = data.get("failure_reason")

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
