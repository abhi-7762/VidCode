"""
Phase 4 Celery tasks — parallel video clip generation and batch job tracking.
"""
import asyncio
from app.celery_app import celery_app
from app.models.video import GenerateClipsRequest, VideoProviderType


@celery_app.task(bind=True, name="tasks.generate_video_clips", max_retries=3)
def generate_video_clips(
    self,
    project_id: str,
    storyboard_id: str,
    provider: str = "mock",
    scene_numbers: list = None,
):
    """
    Celery task that orchestrates parallel clip generation for storyboard scenes.
    Reports progress back to the Celery backend.
    """
    try:
        self.update_state(state="PROGRESS", meta={"progress": 15, "step": "Initializing video generation..."})

        from app.services.video_service import VideoService

        request = GenerateClipsRequest(
            project_id=project_id,
            storyboard_id=storyboard_id,
            provider=VideoProviderType(provider),
            scene_numbers=scene_numbers,
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            service = VideoService()
            self.update_state(state="PROGRESS", meta={"progress": 40, "step": "Generating scene clips..."})
            clips = loop.run_until_complete(service.generate_clips_for_storyboard(request))
        finally:
            loop.close()

        self.update_state(state="PROGRESS", meta={"progress": 100, "step": "All clips generated successfully."})

        return {
            "status": "completed",
            "project_id": project_id,
            "storyboard_id": storyboard_id,
            "clips_generated": len(clips),
            "clip_ids": [c.get("_id") for c in clips],
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=15)
