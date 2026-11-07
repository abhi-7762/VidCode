from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseVideoProvider(ABC):
    """Abstract interface for AI video generation engines (Runway, Luma, Pika, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the provider."""
        pass

    @abstractmethod
    async def submit_prompt(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
        motion_strength: int = 5,
    ) -> str:
        """
        Submits the generation job to the provider API.
        Returns external_task_id.
        """
        pass

    @abstractmethod
    async def poll_status(self, external_task_id: str) -> Dict[str, Any]:
        """
        Checks status of the submitted task.
        Returns:
            {
                "status": "queued" | "processing" | "completed" | "failed",
                "progress": 0-100,
                "video_url": Optional[str],
                "error": Optional[str]
            }
        """
        pass

    @abstractmethod
    async def fetch_video_bytes(self, video_url: str) -> bytes:
        """Downloads the rendered video bytes."""
        pass

